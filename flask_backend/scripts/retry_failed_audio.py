"""
重试失败的音频任务脚本

用法:
    python flask_backend/scripts/retry_failed_audio.py <session_id> [project_dir]
    
示例:
    python flask_backend/scripts/retry_failed_audio.py session_20251010_143000
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from flask_backend.core.audio_task_queue import AudioTaskQueue
from flask_backend.core.audio_task_executor import AudioTaskExecutor
from flask_backend.core.audio_task_models import TaskStatus
from flask_backend.app.utils.integrated_tts_manager import IntegratedTTSManager, load_tts_config_from_app_config
from flask_backend.app.utils.logger import get_logger


async def retry_failed_tasks(session_id: str, project_dir: Path):
    """重试失败的任务
    
    Args:
        session_id: 会话ID
        project_dir: 项目目录
    """
    logger = get_logger(__name__)
    
    print(f"\n{'='*60}")
    print(f"  🔄 重试失败的音频任务")
    print(f"{'='*60}\n")
    print(f"📁 项目目录: {project_dir}")
    print(f"🆔 会话ID: {session_id}\n")
    
    # 加载任务队列
    task_queue = AudioTaskQueue(session_id, project_dir)
    
    # 获取统计信息
    stats = task_queue.get_statistics()
    print(f"📊 当前任务状态:")
    print(f"   总计: {stats['total_tasks']}")
    print(f"   完成: {stats['completed']}")
    print(f"   失败: {stats['failed']}")
    print(f"   待处理: {stats['pending']}")
    print(f"   成功率: {stats['success_rate']*100:.1f}%\n")
    
    # 获取失败的任务
    failed_tasks = task_queue.get_failed_tasks()
    
    if not failed_tasks:
        print("✅ 没有失败的任务，无需重试！")
        return
    
    print(f"⚠️ 发现 {len(failed_tasks)} 个失败任务:\n")
    for i, task in enumerate(failed_tasks, 1):
        error_msg = (task.last_error or "未知错误")[:80]
        print(f"   {i}. 页{task.page_number:3d} ({task.task_id})")
        print(f"      错误: {error_msg}...")
        print(f"      已重试: {task.retry_count} 次\n")
    
    # 询问用户是否继续
    response = input("是否重试这些失败的任务? (y/n): ")
    if response.lower() != 'y':
        print("❌ 取消重试")
        return
    
    # 重置失败任务
    print(f"\n🔄 重置失败任务状态...")
    for task in failed_tasks:
        logger.info(f"重置任务: {task.task_id}")
        task_queue.update_task_status(
            task.task_id,
            TaskStatus.PENDING,
            retry_count=0,  # 重置重试计数
            last_error=None
        )
    
    print(f"✅ 已重置 {len(failed_tasks)} 个任务\n")
    
    # 重新执行
    print(f"{'='*60}")
    print(f"  🚀 开始重试音频生成")
    print(f"{'='*60}\n")
    
    # 加载TTS配置
    tts_config = load_tts_config_from_app_config()
    tts_manager = IntegratedTTSManager(tts_config)
    
    # 创建执行器（使用较少的并发数以提高稳定性）
    executor = AudioTaskExecutor(
        task_queue=task_queue,
        tts_manager=tts_manager,
        max_concurrent=2  # 重试时使用较少的并发数
    )
    
    # 执行重试
    await executor.start()
    
    # 查看结果
    print(f"\n{'='*60}")
    print(f"  📊 重试完成")
    print(f"{'='*60}\n")
    
    final_stats = task_queue.get_statistics()
    print(f"最终统计:")
    print(f"   总计: {final_stats['total_tasks']}")
    print(f"   完成: {final_stats['completed']}")
    print(f"   失败: {final_stats['failed']}")
    print(f"   成功率: {final_stats['success_rate']*100:.1f}%")
    print(f"   平均重试: {final_stats['average_retries']:.1f} 次\n")
    
    if final_stats['failed'] > 0:
        remaining_failed = task_queue.get_failed_tasks()
        print(f"⚠️ 仍有 {len(remaining_failed)} 个任务失败:\n")
        for task in remaining_failed:
            error_msg = (task.last_error or "未知错误")[:60]
            print(f"   - 页{task.page_number} ({task.task_id}): {error_msg}")
        print(f"\n💡 建议: 检查网络连接和API配置后再次运行此脚本\n")
    else:
        print(f"🎉 所有任务都已成功完成！\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python retry_failed_audio.py <session_id> [project_dir]")
        print("\n示例:")
        print("  python flask_backend/scripts/retry_failed_audio.py session_20251010_143000")
        print("  python flask_backend/scripts/retry_failed_audio.py session_20251010_143000 D:/projects/my_ppt")
        sys.exit(1)
    
    session_id = sys.argv[1]
    
    if len(sys.argv) > 2:
        project_dir = Path(sys.argv[2])
    else:
        # 默认使用当前工作目录
        project_dir = Path.cwd()
    
    if not project_dir.exists():
        print(f"❌ 错误: 项目目录不存在: {project_dir}")
        sys.exit(1)
    
    # 运行重试
    asyncio.run(retry_failed_tasks(session_id, project_dir))
