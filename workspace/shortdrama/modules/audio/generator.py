import os
import json
from typing import List, Dict
from config.config import Config

class AudioGenerator:
    def __init__(self):
        self.audio_dir = Config.AUDIO_DIR
    
    def generate_audio(self, script_path: str) -> Dict[str, List[str]]:
        """
        为剧本生成音频
        
        Args:
            script_path: 剧本文件路径
            
        Returns:
            音频文件路径字典，键为场景ID，值为音频文件路径列表
        """
        # 加载剧本
        with open(script_path, 'r', encoding='utf-8') as f:
            script = json.load(f)
        
        scenes = script.get('scenes', [])
        audio_paths = {}
        
        # 为每个场景生成音频
        for scene in scenes:
            scene_id = scene.get('scene_id')
            dialogues = scene.get('dialogues', [])
            scene_audio_paths = []
            
            # 为每个对话生成音频
            for i, dialogue in enumerate(dialogues):
                # 生成音频文件路径
                audio_file = f"{scene_id}_dialogue_{i}.mp3"
                audio_path = os.path.join(self.audio_dir, audio_file)
                
                # 创建占位文件
                os.makedirs(os.path.dirname(audio_path), exist_ok=True)
                with open(audio_path, 'w') as f:
                    f.write(f"Audio for {scene_id} dialogue {i}")
                
                # 保存音频路径到对话中
                dialogue['audio_path'] = audio_path
                scene_audio_paths.append(audio_path)
            
            audio_paths[scene_id] = scene_audio_paths
        
        # 保存更新后的剧本
        with open(script_path, 'w', encoding='utf-8') as f:
            json.dump(script, f, ensure_ascii=False, indent=2)
        
        return audio_paths