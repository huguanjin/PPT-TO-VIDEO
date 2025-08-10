"""
测试配置管理和任务管理功能
"""
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent))

from utils.config_manager import ConfigManager
from utils.task_manager import TaskManager, TaskStatus

def test_config_manager():
    """测试配置管理器"""
    print("=== 测试配置管理器 ===")
    
    config_manager = ConfigManager()
    
    # 测试加载配置
    config = config_manager.load_config()
    print(f"加载的配置: {config}")
    
    # 测试保存配置
    test_config = config.copy()
    test_config['project_name'] = 'test_project'
    test_config['tts_voice'] = 'zh-CN-YunxiNeural'
    
    if config_manager.save_config(test_config):
        print("✅ 配置保存成功")
    else:
        print("❌ 配置保存失败")
    
    # 测试重新加载
    reloaded_config = config_manager.load_config()
    print(f"重新加载的配置: {reloaded_config}")
    
    # 显示配置信息
    info = config_manager.get_config_display_info()
    print(f"配置信息: {info}")

def test_task_manager():
    """测试任务管理器"""
    print("\n=== 测试任务管理器 ===")
    
    project_dir = Path("output/test_project")
    task_manager = TaskManager(project_dir)
    
    # 模拟幻灯片数据
    slides_data = [
        {"slide_number": 1, "notes_text": "第一张幻灯片内容", "notes_word_count": 10},
        {"slide_number": 2, "notes_text": "第二张幻灯片内容", "notes_word_count": 12},
        {"slide_number": 3, "notes_text": "第三张幻灯片内容", "notes_word_count": 8}
    ]
    
    # 初始化任务
    if task_manager.initialize_tasks(slides_data):
        print("✅ 任务表初始化成功")
    else:
        print("❌ 任务表初始化失败")
    
    # 加载任务
    df = task_manager.load_tasks()
    if df is not None:
        print(f"任务表加载成功，共 {len(df)} 个任务")
        print("\n任务列表:")
        print(df[['步骤ID', '任务名称', '任务状态']].to_string(index=False))
    else:
        print("❌ 任务表加载失败")
    
    # 更新任务状态
    print("\n更新任务状态...")
    task_manager.update_task_status(
        task_id="tts_slide_001",
        status=TaskStatus.COMPLETED,
        start_time="2025-01-08T10:00:00",
        end_time="2025-01-08T10:01:00",
        duration=60.0,
        result="成功生成第1张幻灯片语音"
    )
    
    # 获取步骤摘要
    summary = task_manager.get_step_summary()
    print(f"\n步骤摘要: {summary}")
    
    # 导出报告
    report_file = task_manager.export_task_report()
    if report_file:
        print(f"✅ 任务报告已导出: {report_file}")
    else:
        print("❌ 任务报告导出失败")

if __name__ == "__main__":
    test_config_manager()
    test_task_manager()
    print("\n🎉 测试完成！")
