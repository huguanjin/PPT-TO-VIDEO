"""
AI语义分割模块
基于分析的开源项目，实现智能字幕语义分割功能
支持多种AI模型进行语义理解和断句
支持自定义base_url和model配置
"""
import json
import re
from typing import List, Dict, Any, Optional, Union, Type
import logging
from datetime import datetime
import asyncio
from pathlib import Path
import sys

try:
    from app.utils.config_manager import ConfigManager
    ConfigManagerClass: Optional[Type] = ConfigManager
except ImportError:
    # 如果导入失败，使用简单的配置管理
    ConfigManagerClass = None

# AI提示词模板 (基于Netflix标准)
NETFLIX_SUBTITLE_PROMPTS = {
    "semantic_split": {
        "system": """你是一个专业的字幕编辑专家，专门负责将长文本按照语义进行智能分割。

任务要求：
1. 保持语义完整性，不能破坏句子的逻辑结构
2. 每行字幕的显示权重不超过指定限制
3. 优先在标点符号处分割
4. 避免单字或短词独立成行
5. 保持自然的阅读节奏

字符权重规则：
- 中文/日文字符：1.75倍权重
- 韩文字符：1.5倍权重  
- 英文字符：1.0倍权重
- 标点符号：0.8倍权重
- 空格：0.5倍权重
- 数字：0.8倍权重

请按照以上规则进行语义分割。""",
        
        "user": """请将以下文本按照语义进行智能分割，每行的字符权重不超过{max_weight}：

原文：{text}

要求：
1. 返回JSON格式：{{"lines": ["第一行", "第二行", ...]}}
2. 每行保持语义完整
3. 控制每行的显示权重在{max_weight}以内
4. 优化断句位置

请直接返回JSON，不要包含其他解释。"""
    },
    
    "validate_split": {
        "system": """你是一个字幕质量检查专家，负责验证字幕分割的质量。

检查标准：
1. 语义完整性：每行是否表达完整的语义
2. 权重控制：是否超过指定的字符权重限制
3. 阅读流畅性：分割点是否自然
4. 视觉效果：行长是否适合屏幕显示

请对字幕分割结果进行专业评估。""",
        
        "user": """请评估以下字幕分割质量：

原文：{original_text}
分割结果：{split_lines}
权重限制：{max_weight}

请返回JSON格式的评估结果：
{{
    "is_valid": true/false,
    "quality_score": 0-100,
    "issues": ["问题1", "问题2"],
    "suggestions": ["建议1", "建议2"]
}}"""
    }
}


