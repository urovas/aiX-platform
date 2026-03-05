import os
import json
from modules.script.generator import ScriptGenerator
from modules.character.generator import CharacterGenerator
from modules.scene.generator import SceneGenerator
from modules.audio.generator import AudioGenerator
from modules.video.generator import VideoGenerator
from modules.post.producer import PostProducer

class ShortDramaWorkflow:
    def __init__(self):
        self.script_generator = ScriptGenerator()
        self.character_generator = CharacterGenerator()
        self.scene_generator = SceneGenerator()
        self.audio_generator = AudioGenerator()
        self.video_generator = VideoGenerator()
        self.post_producer = PostProducer()
    
    def run_workflow(self, topic: str, genre: str, duration: str, characters: list, setting: str) -> str:
        """
        运行完整的短剧制作工作流
        
        Args:
            topic: 短剧主题
            genre: 短剧类型
            duration: 短剧时长
            characters: 角色列表
            setting: 场景设置
            
        Returns:
            最终视频文件路径
        """
        print("=== 开始短剧制作工作流 ===")
        
        # 1. 生成剧本
        print("\n1. 正在生成剧本...")
        script = self.script_generator.generate_script(
            topic=topic,
            genre=genre,
            duration=duration,
            characters=characters,
            setting=setting
        )
        script_path = script['script_path']
        print(f"   剧本生成完成: {script_path}")
        
        # 2. 生成角色形象
        print("\n2. 正在生成角色形象...")
        self.character_generator.generate_characters(script_path)
        print("   角色形象生成完成")
        
        # 3. 生成场景背景
        print("\n3. 正在生成场景背景...")
        self.scene_generator.generate_scenes(script_path)
        print("   场景背景生成完成")
        
        # 4. 生成音频
        print("\n4. 正在生成音频...")
        self.audio_generator.generate_audio(script_path)
        print("   音频生成完成")
        
        # 5. 生成视频
        print("\n5. 正在生成视频...")
        self.video_generator.generate_video(script_path)
        print("   视频生成完成")
        
        # 6. 制作最终视频
        print("\n6. 正在制作最终视频...")
        final_video_path = self.post_producer.produce_final_video(script_path)
        print(f"   最终视频制作完成: {final_video_path}")
        
        print("\n=== 短剧制作工作流完成 ===")
        return final_video_path