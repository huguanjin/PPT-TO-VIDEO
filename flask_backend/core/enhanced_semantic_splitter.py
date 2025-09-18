"""
增强型语义分割器
基于AI的智能字幕分割，确保URL、邮箱、技术术语等内容的完整性
"""
import re
import json
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import logging
from pathlib import Path

from .custom_ai_models import CustomAIModelManager, AIAnalysisRequest, ModelConfig, ModelProvider

logger = logging.getLogger(__name__)

class EnhancedSemanticSplitter:
    """增强型语义分割器"""
    
    def __init__(self, ai_model_manager: Optional[CustomAIModelManager] = None):
        self.ai_manager = ai_model_manager or CustomAIModelManager()
        self.model_name = "gemini-2.0-flash-custom"
        
        # 语义保护单元的正则模式
        self.semantic_patterns = [
            (r'https?://[^\s\u4e00-\u9fff]+', 'url'),  # URL (避免匹配中文)
            (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', 'email'),  # 邮箱
            (r'\b[A-Z]{2,}(?:[A-Z][a-z]+)*\b', 'acronym'),  # 缩写词
            (r'\d+(?:\.\d+)*\s*[a-zA-Z%]+', 'number_unit'),  # 数字+单位
            (r'[a-zA-Z0-9_]+\.[a-zA-Z0-9_\.]+', 'tech_term'),  # 技术术语
            (r'[a-zA-Z][a-zA-Z0-9]*://[^\s]+', 'protocol'),  # 协议地址
            (r'\$[a-zA-Z_][a-zA-Z0-9_]*', 'variable'),  # 变量名
            (r'#[a-zA-Z_][a-zA-Z0-9_]*', 'hashtag'),  # 标签
            (r'@[a-zA-Z_][a-zA-Z0-9_]*', 'mention'),  # 提及
        ]
        
        # 配置
        self.max_chars_per_line = 26
        self.max_lines = 2
        
        # 初始化AI模型
        self._setup_ai_model()
    
    def _setup_ai_model(self):
        """设置AI模型"""
        try:
            # 使用Flask后端的正确配置
            config = ModelConfig(
                name="Gemini 2.0 Flash for Semantic Splitting",
                provider=ModelProvider.CUSTOM_API,
                model_id="gemini-2.0-flash",
                base_url="https://fast.yourapi.cn/v1",  # 使用v1端点
                api_key="sk-U5qHXmNVAOwMb3k1ITTQwSs67wR77ptgAcQLucrgiai5e6Aq",
                support_json=True,
                enable_function_calling=False,
                temperature=0.1,  # 低温度确保一致性
                max_tokens=1000,
                timeout=30
            )
            
            success = self.ai_manager.register_model(self.model_name, config)
            if success:
                logger.info(f"✅ AI语义分割模型 {self.model_name} 注册成功")
            else:
                logger.warning(f"⚠️ AI模型注册失败，将使用备用分割方案")
                
        except Exception as e:
            logger.error(f"❌ AI模型设置失败: {e}")
    
    async def split_with_semantic_awareness(self, text: str) -> List[str]:
        """
        语义感知的智能分割
        
        Args:
            text: 需要分割的文本
            
        Returns:
            分割后的行列表
        """
        try:
            logger.info(f"开始语义分割: {text[:50]}...")
            
            # 1. 检测需要保护的语义单元
            protected_units = self._detect_semantic_units(text)
            logger.info(f"检测到保护单元: {[unit['text'] for unit in protected_units]}")
            
            # 2. 尝试AI增强分割
            if self.ai_manager and self.model_name in self.ai_manager.models:
                ai_result = await self._ai_semantic_split(text, protected_units)
                
                if ai_result and self._validate_result(ai_result, text, protected_units):
                    logger.info("✅ AI语义分割成功")
                    return ai_result
                else:
                    logger.warning("⚠️ AI分割结果验证失败，使用备用方案")
            
            # 3. Fallback到规则分割
            fallback_result = self._fallback_split(text, protected_units)
            logger.info("使用规则分割方案")
            return fallback_result
            
        except Exception as e:
            logger.error(f"语义分割失败: {e}")
            # 最后的保底方案
            return self._simple_split(text)
    
    def _detect_semantic_units(self, text: str) -> List[Dict[str, Any]]:
        """检测语义单元（URL、邮箱、专业术语等）"""
        semantic_units = []
        
        for pattern, unit_type in self.semantic_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                unit = {
                    'text': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'type': unit_type,
                    'priority': self._get_protection_priority(unit_type)
                }
                semantic_units.append(unit)
        
        # 按位置排序
        semantic_units.sort(key=lambda x: x['start'])
        
        # 去除重叠的单元（保留优先级高的）
        filtered_units = []
        for unit in semantic_units:
            overlaps = False
            for existing in filtered_units:
                if (unit['start'] < existing['end'] and unit['end'] > existing['start']):
                    if unit['priority'] > existing['priority']:
                        filtered_units.remove(existing)
                    else:
                        overlaps = True
                        break
            
            if not overlaps:
                filtered_units.append(unit)
        
        return filtered_units
    
    def _get_protection_priority(self, unit_type: str) -> int:
        """获取保护单元的优先级"""
        priorities = {
            'url': 10,
            'email': 9,
            'protocol': 8,
            'tech_term': 7,
            'number_unit': 6,
            'acronym': 5,
            'variable': 4,
            'hashtag': 3,
            'mention': 2
        }
        return priorities.get(unit_type, 1)
    
    async def _ai_semantic_split(self, text: str, protected_units: List[Dict]) -> Optional[List[str]]:
        """AI增强的语义分割"""
        try:
            # 构建提示词
            prompt = self._build_semantic_optimization_prompt(text, protected_units)
            
            # 创建AI请求
            request = AIAnalysisRequest(
                text=text,
                task_type="semantic_split",
                language="zh",
                max_output_length=500
            )
            
            # 调用AI分析
            result = await self.ai_manager.analyze_content(request, self.model_name)
            
            if result.success and result.result:
                return self._parse_ai_response(result.result, text, protected_units)
            else:
                logger.warning(f"AI分析失败: {result.error_message}")
                return None
                
        except Exception as e:
            logger.error(f"AI语义分割异常: {e}")
            return None
    
    def _build_semantic_optimization_prompt(self, content: str, protected_units: List[Dict]) -> str:
        """构建语义优化提示词"""
        protected_list = '\n'.join([f"- {unit['text']} (类型: {unit['type']})" for unit in protected_units])
        
        prompt = f"""你是专业的字幕分割优化专家，需要将以下内容进行智能分割，确保语义完整性。

原始内容：
{content}

需要保护的完整单元（绝对不能分割）：
{protected_list}

分割要求：
1. 每行最多{self.max_chars_per_line}个中文字符（英文字符按0.5计算）
2. 最多{self.max_lines}行
3. 保护单元必须完整，不能跨行分割
4. 优先保证语义完整性，在语义边界进行分割
5. 避免在标点符号前分割

请返回JSON格式：
{{
    "lines": [
        "第一行内容",
        "第二行内容"
    ],
    "protected_units_preserved": true,
    "semantic_quality_score": 0.95,
    "reasoning": "分割决策的原因"
}}

直接返回JSON，不要其他解释。"""
        
        return prompt
    
    def _parse_ai_response(self, response: Any, original: str, protected_units: List[Dict]) -> Optional[List[str]]:
        """解析AI响应"""
        try:
            # 如果response已经是dict，直接使用
            if isinstance(response, dict):
                data = response
            else:
                # 尝试解析JSON字符串
                data = json.loads(str(response))
            
            # 尝试多种可能的字段名
            lines = data.get('lines', []) or data.get('segments', []) or data.get('split_result', [])
            
            if not lines:
                logger.warning(f"AI响应中未找到分割结果: {data}")
                return None
            
            logger.info(f"AI返回分割结果: {lines}")
            
            # 验证保护单元 (可选检查)
            if 'protected_units_preserved' in data and not data.get('protected_units_preserved', False):
                logger.warning("AI响应表明保护单元未完全保留")
            
            # 基本验证 - 允许适当超过行数限制，如果字符分布合理
            if len(lines) > self.max_lines:
                # 如果超过行数限制，检查是否是因为合理的语义分割
                total_chars = sum(len(line) for line in lines)
                avg_chars_per_line = total_chars / len(lines)
                
                print(f"🔍 行数验证: {len(lines)}行 > {self.max_lines}行")
                print(f"   总字符: {total_chars}, 平均: {avg_chars_per_line:.1f}字符/行")
                print(f"   限制检查: {len(lines)} <= {self.max_lines + 1} = {len(lines) <= self.max_lines + 1}")
                
                # 检查是否有保护单元导致某行超长
                has_protected_content = any(
                    any(unit['text'] in line for unit in protected_units) 
                    for line in lines
                )
                
                # 更宽松的字符限制，特别是当有保护内容时
                char_limit = self.max_chars_per_line * (1.1 if has_protected_content else 0.8)
                print(f"   字符检查: {avg_chars_per_line:.1f} <= {char_limit} = {avg_chars_per_line <= char_limit}")
                print(f"   保护内容: {has_protected_content}")
                
                # 如果平均每行字符数合理，且不是太多行，可以接受
                if len(lines) <= self.max_lines + 1 and avg_chars_per_line <= char_limit:
                    logger.info(f"✅ 接受AI分割: {len(lines)}行(限制{self.max_lines}), 平均{avg_chars_per_line:.1f}字符/行")
                    print(f"✅ 接受AI分割")
                else:
                    logger.warning(f"❌ AI返回行数 {len(lines)} 超过限制 {self.max_lines}")
                    print(f"❌ 拒绝AI分割")
                    return None
            
            # 验证字符长度 - 允许20%容忍度
            tolerance = self.max_chars_per_line * 1.2
            for i, line in enumerate(lines):
                if len(line) > tolerance:
                    logger.warning(f"第{i+1}行字符数 {len(line)} 超过容忍度 {tolerance}")
                    return None
            
            logger.info(f"✅ AI分割解析成功: {len(lines)}行")
            return lines
            
        except Exception as e:
            logger.error(f"AI响应解析失败: {e}")
            return None
    
    def _validate_result(self, result: List[str], original: str, protected_units: List[Dict]) -> bool:
        """验证分割结果 - 允许适当的灵活性"""
        try:
            # 1. 行数验证 - 允许适当超出，如果有合理原因
            if len(result) > self.max_lines:
                # 检查是否是AI生成的合理分割
                total_chars = sum(len(line) for line in result)
                avg_chars_per_line = total_chars / len(result)
                has_protected_content = any(
                    any(unit['text'] in line for unit in protected_units) 
                    for line in result
                )
                
                # 更宽松的字符限制，特别是当有保护内容时
                char_limit = self.max_chars_per_line * (1.1 if has_protected_content else 0.8)
                
                # 如果不超过+1行且平均字符数合理，接受
                if len(result) <= self.max_lines + 1 and avg_chars_per_line <= char_limit:
                    logger.info(f"✅ 接受合理的AI分割: {len(result)}行(限制{self.max_lines}), 平均{avg_chars_per_line:.1f}字符/行")
                else:
                    logger.warning(f"行数 {len(result)} 超过限制 {self.max_lines}")
                    return False
            
            # 2. 字符数验证 - 允许20%的灵活性
            tolerance = self.max_chars_per_line * 1.2
            for i, line in enumerate(result):
                if len(line) > tolerance:
                    logger.warning(f"第{i+1}行字符数 {len(line)} 超过容忍度 {tolerance}")
                    return False
            
            # 3. 内容完整性验证 - 放宽到70%
            combined = ''.join(result)
            content_ratio = len(combined.replace(' ', '')) / len(original.replace(' ', ''))
            if content_ratio < 0.7:
                logger.warning(f"分割后内容丢失过多: {content_ratio:.2%}")
                return False
            
            # 4. 保护单元完整性验证
            for unit in protected_units:
                unit_text = unit['text']
                if unit_text in original and not self._is_unit_intact(unit_text, result):
                    logger.warning(f"保护单元被分割: {unit_text}")
                    return False
            
            logger.info(f"✅ 分割结果验证通过: {len(result)}行, 内容保持度{content_ratio:.2%}")
            return True
            
        except Exception as e:
            logger.error(f"结果验证失败: {e}")
            return False
    
    def _is_unit_intact(self, unit_text: str, lines: List[str]) -> bool:
        """检查保护单元是否完整"""
        for line in lines:
            if unit_text in line:
                return True
        return False
    
    def _fallback_split(self, text: str, protected_units: List[Dict]) -> List[str]:
        """备用规则分割方法"""
        try:
            # 如果有保护单元，使用保护感知的分割
            if protected_units:
                return self._protected_rule_split(text, protected_units)
            
            # 否则使用普通规则分割
            return self._standard_rule_split(text)
            
        except Exception as e:
            logger.error(f"规则分割失败: {e}")
            return self._simple_split(text)
    
    def _protected_rule_split(self, text: str, protected_units: List[Dict]) -> List[str]:
        """保护感知的规则分割"""
        # 创建保护区域映射
        protected_ranges = [(unit['start'], unit['end']) for unit in protected_units]
        
        # 寻找安全的分割点
        safe_split_points = []
        
        # 在标点符号处寻找分割点
        punctuation_pattern = r'[，。！？；：]'
        for match in re.finditer(punctuation_pattern, text):
            pos = match.end()
            
            # 检查是否在保护区域内
            in_protected = False
            for start, end in protected_ranges:
                if start <= pos <= end:
                    in_protected = True
                    break
            
            if not in_protected:
                safe_split_points.append(pos)
        
        # 选择最佳分割点
        if not safe_split_points:
            return [text]  # 无法安全分割
        
        # 尝试找到最接近理想长度的分割点
        ideal_split = len(text) // 2
        best_split = min(safe_split_points, key=lambda x: abs(x - ideal_split))
        
        # 分割
        line1 = text[:best_split].strip()
        line2 = text[best_split:].strip()
        
        # 验证长度
        if len(line1) <= self.max_chars_per_line and len(line2) <= self.max_chars_per_line:
            return [line1, line2] if line2 else [line1]
        else:
            return [text]  # 无法满足长度要求
    
    def _standard_rule_split(self, text: str) -> List[str]:
        """标准规则分割"""
        # 按标点符号分割
        sentences = re.split(r'([，。！？；：])', text)
        
        lines = []
        current_line = ""
        
        for i in range(0, len(sentences), 2):
            if i < len(sentences):
                sentence = sentences[i].strip()
                punct = sentences[i + 1] if i + 1 < len(sentences) else ""
                
                if sentence:
                    full_sentence = sentence + punct
                    
                    if len(current_line + full_sentence) <= self.max_chars_per_line:
                        current_line += full_sentence
                    else:
                        if current_line:
                            lines.append(current_line.strip())
                            if len(lines) >= self.max_lines:
                                break
                        current_line = full_sentence
        
        if current_line and len(lines) < self.max_lines:
            lines.append(current_line.strip())
        
        return lines or [text]
    
    def _simple_split(self, text: str) -> List[str]:
        """简单分割（最后的保底方案）"""
        if len(text) <= self.max_chars_per_line:
            return [text]
        
        # 强制在中点附近分割
        mid_point = len(text) // 2
        
        # 寻找附近的空格或标点
        for offset in range(min(5, mid_point)):
            for pos in [mid_point + offset, mid_point - offset]:
                if pos > 0 and pos < len(text) and text[pos] in ' ，。！？；：':
                    line1 = text[:pos + 1].strip()
                    line2 = text[pos + 1:].strip()
                    
                    if len(line1) <= self.max_chars_per_line and len(line2) <= self.max_chars_per_line:
                        return [line1, line2] if line2 else [line1]
        
        # 强制分割
        return [text[:self.max_chars_per_line], text[self.max_chars_per_line:]]


# 全局实例
enhanced_semantic_splitter = EnhancedSemanticSplitter()


async def split_text_semantically(text: str) -> List[str]:
    """
    语义分割文本的便捷函数
    
    Args:
        text: 需要分割的文本
        
    Returns:
        分割后的行列表
    """
    return await enhanced_semantic_splitter.split_with_semantic_awareness(text)


if __name__ == "__main__":
    # 测试用例
    async def test_semantic_splitter():
        splitter = EnhancedSemanticSplitter()
        
        test_cases = [
            "请访问我们的官方网站：https://www.cherry-ai.com 获取更多信息",
            "联系邮箱：support@example.com 或致电400-123-4567",
            "这是一个包含技术术语的句子，比如API接口和JSON格式数据",
            "欢迎使用我们的产品，版本号为v2.1.0，支持多种操作系统",
            "访问地址：http://localhost:8080/api/v1/users 查看用户列表"
        ]
        
        for i, text in enumerate(test_cases, 1):
            print(f"\n测试用例 {i}: {text}")
            result = await splitter.split_with_semantic_awareness(text)
            print(f"分割结果: {result}")
    
    # 运行测试
    asyncio.run(test_semantic_splitter())