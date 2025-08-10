"""
PPT转视频教程工具 - Streamlit主应用
"""
import streamlit as st
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ui.pages.upload_page import render_upload_page
from ui.pages.workflow_page import render_workflow_page  
from ui.pages.preview_page import render_preview_page
from config.logging_config import setup_logging

# 设置页面配置
st.set_page_config(
    page_title="PPT转视频教程工具",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化日志
setup_logging()

def main():
    """主函数"""
    
    # 应用标题
    st.title("🎬 PPT转视频教程生成工具")
    st.markdown("""
    一个自动化的PPT转视频教程生成工具，支持PPT解析、语音合成、视频生成和字幕合并。
    
    ⭐ **新功能**: 支持单步执行测试，可以逐个步骤调试和验证处理流程！
    """)
    st.markdown("---")
    
    # 侧边栏导航
    with st.sidebar:
        st.header("📋 导航菜单")
        
        page = st.radio(
            "选择功能页面",
            ["📁 文件上传", "⚙️ 工作流执行", "👁️ 结果预览"],
            index=0,  # 默认选择文件上传页面
            help="选择要使用的功能页面"
        )
        
        st.markdown("---")
        
        # 项目信息
        st.header("ℹ️ 项目信息")
        st.info("""
        **版本**: v1.0.0  
        **开发**: Python + Streamlit  
        **功能**: PPT → 视频教程
        """)
        
        # 使用说明
        with st.expander("📖 使用说明"):
            st.markdown("""
            **使用流程：**
            1. **📁 文件上传**: 
               - 上传PPT文件
               - 配置语音、视频、字幕参数
               - **支持单步执行测试各个步骤**
               - 可一键完成整个流程
            2. **⚙️ 工作流执行**: 批量处理模式
            3. **👁️ 结果预览**: 查看和下载结果
            
            **新功能亮点：**
            - ✨ **单步测试**: 可逐步执行每个处理步骤
            - 📊 **实时进度**: 显示处理进度和状态
            - 🎮 **步骤控制**: 5个独立的执行按钮
            - 📋 **状态跟踪**: 实时显示每步执行结果
            
            **支持格式：**
            - 输入: .pptx文件
            - 输出: .mp4视频文件
            
            **处理步骤：**
            - 📋 步骤1: PPT解析
            - 🎵 步骤2: 语音合成  
            - 🎬 步骤3: 视频生成
            - 📄 步骤4: 字幕生成
            - 🎯 步骤5: 最终合并
            """)
            
            st.info("💡 **推荐**: 在文件上传页面完成所有操作，支持单步测试！")
        
        # 技术栈信息
        with st.expander("🔧 技术栈"):
            st.markdown("""
            - **Python**: 核心开发语言
            - **Streamlit**: Web应用框架
            - **python-pptx**: PPT文件解析
            - **多引擎TTS**: Edge TTS, Fish TTS, OpenAI TTS, Azure TTS
            - **FFmpeg**: 高性能视频处理和合并
            - **moviepy**: 视频生成和处理
            - **pysrt**: 字幕文件处理
            """)
    
    # 主内容区域
    if page == "📁 文件上传":
        render_upload_page()
    elif page == "⚙️ 工作流执行":
        render_workflow_page()
    elif page == "👁️ 结果预览":
        render_preview_page()
    
    # 底部信息
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🎯 当前状态**")
        if st.session_state.get('workflow_config'):
            st.success("✅ 配置已就绪")
        else:
            st.info("⏳ 等待配置")
    
    with col2:
        st.markdown("**📊 步骤进度**")
        step_results = st.session_state.get('step_results', {})
        if step_results:
            completed_steps = len([r for r in step_results.values() if r.get('success', False)])
            st.info(f"✅ 已完成 {completed_steps}/5 个步骤")
        else:
            st.info("⏸️ 未开始")
    
    with col3:
        st.markdown("**💾 输出文件**")
        if st.session_state.get('step_results', {}).get('步骤5', {}).get('success', False):
            st.success("✅ 视频已生成")
        else:
            st.info("⏳ 等待生成")

if __name__ == "__main__":
    main()
