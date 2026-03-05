import os
import json
from typing import List, Dict
from config.config import Config

class SceneGenerator:
    def __init__(self):
        self.scene_dir = Config.SCENE_DIR
    
    def generate_scenes(self, script_path: str) -> List[Dict]:
        """
        生成场景背景
        
        Args:
            script_path: 剧本文件路径
            
        Returns:
            场景信息列表
        """
        # 加载剧本
        with open(script_path, 'r', encoding='utf-8') as f:
            script = json.load(f)
        
        scenes = script.get('scenes', [])
        
        # 为每个场景生成背景
        for i, scene in enumerate(scenes):
            scene_id = scene.get('scene_id', f'scene_{i+1}')
            # 生成场景图片路径
            image_file = f"{scene_id}.png"
            image_path = os.path.join(self.scene_dir, image_file)
            
            # 创建占位文件
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            with open(image_path, 'w') as f:
                f.write(f"Scene background for {scene_id}")
            
            scene['image_path'] = image_path
        
        # 保存更新后的剧本
        with open(script_path, 'w', encoding='utf-8') as f:
            json.dump(script, f, ensure_ascii=False, indent=2)
        
        return scenes