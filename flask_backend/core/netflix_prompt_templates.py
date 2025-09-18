"""
Netflix专业提示词模板系统 - Phase 2核心实现
设计角色定位、任务说明、分析工作流的Netflix级别提示词模板
"""

import json
import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from abc import ABC, abstractmethod

from flask_backend.core.unified_config_manager import UnifiedConfigManager, ConfigContext, ConfigModuleType, ConfigComplexityLevel

@dataclass
class PromptContext:
    """提示词上下文数据类"""
    text: str
    target_lines: int
    complexity_score: float
    protected_units: List[Dict[str, Any]]
    split_candidates: List[Dict[str, Any]]
    linguistic_features: Dict[str, Any]
    quality_requirements: Dict[str, Any]
    previous_attempts: List[Dict[str, Any]]
    
    def get_char_count(self) -> int:
        return len(self.text)
    
    def get_word_count(self) -> int:
        # 中英文混合计数
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', self.text))
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', self.text))
        return chinese_chars + english_words
    
    def get_difficulty_level(self) -> str:
        """根据复杂度评估难度等级"""
        if self.complexity_score <= 3:
            return '简单'
        elif self.complexity_score <= 6:
            return '中等'
        elif self.complexity_score <= 8:
            return '困难'
        else:
            return '极难'

class NetflixPromptTemplate(ABC):
    """Netflix提示词模板抽象基类"""
    
    @abstractmethod
    def generate_prompt(self, context: PromptContext) -> str:
        """生成提示词"""
        pass
    
    @abstractmethod
    def get_template_name(self) -> str:
        """获取模板名称"""
        pass

