"""
服务器配置管理工具
统一管理各个服务器的端口和配置
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

class ServerConfigManager:
    """服务器配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        if config_file is None:
            # 使用相对于当前文件的配置路径
            self.config_file = Path(__file__).parent.parent / "config_data" / "server_config.json"
        else:
            self.config_file = Path(config_file)
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return self._get_default_config()
        except Exception as e:
            print(f"⚠️ 配置文件加载失败: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "development": {
                "servers": {
                    "frontend": {
                        "host": "localhost",
                        "port": 5173,
                        "description": "PPTist前端开发服务器"
                    },
                    "main_api": {
                        "host": "0.0.0.0",
                        "port": 8502,
                        "description": "主要API服务器"
                    },
                    "pptist_api": {
                        "host": "0.0.0.0",
                        "port": 8001,
                        "description": "PPTist集成API服务器"
                    }
                }
            }
        }
    
    def get_server_config(self, server_name: str, environment: str = "development") -> Dict[str, Any]:
        """获取指定服务器的配置"""
        try:
            return self.config[environment]["servers"][server_name]
        except KeyError:
            print(f"⚠️ 未找到服务器配置: {server_name} (环境: {environment})")
            return {"host": "localhost", "port": 8000}
    
    def get_port(self, server_name: str, environment: str = "development") -> int:
        """获取指定服务器的端口"""
        config = self.get_server_config(server_name, environment)
        return config.get("port", 8000)
    
    def get_host(self, server_name: str, environment: str = "development") -> str:
        """获取指定服务器的主机地址"""
        config = self.get_server_config(server_name, environment)
        return config.get("host", "localhost")
    
    def get_url(self, server_name: str, environment: str = "development", path: str = "") -> str:
        """获取指定服务器的完整URL"""
        config = self.get_server_config(server_name, environment)
        host = config.get("host", "localhost")
        port = config.get("port", 8000)
        
        # 如果host是0.0.0.0，改为localhost用于客户端连接
        if host == "0.0.0.0":
            host = "localhost"
            
        base_url = f"http://{host}:{port}"
        return f"{base_url}{path}" if path else base_url
    
    def list_servers(self, environment: str = "development") -> Dict[str, Dict[str, Any]]:
        """列出所有服务器配置"""
        try:
            return self.config[environment]["servers"]
        except KeyError:
            return {}
    
    def print_server_info(self, environment: str = "development"):
        """打印服务器信息"""
        servers = self.list_servers(environment)
        print(f"\n🌐 {environment.upper()} 环境服务器配置:")
        print("=" * 50)
        
        for name, config in servers.items():
            host = config.get("host", "localhost")
            port = config.get("port", 8000)
            description = config.get("description", "")
            features = config.get("features", [])
            
            # 显示用于连接的URL
            display_host = "localhost" if host == "0.0.0.0" else host
            url = f"http://{display_host}:{port}"
            
            print(f"📡 {name}:")
            print(f"   URL: {url}")
            print(f"   描述: {description}")
            if features:
                print(f"   功能: {', '.join(features)}")
            print()

# 全局配置实例
server_config = ServerConfigManager()

# 便捷函数
def get_server_port(server_name: str, environment: str = "development") -> int:
    """获取服务器端口的便捷函数"""
    return server_config.get_port(server_name, environment)

def get_server_url(server_name: str, environment: str = "development", path: str = "") -> str:
    """获取服务器URL的便捷函数"""
    return server_config.get_url(server_name, environment, path)

def print_all_servers(environment: str = "development"):
    """打印所有服务器信息的便捷函数"""
    server_config.print_server_info(environment)

if __name__ == "__main__":
    # 测试配置管理器
    print("🚀 服务器配置管理器测试")
    
    # 打印所有服务器信息
    print_all_servers()
    
    # 测试获取特定服务器配置
    print("🔍 测试获取服务器配置:")
    print(f"主API服务器端口: {get_server_port('main_api')}")
    print(f"前端服务器URL: {get_server_url('frontend')}")
    print(f"PPTist API URL: {get_server_url('pptist_api', path='/pm/api')}")
