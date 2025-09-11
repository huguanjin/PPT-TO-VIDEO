"""
字幕多行显示修复配置应用脚本
将优化的配置参数应用到现有的VideoLingo集成系统中
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

class SubtitleConfigUpdater:
    """字幕配置更新器"""
    
    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path(__file__).parent
        self.backup_dir = self.project_root / "config_data" / "backup"
        self.backup_dir.mkdir(exist_ok=True)
        
    def backup_existing_configs(self) -> Dict[str, Path]:
        """备份现有配置文件"""
        configs_to_backup = [
            "flask_backend/config_data/netflix_subtitle_config.json",
            "flask_backend/config_data/app_config.json",
            "config_data/subtitle_multiline_fix_config.json"
        ]
        
        backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_mapping = {}
        
        for config_path in configs_to_backup:
            full_path = self.project_root / config_path
            if full_path.exists():
                backup_name = f"{full_path.stem}_backup_{backup_timestamp}{full_path.suffix}"
                backup_path = self.backup_dir / backup_name
                shutil.copy2(full_path, backup_path)
                backup_mapping[config_path] = backup_path
                print(f"已备份: {config_path} -> {backup_path}")
        
        return backup_mapping
    
    def update_netflix_config(self) -> bool:
        """更新Netflix字幕配置"""
        config_path = self.project_root / "flask_backend/config_data/netflix_subtitle_config.json"
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 更新字符权重 - 解决多行显示问题的关键
            if "smart_processing" in config and "character_weights" in config["smart_processing"]:
                weights = config["smart_processing"]["character_weights"]
                
                # 应用分析报告中的优化建议
                weights.update({
                    "chinese": 2.0,      # 从1.75提升到2.0
                    "english": 1.0,      # 保持不变
                    "punctuation": 0.6,  # 从0.8降低到0.6
                    "space": 0.3,        # 从0.5降低到0.3
                    "number": 0.8        # 新增数字权重
                })
                
                print("✓ 已更新字符权重配置")
            
            # 更新布局规则 - 强化行数限制
            if "layout_rules" in config:
                layout = config["layout_rules"]
                layout.update({
                    "max_lines_per_subtitle": 2,           # 强制最大2行
                    "max_chars_per_line_cjk": 30,         # 中日韩字符每行30个权重单位
                    "enforce_strict_line_limit": True,     # 启用严格行数限制
                    "prefer_semantic_over_length": False   # 优先长度而非语义分割
                })
                
                print("✓ 已更新布局规则配置")
            
            # 更新时间规则 - 确保足够的显示时间
            if "timing_rules" in config:
                timing = config["timing_rules"]
                timing.update({
                    "min_duration_per_char": 0.15,  # 每字符最小显示时间
                    "max_reading_speed": 4.0        # 最大阅读速度（字/秒）
                })
                
                print("✓ 已更新时间规则配置")
            
            # 保存更新后的配置
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            print(f"✓ Netflix字幕配置已更新: {config_path}")
            return True
            
        except Exception as e:
            print(f"✗ 更新Netflix配置失败: {e}")
            return False
    
    def update_app_config(self) -> bool:
        """更新应用程序配置"""
        config_path = self.project_root / "flask_backend/config_data/app_config.json"
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 更新字幕相关配置
            if "subtitle_generation" not in config:
                config["subtitle_generation"] = {}
            
            subtitle_config = config["subtitle_generation"]
            subtitle_config.update({
                "enable_multiline_fix": True,
                "character_weight_mode": "enhanced",
                "strict_line_limit": True,
                "max_lines": 2,
                "resolution_adaptive_font": True,
                "videolingo_integration": {
                    "enabled": True,
                    "use_smart_splitting": True,
                    "use_character_weights": True,
                    "use_netflix_timing": True
                }
            })
            
            # 保存配置
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            print(f"✓ 应用程序配置已更新: {config_path}")
            return True
            
        except Exception as e:
            print(f"✗ 更新应用配置失败: {e}")
            return False
    
    def create_fix_config(self) -> bool:
        """创建修复配置文件"""
        config_path = self.project_root / "config_data/subtitle_multiline_fix_config.json"
        config_path.parent.mkdir(exist_ok=True)
        
        fix_config = {
            "subtitle_multiline_fix_config": {
                "version": "1.0.0",
                "last_updated": datetime.now().isoformat(),
                "description": "字幕多行显示问题修复配置 - 基于VideoLingo集成分析优化",
                
                "character_weight_adjustments": {
                    "chinese": 2.0,
                    "japanese": 2.0,
                    "korean": 1.8,
                    "english": 1.0,
                    "punctuation": 0.6,
                    "space": 0.3,
                    "number": 0.8
                },
                
                "line_control_rules": {
                    "max_lines_strict": 2,
                    "max_chars_per_line_chinese": 30,
                    "enforce_line_limit": True,
                    "prefer_length_over_semantic": True
                },
                
                "resolution_adaptive_font": {
                    "enabled": True,
                    "base_resolution": [1920, 1080],
                    "min_font_size": 16,
                    "max_font_size": 60,
                    "scale_factor_limit": [0.5, 2.0]
                },
                
                "videolingo_integration_options": {
                    "preserve_smart_features": True,
                    "override_semantic_splitting": True,
                    "use_enhanced_character_weights": True,
                    "apply_netflix_timing_standards": True
                }
            }
        }
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(fix_config, f, ensure_ascii=False, indent=2)
            
            print(f"✓ 修复配置文件已创建: {config_path}")
            return True
            
        except Exception as e:
            print(f"✗ 创建修复配置失败: {e}")
            return False
    
    def validate_configurations(self) -> Dict[str, bool]:
        """验证配置文件的完整性"""
        validation_results = {}
        
        configs_to_check = [
            "flask_backend/config_data/netflix_subtitle_config.json",
            "flask_backend/config_data/app_config.json", 
            "config_data/subtitle_multiline_fix_config.json"
        ]
        
        for config_path in configs_to_check:
            full_path = self.project_root / config_path
            try:
                if full_path.exists():
                    with open(full_path, 'r', encoding='utf-8') as f:
                        json.load(f)  # 尝试解析JSON
                    validation_results[config_path] = True
                else:
                    validation_results[config_path] = False
                    
            except Exception as e:
                print(f"✗ 配置文件验证失败 {config_path}: {e}")
                validation_results[config_path] = False
        
        return validation_results
    
    def apply_all_fixes(self) -> bool:
        """应用所有修复配置"""
        print("字幕多行显示修复配置应用程序")
        print("=" * 50)
        
        # 1. 备份现有配置
        print("\n1. 备份现有配置...")
        backup_mapping = self.backup_existing_configs()
        
        # 2. 创建修复配置
        print("\n2. 创建修复配置...")
        fix_config_created = self.create_fix_config()
        
        # 3. 更新Netflix配置
        print("\n3. 更新Netflix字幕配置...")
        netflix_updated = self.update_netflix_config()
        
        # 4. 更新应用配置
        print("\n4. 更新应用程序配置...")
        app_updated = self.update_app_config()
        
        # 5. 验证配置
        print("\n5. 验证配置完整性...")
        validation_results = self.validate_configurations()
        
        # 6. 生成报告
        success_count = sum([fix_config_created, netflix_updated, app_updated])
        total_operations = 3
        
        print("\n" + "=" * 50)
        print("配置应用结果:")
        print(f"成功操作: {success_count}/{total_operations}")
        
        for config_path, is_valid in validation_results.items():
            status = "✓ 有效" if is_valid else "✗ 无效"
            print(f"{config_path}: {status}")
        
        if success_count == total_operations:
            print("\n🎉 所有配置更新完成！字幕多行显示问题已修复。")
            print("\n后续步骤:")
            print("1. 重启Flask后端服务")
            print("2. 测试字幕生成功能")
            print("3. 验证多行显示是否得到改善")
            return True
        else:
            print(f"\n⚠️  部分配置更新失败，请检查错误信息并手动修复。")
            print(f"备份文件位于: {self.backup_dir}")
            return False


def main():
    """主函数"""
    updater = SubtitleConfigUpdater()
    success = updater.apply_all_fixes()
    
    if success:
        print(f"\n配置更新成功完成！")
    else:
        print(f"\n配置更新过程中出现问题，请查看上述错误信息。")


if __name__ == "__main__":
    main()
