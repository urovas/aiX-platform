import sys
import os

# 设置CARLA路径
carla_path = '/home/xcc/UROVAs/close_loop/SparseDrive_MomAD/CARLA'
carla_egg = os.path.join(carla_path, 'PythonAPI', 'carla', 'dist', 'carla-0.9.15-py3.7-linux-x86_64.egg')

# 添加CARLA egg到Python路径
sys.path.append(carla_egg)

import carla

print("尝试连接CARLA服务器...")
try:
    # 连接到CARLA服务器
    client = carla.Client('localhost', 2000)
    client.set_timeout(10.0)
    
    # 获取世界
    world = client.get_world()
    print("成功连接到CARLA服务器!")
    print(f"服务器版本: {client.get_server_version()}")
    print(f"客户端版本: {client.get_client_version()}")
    
    # 获取地图
    map = world.get_map()
    print(f"当前地图: {map.name}")
    
    print("测试成功!")
except Exception as e:
    print(f"连接失败: {e}")
    import traceback
    traceback.print_exc()