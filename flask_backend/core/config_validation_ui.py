"""
配置验证和优化Web界面集成
为Streamlit应用提供配置验证和优化功能
"""

import streamlit as st
import json
from typing import Dict, Any, List
from datetime import datetime
from .config_validator import ConfigValidator, ValidationLevel
from .config_optimizer import ConfigOptimizer
from .config_presets import ConfigPresets

class ConfigValidationUI:
    """配置验证UI组件"""
    
    def __init__(self):
        self.validator = ConfigValidator()
        self.optimizer = ConfigOptimizer()
        self.presets = ConfigPresets()
    
    def render_validation_panel(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        渲染配置验证面板
        
        Args:
            config: 当前配置
            
        Returns:
            验证结果和用户操作
        """
        st.subheader("🔍 配置验证与优化")
        
        # 创建列布局
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 显示验证结果
            validation_report = self.validator.generate_validation_report(config)
            self._render_validation_results(validation_report)
        
        with col2:
            # 显示快速操作
            actions = self._render_quick_actions(config, validation_report)
        
        # 详细分析面板
        if st.expander("📊 详细分析", expanded=False):
            self._render_detailed_analysis(config)
        
        return {
            "validation_report": validation_report,
            "user_actions": actions
        }
    
    def _render_validation_results(self, report: Dict[str, Any]):
        """渲染验证结果"""
        score = report["overall_score"]
        status = report["status"]
        
        # 显示总体评分
        score_color = "green" if score >= 85 else "orange" if score >= 70 else "red"
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; border-radius: 10px; 
                    background: linear-gradient(90deg, {score_color}20, {score_color}10);">
            <h2 style="color: {score_color};">配置评分: {score}/100</h2>
            <p>状态: {self._get_status_text(status)}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 显示问题摘要
        summary = report["summary"]
        if summary["errors"] > 0:
            st.error(f"🚨 发现 {summary['errors']} 个严重错误")
        if summary["warnings"] > 0:
            st.warning(f"⚠️ 发现 {summary['warnings']} 个警告")
        if summary["errors"] == 0 and summary["warnings"] == 0:
            st.success("✅ 配置验证通过，没有发现问题")
        
        # 显示推荐建议
        if report["recommendations"]:
            st.info("💡 推荐建议:")
            for rec in report["recommendations"]:
                st.write(f"• {rec}")
    
    def _render_quick_actions(self, config: Dict[str, Any], 
                            validation_report: Dict[str, Any]) -> Dict[str, Any]:
        """渲染快速操作面板"""
        st.markdown("### 🚀 快速操作")
        
        actions = {}
        
        # 自动修复按钮
        if validation_report["summary"]["errors"] > 0:
            if st.button("🔧 自动修复错误", type="primary"):
                actions["auto_fix"] = True
        
        # 应用Netflix标准
        if not self._is_netflix_compliant(config):
            if st.button("⭐ 应用Netflix标准"):
                actions["apply_netflix"] = True
        
        # 性能优化
        if self._needs_performance_optimization(config):
            if st.button("⚡ 性能优化"):
                actions["performance_optimize"] = True
        
        # 自动优化选项
        st.markdown("### 🎯 智能优化")
        optimization_level = st.selectbox(
            "优化级别:",
            ["conservative", "balanced", "aggressive"],
            format_func=lambda x: {
                "conservative": "保守 (仅安全优化)",
                "balanced": "平衡 (推荐)",
                "aggressive": "积极 (全面优化)"
            }[x],
            index=1
        )
        
        if st.button("🚀 执行智能优化"):
            actions["smart_optimize"] = optimization_level
        
        return actions
    
    def _render_detailed_analysis(self, config: Dict[str, Any]):
        """渲染详细分析"""
        # 用户上下文输入
        st.markdown("#### 📝 使用场景 (可选)")
        col1, col2 = st.columns(2)
        
        with col1:
            use_case = st.selectbox(
                "使用场景:",
                ["general", "education", "entertainment", "business"],
                format_func=lambda x: {
                    "general": "一般用途",
                    "education": "教育培训",
                    "entertainment": "娱乐内容",
                    "business": "商务演示"
                }[x]
            )
            
            platform = st.selectbox(
                "目标平台:",
                ["web", "mobile", "tv"],
                format_func=lambda x: {
                    "web": "网页端",
                    "mobile": "移动端",
                    "tv": "电视端"
                }[x]
            )
        
        with col2:
            quality_priority = st.selectbox(
                "质量优先级:",
                ["low", "balanced", "high"],
                format_func=lambda x: {
                    "low": "低 (快速处理)",
                    "balanced": "平衡",
                    "high": "高 (最佳质量)"
                }[x],
                index=1
            )
            
            target_audience = st.selectbox(
                "目标受众:",
                ["general", "students", "professionals", "elderly"],
                format_func=lambda x: {
                    "general": "一般用户",
                    "students": "学生",
                    "professionals": "专业人士",
                    "elderly": "老年用户"
                }[x]
            )
        
        # 生成详细分析
        if st.button("📊 生成详细分析"):
            user_context = {
                "use_case": use_case,
                "platform": platform,
                "quality_priority": quality_priority,
                "target_audience": target_audience
            }
            
            analysis = self.optimizer.analyze_config(config, user_context)
            self._display_detailed_analysis_results(analysis)
    
    def _display_detailed_analysis_results(self, analysis: Dict[str, Any]):
        """显示详细分析结果"""
        config_analysis = analysis["config_analysis"]
        
        # 智能建议
        st.markdown("#### 🧠 智能建议")
        smart_suggestions = config_analysis["smart_suggestions"]
        
        for suggestion in smart_suggestions:
            priority_color = "red" if suggestion["priority"] >= 8 else "orange" if suggestion["priority"] >= 6 else "green"
            
            with st.expander(f"[优先级 {suggestion['priority']}/10] {suggestion['title']}"):
                st.write(suggestion["description"])
                
                if suggestion.get("config_changes"):
                    st.json(suggestion["config_changes"])
        
        # 预设推荐
        st.markdown("#### 📋 预设推荐")
        preset_recommendations = config_analysis["preset_recommendations"]
        
        for rec in preset_recommendations:
            preset = rec["preset"]
            similarity = rec["similarity"]
            
            with st.expander(f"{preset['display_name']} (相似度: {similarity:.1%})"):
                st.write(f"**描述:** {preset['description']}")
                st.write(f"**目标用户:** {', '.join(preset['target_users'])}")
                
                if rec["benefits"]:
                    st.write("**优势:**")
                    for benefit in rec["benefits"]:
                        st.write(f"• {benefit}")
    
    def render_optimization_history(self):
        """渲染优化历史"""
        st.subheader("📈 优化历史")
        
        if hasattr(self.optimizer, 'optimization_history') and self.optimizer.optimization_history:
            for i, history in enumerate(reversed(self.optimizer.optimization_history[-5:])):  # 显示最近5次
                with st.expander(f"优化 {len(self.optimizer.optimization_history) - i} - {history['timestamp'][:19]}"):
                    st.write(f"**优化级别:** {history['optimization_level']}")
                    
                    if history["applied_optimizations"]:
                        st.write("**应用的优化:**")
                        for opt in history["applied_optimizations"]:
                            st.write(f"• [{opt['type']}] {opt['title']}")
                            st.write(f"  预期改进: {opt['improvement']}")
        else:
            st.info("暂无优化历史记录")
    
    def apply_user_actions(self, config: Dict[str, Any], actions: Dict[str, Any]) -> Dict[str, Any]:
        """
        应用用户操作
        
        Args:
            config: 原始配置
            actions: 用户操作
            
        Returns:
            更新后的配置
        """
        updated_config = config.copy()
        
        if actions.get("auto_fix"):
            # 自动修复错误
            validation_results = self.validator.validate_config(config)
            errors = [r for r in validation_results if r.level == ValidationLevel.ERROR]
            
            for error in errors:
                if error.suggested_value is not None:
                    updated_config[error.field] = error.suggested_value
            
            st.success(f"已修复 {len(errors)} 个错误")
        
        if actions.get("apply_netflix"):
            # 应用Netflix标准
            netflix_config = self.presets.get_preset_config("professional")
            if netflix_config:
                # 只更新Netflix相关的字段
                netflix_fields = ["max_length", "font_family", "background_opacity", "outline_width"]
                for field in netflix_fields:
                    if field in netflix_config:
                        updated_config[field] = netflix_config[field]
                
                st.success("已应用Netflix标准配置")
        
        if actions.get("performance_optimize"):
            # 性能优化
            updated_config.update({
                "processing_mode": "balanced",
                "use_spacy": False,
                "ai_splitting": False
            })
            st.success("已应用性能优化")
        
        if actions.get("smart_optimize"):
            # 智能优化
            optimization_level = actions["smart_optimize"]
            updated_config = self.optimizer.auto_optimize_config(
                updated_config, 
                optimization_level=optimization_level
            )
            
            if "_optimizations" in updated_config:
                opt_count = len(updated_config["_optimizations"])
                st.success(f"智能优化完成，应用了 {opt_count} 个优化")
        
        return updated_config
    
    def _get_status_text(self, status: str) -> str:
        """获取状态文本"""
        status_map = {
            "excellent": "优秀 ✨",
            "good": "良好 👍",
            "needs_improvement": "需要改进 🔧",
            "critical": "严重问题 🚨"
        }
        return status_map.get(status, status)
    
    def _is_netflix_compliant(self, config: Dict[str, Any]) -> bool:
        """检查是否符合Netflix标准"""
        return (config.get("max_length", 75) <= 40 and
                config.get("font_family") in ["Helvetica Neue", "Arial"] and
                config.get("background_opacity", 0) >= 0.8)
    
    def _needs_performance_optimization(self, config: Dict[str, Any]) -> bool:
        """检查是否需要性能优化"""
        return (config.get("processing_mode") == "quality" and
                config.get("use_spacy", False) and
                config.get("ai_splitting", False))

def create_config_validation_component():
    """创建配置验证组件的工厂函数"""
    return ConfigValidationUI()

# 使用示例
def demo_config_validation():
    """演示配置验证功能"""
    st.title("配置验证与优化演示")
    
    # 示例配置
    demo_config = {
        "max_length": 100,  # 需要优化
        "target_multiplier": 1.5,
        "font_size": 16,  # 可以优化
        "processing_mode": "quality",
        "use_spacy": True,  # 性能影响
        "ai_splitting": False
    }
    
    # 创建验证UI
    validator_ui = create_config_validation_component()
    
    # 渲染验证面板
    result = validator_ui.render_validation_panel(demo_config)
    
    # 应用用户操作
    if result["user_actions"]:
        optimized_config = validator_ui.apply_user_actions(demo_config, result["user_actions"])
        
        st.subheader("优化后的配置")
        st.json(optimized_config)

if __name__ == "__main__":
    demo_config_validation()