class AISemanticSplitter:
    """AI语义分割器"""
    
    def __init__(self, ai_config: Optional[Dict[str, Any]] = None, service: Optional[str] = None):
        """
        初始化AI语义分割器
        
        Args:
            ai_config: AI配置参数（可选，如果不提供则从配置管理器加载）
            service: AI服务类型（'openai', 'anthropic', 'custom'）
        """
        self.logger = logging.getLogger(__name__)
        
        # 初始化配置管理器
        if ConfigManagerClass is not None:
            try:
                self.config_manager = ConfigManagerClass()  # type: ignore
                self.use_config_manager = True
            except Exception as e:
                self.logger.warning(f"配置管理器初始化失败: {e}")
                self.config_manager = None
                self.use_config_manager = False
        else:
            self.config_manager = None
            self.use_config_manager = False
        
        # 获取AI配置
        self.ai_config: Dict[str, Any] = {}  # 明确类型注解
        if ai_config:
            # 使用传入的配置
            self.ai_config = ai_config
            self.ai_service_type = ai_config.get('service_type', 'openai')
        elif self.use_config_manager:
            # 从配置管理器加载配置
            if service is None:
                if hasattr(self.config_manager, 'load_key'):
                    service = self.config_manager.load_key('ai.default_service') or 'openai'  # type: ignore
                else:
                    service = 'openai'
            self.ai_service_type = service
            if hasattr(self.config_manager, 'get_ai_config'):
                self.ai_config = self.config_manager.get_ai_config(service)  # type: ignore
            else:
                self.ai_config = {
                    'api_key': '',
                    'base_url': '',
                    'model': 'gpt-3.5-turbo',
                    'timeout': 300,
                    'max_retries': 3,
                    'support_json': True
                }
        else:
            # 使用默认配置
            self._setup_default_config()
        
        # 设置配置属性（使用显式键访问）
        config = self.ai_config if isinstance(self.ai_config, dict) else {}
        self.api_key = config['api_key'] if 'api_key' in config else ''
        self.model = config['model'] if 'model' in config else 'gpt-3.5-turbo'
        self.base_url = config['base_url'] if 'base_url' in config else ''
        self.timeout = config['timeout'] if 'timeout' in config else 300
        self.max_retries = config['max_retries'] if 'max_retries' in config else 3
        self.support_json = config['support_json'] if 'support_json' in config else True
        
        # 初始化AI客户端
        self._init_ai_client()
        
    def _setup_default_config(self):
        """设置默认配置"""
        self.ai_service_type = 'openai'
        self.ai_config = {
            'api_key': '',
            'base_url': '',
            'model': 'gpt-3.5-turbo',
            'timeout': 300,
            'max_retries': 3,
            'support_json': True
        }
        
    def _init_ai_client(self):
        """初始化AI客户端"""
        try:
            if self.ai_service_type == 'openai' or self.ai_service_type == 'custom':
                try:
                    import openai
                    
                    # 处理base_url
                    client_base_url = self.base_url
                    if client_base_url and not client_base_url.endswith('/v1'):
                        if not client_base_url.endswith('/'):
                            client_base_url += '/'
                        client_base_url += 'v1'
                    
                    self.ai_client = openai.OpenAI(
                        api_key=self.api_key,
                        base_url=client_base_url if client_base_url else None,
                        timeout=self.timeout
                    )
                    self.logger.info(f"OpenAI客户端初始化成功，base_url: {client_base_url}, model: {self.model}")
                except ImportError:
                    self.logger.warning("OpenAI包未安装，请安装: pip install openai")
                    self.ai_client = None
            elif self.ai_service_type == 'anthropic':
                try:
                    import anthropic
                    self.ai_client = anthropic.Anthropic(
                        api_key=self.api_key,
                        timeout=self.timeout
                    )
                    self.logger.info(f"Anthropic客户端初始化成功，model: {self.model}")
                except ImportError:
                    self.logger.warning("Anthropic包未安装，请安装: pip install anthropic")
                    self.ai_client = None
                except Exception as e:
                    self.logger.warning(f"Anthropic客户端初始化失败: {e}")
                    self.ai_client = None
            else:
                self.logger.warning(f"不支持的AI服务类型: {self.ai_service_type}")
                self.ai_client = None
        except Exception as e:
            self.logger.warning(f"AI客户端初始化失败: {e}")
            self.ai_client = None
    
    async def split_text_semantically(self, text: str, max_weight: float = 75.0) -> List[str]:
        """
        使用AI进行语义分割
        
        Args:
            text: 原始文本
            max_weight: 最大字符权重
            
        Returns:
            分割后的文本行列表
        """
        if not self.ai_client or not text:
            return [text] if text else []
            
        try:
            # 构建提示词
            prompt_template = NETFLIX_SUBTITLE_PROMPTS["semantic_split"]
            
            messages = [
                {"role": "system", "content": prompt_template["system"]},
                {"role": "user", "content": prompt_template["user"].format(
                    text=text,
                    max_weight=max_weight
                )}
            ]
            
            # 调用AI服务
            if self.ai_service_type == 'openai' or self.ai_service_type == 'custom':
                response = await self._call_openai(messages)
            elif self.ai_service_type == 'anthropic':
                response = await self._call_anthropic(messages)
            else:
                raise ValueError(f"不支持的AI服务类型: {self.ai_service_type}")
            
            # 解析响应
            result = self._parse_ai_response(response)
            return result.get('lines', [text])
            
        except Exception as e:
            self.logger.error(f"AI语义分割失败: {e}")
            return [text]
    
    async def _call_openai(self, messages: List[Dict]) -> str:
        """调用OpenAI API"""
        for attempt in range(self.max_retries):
            try:
                # 构建请求参数
                params = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 1000,
                    "timeout": self.timeout
                }
                
                # 如果支持JSON格式，添加response_format
                if self.support_json:
                    params["response_format"] = {"type": "json_object"}
                
                response = await asyncio.to_thread(
                    self.ai_client.chat.completions.create,  # type: ignore
                    **params
                )
                return response.choices[0].message.content or ""
                
            except Exception as e:
                self.logger.warning(f"OpenAI API调用失败 (第{attempt + 1}次尝试): {e}")
                if attempt == self.max_retries - 1:
                    raise
                # 等待后重试
                await asyncio.sleep(2 ** attempt)
        
        # 如果所有尝试都失败，返回空字符串
        return ""
    
    async def _call_anthropic(self, messages: List[Dict]) -> str:
        """调用Anthropic API"""
        for attempt in range(self.max_retries):
            try:
                # 转换消息格式
                system_message = ""
                user_messages = []
                
                for msg in messages:
                    if msg["role"] == "system":
                        system_message = msg["content"]
                    else:
                        user_messages.append(msg)
                
                response = await asyncio.to_thread(
                    self.ai_client.messages.create,  # type: ignore
                    model=self.model,
                    max_tokens=1000,
                    system=system_message,
                    messages=user_messages,
                    timeout=self.timeout
                )
                return response.content[0].text if hasattr(response.content[0], 'text') else str(response.content[0])  # type: ignore
                
            except Exception as e:
                self.logger.warning(f"Anthropic API调用失败 (第{attempt + 1}次尝试): {e}")
                if attempt == self.max_retries - 1:
                    raise
                # 等待后重试
                await asyncio.sleep(2 ** attempt)
        
        # 如果所有尝试都失败，返回空字符串
        return ""
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """解析AI响应"""
        try:
            # 清理响应文本
            response = response.strip()
            
            # 尝试提取JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                # 如果没有找到JSON，尝试按行分割
                lines = [line.strip() for line in response.split('\n') if line.strip()]
                return {"lines": lines}
                
        except json.JSONDecodeError as e:
            self.logger.error(f"AI响应解析失败: {e}")
            return {"lines": [response]}
    
    async def validate_split_quality(self, original_text: str, split_lines: List[str], max_weight: float) -> Dict[str, Any]:
        """
        验证分割质量
        
        Args:
            original_text: 原始文本
            split_lines: 分割结果
            max_weight: 权重限制
            
        Returns:
            质量评估结果
        """
        if not self.ai_client:
            return {"is_valid": True, "quality_score": 80, "issues": [], "suggestions": []}
            
        try:
            prompt_template = NETFLIX_SUBTITLE_PROMPTS["validate_split"]
            
            messages = [
                {"role": "system", "content": prompt_template["system"]},
                {"role": "user", "content": prompt_template["user"].format(
                    original_text=original_text,
                    split_lines=split_lines,
                    max_weight=max_weight
                )}
            ]
            
            # 调用AI服务
            if self.ai_service_type == 'openai' or self.ai_service_type == 'custom':
                response = await self._call_openai(messages)
            elif self.ai_service_type == 'anthropic':
                response = await self._call_anthropic(messages)
            else:
                raise ValueError(f"不支持的AI服务类型: {self.ai_service_type}")
            
            # 解析响应
            result = self._parse_ai_response(response)
            return result
            
        except Exception as e:
            self.logger.error(f"分割质量验证失败: {e}")
            return {"is_valid": True, "quality_score": 80, "issues": [], "suggestions": []}


