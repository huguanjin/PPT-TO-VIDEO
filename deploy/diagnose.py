#!/usr/bin/env python3
"""
生产环境诊断脚本
检查PPT转视频工具的运行状态和常见问题
"""
import os
import sys
import json
from pathlib import Path
import subprocess
import pwd
import grp

def check_permissions():
    """检查文件权限"""
    print("=== 权限检查 ===")
    
    project_root = Path("/www/wwwroot/ppt-video")
    backend_root = project_root / "backend"
    
    critical_paths = [
        project_root / "output",
        project_root / "output/task_status",
        project_root / "output/task_status/task_statuses.json",
        backend_root / "output",
        backend_root / "logs",
        project_root / "uploads",
        project_root / "temp"
    ]
    
    for path in critical_paths:
        if path.exists():
            stat = path.stat()
            owner = pwd.getpwuid(stat.st_uid).pw_name
            group = grp.getgrgid(stat.st_gid).gr_name
            perms = oct(stat.st_mode)[-3:]
            print(f"✓ {path}: {owner}:{group} {perms}")
        else:
            print(f"✗ {path}: 不存在")

def check_processes():
    """检查运行进程"""
    print("\n=== 进程检查 ===")
    
    try:
        # 检查Flask进程
        result = subprocess.run(['pgrep', '-f', 'python.*app.py'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            print(f"✓ Flask进程运行中: PIDs {', '.join(pids)}")
        else:
            print("✗ Flask进程未运行")
            
        # 检查端口占用
        result = subprocess.run(['netstat', '-tlnp'], 
                              capture_output=True, text=True)
        if ':5000' in result.stdout:
            print("✓ 端口5000已监听")
        else:
            print("✗ 端口5000未监听")
            
    except Exception as e:
        print(f"进程检查失败: {e}")

def check_files():
    """检查关键文件"""
    print("\n=== 文件检查 ===")
    
    backend_root = Path("/www/wwwroot/ppt-video/backend")
    
    critical_files = [
        backend_root / "app.py",
        backend_root / "core/step02_tts_generator.py",
        backend_root / "core/step04_subtitle_generator.py",
        backend_root / "core/enhanced_workflow_executor.py",
        backend_root / "app/api/workspace.py"
    ]
    
    for file_path in critical_files:
        if file_path.exists():
            print(f"✓ {file_path}")
            # 检查关键方法是否存在
            if file_path.name == "step02_tts_generator.py":
                content = file_path.read_text()
                if "def generate_audio" in content:
                    print("  ✓ generate_audio方法存在")
                else:
                    print("  ✗ generate_audio方法缺失")
            elif file_path.name == "step04_subtitle_generator.py":
                content = file_path.read_text()
                if "def generate_subtitles" in content:
                    print("  ✓ generate_subtitles方法存在")
                else:
                    print("  ✗ generate_subtitles方法缺失")
        else:
            print(f"✗ {file_path}: 不存在")

def check_config():
    """检查配置文件"""
    print("\n=== 配置检查 ===")
    
    backend_root = Path("/www/wwwroot/ppt-video/backend")
    config_files = [
        backend_root / "config_data/app_config.json",
        backend_root / "config_data/tts_config.json"
    ]
    
    for config_file in config_files:
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"✓ {config_file}: 有效JSON")
            except json.JSONDecodeError as e:
                print(f"✗ {config_file}: JSON格式错误 - {e}")
        else:
            print(f"✗ {config_file}: 不存在")

def check_logs():
    """检查日志文件"""
    print("\n=== 日志检查 ===")
    
    log_paths = [
        Path("/www/logs/flask.log"),
        Path("/www/wwwroot/ppt-video/backend/logs")
    ]
    
    for log_path in log_paths:
        if log_path.exists():
            if log_path.is_file():
                size = log_path.stat().st_size
                print(f"✓ {log_path}: {size} bytes")
                # 显示最后几行
                try:
                    with open(log_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        if lines:
                            print(f"  最后一行: {lines[-1].strip()}")
                except Exception as e:
                    print(f"  读取失败: {e}")
            else:
                files = list(log_path.glob("*.log"))
                print(f"✓ {log_path}: {len(files)} 个日志文件")
        else:
            print(f"✗ {log_path}: 不存在")

def main():
    """主函数"""
    print("PPT转视频工具 - 生产环境诊断")
    print("=" * 50)
    
    check_permissions()
    check_processes()
    check_files()
    check_config()
    check_logs()
    
    print("\n=== 建议操作 ===")
    print("如果发现问题，请按以下顺序执行：")
    print("1. 运行权限修复脚本: bash /www/wwwroot/ppt-video/backend/deploy/fix_permissions.sh")
    print("2. 更新代码: bash /www/wwwroot/ppt-video/backend/deploy/update_production.sh")
    print("3. 重启Flask服务: systemctl restart flask-app 或手动重启")
    print("4. 检查日志: tail -f /www/logs/flask.log")

if __name__ == "__main__":
    main()