class NetflixStandardPromptTemplate(NetflixPromptTemplate):
    """Netflix标准提示词模板"""
    
    def __init__(self, config_manager: Optional[UnifiedConfigManager] = None):
        self.config = config_manager or UnifiedConfigManager()
        # 创建Netflix配置上下文
        self.context = ConfigContext(
            module_type=ConfigModuleType.NETFLIX,
            complexity_level=ConfigComplexityLevel.PROFESSIONAL,
            preset_name="netflix_optimized"
        )
        self.netflix_config = self.config.get_config(self.context)
        self.netflix_standards = self.netflix_config.get('netflix_standards', {})
        self.ai_settings = self.netflix_config.get('ai_settings', {})
        self.logger = logging.getLogger(__name__)
    
    def generate_prompt(self, context: PromptContext) -> str:
        """生成Netflix标准提示词"""
        
        # 构建核心提示词结构
        prompt_sections = [
            self._build_role_section(),
            self._build_task_section(context),
            self._build_standards_section(),
            self._build_analysis_section(context),
            self._build_candidate_guidance_section(context),
            self._build_workflow_section(),
            self._build_output_format_section()
        ]
        
        return "\n\n".join(prompt_sections)
    
    def get_template_name(self) -> str:
        return "netflix_standard"
    
    def _build_role_section(self) -> str:
        """构建角色定位部分"""
        return """## Role & Expertise
你是一位资深的Netflix中文字幕分割专家，具备以下专业能力：
- **语言学背景**：精通现代汉语语法结构、语义分析和语用学原理
- **Netflix认证**：熟悉Netflix全球字幕标准，拥有国际字幕制作经验
- **技术专长**：教育内容字幕优化、单行显示策略、跨设备适配
- **质量保证**：追求90%+的分割准确度和用户体验优化

## Professional Standards
- 遵循Netflix单行字幕显示最佳实践
- 确保语义完整性和阅读连贯性
- 保持技术术语和专有名词的完整性
- 优化移动设备和大屏幕的显示效果"""
    
    def _build_task_section(self, context: PromptContext) -> str:
        """构建任务说明部分"""
        difficulty = context.get_difficulty_level()
        char_count = context.get_char_count()
        word_count = context.get_word_count()
        
        return f"""## Current Task
**任务类型**：教育内容字幕分割优化
**目标行数**：{context.target_lines}行
**难度等级**：{difficulty} (复杂度评分: {context.complexity_score:.1f}/10)

**文本特征**：
- 总字符数：{char_count}个字符
- 词汇数量：{word_count}个词汇
- 保护单元：{len(context.protected_units)}个特殊内容
- 分割挑战：{self._analyze_split_challenges(context)}

**质量要求**：
- 单行显示优先，确保移动端可读性
- 语义边界完整，避免破坏概念表达
- 长度均衡合理，最大比例不超过{self.netflix_standards.get('length_balance_ratio', 2.5)}:1
- 保护单元完整性100%保持"""
    
    def _build_standards_section(self) -> str:
        """构建Netflix标准部分"""
        max_chars = self.netflix_standards.get('max_chars_per_line', 20)
        min_chars = self.netflix_standards.get('min_chars_per_line', 3)
        
        return f"""## Netflix Global Standards
**字符限制**：
- 每行最多{max_chars}个字符 (严格限制)
- 每行最少{min_chars}个字符 (避免孤立短句)
- 中英文混合时按字符数计算

**显示规范**：
- 单行完整表达，减少跨行阅读负担
- 避免在词汇中间分割 (特别是专业术语)
- 标点符号遵循中文排版规范
- 保持逻辑连接词的语境完整

**质量标准**：
- 语义保持度：≥95% (SequenceMatcher算法验证)
- 可读性评分：≥85分 (Netflix内部标准)
- 平衡性指标：长度比例≤2.5:1
- 错误容忍度：0个关键信息丢失"""
    
    def _build_analysis_section(self, context: PromptContext) -> str:
        """构建分析部分"""
        protected_info = self._format_protected_units(context.protected_units)
        linguistic_info = self._format_linguistic_features(context.linguistic_features)
        
        return f"""## Text Deep Analysis
**原始文本**：{context.text}

**语言学特征分析**：
{linguistic_info}

**保护单元识别**：
{protected_info}

**复杂性评估**：
- 整体复杂度：{context.complexity_score:.2f}/10
- 主要挑战：{self._identify_main_challenges(context)}
- 建议策略：{self._suggest_split_strategy(context)}"""
    
    def _build_candidate_guidance_section(self, context: PromptContext) -> str:
        """构建候选引导部分"""
        candidates_info = self._format_split_candidates(context.split_candidates, context.text)
        
        return f"""## NLP Analysis & Candidate Guidance
基于深度语言学分析，系统识别出以下优质分割候选点：

{candidates_info}

**分割决策指导**：
1. **优先选择**：标点符号边界，特别是句号、感叹号、问号
2. **次优选择**：逻辑连接词前后，如"但是"、"因此"、"而且"
3. **可考虑选择**：动词短语边界、名词短语边界
4. **避免选择**：专业术语中间、URL/邮箱中间、数字表达式中间

**质量评估标准**：
- 每个候选点都有NLP算法计算的置信度评分
- 综合考虑语法结构、语义连贯性、显示效果
- 确保分割后每部分都是独立的语义单元"""
    
    def _build_workflow_section(self) -> str:
        """构建工作流程部分"""
        return """## Professional Workflow
请按照以下Netflix认证工作流程进行分割：

### Step 1: Structure Analysis (结构分析)
- 识别文本的主要语法结构 (主谓宾、定状补)
- 分析句子层次和逻辑关系
- 确定核心信息点和支撑细节

### Step 2: Challenge Identification (挑战识别)
- 识别可能影响分割质量的关键因素
- 评估保护单元的分布和影响
- 分析长度限制对表达完整性的影响

### Step 3: Strategy Selection (策略选择)
- 基于文本特征选择最佳分割策略
- 平衡语义完整性和显示限制
- 考虑用户阅读体验和理解效果

### Step 4: Dual Approach Generation (双方案生成)
- 生成两种不同的高质量分割方案
- 每种方案采用不同的分割理念或技术
- 确保两种方案都符合Netflix基础标准

### Step 5: Comparative Assessment (比较评估)
- 从可读性、语义保持、显示效果三个维度评估
- 识别每种方案的独特优势和潜在劣势
- 基于当前文本特征进行针对性分析

### Step 6: Optimal Selection (最优选择)
- 综合评估结果选择最佳方案
- 提供清晰的选择理由和技术依据
- 确保选择符合Netflix专业标准"""
    
    def _build_output_format_section(self) -> str:
        """构建输出格式部分"""
        return """## Output Format (严格JSON格式)
请严格按照以下JSON结构输出，确保语法正确且包含所有必需字段：

```json
{
    "structure_analysis": "简要描述文本的语法结构、主要语义单元和分割难点",
    "challenge_identification": "识别的主要分割挑战，包括保护单元、长度限制、语义边界等",
    "strategy_rationale": "选择的分割策略说明，包括优先考虑的因素和权衡决策",
    
    "split_approach_1": {
        "method": "第一种分割方法的技术名称 (如: 标点分割法、语法边界法、语义单元法)",
        "result": "分割结果，用[分割]标记分割位置",
        "reasoning": "该方法的具体理由和优势分析"
    },
    
    "split_approach_2": {
        "method": "第二种分割方法的技术名称",
        "result": "分割结果，用[分割]标记分割位置", 
        "reasoning": "该方法的具体理由和优势分析"
    },
    
    "comparative_assessment": {
        "readability_comparison": "两种方案的可读性对比分析",
        "semantic_preservation": "语义保持度的详细比较",
        "display_optimization": "显示效果和用户体验对比",
        "technical_compliance": "Netflix技术标准符合度评估"
    },
    
    "final_decision": {
        "choice": "1 或 2",
        "primary_reasons": ["选择该方案的主要理由1", "主要理由2", "主要理由3"],
        "technical_advantages": "该方案的技术优势说明",
        "quality_metrics": {
            "netflix_compliant": true/false,
            "protected_units_preserved": true/false,
            "readability_score": "估算的可读性评分 (1-10)",
            "semantic_integrity": "语义完整性评分 (1-10)"
        }
    }
}
```

**输出要求**：
- 必须是有效的JSON格式，不包含任何额外的文本或代码块标记
- 所有字符串字段都要填写，不能留空
- choice字段只能是"1"或"2"
- 布尔值字段使用true/false，不使用字符串
- 分割结果中必须使用[分割]标记，不使用其他符号"""
    
    def _analyze_split_challenges(self, context: PromptContext) -> str:
        """分析分割挑战"""
        challenges = []
        
        if context.complexity_score > 7:
            challenges.append("高复杂度语法结构")
        
        if len(context.protected_units) > 3:
            challenges.append("多个保护单元分布")
        
        if context.get_char_count() > context.target_lines * self.netflix_standards.get('max_chars_per_line', 20):
            challenges.append("内容密度过高")
        
        if context.target_lines > 3:
            challenges.append("多行分割均衡")
        
        return "、".join(challenges) if challenges else "无特殊挑战"
    
    def _format_protected_units(self, protected_units: List[Dict]) -> str:
        """格式化保护单元信息"""
        if not protected_units:
            return "未检测到需要特殊保护的内容"
        
        formatted = []
        for i, unit in enumerate(protected_units[:5], 1):  # 只显示前5个
            unit_type = unit.get('type', '未知')
            unit_text = unit.get('text', '')
            confidence = unit.get('confidence', 0)
            formatted.append(f"  {i}. [{unit_type}] '{unit_text}' (置信度: {confidence:.2f})")
        
        if len(protected_units) > 5:
            formatted.append(f"  ... 还有{len(protected_units) - 5}个保护单元")
        
        return "\n".join(formatted)
    
    def _format_linguistic_features(self, features: Dict[str, Any]) -> str:
        """格式化语言学特征"""
        if not features:
            return "语言学特征分析未完成"
        
        formatted = []
        if 'verb_count' in features:
            formatted.append(f"动词数量：{features['verb_count']}个")
        if 'noun_count' in features:
            formatted.append(f"名词数量：{features['noun_count']}个")
        if 'sentence_count' in features:
            formatted.append(f"句子数量：{features['sentence_count']}个")
        if 'clause_count' in features:
            formatted.append(f"分句数量：{features['clause_count']}个")
        
        return "、".join(formatted) if formatted else "基础特征分析完成"
    
    def _format_split_candidates(self, candidates: List[Dict], text: str) -> str:
        """格式化分割候选点"""
        if not candidates:
            return "**注意**：未发现明显的优质分割候选点，需要依靠专业判断进行分割"
        
        formatted = ["**推荐分割候选点**："]
        
        for i, candidate in enumerate(candidates[:6], 1):  # 显示前6个最佳候选点
            pos = candidate.get('char_position', 0)
            token = candidate.get('token', '')
            score = candidate.get('score', 0)
            reasons = candidate.get('reasons', [])
            
            # 获取上下文
            context_start = max(0, pos - 8)
            context_end = min(len(text), pos + 9)
            context = text[context_start:context_end]
            
            # 在上下文中标记候选点
            mark_pos = pos - context_start
            marked_context = context[:mark_pos] + f'【{token}】' + context[mark_pos + len(token):]
            
            reason_text = "、".join(reasons) if reasons else "语法边界"
            
            formatted.append(f"  候选点{i}: 评分{score:.2f} | 位置{pos} | 原因:{reason_text}")
            formatted.append(f"    上下文: \"{marked_context}\"")
        
        if len(candidates) > 6:
            formatted.append(f"  ... 还有{len(candidates) - 6}个候选点可供参考")
        
        return "\n".join(formatted)
    
    def _identify_main_challenges(self, context: PromptContext) -> str:
        """识别主要挑战"""
        challenges = []
        
        # 基于复杂度评估
        if context.complexity_score > 8:
            challenges.append("复杂语法结构需要精确语义边界识别")
        elif context.complexity_score > 6:
            challenges.append("中等复杂度需要平衡语义和显示")
        
        # 基于长度评估
        char_count = context.get_char_count()
        max_total = context.target_lines * self.netflix_standards.get('max_chars_per_line', 20)
        if char_count > max_total * 0.9:
            challenges.append("字符密度高需要紧凑但清晰的表达")
        
        # 基于保护单元
        if len(context.protected_units) > 2:
            challenges.append("多个保护单元需要避免破坏完整性")
        
        return "、".join(challenges) if challenges else "标准分割任务"
    
    def _suggest_split_strategy(self, context: PromptContext) -> str:
        """建议分割策略"""
        strategies = []
        
        # 基于分割候选点
        if context.split_candidates:
            high_score_candidates = [c for c in context.split_candidates if c.get('score', 0) > 0.8]
            if high_score_candidates:
                strategies.append("优先使用高分候选点进行分割")
            else:
                strategies.append("综合考虑多个中等分候选点")
        
        # 基于复杂度
        if context.complexity_score > 7:
            strategies.append("采用语义单元分割法保持表达完整")
        else:
            strategies.append("可以采用标点符号分割法")
        
        # 基于目标行数
        if context.target_lines == 2:
            strategies.append("寻找最佳单一分割点")
        else:
            strategies.append("多点分割需要保持长度均衡")
        
        return "、".join(strategies)