class HybridSubtitleSplitter:
    """混合字幕分割器 - 结合规则和AI"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化混合分割器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        
        # 基础配置
        self.max_weight = self.config.get('max_length', 75)
        self.use_ai = self.config.get('use_ai_splitting', False)
        self.ai_fallback = self.config.get('ai_fallback', True)
        
        # 初始化组件
        from core.subtitle_utils import SmartSubtitleProcessor
        self.rule_processor = SmartSubtitleProcessor(self.config)
        
        # AI配置
        ai_config = self.config.get('ai_config', {})
        if self.use_ai and ai_config:
            self.ai_splitter = AISemanticSplitter(ai_config)
        else:
            self.ai_splitter = None
            
        self.logger = logging.getLogger(__name__)
    
    async def split_subtitle_text(self, text: str) -> List[str]:
        """
        分割字幕文本 - 使用混合策略
        
        Args:
            text: 原始文本
            
        Returns:
            分割后的文本行列表
        """
        if not text:
            return []
            
        self.logger.debug(f"开始分割字幕文本: {text}")
        
        # 首先尝试AI分割
        if self.use_ai and self.ai_splitter:
            try:
                ai_result = await self.ai_splitter.split_text_semantically(text, self.max_weight)
                
                # 验证AI分割结果
                if ai_result and len(ai_result) > 0:
                    # 检查每行是否符合权重要求
                    all_valid = True
                    for line in ai_result:
                        if not self.rule_processor.validate_subtitle_line(line):
                            all_valid = False
                            break
                    
                    if all_valid:
                        self.logger.debug(f"AI分割成功: {ai_result}")
                        return ai_result
                    else:
                        self.logger.warning("AI分割结果不符合权重要求，使用规则分割")
                        
            except Exception as e:
                self.logger.error(f"AI分割失败: {e}")
        
        # 使用规则分割作为fallback
        rule_result = self.rule_processor.process_subtitle_text(text)
        self.logger.debug(f"规则分割结果: {rule_result}")
        return rule_result
    
    def get_splitting_metrics(self, text: str, split_result: List[str]) -> Dict[str, Any]:
        """获取分割度量"""
        from core.subtitle_utils import calc_text_display_weight
        
        metrics = {
            'original_text': text,
            'original_weight': calc_text_display_weight(text),
            'split_count': len(split_result),
            'split_lines': [],
            'total_weight': 0.0,
            'max_line_weight': 0.0,
            'min_line_weight': float('inf'),
            'avg_line_weight': 0.0,
            'weight_distribution': 'balanced',
            'processing_method': 'ai' if self.use_ai else 'rule',
            'processed_at': datetime.now().isoformat()
        }
        
        for line in split_result:
            weight = calc_text_display_weight(line)
            line_info = {
                'text': line,
                'weight': weight,
                'is_valid': weight <= self.max_weight
            }
            metrics['split_lines'].append(line_info)
            metrics['total_weight'] += weight
            metrics['max_line_weight'] = max(metrics['max_line_weight'], weight)
            metrics['min_line_weight'] = min(metrics['min_line_weight'], weight)
        
        if split_result:
            metrics['avg_line_weight'] = metrics['total_weight'] / len(split_result)
            
            # 判断权重分布
            weight_variance = sum(
                (line['weight'] - metrics['avg_line_weight']) ** 2 
                for line in metrics['split_lines']
            ) / len(split_result)
            
            if weight_variance < 100:
                metrics['weight_distribution'] = 'balanced'
            elif weight_variance < 300:
                metrics['weight_distribution'] = 'moderate'
            else:
                metrics['weight_distribution'] = 'unbalanced'
        
        return metrics


# 便捷函数
async def smart_split_subtitle(text: str, config: Optional[Dict[str, Any]] = None) -> List[str]:
    """
    便捷函数：智能分割字幕
    
    Args:
        text: 原始文本
        config: 配置参数
        
    Returns:
        分割后的文本行列表
    """
    splitter = HybridSubtitleSplitter(config)
    return await splitter.split_subtitle_text(text)


if __name__ == "__main__":
    # 测试代码
    import asyncio
    
    async def test_ai_splitting():
        # 测试配置
        test_config = {
            'max_length': 75,
            'use_ai_splitting': False,  # 设为True需要配置AI服务
            'ai_config': {
                'service_type': 'openai',
                'api_key': 'your-api-key',
                'model': 'gpt-3.5-turbo'
            }
        }
        
        test_texts = [
            "这是一个需要进行智能语义分割的长字幕文本，包含了多个语义单元和复杂的标点符号结构。",
            "Hello, this is a very long English subtitle text that needs to be split intelligently based on semantic meaning and character weights.",
            "混合语言测试：This text contains both Chinese and English content that requires careful handling.",
        ]
        
        splitter = HybridSubtitleSplitter(test_config)
        
        for text in test_texts:
            print(f"\n原文: {text}")
            
            result = await splitter.split_subtitle_text(text)
            print(f"分割结果 ({len(result)} 行):")
            for i, line in enumerate(result, 1):
                print(f"  {i}. {line}")
            
            metrics = splitter.get_splitting_metrics(text, result)
            print(f"权重分布: {metrics['weight_distribution']}")
            print(f"平均权重: {metrics['avg_line_weight']:.2f}")
    
    # 运行测试
    asyncio.run(test_ai_splitting())
