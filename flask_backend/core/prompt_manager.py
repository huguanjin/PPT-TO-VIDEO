"""
AI提示词管理模块
基于otherprojedt项目的设计模式，为PPT转视频项目提供结构化的提示词管理
"""
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys

# 导入配置管理器
current_dir = Path(__file__).parent.parent
utils_dir = current_dir / 'utils'
sys.path.insert(0, str(utils_dir))

try:
    from utils.config_manager import ConfigManager  # type: ignore
except ImportError:
    try:
        # 备用导入方式
        sys.path.insert(0, str(current_dir))
        from utils.config_manager import ConfigManager  # type: ignore
    except ImportError:
        ConfigManager = None

logger = logging.getLogger(__name__)

class PromptManager:
    """AI提示词管理器 - 统一管理各种AI任务的提示词模板"""
    
    def __init__(self):
        """初始化提示词管理器"""
        self.config_manager = ConfigManager() if ConfigManager else None
        self.logger = logging.getLogger(__name__)
        
        # 从配置文件加载语言设置
        self.source_language = self._load_config_key('ai.source_language', '中文')
        self.target_language = self._load_config_key('ai.target_language', '中文') 
        self.ai_service = self._load_config_key('ai.default_service', 'openai')
    
    def _load_config_key(self, key: str, default: Any) -> Any:
        """从配置文件加载键值，失败时返回默认值"""
        if not self.config_manager:
            return default
        try:
            return self.config_manager.load_key(key)
        except (KeyError, Exception) as e:
            self.logger.warning(f"无法加载配置键 {key}: {e}，使用默认值: {default}")
            return default

    # ================================================================
    # Netflix级别字幕分割提示词
    # ================================================================
    def get_subtitle_split_prompt(self, text: str, max_weight: int = 75, num_parts: int = 2) -> str:
        """
        获取字幕语义分割提示词
        
        Args:
            text: 需要分割的文本
            max_weight: 每行最大权重
            num_parts: 分割成几部分
            
        Returns:
            格式化的提示词
        """
        prompt = f"""
## Role
You are a professional Netflix subtitle editor specializing in **{self.source_language}** subtitle optimization.

## Task
Split the given subtitle text into **{num_parts}** semantically coherent parts, each with character weight ≤ **{max_weight}**.

### Character Weight Rules
- Chinese/Japanese characters: 1.75× weight
- Korean characters: 1.5× weight  
- English characters: 1.0× weight
- Punctuation: 0.8× weight
- Spaces: 0.5× weight
- Numbers: 0.8× weight

### Netflix Subtitle Standards
1. Maintain semantic coherence - never break meaningful phrases
2. Prioritize natural reading rhythm and flow
3. Split at punctuation marks when possible
4. Avoid orphan words (single characters/short words alone)
5. Ensure balanced line lengths (minimum 3 characters each)
6. Preserve original meaning and tone

## Steps
1. Calculate character weights and analyze sentence structure
2. Identify optimal split points considering semantic units
3. Generate two alternative splitting approaches
4. Compare approaches and select the best one

## Given Text
<text_to_split>
{text}
</text_to_split>

## Output in JSON format only
```json
{{
    "analysis": "Brief analysis of text structure and splitting challenges",
    "approach1": "First splitting approach with clear break markers",
    "approach2": "Alternative splitting approach with clear break markers", 
    "comparison": "Comparison of both approaches with pros and cons",
    "final_choice": "1 or 2",
    "result": "Final split text with [BREAK] markers at split points",
    "weight_check": "Verification that each part meets weight requirements"
}}
```

Note: Start your answer with ```json and end with ```, no other text.
""".strip()
        return prompt

    # ================================================================
    # PPT内容总结和术语提取提示词
    # ================================================================
    def get_ppt_summary_prompt(self, ppt_content: str, existing_terms: Optional[List[Dict]] = None) -> str:
        """
        获取PPT内容总结和术语提取提示词
        
        Args:
            ppt_content: PPT文本内容
            existing_terms: 已存在的术语列表
            
        Returns:
            格式化的提示词
        """
        # 构建已存在术语的注释
        terms_note = ""
        if existing_terms:
            terms_list = []
            for term in existing_terms:
                terms_list.append(f"- {term.get('term', '')}: {term.get('definition', '')} ({term.get('note', '')})")
            terms_note = "\\n### Existing Terms\\nPlease exclude these terms in your extraction:\\n" + "\\n".join(terms_list)

        prompt = f"""
## Role
You are a professional presentation analyst and educational content expert, specializing in {self.source_language} content comprehension and knowledge extraction.

## Task
For the provided PPT content:
1. Generate a comprehensive 2-sentence summary of the main topic
2. Extract key terms, concepts, and technical vocabulary with clear definitions
3. Provide educational context and explanations for each term

{terms_note}

### Processing Steps:
1. **Content Analysis**:
   - Quick scan for overall theme and structure
   - Identify key concepts and learning objectives
   - Note the presentation style and target audience

2. **Summary Generation**:
   - First sentence: Main topic and scope
   - Second sentence: Key insights or conclusions

3. **Term Extraction**:
   - Extract important terminology and concepts (max 15 terms)
   - Provide clear, concise definitions
   - Add educational context where helpful
   - Exclude overly common words and existing terms

## INPUT
<ppt_content>
{ppt_content}
</ppt_content>

## Output in JSON format only
```json
{{
  "summary": "Two-sentence comprehensive summary of the PPT content",
  "key_topics": ["topic1", "topic2", "topic3"],
  "terms": [
    {{
      "term": "extracted term",
      "definition": "clear definition or explanation", 
      "note": "additional context or usage example",
      "importance": "high/medium/low"
    }},
    ...
  ],
  "presentation_style": "educational/business/technical/casual",
  "target_audience": "estimated target audience"
}}
```

## Example Output
```json
{{
  "summary": "本PPT介绍了人工智能在现代教育中的应用现状和发展趋势。重点阐述了AI技术如何个性化学习体验并提高教学效率。",
  "key_topics": ["人工智能", "个性化学习", "教学效率", "技术应用"],
  "terms": [
    {{
      "term": "机器学习",
      "definition": "让计算机通过数据学习规律的技术",
      "note": "AI的核心技术之一，可用于学习行为分析",
      "importance": "high"
    }}
  ],
  "presentation_style": "educational",
  "target_audience": "educators and technology enthusiasts"
}}
```

Note: Start your answer with ```json and end with ```, no other text.
""".strip()
        return prompt

    # ================================================================
    # 配音文本优化提示词
    # ================================================================
    def get_tts_optimization_prompt(self, text: str, target_duration: float, style: str = "natural") -> str:
        """
        获取TTS配音文本优化提示词
        
        Args:
            text: 原始文本
            target_duration: 目标时长（秒）
            style: 配音风格 (natural/formal/casual/energetic)
            
        Returns:
            格式化的提示词
        """
        style_guides = {
            "natural": "自然流畅，适合日常对话和教学场景",
            "formal": "正式严谨，适合商务演示和学术报告", 
            "casual": "轻松随意，适合生活化内容和娱乐场景",
            "energetic": "活力充沛，适合激励性内容和广告配音"
        }
        
        style_description = style_guides.get(style, style_guides["natural"])
        
        prompt = f"""
## Role
You are a professional voiceover script editor and TTS optimization expert, specializing in {self.source_language} speech optimization.

## Task
Optimize the given text for TTS (Text-to-Speech) synthesis to achieve the target duration while maintaining naturalness and clarity.

### Target Specifications
- **Duration**: {target_duration} seconds
- **Style**: {style} ({style_description})
- **Language**: {self.source_language}

### Optimization Rules
1. **Content Preservation**: Maintain core message and meaning
2. **Natural Flow**: Ensure smooth, conversational rhythm
3. **TTS-Friendly**: Remove complex punctuation, optimize for speech synthesis
4. **Duration Control**: Adjust content length to match target duration
   - Average speaking rate: 150-180 words/minute for Chinese
   - Add pauses with commas for better pacing
   - Remove filler words and redundant expressions

### Processing Steps
1. Analyze original text structure and identify key messages
2. Calculate estimated speaking time and adjust content accordingly
3. Optimize for TTS synthesis (punctuation, numbers, abbreviations)
4. Apply style-specific adjustments
5. Verify final result meets duration and quality requirements

## INPUT
<original_text>
{text}
</original_text>

## Output in JSON format only
```json
{{
    "analysis": "Analysis of original text length, complexity, and optimization needs",
    "estimated_original_duration": "estimated seconds for original text",
    "optimization_strategy": "approach taken to meet target duration and style",
    "optimized_text": "final TTS-optimized text",
    "estimated_final_duration": "estimated seconds for optimized text",
    "style_adjustments": "specific changes made for the target style",
    "tts_notes": "special considerations for TTS synthesis"
}}
```

## Style Guidelines
- **Natural**: Conversational tone, moderate pace, clear articulation
- **Formal**: Professional language, measured pace, precise pronunciation
- **Casual**: Relaxed tone, natural pauses, friendly delivery
- **Energetic**: Dynamic rhythm, varied intonation, engaging delivery

Note: Start your answer with ```json and end with ```, no other text.
""".strip()
        return prompt

    # ================================================================
    # PPT内容理解和解说词生成提示词
    # ================================================================
    def get_ppt_narration_prompt(self, slide_content: str, slide_context: str = "", narration_style: str = "educational") -> str:
        """
        获取PPT解说词生成提示词
        
        Args:
            slide_content: 幻灯片内容
            slide_context: 幻灯片上下文
            narration_style: 解说风格
            
        Returns:
            格式化的提示词
        """
        style_guides = {
            "educational": "教育性强，解释详细，适合学习场景",
            "presentation": "演示风格，重点突出，适合商务汇报",
            "story": "故事化叙述，生动有趣，适合知识科普",
            "conversational": "对话式风格，亲切自然，适合日常分享"
        }
        
        style_description = style_guides.get(narration_style, style_guides["educational"])
        
        prompt = f"""
## Role
You are a professional presentation narrator and educational content creator, expert in transforming slide content into engaging spoken narration.

## Task
Generate natural, flowing narration for the given PPT slide content that enhances understanding and engagement.

### Narration Requirements
- **Style**: {narration_style} ({style_description})
- **Language**: {self.source_language}
- **Purpose**: Transform visual content into compelling audio narrative

### Content Guidelines
1. **Clarity**: Make complex concepts accessible and easy to understand
2. **Engagement**: Use conversational tone and relatable examples
3. **Structure**: Logical flow with smooth transitions
4. **Completeness**: Cover all key points without redundancy
5. **Speaking-Friendly**: Optimize for natural speech patterns

### Context Integration
- Reference previous/next content when provided
- Maintain consistency with overall presentation theme
- Bridge visual elements with verbal descriptions

## INPUT
<slide_content>
{slide_content}
</slide_content>

<context>
{slide_context}
</context>

## Output in JSON format only
```json
{{
    "content_analysis": "analysis of slide key points and visual elements",
    "narrative_approach": "chosen approach for this specific slide",
    "main_narration": "primary narration text optimized for speech",
    "alternative_version": "alternative narration approach for comparison",
    "speaking_notes": "guidance for tone, pace, and emphasis",
    "estimated_duration": "estimated speaking time in seconds",
    "transition_suggestions": "how to connect with previous/next slides"
}}
```

## Style Specifications
- **Educational**: Explain concepts step-by-step, provide context and examples
- **Presentation**: Highlight key points, use confident and authoritative tone
- **Story**: Create narrative flow, use analogies and engaging scenarios  
- **Conversational**: Speak directly to audience, use inclusive language

Note: Start your answer with ```json and end with ```, no other text.
""".strip()
        return prompt

    # ================================================================
    # 文本清理和格式化提示词 (TTS专用)
    # ================================================================
    def get_text_cleanup_prompt(self, text: str) -> str:
        """
        获取TTS文本清理提示词
        
        Args:
            text: 需要清理的文本
            
        Returns:
            格式化的提示词
        """
        prompt = f"""
## Role
You are a TTS (Text-to-Speech) text preprocessing expert for {self.source_language} content.

## Task
Clean and optimize the given text for high-quality TTS synthesis by removing or converting elements that cause pronunciation issues.

### Cleaning Rules
1. **Punctuation**: Keep only basic punctuation (.,?!;:) that aids speech rhythm
2. **Numbers**: Convert to spoken form (e.g., "2024年" → "二零二四年")
3. **Symbols**: Remove or convert special characters to spoken equivalents
4. **Abbreviations**: Expand to full words when necessary
5. **URLs/Emails**: Remove or convert to readable format
6. **Formatting**: Remove markdown, HTML tags, and formatting codes
7. **Spacing**: Normalize whitespace and line breaks

### Preservation Guidelines
- Maintain original meaning and context
- Keep natural sentence structure
- Preserve important pauses with commas
- Retain emphasis through word choice, not formatting

## INPUT
<text_to_clean>
{text}
</text_to_clean>

## Output in JSON format only
```json
{{
    "original_issues": "identified problematic elements in original text",
    "cleaning_steps": "specific cleaning operations performed",
    "cleaned_text": "final TTS-optimized text",
    "pronunciation_notes": "special pronunciation considerations if any"
}}
```

Note: Start your answer with ```json and end with ```, no other text.
""".strip()
        return prompt

    # ================================================================
    # 通用API调用方法
    # ================================================================
    def format_prompt_for_api(self, prompt: str, system_message: str = "") -> Dict[str, Any]:
        """
        为API调用格式化提示词
        
        Args:
            prompt: 主要提示词内容
            system_message: 系统消息（可选）
            
        Returns:
            格式化的API请求参数
        """
        if not system_message:
            system_message = f"You are a professional AI assistant specialized in {self.source_language} content processing and optimization."
        
        return {
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 2000,
            "response_format": {"type": "json_object"} if self.ai_service == "openai" else None
        }

    # ================================================================
    # 提示词模板管理
    # ================================================================
    def get_available_prompts(self) -> List[str]:
        """获取所有可用的提示词类型"""
        return [
            "subtitle_split",
            "ppt_summary", 
            "tts_optimization",
            "ppt_narration",
            "text_cleanup"
        ]
    
    def get_prompt_description(self, prompt_type: str) -> str:
        """获取提示词类型的描述"""
        descriptions = {
            "subtitle_split": "Netflix级别字幕语义分割，支持多语言权重计算",
            "ppt_summary": "PPT内容总结和关键术语提取，适合教育内容分析",
            "tts_optimization": "TTS配音文本优化，支持时长控制和风格调整",
            "ppt_narration": "PPT解说词生成，将视觉内容转换为口语化叙述",
            "text_cleanup": "TTS文本清理，移除影响语音合成质量的元素"
        }
        return descriptions.get(prompt_type, "未知提示词类型")

if __name__ == "__main__":
    # 测试提示词管理器
    prompt_manager = PromptManager()
    
    # 测试字幕分割提示词
    test_text = "人工智能技术正在快速发展，它在教育、医疗、交通等各个领域都有广泛的应用前景。"
    split_prompt = prompt_manager.get_subtitle_split_prompt(test_text, max_weight=75)
    print("字幕分割提示词生成成功")
    
    # 测试PPT总结提示词
    ppt_content = "今天我们来学习机器学习的基本概念和应用。机器学习是人工智能的一个重要分支。"
    summary_prompt = prompt_manager.get_ppt_summary_prompt(ppt_content)
    print("PPT总结提示词生成成功")
    
    print(f"\\n可用提示词类型: {prompt_manager.get_available_prompts()}")
