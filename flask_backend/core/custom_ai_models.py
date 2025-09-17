#!/usr/bin/env python3
"""
自定义AI大模型集成系统
支持本地模型、私有部署模型、以及各种兼容OpenAI格式的模型接入
实现人类级别的句子分析和理解能力
"""

import asyncio
import json
import logging
import time
import traceback
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import requests
import openai
from openai import AsyncOpenAI
from enum import Enum

# 本地模型支持
try:
    import torch
    import transformers
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
    LOCAL_MODEL_SUPPORT = True
except ImportError:
    LOCAL_MODEL_SUPPORT = False

logger = logging.getLogger(__name__)


class ModelProvider(Enum):
    """模型提供商类型"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    CUSTOM_API = "custom_api"
    LOCAL_HUGGINGFACE = "local_huggingface"
    OLLAMA = "ollama"
    XINFERENCE = "xinference"
    CHATGLM = "chatglm"
    QWEN = "qwen"
    BAICHUAN = "baichuan"


@dataclass
class ModelConfig:
    """模型配置"""
    name: str
    provider: ModelProvider
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_id: str = ""
    max_tokens: int = 4000
    temperature: float = 0.7
    timeout: int = 300
    support_json: bool = True
    custom_headers: Optional[Dict[str, str]] = None
    local_model_path: Optional[str] = None
    
    # 高级配置
    context_length: int = 4096
    batch_size: int = 1
    enable_streaming: bool = False
    enable_function_calling: bool = False
    
    # 性能配置
    enable_cache: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class AIAnalysisRequest:
    """AI分析请求"""
    text: str
    task_type: str  # 'semantic_split', 'content_analysis', 'emotion_analysis', etc.
    context: Optional[str] = None
    max_output_length: Optional[int] = None
    language: str = "zh"
    custom_prompt: Optional[str] = None


@dataclass
class AIAnalysisResult:
    """AI分析结果"""
    success: bool
    result: Any
    confidence: float
    processing_time: float
    model_used: str
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class CustomAIModelManager:
    """自定义AI模型管理器 - 统一管理各种AI模型"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.models: Dict[str, ModelConfig] = {}
        self.active_clients: Dict[str, Any] = {}
        
        # 预定义模型配置模板
        self.model_templates = self._initialize_model_templates()
        
        # 性能统计
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_processing_time": 0.0,
            "model_usage": {}
        }
        
        self.logger.info("🤖 自定义AI模型管理器初始化完成")
    
    def _initialize_model_templates(self) -> Dict[str, ModelConfig]:
        """初始化模型配置模板"""
        templates = {
            # OpenAI兼容模型
            "openai_compatible": ModelConfig(
                name="OpenAI兼容模型",
                provider=ModelProvider.CUSTOM_API,
                model_id="gpt-3.5-turbo",
                base_url="https://api.openai.com/v1",
                support_json=True,
                enable_function_calling=True
            ),
            
            # Ollama本地模型
            "ollama": ModelConfig(
                name="Ollama本地模型",
                provider=ModelProvider.OLLAMA,
                base_url="http://localhost:11434",
                model_id="llama2:7b",
                api_key=None,
                support_json=False
            ),
            
            # 智谱AI GLM
            "chatglm": ModelConfig(
                name="智谱AI ChatGLM",
                provider=ModelProvider.CHATGLM,
                base_url="https://open.bigmodel.cn/api/paas/v4",
                model_id="glm-4",
                support_json=True
            ),
            
            # 通义千问
            "qwen": ModelConfig(
                name="通义千问",
                provider=ModelProvider.QWEN,
                base_url="https://dashscope.aliyuncs.com/api/v1",
                model_id="qwen-turbo",
                support_json=True
            ),
            
            # 百川AI
            "baichuan": ModelConfig(
                name="百川AI",
                provider=ModelProvider.BAICHUAN,
                base_url="https://api.baichuan-ai.com/v1",
                model_id="Baichuan2-Turbo",
                support_json=True
            ),
            
            # XInference部署
            "xinference": ModelConfig(
                name="XInference部署",
                provider=ModelProvider.XINFERENCE,
                base_url="http://localhost:9997/v1",
                model_id="chatglm3-6b",
                support_json=True
            ),
            
            # 本地HuggingFace模型
            "local_huggingface": ModelConfig(
                name="本地HuggingFace模型",
                provider=ModelProvider.LOCAL_HUGGINGFACE,
                model_id="THUDM/chatglm3-6b",
                local_model_path="/path/to/model",
                api_key=None,
                base_url=None
            )
        }
        
        return templates
    
    def register_model(self, model_name: str, config: ModelConfig) -> bool:
        """注册新的AI模型"""
        try:
            # 验证配置
            if not self._validate_model_config(config):
                raise ValueError("模型配置验证失败")
            
            # 注册模型
            self.models[model_name] = config
            
            # 初始化客户端
            if self._initialize_client(model_name, config):
                self.logger.info(f"✅ 成功注册AI模型: {model_name}")
                return True
            else:
                self.logger.error(f"❌ 模型客户端初始化失败: {model_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 注册模型失败 {model_name}: {str(e)}")
            return False
    
    def _validate_model_config(self, config: ModelConfig) -> bool:
        """验证模型配置"""
        if not config.name or not config.model_id:
            return False
        
        if config.provider == ModelProvider.LOCAL_HUGGINGFACE:
            return LOCAL_MODEL_SUPPORT and config.local_model_path is not None
        
        if config.provider in [ModelProvider.CUSTOM_API, ModelProvider.OLLAMA]:
            return config.base_url is not None
        
        return True
    
    def _initialize_client(self, model_name: str, config: ModelConfig) -> bool:
        """初始化模型客户端"""
        try:
            if config.provider == ModelProvider.LOCAL_HUGGINGFACE:
                return self._init_local_model(model_name, config)
            elif config.provider == ModelProvider.OLLAMA:
                return self._init_ollama_client(model_name, config)
            elif config.provider in [ModelProvider.CUSTOM_API, ModelProvider.CHATGLM, ModelProvider.QWEN]:
                return self._init_openai_compatible_client(model_name, config)
            else:
                return self._init_generic_client(model_name, config)
                
        except Exception as e:
            self.logger.error(f"初始化客户端失败 {model_name}: {str(e)}")
            return False
    
    def _init_local_model(self, model_name: str, config: ModelConfig) -> bool:
        """初始化本地HuggingFace模型"""
        if not LOCAL_MODEL_SUPPORT:
            self.logger.error("本地模型支持库未安装")
            return False
        
        try:
            # 加载tokenizer和model
            tokenizer = AutoTokenizer.from_pretrained(
                config.local_model_path or config.model_id,
                trust_remote_code=True
            )
            model = AutoModelForCausalLM.from_pretrained(
                config.local_model_path or config.model_id,
                trust_remote_code=True,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )
            
            self.active_clients[model_name] = {
                'tokenizer': tokenizer,
                'model': model,
                'pipeline': pipeline(
                    "text-generation", 
                    model=model, 
                    tokenizer=tokenizer,
                    max_length=config.max_tokens
                )
            }
            
            return True
            
        except Exception as e:
            self.logger.error(f"本地模型初始化失败: {str(e)}")
            return False
    
    def _init_ollama_client(self, model_name: str, config: ModelConfig) -> bool:
        """初始化Ollama客户端"""
        try:
            # 测试连接
            response = requests.get(f"{config.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                self.active_clients[model_name] = {
                    'base_url': config.base_url,
                    'model_id': config.model_id
                }
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Ollama连接测试失败: {str(e)}")
            return False
    
    def _init_openai_compatible_client(self, model_name: str, config: ModelConfig) -> bool:
        """初始化OpenAI兼容客户端"""
        try:
            headers = config.custom_headers or {}
            if config.api_key:
                headers["Authorization"] = f"Bearer {config.api_key}"
            
            client = AsyncOpenAI(
                api_key=config.api_key or "dummy-key",
                base_url=config.base_url,
                timeout=config.timeout,
                max_retries=config.max_retries,
                default_headers=headers
            )
            
            self.active_clients[model_name] = client
            return True
            
        except Exception as e:
            self.logger.error(f"OpenAI兼容客户端初始化失败: {str(e)}")
            return False
    
    def _init_generic_client(self, model_name: str, config: ModelConfig) -> bool:
        """初始化通用HTTP客户端"""
        self.active_clients[model_name] = {
            'config': config,
            'session': requests.Session()
        }
        
        if config.custom_headers:
            self.active_clients[model_name]['session'].headers.update(config.custom_headers)
        
        return True
    
    async def analyze_content(self, request: AIAnalysisRequest, model_name: str) -> AIAnalysisResult:
        """使用指定模型分析内容"""
        start_time = time.time()
        
        try:
            if model_name not in self.models:
                raise ValueError(f"模型 {model_name} 未注册")
            
            config = self.models[model_name]
            
            # 根据任务类型构建提示词
            prompt = self._build_task_prompt(request, config)
            
            # 调用相应的模型处理方法
            if config.provider == ModelProvider.LOCAL_HUGGINGFACE:
                result = await self._process_local_model(model_name, prompt, request)
            elif config.provider == ModelProvider.OLLAMA:
                result = await self._process_ollama_model(model_name, prompt, request)
            elif config.provider in [ModelProvider.CUSTOM_API, ModelProvider.CHATGLM, ModelProvider.QWEN]:
                result = await self._process_openai_compatible(model_name, prompt, request)
            else:
                result = await self._process_generic_model(model_name, prompt, request)
            
            processing_time = time.time() - start_time
            
            # 更新统计
            self._update_stats(model_name, True, processing_time)
            
            return AIAnalysisResult(
                success=True,
                result=result,
                confidence=0.85,  # 可以根据实际情况调整
                processing_time=processing_time,
                model_used=model_name
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            self._update_stats(model_name, False, processing_time)
            
            self.logger.error(f"模型分析失败 {model_name}: {str(e)}")
            
            return AIAnalysisResult(
                success=False,
                result=None,
                confidence=0.0,
                processing_time=processing_time,
                model_used=model_name,
                error_message=str(e)
            )
    
    def _build_task_prompt(self, request: AIAnalysisRequest, config: ModelConfig) -> str:
        """根据任务类型构建提示词"""
        base_prompts = {
            'semantic_split': self._get_semantic_split_prompt(),
            'content_analysis': self._get_content_analysis_prompt(),
            'emotion_analysis': self._get_emotion_analysis_prompt(),
            'sentence_analysis': self._get_sentence_analysis_prompt()
        }
        
        if request.custom_prompt:
            return request.custom_prompt.format(text=request.text, context=request.context or "")
        
        prompt_template = base_prompts.get(request.task_type, base_prompts['sentence_analysis'])
        return prompt_template.format(
            text=request.text,
            context=request.context or "",
            language=request.language
        )
    
    def _get_sentence_analysis_prompt(self) -> str:
        """获取句子分析提示词 - 人类级别理解"""
        return """你是一个专业的语言学家和AI助手，具有人类级别的句子理解能力。请分析以下句子：

文本：{text}
语言：{language}
上下文：{context}

请从以下维度进行深度分析：
1. 语法结构：句子的语法成分、修辞手法、语言特点
2. 语义理解：句子的核心含义、隐含信息、歧义分析
3. 情感色彩：情感倾向、语调分析、情感强度
4. 语用功能：交际意图、表达效果、适用场景
5. 逻辑关系：因果关系、时间顺序、重要性层级
6. 文化背景：文化内涵、社会语境、表达习惯

请返回JSON格式的详细分析结果：
{{
    "grammar_analysis": "语法分析结果",
    "semantic_meaning": "语义理解结果", 
    "emotion_analysis": "情感分析结果",
    "pragmatic_function": "语用功能分析",
    "logical_structure": "逻辑关系分析",
    "cultural_context": "文化背景分析",
    "key_concepts": ["关键概念1", "关键概念2"],
    "complexity_score": 0.0-1.0,
    "confidence": 0.0-1.0
}}"""
    
    def _get_semantic_split_prompt(self) -> str:
        """获取语义分割提示词"""
        return """请将以下文本按照语义进行智能分割，保持每个片段的语义完整性：

文本：{text}
语言：{language}

要求：
1. 按照语义单元进行分割
2. 每个片段表达完整意思
3. 保持逻辑连贯性
4. 考虑停顿和节奏

返回JSON格式：{{"segments": ["片段1", "片段2", ...]}}"""
    
    def _get_content_analysis_prompt(self) -> str:
        """获取内容分析提示词"""
        return """请分析以下内容的主题、结构和重点：

内容：{text}
语言：{language}
上下文：{context}

返回JSON格式的分析结果：
{{
    "main_topic": "主要话题",
    "key_points": ["要点1", "要点2"],
    "content_type": "内容类型",
    "structure": "结构分析",
    "importance_ranking": ["重要性排序"]
}}"""
    
    def _get_emotion_analysis_prompt(self) -> str:
        """获取情感分析提示词"""
        return """请分析以下文本的情感特征：

文本：{text}
语言：{language}

返回JSON格式：
{{
    "primary_emotion": "主要情感",
    "emotion_intensity": 0.0-1.0,
    "sentiment_polarity": "positive/negative/neutral", 
    "emotional_keywords": ["情感关键词"],
    "tone_analysis": "语调分析"
}}"""
    
    async def _process_local_model(self, model_name: str, prompt: str, request: AIAnalysisRequest) -> Any:
        """处理本地模型请求"""
        client = self.active_clients[model_name]
        
        try:
            # 使用pipeline生成
            response = client['pipeline'](
                prompt, 
                max_length=request.max_output_length or 2048,
                temperature=self.models[model_name].temperature,
                do_sample=True,
                pad_token_id=client['tokenizer'].eos_token_id
            )
            
            generated_text = response[0]['generated_text']
            # 提取回复部分（去除输入prompt）
            if len(generated_text) > len(prompt):
                result_text = generated_text[len(prompt):].strip()
            else:
                result_text = generated_text.strip()
            
            # 尝试解析JSON
            try:
                return json.loads(result_text)
            except:
                return {"raw_response": result_text}
                
        except Exception as e:
            raise Exception(f"本地模型处理失败: {str(e)}")
    
    async def _process_ollama_model(self, model_name: str, prompt: str, request: AIAnalysisRequest) -> Any:
        """处理Ollama模型请求"""
        client = self.active_clients[model_name]
        
        payload = {
            "model": client['model_id'],
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.models[model_name].temperature,
                "num_predict": request.max_output_length or 2048
            }
        }
        
        try:
            response = requests.post(
                f"{client['base_url']}/api/generate",
                json=payload,
                timeout=self.models[model_name].timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '')
                
                # 尝试解析JSON
                try:
                    return json.loads(response_text)
                except:
                    return {"raw_response": response_text}
            else:
                raise Exception(f"Ollama API错误: {response.status_code}")
                
        except Exception as e:
            raise Exception(f"Ollama模型处理失败: {str(e)}")
    
    async def _process_openai_compatible(self, model_name: str, prompt: str, request: AIAnalysisRequest) -> Any:
        """处理OpenAI兼容模型请求"""
        client = self.active_clients[model_name]
        config = self.models[model_name]
        
        try:
            messages = [{"role": "user", "content": prompt}]
            
            kwargs = {
                "model": config.model_id,
                "messages": messages,
                "temperature": config.temperature,
                "max_tokens": request.max_output_length or config.max_tokens,
                "timeout": config.timeout
            }
            
            # 如果支持JSON模式
            if config.support_json and 'json' in prompt.lower():
                kwargs["response_format"] = {"type": "json_object"}
            
            response = await client.chat.completions.create(**kwargs)
            
            # 兼容性处理：检查响应类型
            if hasattr(response, 'choices') and response.choices:
                content = response.choices[0].message.content
            elif isinstance(response, dict):
                # 处理字典格式的响应
                content = response.get('content', response.get('text', str(response)))
            elif isinstance(response, str):
                # 处理字符串响应
                content = response
            else:
                # 最后尝试直接转换为字符串
                content = str(response)
            
            # 尝试解析JSON
            try:
                return json.loads(content)
            except:
                return {"raw_response": content}
                
        except Exception as e:
            raise Exception(f"OpenAI兼容模型处理失败: {str(e)}")
    
    async def _process_generic_model(self, model_name: str, prompt: str, request: AIAnalysisRequest) -> Any:
        """处理通用HTTP API模型"""
        client = self.active_clients[model_name]
        config = client['config']
        
        # 构建请求数据（需要根据具体API格式调整）
        payload = {
            "prompt": prompt,
            "max_tokens": request.max_output_length or config.max_tokens,
            "temperature": config.temperature
        }
        
        try:
            response = client['session'].post(
                f"{config.base_url}/chat/completions",  # 假设使用标准endpoint
                json=payload,
                timeout=config.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                # 根据具体API响应格式解析
                content = result.get('response', result.get('choices', [{}])[0].get('text', ''))
                
                try:
                    return json.loads(content)
                except:
                    return {"raw_response": content}
            else:
                raise Exception(f"API错误: {response.status_code}")
                
        except Exception as e:
            raise Exception(f"通用模型处理失败: {str(e)}")
    
    def _update_stats(self, model_name: str, success: bool, processing_time: float):
        """更新统计信息"""
        self.stats["total_requests"] += 1
        self.stats["total_processing_time"] += processing_time
        
        if success:
            self.stats["successful_requests"] += 1
        else:
            self.stats["failed_requests"] += 1
        
        if model_name not in self.stats["model_usage"]:
            self.stats["model_usage"][model_name] = {"requests": 0, "success": 0, "total_time": 0}
        
        self.stats["model_usage"][model_name]["requests"] += 1
        self.stats["model_usage"][model_name]["total_time"] += processing_time
        if success:
            self.stats["model_usage"][model_name]["success"] += 1
    
    def get_available_models(self) -> Dict[str, Dict[str, Any]]:
        """获取可用模型列表"""
        return {
            name: {
                "name": config.name,
                "provider": config.provider.value,
                "model_id": config.model_id,
                "support_json": config.support_json,
                "is_active": name in self.active_clients
            }
            for name, config in self.models.items()
        }
    
    def get_model_templates(self) -> Dict[str, Dict[str, Any]]:
        """获取模型配置模板"""
        templates = {}
        for name, config in self.model_templates.items():
            config_dict = asdict(config)
            # 确保枚举值被序列化为字符串
            if 'provider' in config_dict:
                config_dict['provider'] = config_dict['provider'].value if hasattr(config_dict['provider'], 'value') else str(config_dict['provider'])
            templates[name] = config_dict
        return templates
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self.stats.copy()
        if stats["total_requests"] > 0:
            stats["success_rate"] = stats["successful_requests"] / stats["total_requests"]
            stats["average_processing_time"] = stats["total_processing_time"] / stats["total_requests"]
        else:
            stats["success_rate"] = 0.0
            stats["average_processing_time"] = 0.0
        
        return stats


# 全局模型管理器实例
custom_ai_manager = CustomAIModelManager()


async def analyze_sentence_with_ai(
    text: str, 
    model_name: str = "default",
    task_type: str = "sentence_analysis",
    context: Optional[str] = None,
    language: str = "zh"
) -> AIAnalysisResult:
    """
    使用AI模型进行句子分析 - 人类级别理解
    
    Args:
        text: 待分析的文本
        model_name: 使用的模型名称
        task_type: 任务类型
        context: 上下文信息
        language: 语言代码
        
    Returns:
        AI分析结果
    """
    request = AIAnalysisRequest(
        text=text,
        task_type=task_type,
        context=context,
        language=language
    )
    
    return await custom_ai_manager.analyze_content(request, model_name)


if __name__ == "__main__":
    # 示例用法
    async def demo():
        # 注册一个自定义模型
        config = ModelConfig(
            name="本地ChatGLM",
            provider=ModelProvider.OLLAMA,
            base_url="http://localhost:11434",
            model_id="chatglm3:6b",
            support_json=True
        )
        
        success = custom_ai_manager.register_model("local_chatglm", config)
        print(f"模型注册结果: {success}")
        
        if success:
            # 测试句子分析
            result = await analyze_sentence_with_ai(
                text="今天天气真好，我们去公园散步吧。",
                model_name="local_chatglm",
                task_type="sentence_analysis"
            )
            
            print(f"分析结果: {result}")
    
    # 运行示例
    asyncio.run(demo())