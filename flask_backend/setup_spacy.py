"""
Spacy模型安装和管理脚本
自动安装所需的语言模型
"""

import subprocess
import sys
import logging
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)

# 支持的语言模型
LANGUAGE_MODELS = {
    'zh': {
        'model': 'zh_core_web_sm',
        'description': '中文小型模型',
        'size': '约50MB'
    },
    'en': {
        'model': 'en_core_web_sm',
        'description': '英文小型模型', 
        'size': '约15MB'
    },
    'ja': {
        'model': 'ja_core_news_sm',
        'description': '日文小型模型',
        'size': '约40MB'
    }
}


def check_spacy_available() -> bool:
    """检查Spacy是否可用"""
    try:
        import spacy
        return True
    except ImportError:
        return False


def check_model_installed(model_name: str) -> bool:
    """检查模型是否已安装"""
    try:
        import spacy
        spacy.load(model_name)
        return True
    except (ImportError, OSError):
        return False


def install_spacy() -> bool:
    """安装Spacy包"""
    try:
        print("正在安装Spacy...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'spacy>=3.4.0'])
        print("✅ Spacy安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Spacy安装失败: {e}")
        return False


def install_model(model_name: str) -> bool:
    """安装指定的语言模型"""
    try:
        print(f"正在安装模型 {model_name}...")
        subprocess.check_call([sys.executable, '-m', 'spacy', 'download', model_name])
        print(f"✅ 模型 {model_name} 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 模型 {model_name} 安装失败: {e}")
        return False


def install_all_models() -> Dict[str, bool]:
    """安装所有支持的语言模型"""
    results = {}
    
    for lang_code, model_info in LANGUAGE_MODELS.items():
        model_name = model_info['model']
        
        print(f"\n检查 {model_info['description']} ({model_name})...")
        
        if check_model_installed(model_name):
            print(f"✅ 模型 {model_name} 已安装")
            results[lang_code] = True
        else:
            print(f"⏳ 正在安装 {model_name} ({model_info['size']})...")
            success = install_model(model_name)
            results[lang_code] = success
    
    return results


def setup_spacy_environment() -> bool:
    """设置Spacy环境"""
    print("=== Spacy语法分析环境设置 ===\n")
    
    # 检查Spacy是否安装
    if not check_spacy_available():
        print("Spacy未安装，正在安装...")
        if not install_spacy():
            return False
    else:
        print("✅ Spacy已安装")
    
    # 安装语言模型
    print("\n正在检查和安装语言模型...")
    model_results = install_all_models()
    
    # 统计结果
    successful_models = sum(1 for success in model_results.values() if success)
    total_models = len(model_results)
    
    print(f"\n=== 安装结果 ===")
    print(f"成功安装: {successful_models}/{total_models} 个模型")
    
    for lang_code, success in model_results.items():
        model_info = LANGUAGE_MODELS[lang_code]
        status = "✅" if success else "❌"
        print(f"  {status} {model_info['description']}: {model_info['model']}")
    
    # 验证功能
    print(f"\n正在验证Spacy功能...")
    try:
        from core.nlp_utils.spacy_processor import SpacyProcessor
        
        # 测试中文模型
        if model_results.get('zh', False):
            processor_zh = SpacyProcessor('zh')
            if processor_zh.is_model_available():
                print("✅ 中文语法分析功能正常")
            else:
                print("⚠️ 中文语法分析功能异常")
        
        # 测试英文模型
        if model_results.get('en', False):
            processor_en = SpacyProcessor('en')
            if processor_en.is_model_available():
                print("✅ 英文语法分析功能正常")
            else:
                print("⚠️ 英文语法分析功能异常")
                
    except Exception as e:
        print(f"⚠️ 功能验证失败: {e}")
    
    if successful_models > 0:
        print(f"\n🎉 Spacy环境设置完成！已安装 {successful_models} 个语言模型。")
        return True
    else:
        print(f"\n❌ Spacy环境设置失败，没有成功安装任何模型。")
        return False


def main():
    """主函数"""
    try:
        success = setup_spacy_environment()
        if success:
            print("\n📝 使用说明:")
            print("1. 系统将自动使用Spacy进行语法分析")
            print("2. 如果模型不可用，系统会自动降级到基础分析")
            print("3. 可以通过配置文件控制Spacy功能的启用/禁用")
        else:
            print("\n⚠️ 注意事项:")
            print("1. Spacy安装失败，系统将使用基础分析功能")
            print("2. 可以稍后手动安装: python -m spacy download zh_core_web_sm")
            print("3. 或者禁用Spacy功能: use_spacy=False")
            
    except KeyboardInterrupt:
        print("\n\n用户取消安装")
    except Exception as e:
        print(f"\n❌ 安装过程出错: {e}")


if __name__ == "__main__":
    main()
