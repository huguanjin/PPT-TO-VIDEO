"""
Netflix级字符权重计算系统
基于VideoLingo的CJK字符权重标准，实现精确的字符权重计算
符合Netflix专业字幕制作规范
"""
import re
import unicodedata
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class CharacterWeightConfig:
    """字符权重配置"""
    # Netflix标准CJK权重
    cjk_weight: float = 1.75
    latin_weight: float = 1.0
    
    # 精细化权重配置
    chinese_weight: float = 1.75
    japanese_weight: float = 1.75
    korean_weight: float = 1.75
    english_weight: float = 1.0
    number_weight: float = 0.8
    punctuation_weight: float = 0.6
    space_weight: float = 0.3
    emoji_weight: float = 1.5
    symbol_weight: float = 0.7
    
    # Netflix标准配置
    max_line_length: int = 42
    max_lines: int = 2
    reading_speed_cps: float = 17.0  # 每秒字符数
    min_subtitle_duration: float = 1.0  # 最小显示时间(秒)
    max_subtitle_duration: float = 6.0  # 最大显示时间(秒)


class NetflixCharacterWeightCalculator:
    """Netflix级字符权重计算器"""
    
    def __init__(self, config: Optional[CharacterWeightConfig] = None):
        self.config = config or CharacterWeightConfig()
        
        # 构建字符分类缓存
        self._char_cache = {}
        
        # CJK字符范围 (基于Unicode标准)
        self.cjk_ranges = [
            (0x4E00, 0x9FFF),   # CJK统一汉字
            (0x3400, 0x4DBF),   # CJK扩展A
            (0x20000, 0x2A6DF), # CJK扩展B
            (0x2A700, 0x2B73F), # CJK扩展C
            (0x2B740, 0x2B81F), # CJK扩展D
            (0x2B820, 0x2CEAF), # CJK扩展E
            (0x2CEB0, 0x2EBEF), # CJK扩展F
            (0x3000, 0x303F),   # CJK符号和标点
            (0x31C0, 0x31EF),   # CJK笔画
            (0x3200, 0x32FF),   # 带圈CJK字符
            (0x3300, 0x33FF),   # CJK兼容
            (0xF900, 0xFAFF),   # CJK兼容汉字
            (0xFE30, 0xFE4F),   # CJK兼容形式
            # 日文特有
            (0x3040, 0x309F),   # 平假名
            (0x30A0, 0x30FF),   # 片假名
            (0x31F0, 0x31FF),   # 片假名扩展
            # 韩文特有
            (0xAC00, 0xD7AF),   # 韩文音节
            (0x1100, 0x11FF),   # 韩文字母
            (0x3130, 0x318F),   # 韩文兼容字母
            (0xA960, 0xA97F),   # 韩文扩展A
            (0xD7B0, 0xD7FF),   # 韩文扩展B
        ]
        
        logger.info(f"Netflix字符权重计算器初始化完成 - CJK权重: {self.config.cjk_weight}")
    
    def _is_cjk_character(self, char: str) -> bool:
        """判断是否为CJK字符"""
        if char in self._char_cache:
            return self._char_cache[char]
        
        char_code = ord(char)
        is_cjk = any(start <= char_code <= end for start, end in self.cjk_ranges)
        
        self._char_cache[char] = is_cjk
        return is_cjk
    
    def _get_character_category(self, char: str) -> str:
        """获取字符分类"""
        # Unicode分类
        category = unicodedata.category(char)
        
        # CJK字符
        if self._is_cjk_character(char):
            # 进一步细分CJK字符
            char_code = ord(char)
            if 0x4E00 <= char_code <= 0x9FFF:
                return 'chinese'
            elif 0x3040 <= char_code <= 0x30FF:
                return 'japanese'
            elif 0xAC00 <= char_code <= 0xD7AF:
                return 'korean'
            else:
                return 'cjk_other'
        
        # 拉丁字符
        if category.startswith('L') and ord(char) < 256:
            return 'latin'
        
        # 数字
        if category.startswith('N'):
            return 'number'
        
        # 标点符号
        if category.startswith('P'):
            return 'punctuation'
        
        # 空格
        if category.startswith('Z'):
            return 'space'
        
        # 符号
        if category.startswith('S'):
            # 检查是否为emoji
            if self._is_emoji(char):
                return 'emoji'
            return 'symbol'
        
        # 其他
        return 'other'
    
    def _is_emoji(self, char: str) -> bool:
        """简单的emoji检测"""
        char_code = ord(char)
        # 常见emoji范围
        emoji_ranges = [
            (0x1F600, 0x1F64F),  # 表情符号
            (0x1F300, 0x1F5FF),  # 杂项符号
            (0x1F680, 0x1F6FF),  # 交通和地图符号
            (0x1F700, 0x1F77F),  # 炼金术符号
            (0x1F780, 0x1F7FF),  # 几何形状扩展
            (0x1F800, 0x1F8FF),  # 补充箭头C
            (0x2600, 0x26FF),    # 杂项符号
            (0x2700, 0x27BF),    # 装饰符号
            (0xFE00, 0xFE0F),    # 变体选择器
        ]
        return any(start <= char_code <= end for start, end in emoji_ranges)
    
    def get_character_weight(self, char: str) -> float:
        """获取单个字符的权重"""
        category = self._get_character_category(char)
        
        weight_map = {
            'chinese': self.config.chinese_weight,
            'japanese': self.config.japanese_weight,
            'korean': self.config.korean_weight,
            'cjk_other': self.config.cjk_weight,
            'latin': self.config.english_weight,
            'number': self.config.number_weight,
            'punctuation': self.config.punctuation_weight,
            'space': self.config.space_weight,
            'emoji': self.config.emoji_weight,
            'symbol': self.config.symbol_weight,
            'other': self.config.english_weight  # 默认权重
        }
        
        return weight_map.get(category, 1.0)
    
    def calculate_text_weight(self, text: str) -> float:
        """计算文本总权重"""
        if not text:
            return 0.0
        
        total_weight = 0.0
        for char in text:
            total_weight += self.get_character_weight(char)
        
        return total_weight
    
    def calculate_text_metrics(self, text: str) -> Dict[str, Any]:
        """计算文本详细度量"""
        if not text:
            return {
                'total_weight': 0.0,
                'character_count': 0,
                'effective_length': 0.0,
                'netflix_compliant': True,
                'character_breakdown': {},
                'weight_distribution': {}
            }
        
        # 字符分类统计
        char_breakdown = {
            'chinese': 0, 'japanese': 0, 'korean': 0, 'cjk_other': 0,
            'latin': 0, 'number': 0, 'punctuation': 0, 'space': 0,
            'emoji': 0, 'symbol': 0, 'other': 0
        }
        
        weight_breakdown = {category: 0.0 for category in char_breakdown.keys()}
        
        total_weight = 0.0
        
        for char in text:
            category = self._get_character_category(char)
            weight = self.get_character_weight(char)
            
            char_breakdown[category] += 1
            weight_breakdown[category] += weight
            total_weight += weight
        
        # 计算有效长度 (基于Netflix标准)
        effective_length = total_weight
        
        # Netflix合规性检查
        netflix_compliant = effective_length <= self.config.max_line_length
        
        # 权重分布分析
        if total_weight > 0:
            weight_distribution = {
                category: (weight / total_weight * 100)
                for category, weight in weight_breakdown.items()
                if weight > 0
            }
        else:
            weight_distribution = {}
        
        return {
            'total_weight': total_weight,
            'character_count': len(text),
            'effective_length': effective_length,
            'netflix_compliant': netflix_compliant,
            'character_breakdown': char_breakdown,
            'weight_breakdown': weight_breakdown,
            'weight_distribution': weight_distribution,
            'cjk_ratio': sum(weight_breakdown[k] for k in ['chinese', 'japanese', 'korean', 'cjk_other']) / total_weight * 100 if total_weight > 0 else 0
        }
    
    def validate_netflix_standards(self, text_lines: List[str]) -> Dict[str, Any]:
        """验证是否符合Netflix字幕标准"""
        if not text_lines:
            return {'compliant': True, 'issues': [], 'recommendations': []}
        
        issues = []
        recommendations = []
        
        # 检查行数
        if len(text_lines) > self.config.max_lines:
            issues.append(f"行数超标: {len(text_lines)} > {self.config.max_lines}")
            recommendations.append(f"将字幕压缩至{self.config.max_lines}行以内")
        
        # 检查每行长度
        for i, line in enumerate(text_lines, 1):
            metrics = self.calculate_text_metrics(line)
            
            if not metrics['netflix_compliant']:
                issues.append(f"第{i}行长度超标: {metrics['effective_length']:.1f} > {self.config.max_line_length}")
                recommendations.append(f"第{i}行需要分割或缩短")
        
        # 检查整体长度平衡
        if len(text_lines) == 2:
            weights = [self.calculate_text_weight(line) for line in text_lines]
            weight_diff = abs(weights[0] - weights[1])
            max_weight = max(weights)
            
            if max_weight > 0 and weight_diff / max_weight > 0.3:  # 30%差异阈值
                issues.append(f"行长度不平衡: {weights[0]:.1f} vs {weights[1]:.1f}")
                recommendations.append("调整分割点以平衡行长度")
        
        return {
            'compliant': len(issues) == 0,
            'issues': issues,
            'recommendations': recommendations,
            'total_lines': len(text_lines),
            'line_weights': [self.calculate_text_weight(line) for line in text_lines],
            'max_weight': max([self.calculate_text_weight(line) for line in text_lines]) if text_lines else 0
        }
    
    def suggest_optimal_split(self, text: str) -> List[str]:
        """建议最优分割方案"""
        if not text:
            return []
        
        total_weight = self.calculate_text_weight(text)
        
        # 如果符合单行标准
        if total_weight <= self.config.max_line_length:
            return [text]
        
        # 寻找最佳分割点
        best_split = self._find_optimal_split_point(text)
        
        if best_split > 0:
            line1 = text[:best_split].strip()
            line2 = text[best_split:].strip()
            
            # 验证分割结果
            validation = self.validate_netflix_standards([line1, line2])
            
            if validation['compliant']:
                return [line1, line2]
        
        # 如果无法找到合适分割点，使用强制分割
        return self._force_split(text)
    
    def _find_optimal_split_point(self, text: str) -> int:
        """寻找最优分割点"""
        # 定义分割点优先级
        split_chars = [
            ('，', 3),    # 逗号 - 高优先级
            ('、', 3),    # 顿号 - 高优先级
            ('；', 4),    # 分号 - 高优先级
            ('。', 5),    # 句号 - 最高优先级
            ('！', 5),    # 感叹号 - 最高优先级
            ('？', 5),    # 问号 - 最高优先级
            (' ', 1),     # 空格 - 低优先级
            ('-', 2),     # 连字符 - 中优先级
            ('—', 2),     # 破折号 - 中优先级
        ]
        
        target_weight = self.calculate_text_weight(text) / 2
        
        best_split = -1
        best_score = float('inf')
        
        for i in range(1, len(text) - 1):
            char = text[i]
            
            # 检查是否为合适的分割点
            char_priority = 0
            for split_char, priority in split_chars:
                if char == split_char:
                    char_priority = priority
                    break
            
            if char_priority == 0:
                continue
            
            # 计算分割后的权重
            line1_weight = self.calculate_text_weight(text[:i + 1])
            line2_weight = self.calculate_text_weight(text[i + 1:])
            
            # 检查是否符合长度限制
            if (line1_weight > self.config.max_line_length or 
                line2_weight > self.config.max_line_length):
                continue
            
            # 计算分割质量分数
            weight_balance = abs(line1_weight - line2_weight)
            position_bias = abs(i - len(text) / 2) / len(text)
            
            score = weight_balance + position_bias * 10 - char_priority * 2
            
            if score < best_score:
                best_score = score
                best_split = i + 1
        
        return best_split
    
    def _force_split(self, text: str) -> List[str]:
        """强制分割（当无法找到理想分割点时）"""
        target_weight = self.config.max_line_length
        
        current_weight = 0.0
        split_point = 0
        
        for i, char in enumerate(text):
            char_weight = self.get_character_weight(char)
            
            if current_weight + char_weight > target_weight and i > 0:
                split_point = i
                break
            
            current_weight += char_weight
        
        if split_point == 0:
            split_point = len(text) // 2
        
        line1 = text[:split_point].strip()
        line2 = text[split_point:].strip()
        
        return [line1, line2] if line1 and line2 else [text]
    
    def calculate_subtitle_duration(self, text_lines: List[str]) -> Dict[str, float]:
        """计算字幕显示时长（基于Netflix阅读速度标准）"""
        if not text_lines:
            return {'recommended_duration': 0.0, 'min_duration': 0.0, 'max_duration': 0.0}
        
        total_weight = sum(self.calculate_text_weight(line) for line in text_lines)
        
        # 基于阅读速度计算推荐时长
        recommended_duration = total_weight / self.config.reading_speed_cps
        
        # 应用最小/最大时长限制
        min_duration = max(recommended_duration, self.config.min_subtitle_duration)
        max_duration = min(recommended_duration * 1.5, self.config.max_subtitle_duration)
        
        return {
            'recommended_duration': round(recommended_duration, 2),
            'min_duration': round(min_duration, 2),
            'max_duration': round(max_duration, 2),
            'reading_speed_cps': self.config.reading_speed_cps,
            'total_weight': total_weight
        }
    
    def get_detailed_analysis(self, text: str) -> Dict[str, Any]:
        """获取文本的详细分析报告"""
        metrics = self.calculate_text_metrics(text)
        optimal_split = self.suggest_optimal_split(text)
        validation = self.validate_netflix_standards(optimal_split)
        duration = self.calculate_subtitle_duration(optimal_split)
        
        return {
            'input_text': text,
            'text_metrics': metrics,
            'optimal_split': optimal_split,
            'netflix_validation': validation,
            'duration_analysis': duration,
            'recommendations': self._generate_recommendations(metrics, validation, optimal_split)
        }
    
    def _generate_recommendations(self, metrics: Dict[str, Any], 
                                validation: Dict[str, Any], 
                                optimal_split: List[str]) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        if not validation['compliant']:
            recommendations.extend(validation['recommendations'])
        
        # CJK比例分析
        cjk_ratio = metrics.get('cjk_ratio', 0)
        if cjk_ratio > 80:
            recommendations.append("文本主要为CJK字符，建议使用较短的行长度")
        elif cjk_ratio < 20:
            recommendations.append("文本主要为拉丁字符，可以使用较长的行长度")
        
        # 分割质量分析
        if len(optimal_split) == 2:
            weights = [self.calculate_text_weight(line) for line in optimal_split]
            if max(weights) - min(weights) > 10:
                recommendations.append("建议调整分割点以平衡行长度")
        
        return recommendations