class NetflixEducationalPromptTemplate(NetflixStandardPromptTemplate):
    """Netflix教育内容专用提示词模板"""
    
    def get_template_name(self) -> str:
        return "netflix_educational"
    
    def _build_role_section(self) -> str:
        """教育内容专门的角色定位"""
        return """## Role & Educational Expertise  
你是一位专精教育内容的Netflix中文字幕专家，具备：
- **教育技术背景**：深入理解教学内容的信息层次和学习认知规律
- **字幕教育学**：掌握教育视频字幕对学习效果的影响机制
- **专业术语处理**：精通各学科专业术语的准确表达和理解
- **认知负荷优化**：通过字幕设计减少学习者的认知负担

## Educational Content Standards
- 确保专业概念的完整性和准确性
- 保持教学逻辑的清晰性和连贯性  
- 优化知识点的显示和理解效果
- 照顾不同学习水平的理解需求"""
    
    def _build_standards_section(self) -> str:
        """教育内容的特殊标准"""
        base_standards = super()._build_standards_section()
        
        educational_standards = """
**教育内容特殊要求**：
- 专业术语100%完整保持，不允许截断
- 定义性表述保持在同一字幕行内
- 数学公式、化学式等符号表达完整显示
- 因果关系、逻辑推理链条保持连贯
- 关键概念突出显示，避免被分割掩盖"""
        
        return base_standards + educational_standards

