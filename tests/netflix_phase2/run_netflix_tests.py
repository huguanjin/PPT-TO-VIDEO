#!/usr/bin/env python3
"""
Netflix Phase 2测试运行器
自动执行所有Netflix Phase 2相关的测试
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class NetflixPhase2TestRunner:
    """Netflix Phase 2测试运行器"""
    
    def __init__(self):
        self.project_root = project_root
        self.test_dir = self.project_root / "tests" / "netflix_phase2"
        self.results = {}
        self.summary = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'skipped_tests': 0,
            'execution_time': 0,
            'test_files': []
        }
    
    def discover_test_files(self) -> List[Path]:
        """发现所有测试文件"""
        test_files = []
        
        if self.test_dir.exists():
            for test_file in self.test_dir.glob("test_*.py"):
                test_files.append(test_file)
        
        # 按文件名排序，确保执行顺序一致
        test_files.sort()
        return test_files
    
    def run_single_test_file(self, test_file: Path) -> Dict[str, Any]:
        """运行单个测试文件"""
        print(f"\n{'='*60}")
        print(f"运行测试文件: {test_file.name}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            # 构建pytest命令
            cmd = [
                sys.executable, "-m", "pytest",
                str(test_file),
                "-v",                    # 详细输出
                "--tb=short",           # 简短的错误回溯
                "--strict-markers",     # 严格标记模式
                "--disable-warnings",   # 禁用警告
                "--maxfail=10"          # 最多失败10个就停止
            ]
            
            # 运行测试
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                encoding='utf-8',      # 指定UTF-8编码
                errors='ignore',       # 忽略编码错误
                timeout=300  # 5分钟超时
            )
            
            execution_time = time.time() - start_time
            
            # 解析测试结果（从pytest输出）
            passed_tests = 0
            failed_tests = 0
            skipped_tests = 0
            
            # 简单解析pytest输出
            output_lines = result.stdout.split('\n')
            for line in output_lines:
                if " passed" in line and " failed" in line:
                    # pytest summary line like "5 failed, 3 passed in 2.45s"
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "passed" and i > 0:
                            try:
                                passed_tests = int(parts[i-1])
                            except:
                                pass
                        elif part == "failed" and i > 0:
                            try:
                                failed_tests = int(parts[i-1])
                            except:
                                pass
                        elif part == "skipped" and i > 0:
                            try:
                                skipped_tests = int(parts[i-1])
                            except:
                                pass
                elif " passed in " in line:
                    # pytest summary line like "5 passed in 2.45s"
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "passed" and i > 0:
                            try:
                                passed_tests = int(parts[i-1])
                            except:
                                pass
            
            # 构建结果
            test_result = {
                'file': test_file.name,
                'return_code': result.returncode,
                'execution_time': execution_time,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'success': result.returncode == 0,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'skipped_tests': skipped_tests
            }
            
            # 更新总统计
            self.summary['total_tests'] += passed_tests + failed_tests + skipped_tests
            self.summary['passed_tests'] += passed_tests
            self.summary['failed_tests'] += failed_tests
            self.summary['skipped_tests'] += skipped_tests
            
            # 显示结果
            if result.returncode == 0:
                success_icon = "✅ 通过"
            else:
                success_icon = "❌ 失败"
            
            print(f"\n{test_file.name}: {success_icon} ({failed_tests} failed)")
            print(f"执行时间: {execution_time:.2f}s")
            
            if result.returncode != 0 and result.stderr:
                print(f"错误信息: {result.stderr[:200]}...")
            
            self.results[test_file.name] = test_result
            return test_result
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return {
                'file': test_file.name,
                'return_code': -1,
                'execution_time': execution_time,
                'success': False,
                'error': 'Timeout (5分钟)',
                'passed_tests': 0,
                'failed_tests': 0,
                'skipped_tests': 0
            }
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                'file': test_file.name,
                'return_code': -2,
                'execution_time': execution_time,
                'success': False,
                'error': str(e),
                'passed_tests': 0,
                'failed_tests': 0,
                'skipped_tests': 0
            }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        print("Netflix Phase 2 测试套件")
        print("=" * 60)
        
        test_files = self.discover_test_files()
        
        if not test_files:
            print("没有找到测试文件!")
            return self.summary
        
        print(f"发现 {len(test_files)} 个测试文件:")
        for test_file in test_files:
            print(f"  - {test_file.name}")
        
        total_start_time = time.time()
        
        # 运行每个测试文件
        for test_file in test_files:
            result = self.run_single_test_file(test_file)
            self.results[test_file.name] = result
            
            # 更新总体统计
            self.summary['total_tests'] += result.get('total', 0)
            self.summary['passed_tests'] += result.get('passed', 0)
            self.summary['failed_tests'] += result.get('failed', 0)
            self.summary['skipped_tests'] += result.get('skipped', 0)
            
            self.summary['test_files'].append({
                'name': test_file.name,
                'success': result['success'],
                'execution_time': result['execution_time'],
                'total': result.get('total', 0),
                'passed': result.get('passed', 0),
                'failed': result.get('failed', 0)
            })
            
            # 打印即时结果
            if result['success']:
                status = "✅ 通过"
                details = f"({result.get('passed', 0)} passed"
                if result.get('skipped', 0) > 0:
                    details += f", {result.get('skipped', 0)} skipped"
                details += ")"
            else:
                status = "❌ 失败"
                details = f"({result.get('failed', 0)} failed"
                if result.get('passed', 0) > 0:
                    details += f", {result.get('passed', 0)} passed"
                details += ")"
            
            print(f"\n{test_file.name}: {status} {details}")
            print(f"执行时间: {result['execution_time']:.2f}s")
            
            if not result['success'] and result.get('stderr'):
                print(f"错误信息: {result['stderr'][:200]}...")
        
        self.summary['execution_time'] = time.time() - total_start_time
        
        return self.summary
    
    def print_final_summary(self):
        """打印最终总结"""
        print("\n" + "="*60)
        print("测试执行总结")
        print("="*60)
        
        # 总体统计
        total = self.summary['total_tests']
        passed = self.summary['passed_tests']
        failed = self.summary['failed_tests']
        skipped = self.summary['skipped_tests']
        
        print(f"总测试数: {total}")
        print(f"通过: {passed} ({passed/total*100:.1f}% if total > 0 else 0)")
        print(f"失败: {failed} ({failed/total*100:.1f}% if total > 0 else 0)")
        if skipped > 0:
            print(f"跳过: {skipped} ({skipped/total*100:.1f}% if total > 0 else 0)")
        
        print(f"总执行时间: {self.summary['execution_time']:.2f}s")
        
        # 每个文件的详细情况
        print("\n文件详情:")
        print("-" * 60)
        for file_info in self.summary['test_files']:
            status_icon = "✅" if file_info['success'] else "❌"
            print(f"{status_icon} {file_info['name']:<35} "
                  f"{file_info['passed']:>3}/{file_info['total']:<3} "
                  f"({file_info['execution_time']:>5.1f}s)")
        
        # 失败文件的详细错误信息
        failed_files = [name for name, result in self.results.items() if not result['success']]
        if failed_files:
            print("\n失败文件详情:")
            print("-" * 60)
            for file_name in failed_files:
                result = self.results[file_name]
                print(f"\n{file_name}:")
                if result.get('error'):
                    print(f"  错误: {result['error']}")
                if result.get('stderr'):
                    stderr_lines = result['stderr'].split('\n')[:5]  # 只显示前5行
                    for line in stderr_lines:
                        if line.strip():
                            print(f"  {line}")
        
        # 成功率评估
        success_rate = passed / total if total > 0 else 0
        print(f"\n总体成功率: {success_rate:.1%}")
        
        if success_rate >= 0.95:
            print("🎉 优秀! Netflix Phase 2系统质量很高!")
        elif success_rate >= 0.85:
            print("👍 良好! 大部分功能正常工作")
        elif success_rate >= 0.70:
            print("⚠️  一般! 需要修复一些问题")
        else:
            print("🚨 需要改进! 存在较多问题需要解决")
    
    def save_detailed_report(self, output_file: Optional[str] = None):
        """保存详细报告"""
        if output_file is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_file = f"netflix_phase2_test_report_{timestamp}.json"
        
        report = {
            'summary': self.summary,
            'detailed_results': self.results,
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'environment': {
                'python_version': sys.version,
                'platform': sys.platform,
                'working_directory': str(self.project_root)
            }
        }
        
        output_path = self.project_root / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n详细报告已保存到: {output_path}")

def main():
    """主函数"""
    runner = NetflixPhase2TestRunner()
    
    try:
        # 运行所有测试
        summary = runner.run_all_tests()
        
        # 打印总结
        runner.print_final_summary()
        
        # 保存详细报告
        runner.save_detailed_report()
        
        # 根据结果设置退出码
        if summary['failed_tests'] == 0:
            sys.exit(0)  # 成功
        else:
            sys.exit(1)  # 有失败的测试
            
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(2)
    except Exception as e:
        print(f"\n测试运行器出现错误: {e}")
        sys.exit(3)

if __name__ == "__main__":
    main()