# 便捷函数
def create_netflix_calculator(config: Optional[Dict[str, Any]] = None) -> NetflixCharacterWeightCalculator:
    """创建Netflix字符权重计算器"""
    if config:
        weight_config = CharacterWeightConfig(**config)
    else:
        weight_config = CharacterWeightConfig()
    
    return NetflixCharacterWeightCalculator(weight_config)


def calculate_netflix_weight(text: str, config: Optional[Dict[str, Any]] = None) -> float:
    """计算文本Netflix权重的便捷函数"""
    calculator = create_netflix_calculator(config)
    return calculator.calculate_text_weight(text)


def validate_netflix_compliance(text_lines: List[str], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """验证Netflix合规性的便捷函数"""
    calculator = create_netflix_calculator(config)
    return calculator.validate_netflix_standards(text_lines)


def suggest_netflix_split(text: str, config: Optional[Dict[str, Any]] = None) -> List[str]:
    """建议Netflix分割的便捷函数"""
    calculator = create_netflix_calculator(config)
    return calculator.suggest_optimal_split(text)


if __name__ == "__main__":
    # 测试Netflix字符权重计算器
    print("🎬 Netflix字符权重计算器测试")
    print("=" * 60)
    
    calculator = NetflixCharacterWeightCalculator()
    
    test_texts = [
        "Hello World!",
        "你好世界！",
        "これは日本語のテストです。",
        "안녕하세요 세계입니다!",
        "人工智能技术正在快速发展，它不仅改变了我们的生活方式，还深刻影响着各个行业的发展。",
        "AI technology is revolutionizing various industries and changing our daily lives significantly.",
        "混合文本测试 Mixed text test with 数字123 and symbols @#$%"
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n📝 测试 {i}: {text}")
        
        # 详细分析
        analysis = calculator.get_detailed_analysis(text)
        
        print(f"   总权重: {analysis['text_metrics']['total_weight']:.2f}")
        print(f"   CJK比例: {analysis['text_metrics']['cjk_ratio']:.1f}%")
        print(f"   Netflix合规: {analysis['netflix_validation']['compliant']}")
        print(f"   建议分割: {analysis['optimal_split']}")
        print(f"   推荐时长: {analysis['duration_analysis']['recommended_duration']}秒")
        
        if analysis['recommendations']:
            print(f"   建议: {'; '.join(analysis['recommendations'])}")