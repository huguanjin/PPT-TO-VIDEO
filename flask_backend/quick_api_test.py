#!/usr/bin/env python3
"""快速测试Netflix V2配置管理API路由"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

print("🧪 快速API路由测试")
print("=" * 40)

app = create_app()
print("✅ Flask应用创建完成")

with app.test_client() as client:
    # 测试健康检查
    response = client.get('/api/v2/netflix/config/health')
    print(f"健康检查状态: {response.status_code}")
    if response.status_code == 200:
        data = response.get_json()
        print(f"  服务状态: {data['data']['status']}")
    
    # 测试配置列表
    response = client.get('/api/v2/netflix/config/configs')
    print(f"配置列表状态: {response.status_code}")
    if response.status_code == 200:
        data = response.get_json()
        templates = data['data']['templates']
        print(f"  模板数量: {len(templates)}")

print("✅ API路由测试完成")