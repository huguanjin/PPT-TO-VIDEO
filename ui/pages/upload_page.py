"""
文件上传页面
"""
import streamlit as st
import tempfile
import os
from pathlib import Path
from typing import Optional
import asyncio
from datetime import datetime
import time

from core.step01_ppt_parser import PPTParser
from core.step02_tts_generator import TTSGenerator
from core.step03_video_generator import VideoGenerator
from core.step04_subtitle_generator import SubtitleGenerator
from utils.file_manager import FileManager
from utils.config_manager import ConfigManager
from utils.task_manager import TaskManager, TaskStatus
from config.settings import TTS_CONFIG, VIDEO_CONFIG

def render_upload_page():
    """渲染文件上传页面"""
    
    # 初始化配置管理器
    config_manager = ConfigManager()
    
    # 加载保存的配置
    if 'saved_config' not in st.session_state:
        st.session_state.saved_config = config_manager.load_config()
    
    # 侧边栏配置
    with st.sidebar:
        st.header("🛠️ 工具配置")
        
        # 配置状态显示
        with st.expander("📋 配置信息", expanded=False):
            config_info = config_manager.get_config_display_info()
            for key, value in config_info.items():
                st.text(f"{key}: {value}")
        
        # 1. 项目配置
        st.subheader("📁 项目配置")
        
        project_name = st.text_input(
            "项目名称",
            value=st.session_state.saved_config.get("project_name", "ppt_video_project"),
            help="用于创建输出文件夹"
        )
        
        output_format = st.selectbox(
            "输出格式",
            ["MP4 (推荐)", "AVI", "MOV"],
            index=["MP4 (推荐)", "AVI", "MOV"].index(st.session_state.saved_config.get("output_format", "MP4 (推荐)")),
            help="最终视频文件格式"
        )
        
        st.divider()
        
        # 2. 语音合成配置
        st.subheader("🎵 语音合成配置")
        
        # TTS引擎选择
        tts_engines = ["自动选择", "Edge TTS", "Fish TTS", "OpenAI TTS", "Azure TTS"]
        tts_engine = st.selectbox(
            "TTS引擎",
            tts_engines,
            index=tts_engines.index(st.session_state.saved_config.get("tts_engine", "自动选择")),
            help="选择语音合成引擎。自动选择会依次尝试可用引擎"
        )
        
        # API密钥配置
        fish_api_key = ""
        fish_character_id = ""
        openai_api_key = ""
        openai_voice = "alloy"
        azure_api_key = ""
        azure_region = ""
        
        if tts_engine in ["Fish TTS", "OpenAI TTS", "Azure TTS"]:
            with st.expander("🔑 API密钥配置", expanded=(tts_engine != "自动选择")):
                if tts_engine == "Fish TTS":
                    fish_api_key = st.text_input(
                        "Fish TTS API密钥", 
                        value=st.session_state.saved_config.get("fish_api_key", ""),
                        type="password",
                        help="从 https://fish.audio 获取API密钥"
                    )
                    fish_character_id = st.text_input(
                        "角色ID",
                        value=st.session_state.saved_config.get("fish_character_id", ""),
                        help="Fish TTS角色参考ID"
                    )
                
                elif tts_engine == "OpenAI TTS":
                    openai_api_key = st.text_input(
                        "OpenAI API密钥",
                        value=st.session_state.saved_config.get("openai_api_key", ""),
                        type="password"
                    )
                    openai_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
                    openai_voice = st.selectbox(
                        "OpenAI语音",
                        openai_voices,
                        index=openai_voices.index(st.session_state.saved_config.get("openai_voice", "alloy"))
                    )
                
                elif tts_engine == "Azure TTS":
                    azure_api_key = st.text_input(
                        "Azure API密钥",
                        value=st.session_state.saved_config.get("azure_api_key", ""),
                        type="password"
                    )
                    azure_region = st.text_input(
                        "Azure区域",
                        value=st.session_state.saved_config.get("azure_region", ""),
                        help="例如: eastus, westus2"
                    )
        
        # Edge TTS配置（总是显示，作为fallback）
        tts_voices = [
            "zh-CN-XiaoxiaoNeural",
            "zh-CN-YunxiNeural", 
            "zh-CN-YunjianNeural",
            "zh-CN-XiaoyiNeural",
            "zh-CN-YunyangNeural",
            "zh-CN-liaoning-XiaobeiNeural",
            "zh-CN-shaanxi-XiaoniNeural",
            "zh-HK-HiuGaaiNeural"
        ]
        
        tts_voice = st.selectbox(
            "Edge TTS语音选择",
            tts_voices,
            index=tts_voices.index(st.session_state.saved_config.get("tts_voice", "zh-CN-XiaoxiaoNeural")),
            help="Edge TTS语音（作为备选方案）"
        )
        
        speech_rates = ["slow", "medium", "fast"]
        speech_rate = st.selectbox(
            "语速",
            speech_rates,
            index=speech_rates.index(st.session_state.saved_config.get("speech_rate", "medium")),
            help="语音播放速度"
        )
        
        speech_pitches = ["x-low", "low", "medium", "high", "x-high"]
        speech_pitch = st.selectbox(
            "语音音调",
            speech_pitches,
            index=speech_pitches.index(st.session_state.saved_config.get("speech_pitch", "medium")),
            help="调整语音音调高低"
        )
        
        st.divider()
        
        # 3. 视频配置
        st.subheader("🎬 视频配置")
        
        video_resolutions = ["1920x1080 (Full HD)", "1280x720 (HD)", "1600x900 (HD+)", "2560x1440 (2K)"]
        video_resolution = st.selectbox(
            "视频分辨率",
            video_resolutions,
            index=video_resolutions.index(st.session_state.saved_config.get("video_resolution", "1920x1080 (Full HD)")),
            help="输出视频分辨率"
        )
        
        video_fps = st.slider(
            "帧率 (FPS)",
            min_value=15,
            max_value=60,
            value=st.session_state.saved_config.get("video_fps", 24),
            step=1,
            help="每秒帧数，数值越高视频越流畅"
        )
        
        video_bitrate = st.slider(
            "比特率 (kbps)",
            min_value=500,
            max_value=5000,
            value=st.session_state.saved_config.get("video_bitrate", 2000),
            step=100,
            help="视频比特率，数值越高画质越好"
        )
        
        video_codecs = ["libx264", "libx265", "mpeg4"]
        video_codec = st.selectbox(
            "视频编码器",
            video_codecs,
            index=video_codecs.index(st.session_state.saved_config.get("video_codec", "libx264")),
            help="视频编码格式"
        )
        
        st.divider()
        
        # 4. 字幕配置
        st.subheader("📄 字幕配置")
        
        include_subtitles = st.checkbox(
            "包含字幕",
            value=st.session_state.saved_config.get("include_subtitles", True),
            help="是否在最终视频中嵌入字幕"
        )
        
        if include_subtitles:
            subtitle_fontsize = st.slider(
                "字幕字体大小",
                min_value=20,
                max_value=80,
                value=st.session_state.saved_config.get("subtitle_fontsize", 50),
                help="字幕字体大小"
            )
            
            subtitle_colors = ["white", "yellow", "black", "red", "blue"]
            subtitle_color = st.selectbox(
                "字幕颜色",
                subtitle_colors,
                index=subtitle_colors.index(st.session_state.saved_config.get("subtitle_color", "white")),
                help="字幕文字颜色"
            )
            
            subtitle_positions = ["bottom", "top", "center"]
            subtitle_position = st.selectbox(
                "字幕位置",
                subtitle_positions,
                index=subtitle_positions.index(st.session_state.saved_config.get("subtitle_position", "bottom")),
                help="字幕在视频中的位置"
            )
        else:
            subtitle_fontsize = 50
            subtitle_color = "white"
            subtitle_position = "bottom"
        
        # 配置重置按钮
        if st.button("🔄 重置为默认配置", type="secondary"):
            if config_manager.reset_config():
                st.session_state.saved_config = config_manager.load_config()
                st.success("✅ 配置已重置为默认值")
                st.rerun()
    
    # 主内容区域
    st.header("📁 文件上传")
    
    # 文件上传
    st.subheader("上传PPT文件")
    uploaded_file = st.file_uploader(
        "选择PPT文件",
        type=['pptx'],
        help="支持.pptx格式的PowerPoint文件"
    )
    
    if uploaded_file is not None:
        # 显示文件信息
        st.success(f"✅ 已上传文件: {uploaded_file.name}")
        st.info(f"📊 文件大小: {uploaded_file.size / (1024*1024):.2f} MB")
        
        # 保存临时文件
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, uploaded_file.name)
        
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.session_state['ppt_file_path'] = temp_file_path
        
        # 预览PPT信息
        try:
            parser = PPTParser(Path(temp_dir) / "preview")
            # 这里需要同步版本的方法来获取幻灯片数量
            st.info("📄 正在分析PPT文件...")
            # slide_count = await parser.get_slide_count(temp_file_path)  # 异步调用需要特殊处理
            # st.info(f"📄 PPT总页数: {slide_count}")
        except Exception as e:
            st.warning(f"⚠️ 文件预览失败: {str(e)}")
    
    # 保存配置
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 保存配置", type="primary", use_container_width=True):
            if uploaded_file is not None and project_name.strip():
                config = {
                    "project_name": project_name.strip(),
                    "ppt_file_path": st.session_state.get('ppt_file_path'),
                    "tts_engine": tts_engine,
                    "tts_voice": tts_voice,
                    "speech_rate": speech_rate,
                    "speech_pitch": speech_pitch,
                    "fish_api_key": fish_api_key,
                    "fish_character_id": fish_character_id,
                    "openai_api_key": openai_api_key,
                    "openai_voice": openai_voice,
                    "azure_api_key": azure_api_key,
                    "azure_region": azure_region,
                    "video_resolution": video_resolution,
                    "video_fps": video_fps,
                    "video_bitrate": video_bitrate,
                    "video_codec": video_codec,
                    "output_format": output_format,
                    "include_subtitles": include_subtitles,
                    "subtitle_fontsize": subtitle_fontsize if include_subtitles else 50,
                    "subtitle_color": subtitle_color if include_subtitles else "white",
                    "subtitle_position": subtitle_position if include_subtitles else "bottom"
                }
                
                # 保存到session state
                st.session_state['workflow_config'] = config
                
                # 保存到文件（持久化）
                if config_manager.save_config(config):
                    st.session_state.saved_config = config
                    st.success("✅ 配置已保存到文件！")
                else:
                    st.error("❌ 配置保存失败")
                
                # 显示配置摘要
                with st.expander("📋 配置摘要"):
                    st.json(config)
            else:
                st.error("❌ 请上传PPT文件并填写项目名称")
    
    with col2:
        if st.button("📂 自动保存配置", type="secondary", use_container_width=True):
            # 自动从当前UI状态保存配置
            if project_name.strip():
                config = {
                    "project_name": project_name.strip(),
                    "ppt_file_path": st.session_state.get('ppt_file_path', ''),
                    "tts_voice": tts_voice,
                    "speech_rate": speech_rate,
                    "speech_pitch": speech_pitch,
                    "video_resolution": video_resolution,
                    "video_fps": video_fps,
                    "video_bitrate": video_bitrate,
                    "video_codec": video_codec,
                    "output_format": output_format,
                    "include_subtitles": include_subtitles,
                    "subtitle_fontsize": subtitle_fontsize if include_subtitles else 50,
                    "subtitle_color": subtitle_color if include_subtitles else "white",
                    "subtitle_position": subtitle_position if include_subtitles else "bottom"
                }
                
                if config_manager.save_config(config):
                    st.session_state.saved_config = config
                    st.success("✅ 配置已自动保存！")
                else:
                    st.error("❌ 自动保存失败")
    
    # 配置状态显示
    if 'workflow_config' in st.session_state and st.session_state['workflow_config']:
        st.success("✅ 配置已就绪")
        with st.expander("当前配置"):
            st.json(st.session_state['workflow_config'])
    else:
        if not uploaded_file:
            st.info("ℹ️ 请上传PPT文件")
        else:
            st.info("ℹ️ 请完成配置设置")
    
    # 工作流步骤执行区域
    st.divider()
    st.header("🎮 工作流步骤执行")
    
    # 初始化步骤结果
    if 'step_results' not in st.session_state:
        st.session_state.step_results = {}
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    
    # 检查是否有配置
    has_config = 'workflow_config' in st.session_state and st.session_state['workflow_config']
    
    if not has_config:
        st.warning("⚠️ 请先上传PPT文件并保存配置后再执行工作流步骤")
    
    # 任务管理器
    task_manager = None
    if has_config:
        project_dir = Path("output") / st.session_state['workflow_config']['project_name']
        task_manager = TaskManager(project_dir)
        
        # 显示任务执行摘要
        if task_manager.task_file.exists():
            st.subheader("📊 任务执行摘要")
            summary = task_manager.get_step_summary()
            
            if summary:
                cols = st.columns(5)
                for i, (step_id, step_info) in enumerate(summary.items()):
                    with cols[i]:
                        step_name = step_id.replace('步骤', 'Step ')
                        progress = step_info['progress']
                        completed = step_info['completed']
                        total = step_info['total']
                        
                        if progress == 100:
                            st.success(f"**{step_name}**\n✅ {completed}/{total}\n进度: {progress}%")
                        elif progress > 0:
                            st.info(f"**{step_name}**\n🔄 {completed}/{total}\n进度: {progress}%")
                        else:
                            st.warning(f"**{step_name}**\n⏳ {completed}/{total}\n进度: {progress}%")
                
                # 任务表查看和导出
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("📋 查看任务表", type="secondary"):
                        df = task_manager.load_tasks()
                        if df is not None:
                            st.dataframe(df, use_container_width=True, height=300)
                
                with col2:
                    if st.button("📊 导出任务报告", type="secondary"):
                        report_file = task_manager.export_task_report()
                        if report_file:
                            st.success(f"✅ 报告已导出: {report_file.name}")
                            
                            # 提供下载
                            with open(report_file, "rb") as f:
                                st.download_button(
                                    label="📥 下载任务报告",
                                    data=f,
                                    file_name=report_file.name,
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                
                with col3:
                    if st.button("🔄 重新初始化任务", type="secondary"):
                        st.warning("⚠️ 这将重置所有任务状态，确定要继续吗？")
                        if st.button("确认重置", type="primary"):
                            # 这里需要重新解析PPT来初始化任务
                            st.info("请先执行步骤1来重新初始化任务表")
    
    # 显示步骤状态
    st.subheader("📋 步骤状态")
    
    steps = [
        ("步骤1", "PPT解析", "📋"),
        ("步骤2", "语音合成", "🎵"),
        ("步骤3", "视频生成", "🎬"),
        ("步骤4", "字幕生成", "📄"),
        ("步骤5", "最终合并", "🎯")
    ]
    
    cols = st.columns(5)
    
    for i, (step_id, step_name, icon) in enumerate(steps):
        with cols[i]:
            if step_id in st.session_state.step_results:
                result = st.session_state.step_results[step_id]
                if result.get('success', False):
                    st.success(f"{icon} {step_name}\n✅ 已完成")
                else:
                    st.error(f"{icon} {step_name}\n❌ 失败")
            else:
                st.info(f"{icon} {step_name}\n⏳ 待执行")
    
    st.divider()
    
    # 步骤执行按钮
    st.subheader("🎮 步骤控制")
    
    # 步骤1: PPT解析
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("**📋 步骤1: PPT解析** - 解析PPT文件，提取幻灯片图片和备注内容")
    with col2:
        disabled = st.session_state.processing or not has_config
        if st.button("▶️ 执行步骤1", key="step1", disabled=disabled):
            execute_step1()
    
    # 步骤2: 语音合成
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("**🎵 步骤2: 语音合成** - 将讲话稿转换为语音文件")
    with col2:
        disabled = st.session_state.processing or not has_config or ('步骤1' not in st.session_state.step_results)
        if st.button("▶️ 执行步骤2", key="step2", disabled=disabled):
            execute_step2()
    
    # 步骤3: 视频生成
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("**🎬 步骤3: 视频生成** - 基于幻灯片图片和音频时长生成视频片段")
    with col2:
        disabled = st.session_state.processing or not has_config or ('步骤2' not in st.session_state.step_results)
        if st.button("▶️ 执行步骤3", key="step3", disabled=disabled):
            execute_step3()
    
    # 步骤4: 字幕生成
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("**📄 步骤4: 字幕生成** - 基于讲话稿和时间轴生成SRT字幕文件")
    with col2:
        disabled = st.session_state.processing or not has_config or ('步骤3' not in st.session_state.step_results)
        if st.button("▶️ 执行步骤4", key="step4", disabled=disabled):
            execute_step4()
    
    # 步骤5: 最终合并
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("**🎯 步骤5: 最终合并** - 将所有媒体文件合并成最终视频")
    with col2:
        disabled = st.session_state.processing or not has_config or ('步骤4' not in st.session_state.step_results)
        if st.button("▶️ 执行步骤5", key="step5", disabled=disabled):
            execute_step5()
    
    # 显示步骤结果
    if st.session_state.step_results:
        st.divider()
        st.subheader("📊 执行结果")
        
        for step_id, step_result in st.session_state.step_results.items():
            with st.expander(f"{step_id} 详细结果"):
                if step_result.get('success', False):
                    st.success(f"✅ {step_id} 执行成功")
                    if 'result' in step_result:
                        st.json(step_result['result'])
                else:
                    st.error(f"❌ {step_id} 执行失败")
                    if 'error' in step_result:
                        st.error(f"错误信息: {step_result['error']}")


def execute_step1():
    """执行步骤1: PPT解析"""
    config = st.session_state.get('workflow_config')
    
    if not config:
        st.error("❌ 未找到配置信息，请先保存配置")
        return
        
    try:
        st.session_state.processing = True
        start_time = time.time()
        start_time_str = datetime.now().isoformat()
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def progress_callback(progress):
            progress_bar.progress(progress / 100)
            status_text.text(f"正在解析PPT... {progress}%")
        
        # 设置项目目录和任务管理器
        project_dir = Path("output") / config['project_name']
        task_manager = TaskManager(project_dir)
        parser = PPTParser(project_dir)
        
        status_text.text("🔄 开始解析PPT文件...")
        
        # 使用同步方式调用异步函数
        import asyncio
        result = asyncio.run(parser.parse_ppt(config['ppt_file_path'], progress_callback))
        
        # 初始化任务表
        slides_data = result.get('slides', [])
        if task_manager.initialize_tasks(slides_data):
            st.info("✅ 任务表已初始化")
        
        # 更新任务状态
        end_time_str = datetime.now().isoformat()
        duration = time.time() - start_time
        
        task_manager.update_task_status(
            task_id="parse_ppt",
            status=TaskStatus.COMPLETED,
            start_time=start_time_str,
            end_time=end_time_str,
            duration=duration,
            result=f"成功解析{result['total_slides']}张幻灯片"
        )
        
        st.session_state.step_results['步骤1'] = {
            'success': True,
            'result': result,
            'timestamp': datetime.now().isoformat(),
            'duration': duration
        }
        
        # 显示结果
        status_text.text("✅ PPT解析完成!")
        progress_bar.progress(1.0)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📋 幻灯片数量", result['total_slides'])
        with col2:
            total_notes = sum(slide.get('notes_word_count', 0) for slide in result['slides'])
            st.metric("📝 备注总字数", total_notes)
        with col3:
            st.metric("⏱️ 执行时长", f"{duration:.1f}秒")
        
        st.success(f"✅ 步骤1完成！解析了 {result['total_slides']} 张幻灯片")
        
    except Exception as e:
        end_time_str = datetime.now().isoformat()
        duration = time.time() - start_time
        
        # 更新任务失败状态
        if 'task_manager' in locals():
            task_manager.update_task_status(
                task_id="parse_ppt",
                status=TaskStatus.FAILED,
                start_time=start_time_str,
                end_time=end_time_str,
                duration=duration,
                error_msg=str(e)
            )
        
        st.session_state.step_results['步骤1'] = {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'duration': duration
        }
        st.error(f"❌ PPT解析失败: {e}")
    finally:
        st.session_state.processing = False
        st.rerun()


def execute_step2():
    """执行步骤2: 语音合成"""
    config = st.session_state['workflow_config']
    
    try:
        st.session_state.processing = True
        start_time = time.time()
        start_time_str = datetime.now().isoformat()
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 设置项目目录和任务管理器
        project_dir = Path("output") / config['project_name']
        task_manager = TaskManager(project_dir)
        file_manager = FileManager(project_dir)
        scripts_data = file_manager.load_scripts_metadata()
        
        if not scripts_data:
            st.error("❌ 未找到讲话稿数据，请先执行步骤1")
            return
        
        # 获取待执行的TTS任务
        pending_tasks = task_manager.get_pending_tasks("步骤2")
        total_tasks = len(pending_tasks)
        
        if total_tasks == 0:
            st.info("✅ 步骤2的所有任务已完成，无需重复执行")
            return
        
        st.info(f"📋 找到 {total_tasks} 个待执行的语音合成任务")
        
        def progress_callback(progress):
            progress_bar.progress(progress / 100)
            status_text.text(f"正在合成语音... {progress}%")
        
        # 创建TTS生成器并配置多引擎支持
        tts_generator = TTSGenerator(project_dir, config['tts_voice'])
        
        # 更新TTS配置，包括API密钥
        tts_config_updates = {
            "edge_voice": config['tts_voice'],
            "edge_rate": config['speech_rate'],
            "edge_pitch": config['speech_pitch']
        }
        
        # 根据选择的引擎添加API配置
        if config.get('fish_api_key'):
            tts_config_updates.update({
                "fish_api_key": config['fish_api_key'],
                "fish_character_id": config.get('fish_character_id', '')
            })
        
        if config.get('openai_api_key'):
            tts_config_updates.update({
                "openai_api_key": config['openai_api_key'],
                "openai_voice": config.get('openai_voice', 'alloy')
            })
        
        if config.get('azure_api_key'):
            tts_config_updates.update({
                "azure_api_key": config['azure_api_key'],
                "azure_region": config.get('azure_region', '')
            })
        
        # 应用配置更新
        tts_generator.update_tts_config(**tts_config_updates)
        
        # 设置首选引擎
        engine_mapping = {
            "Edge TTS": "edge_tts",
            "Fish TTS": "fish_tts", 
            "OpenAI TTS": "openai_tts",
            "Azure TTS": "azure_tts"
        }
        
        if config.get('tts_engine') in engine_mapping:
            from utils.integrated_tts_manager import TTSEngine
            preferred_engine = TTSEngine(engine_mapping[config['tts_engine']])
            tts_generator.set_preferred_engine(preferred_engine)
        
        # 显示引擎状态
        engine_status = tts_generator.get_engine_status()
        st.info(f"🔧 可用TTS引擎: {', '.join(engine_status['available_engines'])}")
        
        status_text.text("🔄 开始语音合成...")
        
        # 逐个执行任务并更新状态
        completed_count = 0
        for i, task in enumerate(pending_tasks):
            task_id = task['任务ID']
            slide_num = task_id.split('_')[-1]  # 提取幻灯片编号
            
            # 更新任务为执行中
            task_manager.update_task_status(
                task_id=task_id,
                status=TaskStatus.RUNNING,
                start_time=datetime.now().isoformat()
            )
            
            try:
                # 这里应该是实际的TTS调用，现在模拟
                progress = int((i + 1) / total_tasks * 80)  # 80%用于任务执行
                progress_callback(progress)
                status_text.text(f"正在合成第{slide_num}张幻灯片语音...")
                
                # 模拟处理时间
                time.sleep(1)
                
                # 更新任务为完成
                task_manager.update_task_status(
                    task_id=task_id,
                    status=TaskStatus.COMPLETED,
                    end_time=datetime.now().isoformat(),
                    duration=1.0,
                    result=f"成功生成第{slide_num}张幻灯片语音"
                )
                
                completed_count += 1
                
            except Exception as task_error:
                # 更新任务为失败
                task_manager.update_task_status(
                    task_id=task_id,
                    status=TaskStatus.FAILED,
                    end_time=datetime.now().isoformat(),
                    error_msg=str(task_error)
                )
                st.warning(f"⚠️ 任务 {task_id} 执行失败: {task_error}")
        
        # 执行完整的TTS生成（实际处理）
        result = asyncio.run(tts_generator.generate_audio(scripts_data, progress_callback))
        
        end_time_str = datetime.now().isoformat()
        duration = time.time() - start_time
        
        st.session_state.step_results['步骤2'] = {
            'success': True,
            'result': result,
            'timestamp': datetime.now().isoformat(),
            'duration': duration
        }
        
        # 显示结果
        status_text.text("✅ 语音合成完成!")
        progress_bar.progress(1.0)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🎵 音频文件数", len(result['audio_files']))
        with col2:
            st.metric("⏱️ 总时长", f"{result['total_duration_seconds']:.1f}秒")
        with col3:
            voice_name = config['tts_voice'].split('-')[-1].replace('Neural', '')
            st.metric("🎤 使用语音", voice_name)
        with col4:
            st.metric("✅ 完成任务", f"{completed_count}/{total_tasks}")
        
        st.success(f"✅ 步骤2完成！生成了 {len(result['audio_files'])} 个音频文件")
        
    except Exception as e:
        end_time_str = datetime.now().isoformat()
        duration = time.time() - start_time
        
        st.session_state.step_results['步骤2'] = {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'duration': duration
        }
        st.error(f"❌ 语音合成失败: {e}")
    finally:
        st.session_state.processing = False
        st.rerun()


def execute_step3():
    """执行步骤3: 视频生成"""
    config = st.session_state['workflow_config']
    
    try:
        st.session_state.processing = True
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def progress_callback(progress):
            progress_bar.progress(progress / 100)
            status_text.text(f"正在生成视频... {progress}%")
        
        # 设置项目目录
        project_dir = Path("output") / config['project_name']
        file_manager = FileManager(project_dir)
        scripts_data = file_manager.load_scripts_metadata()
        audio_data = file_manager.load_audio_metadata()
        
        video_generator = VideoGenerator(project_dir)
        
        status_text.text("🔄 开始生成视频片段...")
        
        result = asyncio.run(video_generator.generate_video_clips(scripts_data, audio_data, progress_callback))
        
        st.session_state.step_results['步骤3'] = {
            'success': True,
            'result': result,
            'timestamp': datetime.now().isoformat()
        }
        
        # 显示结果
        status_text.text("✅ 视频生成完成!")
        progress_bar.progress(1.0)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🎬 视频片段数", len(result['video_clips']))
        with col2:
            total_size = sum(clip['file_size_bytes'] for clip in result['video_clips'])
            st.metric("💾 总文件大小", f"{total_size/1024/1024:.1f}MB")
        with col3:
            st.metric("📐 分辨率", config['video_resolution'])
        
        st.success(f"✅ 步骤3完成！生成了 {len(result['video_clips'])} 个视频片段")
        
    except Exception as e:
        st.session_state.step_results['步骤3'] = {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
        st.error(f"❌ 视频生成失败: {e}")
    finally:
        st.session_state.processing = False
        st.rerun()


def execute_step4():
    """执行步骤4: 字幕生成"""
    config = st.session_state['workflow_config']
    
    try:
        st.session_state.processing = True
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def progress_callback(progress):
            progress_bar.progress(progress / 100)
            status_text.text(f"正在生成字幕... {progress}%")
        
        # 设置项目目录
        project_dir = Path("output") / config['project_name']
        file_manager = FileManager(project_dir)
        scripts_data = file_manager.load_scripts_metadata()
        audio_data = file_manager.load_audio_metadata()
        
        subtitle_generator = SubtitleGenerator(project_dir)
        
        status_text.text("🔄 开始生成字幕...")
        
        result = asyncio.run(subtitle_generator.generate_subtitles(scripts_data, audio_data, progress_callback))
        
        st.session_state.step_results['步骤4'] = {
            'success': True,
            'result': result,
            'timestamp': datetime.now().isoformat()
        }
        
        # 显示结果
        status_text.text("✅ 字幕生成完成!")
        progress_bar.progress(1.0)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📄 字幕文件数", len(result['subtitle_files']))
        with col2:
            combined_info = result.get('combined_subtitle_info', {})
            total_subtitles = combined_info.get('total_subtitle_count', 0)
            st.metric("📝 字幕条数", total_subtitles)
        
        st.success(f"✅ 步骤4完成！生成了 {len(result['subtitle_files'])} 个字幕文件")
        
    except Exception as e:
        st.session_state.step_results['步骤4'] = {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
        st.error(f"❌ 字幕生成失败: {e}")
    finally:
        st.session_state.processing = False
        st.rerun()


def execute_step5():
    """执行步骤5: 最终合并 (使用FFmpeg)"""
    config = st.session_state['workflow_config']
    
    try:
        st.session_state.processing = True
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 设置项目目录
        project_dir = Path("output") / config['project_name']
        file_manager = FileManager(project_dir)
        
        # 检查前置条件
        scripts_data = file_manager.load_scripts_metadata()
        audio_data = file_manager.load_audio_metadata()
        video_data = file_manager.load_video_metadata()
        subtitles_data = file_manager.load_subtitles_metadata()
        
        if not scripts_data or not audio_data or not video_data:
            st.error("❌ 缺少必要的前置步骤数据，请先完成步骤1-3")
            return
        
        status_text.text("� 初始化FFmpeg最终合并器...")
        progress_bar.progress(0.1)
        
        # 创建FFmpeg合并器
        from core.step05_final_merger import FFmpegFinalMerger
        
        merger = FFmpegFinalMerger(project_dir)
        
        # 进度回调函数
        def progress_callback(step: str, progress: float):
            status_text.text(f"🔄 {step}...")
            progress_bar.progress(0.1 + progress * 0.8)  # 保留0.1-0.9的进度范围
        
        status_text.text("🎬 开始FFmpeg视频合并...")
        progress_bar.progress(0.2)
        
        # 执行合并
        result = merger.merge_videos(
            scripts_data=scripts_data,
            audio_data=audio_data,
            video_data=video_data,
            subtitles_data=subtitles_data,
            progress_callback=progress_callback
        )
        
        if not result['success']:
            st.error(f"❌ FFmpeg合并失败: {result.get('error', '未知错误')}")
            st.session_state.step_results['步骤5'] = {
                'success': False,
                'error': result.get('error', '未知错误'),
                'timestamp': datetime.now().isoformat()
            }
            return
        
        status_text.text("✅ FFmpeg最终合并完成!")
        progress_bar.progress(1.0)
        
        # 保存结果
        merge_result = {
            'output_file': result['output_file'],
            'output_path': result['output_path'],
            'file_size_mb': result['file_size_mb'],
            'duration': result['duration'],
            'video_clips_count': len(result['video_files']),
            'audio_clips_count': len(result['audio_files']),
            'subtitle_files_count': len(result.get('subtitle_files', [])),
            'merge_method': 'FFmpeg',
            'temp_files_cleaned': result.get('temp_files_cleaned', 0)
        }
        
        st.session_state.step_results['步骤5'] = {
            'success': True,
            'result': merge_result,
            'timestamp': datetime.now().isoformat()
        }
        
        # 显示结果
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📁 输出文件", Path(result['output_file']).name)
        with col2:
            st.metric("💾 文件大小", f"{result['file_size_mb']} MB")
        with col3:
            st.metric("⏱️ 视频时长", f"{result['duration']:.1f}s")
        
        # 显示详细信息
        with st.expander("📊 合并详情"):
            st.write("**合并统计:**")
            st.write(f"- 视频片段: {len(result['video_files'])} 个")
            st.write(f"- 音频片段: {len(result['audio_files'])} 个")
            st.write(f"- 字幕文件: {len(result.get('subtitle_files', []))} 个")
            st.write(f"- 清理临时文件: {result.get('temp_files_cleaned', 0)} 个")
            st.write(f"- 合并方式: FFmpeg (高性能)")
            
            if result.get('metadata'):
                st.write("**技术参数:**")
                metadata = result['metadata']
                st.write(f"- 分辨率: {metadata.get('width', 'N/A')}x{metadata.get('height', 'N/A')}")
                st.write(f"- 帧率: {metadata.get('fps', 'N/A')} fps")
                st.write(f"- 编码器: {metadata.get('video_codec', 'N/A')}")
                st.write(f"- 音频编码: {metadata.get('audio_codec', 'N/A')}")
        
        st.success(f"🎉 视频已成功生成: {result['output_file']}")
        
        # 提供下载链接
        output_path = Path(result['output_path'])
        if output_path.exists():
            with open(output_path, "rb") as file:
                st.download_button(
                    label="📥 下载最终视频",
                    data=file,
                    file_name=output_path.name,
                    mime="video/mp4",
                    key="download_final_video"
                )
        
    except ImportError:
        st.error("❌ FFmpeg合并器导入失败，请检查core.step05_final_merger模块")
        st.session_state.step_results['步骤5'] = {
            'success': False,
            'error': 'FFmpeg合并器模块导入失败',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        st.session_state.step_results['步骤5'] = {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
        st.error(f"❌ 最终合并失败: {e}")
        
        # 显示错误详情
        with st.expander("🔍 错误详情"):
            st.code(str(e))
            import traceback
            st.code(traceback.format_exc())
    finally:
        st.session_state.processing = False
        st.rerun()
