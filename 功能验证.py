"""
PPT转视频工具 - 功能验证脚本
验证新的配置持久化和任务管理功能是否正常工作
"""
import streamlit as st
from pathlib import Path
import json
import pandas as pd

def check_config_persistence():
    """检查配置持久化功能"""
    st.header("🔧 配置持久化功能检查")
    
    config_file = Path("config_data/app_config.json")
    
    if config_file.exists():
        st.success(f"✅ 配置文件存在: {config_file}")
        
        # 读取配置内容
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        st.subheader("当前保存的配置:")
        for key, value in config.items():
            if key not in ['last_updated', 'auto_save']:
                st.write(f"- **{key}**: {value}")
        
        st.info(f"最后更新时间: {config.get('last_updated', '未知')}")
    else:
        st.error("❌ 配置文件不存在")

def check_task_management():
    """检查任务管理功能"""
    st.header("📊 任务管理功能检查")
    
    test_project_dir = Path("output/test_project")
    
    if test_project_dir.exists():
        st.success(f"✅ 测试项目目录存在: {test_project_dir}")
        
        # 检查任务记录文件
        task_records_file = test_project_dir / "task_records.xlsx"
        if task_records_file.exists():
            st.success("✅ 任务记录文件存在")
            
            # 读取任务记录
            try:
                df = pd.read_excel(task_records_file)
                st.subheader(f"任务记录详情 (共 {len(df)} 个任务):")
                st.dataframe(df[['步骤ID', '任务名称', '任务状态', '开始时间', '结束时间']])
                
                # 统计各状态任务数量
                status_counts = df['任务状态'].value_counts()
                st.subheader("任务状态统计:")
                for status, count in status_counts.items():
                    st.write(f"- **{status}**: {count} 个")
                    
            except Exception as e:
                st.error(f"❌ 读取任务记录失败: {str(e)}")
        else:
            st.warning("⚠️ 任务记录文件不存在")
        
        # 检查任务报告
        report_files = list(test_project_dir.glob("task_report_*.xlsx"))
        if report_files:
            st.success(f"✅ 找到 {len(report_files)} 个任务报告文件")
            latest_report = max(report_files, key=lambda x: x.stat().st_mtime)
            st.info(f"最新报告: {latest_report.name}")
        else:
            st.warning("⚠️ 未找到任务报告文件")
    else:
        st.error("❌ 测试项目目录不存在")

def check_system_status():
    """检查系统整体状态"""
    st.header("🚀 系统状态检查")
    
    # 检查必要的模块
    modules_to_check = [
        'utils.config_manager',
        'utils.task_manager',
        'core.step01_ppt_parser',
        'core.step02_tts_generator',
        'core.step03_video_generator',
        'core.step04_subtitle_generator',
        'core.step05_final_merger'
    ]
    
    success_count = 0
    for module in modules_to_check:
        try:
            __import__(module)
            st.success(f"✅ {module}")
            success_count += 1
        except ImportError as e:
            st.error(f"❌ {module}: {str(e)}")
    
    st.subheader(f"模块检查结果: {success_count}/{len(modules_to_check)} 成功")
    
    # 检查必要的目录
    directories_to_check = [
        'config_data',
        'output',
        'utils',
        'core',
        'ui/pages'
    ]
    
    dir_success_count = 0
    for directory in directories_to_check:
        if Path(directory).exists():
            st.success(f"✅ 目录存在: {directory}")
            dir_success_count += 1
        else:
            st.error(f"❌ 目录缺失: {directory}")
    
    st.subheader(f"目录检查结果: {dir_success_count}/{len(directories_to_check)} 成功")

def main():
    st.set_page_config(
        page_title="PPT转视频工具 - 功能验证",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 PPT转视频工具 - 功能验证")
    st.markdown("---")
    
    # 创建三列布局
    col1, col2, col3 = st.columns(3)
    
    with col1:
        check_config_persistence()
    
    with col2:
        check_task_management()
    
    with col3:
        check_system_status()
    
    st.markdown("---")
    st.info("💡 这个页面用于验证配置持久化和任务管理功能是否正常工作。")

if __name__ == "__main__":
    main()
