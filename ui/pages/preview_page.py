"""
结果预览页面
"""
import streamlit as st
from pathlib import Path

def render_preview_page():
    """渲染结果预览页面"""
    st.header("👁️ 结果预览")
    
    # 检查是否有完成的工作流
    if not st.session_state.get('workflow_completed', False):
        st.warning("⚠️ 请先完成工作流执行")
        return
    
    st.success("✅ 工作流已完成！")
    
    # 结果摘要
    st.subheader("📊 处理结果摘要")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("PPT页数", "15", help="处理的PPT页面数量")
    
    with col2:
        st.metric("音频时长", "3:45", help="生成的音频总时长")
    
    with col3:
        st.metric("视频大小", "45.2 MB", help="最终视频文件大小")
    
    with col4:
        st.metric("处理时间", "12:05", help="总处理时间")
    
    st.divider()
    
    # 文件列表
    st.subheader("📁 生成的文件")
    
    # 模拟文件结构
    files = [
        {"name": "final_video.mp4", "size": "45.2 MB", "type": "视频文件", "path": "/output/final/"},
        {"name": "final_video_with_subtitles.mp4", "size": "45.5 MB", "type": "带字幕视频", "path": "/output/final/"},
        {"name": "combined_audio.wav", "size": "8.1 MB", "type": "音频文件", "path": "/output/temp/"},
        {"name": "combined_subtitle.srt", "size": "2.3 KB", "type": "字幕文件", "path": "/output/subtitles/"}
    ]
    
    for file in files:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
            
            with col1:
                st.write(f"📄 **{file['name']}**")
            with col2:
                st.write(file['size'])
            with col3:
                st.write(file['type'])
            with col4:
                if st.button(f"下载", key=f"download_{file['name']}"):
                    st.info(f"下载功能待实现: {file['name']}")
    
    st.divider()
    
    # 预览区域
    st.subheader("🎬 视频预览")
    
    # 这里应该显示实际的视频预览
    # 由于没有真实文件，显示占位符
    st.info("📺 视频预览功能开发中...")
    
    # 模拟视频预览界面
    with st.container():
        st.video("https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4")  # 示例视频
    
    # 字幕预览
    with st.expander("📝 字幕预览"):
        st.code("""
1
00:00:00,000 --> 00:00:03,500
大家好，欢迎来到今天的课程

2
00:00:03,500 --> 00:00:07,200
今天我们将学习PPT制作的基础知识

3
00:00:07,200 --> 00:00:11,000
首先，让我们了解什么是演示文稿
        """, language="srt")
    
    # 操作按钮
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 下载所有文件", type="primary", use_container_width=True):
            st.info("批量下载功能开发中...")
    
    with col2:
        if st.button("🔄 重新处理", use_container_width=True):
            # 重置状态，返回工作流页面
            st.session_state['workflow_completed'] = False
            for i in range(1, 7):
                st.session_state[f'step_{i}_completed'] = False
            st.success("已重置，可以重新处理")
    
    with col3:
        if st.button("📤 分享结果", use_container_width=True):
            st.info("分享功能开发中...")
    
    # 反馈区域
    with st.expander("💬 反馈和建议"):
        feedback = st.text_area("请提供您的反馈和建议：", height=100)
        if st.button("提交反馈"):
            if feedback.strip():
                st.success("感谢您的反馈！")
            else:
                st.warning("请输入反馈内容")
