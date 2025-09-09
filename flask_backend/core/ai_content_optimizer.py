"""
AI内容优化器 - 前置断句和内容润色
在TTS生成前对讲话稿进行AI优化，解决多行字幕问题
"""
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import re

from utils.logger import get_logger

class AIContentOptimizer:
    """AI内容优化器 - 断句、润色、字数控制"""
    
    def __init__(self, project_dir: Path, ai_config: Optional[Dict[str, Any]] = None):
        self.project_dir = Path(project_dir)
        self.logger = get_logger(__name__, self.project_dir / "logs")
        
        # AI配置
        self.ai_config = ai_config or {}
        
        # 内容优化配置
        self.optimization_config = {
            "max_chars_per_segment": 35,        # 每段最大字符数
            "min_chars_per_segment": 10,        # 每段最小字符数
            "max_segments_per_slide": 5,        # 每页最大段数
            "target_reading_speed": 3.5,        # 目标阅读速度（字/秒）
            "enable_content_refinement": True,   # 启用内容润色
            "preserve_key_terms": True,          # 保留关键术语
            "remove_redundancy": True            # 去除冗余表达
        }
        
        # 初始化AI客户端
        self._init_ai_client()
    
    def _init_ai_client(self):
        """初始化AI客户端 - 只支持自定义API服务"""
        try:
            service_type = self.ai_config.get('service_type', 'custom')
            
            if service_type == 'custom':
                import openai
                
                base_url = self.ai_config.get('base_url', '')
                if base_url and not base_url.endswith('/v1'):
                    if not base_url.endswith('/'):
                        base_url += '/'
                    base_url += 'v1'
                
                self.ai_client = openai.OpenAI(
                    api_key=self.ai_config.get('api_key', ''),
                    base_url=base_url,
                    timeout=self.ai_config.get('timeout', 30)
                )
                self.logger.info(f"AI客户端初始化成功: 自定义服务 {base_url}")
            else:
                self.logger.error(f"不支持的AI服务类型: {service_type}，只支持自定义API服务")
                self.ai_client = None
                
        except ImportError as e:
            self.logger.error(f"缺少必要的依赖包: {e}")
            self.ai_client = None
        except Exception as e:
            self.logger.error(f"AI客户端初始化失败: {e}")
            self.ai_client = None
    
    async def optimize_scripts_content(self, scripts_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        优化讲话稿内容
        
        Args:
            scripts_data: 原始讲话稿数据
            
        Returns:
            优化后的分段讲话稿数据
        """
        try:
            self.logger.info("开始AI内容优化处理")
            
            scripts = scripts_data.get("scripts", [])
            optimized_scripts = []
            
            for script in scripts:
                slide_number = script["slide_number"]
                original_content = script["script_content"]
                
                if not original_content or not original_content.strip():
                    # 空内容直接跳过
                    optimized_scripts.append(script)
                    continue
                
                self.logger.info(f"优化第 {slide_number} 页内容")
                
                # AI内容优化
                optimized_segments = await self._optimize_single_script(original_content, slide_number)
                
                # 生成优化后的脚本数据
                for i, segment in enumerate(optimized_segments):
                    segment_script = {
                        "slide_number": slide_number,
                        "segment_index": i + 1,
                        "script_content": segment["text"],
                        "word_count": len(segment["text"]),
                        "estimated_duration": segment["estimated_duration"],
                        "optimization_applied": True,
                        "original_content": original_content if i == 0 else "",  # 只在第一段保存原文
                        "segment_type": segment.get("type", "normal")
                    }
                    optimized_scripts.append(segment_script)
            
            # 生成优化后的数据结构
            optimized_data = {
                "scripts": optimized_scripts,
                "total_scripts": len(optimized_scripts),
                "optimization_applied": True,
                "optimization_timestamp": datetime.now().isoformat(),
                "optimization_config": self.optimization_config.copy(),
                "ai_config_used": {
                    "service_type": self.ai_config.get('service_type', 'unknown'),
                    "model": self.ai_config.get('model', 'unknown')
                }
            }
            
            self.logger.info(f"AI内容优化完成: {len(scripts)} 页 → {len(optimized_scripts)} 段")
            return optimized_data
            
        except Exception as e:
            self.logger.error(f"AI内容优化失败: {e}")
            # 返回原始数据
            return scripts_data
    
    async def _optimize_single_script(self, content: str, slide_number: int) -> List[Dict[str, Any]]:
        """
        优化单个讲话稿
        
        Args:
            content: 原始内容
            slide_number: 页码
            
        Returns:
            优化后的分段列表
        """
        try:
            # 清理内容
            content = self._clean_content(content)
            
            if not self.ai_client:
                # AI不可用时使用规则分割
                return await self._fallback_segmentation(content)
            
            # 构建AI提示词
            prompt = self._build_optimization_prompt(content)
            
            # 调用AI API
            response = await self._call_ai_api(prompt)
            
            # 解析AI响应
            segments = self._parse_ai_response(response, content)
            
            if not segments:
                # AI解析失败，使用规则分割
                return await self._fallback_segmentation(content)
            
            # 验证和调整分段
            validated_segments = self._validate_segments(segments)
            
            self.logger.info(f"第 {slide_number} 页优化成功: {len(validated_segments)} 个分段")
            return validated_segments
            
        except Exception as e:
            self.logger.error(f"单个讲话稿优化失败: {e}")
            return await self._fallback_segmentation(content)
    
    def _build_optimization_prompt(self, content: str) -> str:
        """构建AI优化提示词"""
        max_chars = self.optimization_config["max_chars_per_segment"]
        
        prompt = f"""
你是一个专业的内容优化专家，需要将以下讲话稿内容进行智能分割和润色，用于视频字幕显示。

原始内容：
{content}

优化要求：
1. 将内容分割为多个语义完整的段落
2. 每个段落字符数控制在{max_chars}字符以内
3. 保持语义完整性，不能破坏句子逻辑
4. 适当润色，去除冗余，提升表达质量
5. 保留关键信息和专业术语

请返回JSON格式：
{{
    "segments": [
        {{
            "text": "第一段优化后内容",
            "char_count": 25,
            "type": "opening"
        }},
        {{
            "text": "第二段优化后内容", 
            "char_count": 30,
            "type": "main"
        }}
    ]
}}

请直接返回JSON，不要包含其他解释。
"""
        return prompt
    
    async def _call_ai_api(self, prompt: str) -> str:
        """调用AI API - 带超时和错误处理"""
        try:
            # 添加超时机制，防止死循环
            timeout = self.ai_config.get('timeout', 30)
            
            # 使用 asyncio.wait_for 添加超时
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.ai_client.chat.completions.create,
                    model=self.ai_config.get('model', 'gpt-3.5-turbo'),
                    messages=[
                        {"role": "system", "content": "你是一个专业的内容优化助手。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=2000,
                    response_format={"type": "json_object"} if self.ai_config.get('support_json', True) else None
                ),
                timeout=timeout
            )
            
            return response.choices[0].message.content
            
        except asyncio.TimeoutError:
            self.logger.error(f"AI API调用超时 ({timeout}秒)")
            raise Exception("AI API调用超时")
        except Exception as e:
            self.logger.error(f"AI API调用失败: {e}")
            raise
    
    def _parse_ai_response(self, response: str, original_content: str) -> List[Dict[str, Any]]:
        """解析AI响应"""
        try:
            data = json.loads(response)
            segments = data.get("segments", [])
            
            result = []
            for segment in segments:
                text = segment.get("text", "").strip()
                if text:
                    char_count = len(text)
                    estimated_duration = max(char_count / self.optimization_config["target_reading_speed"], 1.0)
                    
                    result.append({
                        "text": text,
                        "char_count": char_count,
                        "estimated_duration": estimated_duration,
                        "type": segment.get("type", "normal")
                    })
            
            return result
            
        except Exception as e:
            self.logger.error(f"AI响应解析失败: {e}")
            return []
    
    async def _fallback_segmentation(self, content: str) -> List[Dict[str, Any]]:
        """备用规则分割方法"""
        max_chars = self.optimization_config["max_chars_per_segment"]
        
        # 按标点符号分割
        sentences = re.split(r'([。！？；])', content)
        
        segments = []
        current_segment = ""
        
        for i in range(0, len(sentences), 2):
            if i < len(sentences):
                sentence = sentences[i].strip()
                punct = sentences[i + 1] if i + 1 < len(sentences) else ""
                
                if sentence:
                    full_sentence = sentence + punct
                    
                    if len(current_segment + full_sentence) <= max_chars:
                        current_segment += full_sentence
                    else:
                        if current_segment:
                            char_count = len(current_segment)
                            estimated_duration = max(char_count / self.optimization_config["target_reading_speed"], 1.0)
                            
                            segments.append({
                                "text": current_segment.strip(),
                                "char_count": char_count,
                                "estimated_duration": estimated_duration,
                                "type": "normal"
                            })
                        
                        current_segment = full_sentence
        
        # 添加最后的段落
        if current_segment:
            char_count = len(current_segment)
            estimated_duration = max(char_count / self.optimization_config["target_reading_speed"], 1.0)
            
            segments.append({
                "text": current_segment.strip(),
                "char_count": char_count,
                "estimated_duration": estimated_duration,
                "type": "normal"
            })
        
        return segments
    
    def _validate_segments(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """验证和调整分段"""
        max_chars = self.optimization_config["max_chars_per_segment"]
        min_chars = self.optimization_config["min_chars_per_segment"]
        
        validated = []
        
        for segment in segments:
            text = segment["text"]
            char_count = len(text)
            
            # 检查长度
            if char_count > max_chars:
                # 过长，需要进一步分割
                sub_segments = self._split_long_segment(text, max_chars)
                validated.extend(sub_segments)
            elif char_count < min_chars and validated:
                # 过短，尝试与前一段合并
                last_segment = validated[-1]
                if len(last_segment["text"] + text) <= max_chars:
                    last_segment["text"] += text
                    last_segment["char_count"] = len(last_segment["text"])
                    last_segment["estimated_duration"] = max(
                        last_segment["char_count"] / self.optimization_config["target_reading_speed"], 1.0
                    )
                else:
                    validated.append(segment)
            else:
                validated.append(segment)
        
        return validated
    
    def _split_long_segment(self, text: str, max_chars: int) -> List[Dict[str, Any]]:
        """分割过长的段落"""
        words = list(text)
        segments = []
        current = ""
        
        for word in words:
            if len(current + word) <= max_chars:
                current += word
            else:
                if current:
                    char_count = len(current)
                    estimated_duration = max(char_count / self.optimization_config["target_reading_speed"], 1.0)
                    
                    segments.append({
                        "text": current.strip(),
                        "char_count": char_count,
                        "estimated_duration": estimated_duration,
                        "type": "split"
                    })
                current = word
        
        if current:
            char_count = len(current)
            estimated_duration = max(char_count / self.optimization_config["target_reading_speed"], 1.0)
            
            segments.append({
                "text": current.strip(),
                "char_count": char_count,
                "estimated_duration": estimated_duration,
                "type": "split"
            })
        
        return segments
    
    def _clean_content(self, content: str) -> str:
        """清理内容"""
        if not content:
            return ""
        
        # 移除HTML标签
        content = re.sub(r'<[^>]+>', '', content)
        
        # 移除多余空白
        content = re.sub(r'\s+', ' ', content).strip()
        
        return content
