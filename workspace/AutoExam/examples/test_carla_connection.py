#!/usr/bin/env python3
"""
简单的CARLA连接测试
"""

import sys
import os

sys.path.insert(0, '/home/xcc/UROVAs/close_loop/SparseDrive_MomAD/CARLA/PythonAPI/carla/dist/carla-0.9.15-py3.7-linux-x86_64.egg')

try:
    import carla
    print("✅ CARLA模块导入成功")
    print(f"   CARLA版本: {carla.__version__}")
    
    client = carla.Client('localhost', 2000)
    client.set_timeout(10.0)
    
    print("✅ 正在连接CARLA服务器...")
    world = client.get_world()
    print(f"✅ 成功连接到CARLA服务器")
    print(f"   当前地图: {world.get_map().name}")
    
    settings = world.get_settings()
    print(f"   同步模式: {settings.synchronous_mode}")
    print(f"   时间步长: {settings.fixed_delta_seconds}")
    
    print("\n✅ CARLA连接测试成功！")
    
except ImportError as e:
    print(f"❌ 导入CARLA失败: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ 连接CARLA失败: {e}")
    print("\n请确保:")
    print("1. CARLA服务器正在运行")
    print("2. CARLA服务器已完全启动（等待30-60秒）")
    print("3. 端口2000未被占用")
    sys.exit(1)
