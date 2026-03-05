import os
import json
from typing import List, Dict
from config.config import Config

class CharacterGenerator:
    def __init__(self):
        self.character_dir = Config.CHARACTER_DIR
    
    def generate_characters(self, script_path: str) -> List[Dict]:
        """
        生成角色形象
        
        Args:
            script_path: 剧本文件路径
            
        Returns:
            角色信息列表
        """
        # 加载剧本
        with open(script_path, 'r', encoding='utf-8') as f:
            script = json.load(f)
        
        characters = script.get('characters', [])
        
        # 为每个角色生成形象
        for character in characters:
            name = character['name']
            # 生成角色图片路径
            image_file = f"{name.lower().replace(' ', '_')}.png"
            image_path = os.path.join(self.character_dir, image_file)
            
            # 创建占位文件
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            with open(image_path, 'w') as f:
                f.write(f"Character image for {name}")
            
            character['image_path'] = image_path
        
        # 保存更新后的剧本
        with open(script_path, 'w', encoding='utf-8') as f:
            json.dump(script, f, ensure_ascii=False, indent=2)
        
        return characters