class NetflixPromptTemplateManager:
    """Netflix提示词模板管理器"""
    
    def __init__(self, config_manager: Optional[UnifiedConfigManager] = None):
        self.config = config_manager or UnifiedConfigManager()
        self.logger = logging.getLogger(__name__)
        
        # 创建Netflix配置上下文
        self.context = ConfigContext(
            module_type=ConfigModuleType.NETFLIX,
            complexity_level=ConfigComplexityLevel.PROFESSIONAL,
            preset_name="netflix_optimized"
        )
        self.netflix_config = self.config.get_config(self.context)
        self.ai_settings = self.netflix_config.get('ai_settings', {})
        
        # 注册可用模板
        self.templates = {
            'standard': NetflixStandardPromptTemplate(config_manager),
            'educational': NetflixEducationalPromptTemplate(config_manager)
        }
        
        # 默认模板
        self.default_template = self.ai_settings.get('prompt_style', 'netflix_professional')
        if self.default_template == 'netflix_professional':
            self.default_template = 'standard'
        
        self.logger.info(f"提示词模板管理器初始化完成，默认模板: {self.default_template}")
    
    def generate_prompt(self, context: PromptContext, 
                       template_name: Optional[str] = None) -> str:
        """生成提示词"""
        
        template_name = template_name or self.default_template
        
        if template_name not in self.templates:
            self.logger.warning(f"未知模板: {template_name}，使用默认模板: standard")
            template_name = 'standard'
        
        template = self.templates[template_name]
        
        try:
            prompt = template.generate_prompt(context)
            self.logger.info(f"成功生成提示词，模板: {template_name}，长度: {len(prompt)}")
            return prompt
            
        except Exception as e:
            self.logger.error(f"提示词生成失败: {e}")
            # 回退到基础模板
            if template_name != 'standard':
                return self.generate_prompt(context, 'standard')
            else:
                raise
    
    def register_template(self, name: str, template: NetflixPromptTemplate):
        """注册新的提示词模板"""
        self.templates[name] = template
        self.logger.info(f"注册新模板: {name}")
    
    def list_templates(self) -> List[str]:
        """列出所有可用模板"""
        return list(self.templates.keys())
    
    def get_template_info(self, template_name: str) -> Dict[str, Any]:
        """获取模板信息"""
        if template_name not in self.templates:
            return {'error': f'模板不存在: {template_name}'}
        
        template = self.templates[template_name]
        return {
            'name': template.get_template_name(),
            'class': template.__class__.__name__,
            'available': True
        }
    
    def validate_prompt_output(self, output: str) -> Dict[str, Any]:
        """验证提示词输出格式"""
        try:
            # 尝试解析JSON
            if output.strip().startswith('```json'):
                output = output.strip()[7:]
            if output.strip().endswith('```'):
                output = output.strip()[:-3]
            
            data = json.loads(output.strip())
            
            # 检查必需字段
            required_fields = [
                'structure_analysis', 'challenge_identification', 'strategy_rationale',
                'split_approach_1', 'split_approach_2', 'comparative_assessment', 'final_decision'
            ]
            
            missing_fields = []
            for field in required_fields:
                if field not in data:
                    missing_fields.append(field)
            
            # 检查final_decision的子字段
            if 'final_decision' in data:
                decision_fields = ['choice', 'primary_reasons', 'technical_advantages', 'quality_metrics']
                for field in decision_fields:
                    if field not in data['final_decision']:
                        missing_fields.append(f'final_decision.{field}')
            
            return {
                'valid': len(missing_fields) == 0,
                'missing_fields': missing_fields,
                'parsed_data': data if len(missing_fields) == 0 else None,
                'format': 'json'
            }
            
        except json.JSONDecodeError as e:
            return {
                'valid': False,
                'error': f'JSON解析失败: {e}',
                'format': 'invalid_json'
            }
        except Exception as e:
            return {
                'valid': False,
                'error': f'验证异常: {e}',
                'format': 'unknown'
            }
    
    def create_context_from_nlp_result(self, text: str, target_lines: int, 
                                     nlp_result: Dict[str, Any]) -> PromptContext:
        """从NLP预处理结果创建提示词上下文"""
        
        # 提取NLP结果中的信息
        complexity_score = nlp_result.get('complexity', 5.0)
        protected_units = nlp_result.get('semantic_units', [])
        split_candidates = nlp_result.get('split_candidates', [])
        linguistic_features = nlp_result.get('linguistic_features', {})
        
        # 质量要求
        quality_requirements = {
            'min_similarity': self.netflix_config.get('line_break_rules', {}).get('similarity_threshold', 0.9),
            'max_chars_per_line': self.netflix_config.get('line_break_rules', {}).get('max_chars_per_line_chinese', 20),
            'netflix_compliant': True
        }
        
        return PromptContext(
            text=text,
            target_lines=target_lines,
            complexity_score=complexity_score,
            protected_units=protected_units,
            split_candidates=split_candidates,
            linguistic_features=linguistic_features,
            quality_requirements=quality_requirements,
            previous_attempts=[]
        )
    
    def get_prompt_statistics(self, prompt: str) -> Dict[str, Any]:
        """获取提示词统计信息"""
        lines = prompt.split('\n')
        chars = len(prompt)
        words = len(prompt.split())
        
        # 统计各个section
        sections = {}
        current_section = None
        
        for line in lines:
            if line.startswith('## '):
                current_section = line[3:].strip()
                sections[current_section] = 0
            elif current_section:
                sections[current_section] += len(line)
        
        return {
            'total_chars': chars,
            'total_lines': len(lines),
            'word_count': words,
            'sections': sections,
            'estimated_tokens': chars // 4,  # 粗略估算
            'complexity': 'high' if chars > 3000 else 'medium' if chars > 1500 else 'low'
        }