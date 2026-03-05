import os
import json
import requests
from typing import Dict, List
from config.config import Config

class ScriptGenerator:
    def __init__(self):
        self.script_dir = Config.SCRIPT_DIR
    
    def generate_script(self, topic: str, genre: str, duration: str, characters: List[str], setting: str) -> Dict:
        """
        生成剧本
        
        Args:
            topic: 短剧主题
            genre: 短剧类型
            duration: 短剧时长
            characters: 角色列表
            setting: 场景设置
            
        Returns:
            剧本信息
        """
        # 生成剧本标题
        title = f"{topic}"
        
        # 使用阿里千问生成剧本
        if Config.DASHSCOPE_API_KEY:
            script_content = self._generate_with_qwen(topic, genre, duration, characters, setting)
        else:
            # 备用方案：使用默认剧本
            script_content = {
                "title": title,
                "genre": genre,
                "duration": duration,
                "setting": setting,
                "characters": [{"name": char} for char in characters],
                "scenes": [
                    {
                        "scene_id": "scene_1",
                        "setting": setting,
                        "dialogues": [
                            {"character": characters[0], "text": "你好，很高兴认识你。"},
                            {"character": characters[1], "text": "你好，我也是。"}
                        ]
                    }
                ]
            }
        
        # 保存剧本
        script_file = f"{title}_script.json"
        script_path = os.path.join(self.script_dir, script_file)
        
        with open(script_path, 'w', encoding='utf-8') as f:
            json.dump(script_content, f, ensure_ascii=False, indent=2)
        
        return {
            "title": title,
            "genre": genre,
            "duration": duration,
            "setting": setting,
            "characters": script_content["characters"],
            "script_path": script_path,
            "script_content": script_content
        }
    
    def _generate_with_qwen(self, topic: str, genre: str, duration: str, characters: List[str], setting: str) -> Dict:
        """
        使用阿里千问生成剧本
        
        Args:
            topic: 短剧主题
            genre: 短剧类型
            duration: 短剧时长
            characters: 角色列表
            setting: 场景设置
            
        Returns:
            剧本内容
        """
        # 构建请求
        url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {Config.DASHSCOPE_API_KEY}"
        }
        
        # 构建提示词
        prompt = "请为我生成一个短剧剧本，具体要求如下：\n" \
                f"主题：{topic}\n" \
                f"类型：{genre}\n" \
                f"时长：{duration}\n" \
                f"角色：{', '.join(characters)}\n" \
                f"场景：{setting}\n" \
                "请生成一个完整的剧本，包括：\n" \
                "1. 剧本标题\n" \
                "2. 剧本类型\n" \
                "3. 剧本时长\n" \
                "4. 场景设置\n" \
                "5. 角色列表\n" \
                "6. 至少2个场景，每个场景包含多个对话\n" \
                "请以JSON格式输出，结构如下：\n" \
                "{\n" \
                "  \"title\": \"剧本标题\",\n" \
                "  \"genre\": \"剧本类型\",\n" \
                "  \"duration\": \"剧本时长\",\n" \
                "  \"setting\": \"场景设置\",\n" \
                "  \"characters\": [{\"name\": \"角色1\"}, {\"name\": \"角色2\"}],\n" \
                "  \"scenes\": [\n" \
                "    {\n" \
                "      \"scene_id\": \"scene_1\",\n" \
                "      \"setting\": \"场景设置\",\n" \
                "      \"dialogues\": [\n" \
                "        {\"character\": \"角色1\", \"text\": \"对话内容\"},\n" \
                "        {\"character\": \"角色2\", \"text\": \"对话内容\"}\n" \
                "      ]\n" \
                "    }\n" \
                "  ]\n" \
                "}"
        
        # 发送请求
        data = {
            "model": Config.DASHSCOPE_MODEL,
            "input": {
                "prompt": prompt
            },
            "parameters": {
                "temperature": Config.SCRIPT_TEMPERATURE,
                "max_tokens": Config.SCRIPT_MAX_TOKENS
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            # 提取剧本内容
            script_content = json.loads(result['output']['text'])
            return script_content
        except Exception as e:
            # 如果调用失败，使用默认剧本
            print(f"阿里千问API调用失败：{e}")
            return {
                "title": topic,
                "genre": genre,
                "duration": duration,
                "setting": setting,
                "characters": [{"name": char} for char in characters],
                "scenes": [
                    {
                        "scene_id": "scene_1",
                        "setting": setting,
                        "dialogues": [
                            {"character": characters[0], "text": "你好，很高兴认识你。"},
                            {"character": characters[1], "text": "你好，我也是。"}
                        ]
                    }
                ]
            }
    
    def update_script(self, script_path: str, updated_content: Dict) -> Dict:
        """
        更新剧本
        
        Args:
            script_path: 剧本文件路径
            updated_content: 更新后的剧本内容
            
        Returns:
            更新后的剧本信息
        """
        # 保存更新后的剧本
        with open(script_path, 'w', encoding='utf-8') as f:
            json.dump(updated_content, f, ensure_ascii=False, indent=2)
        
        # 加载更新后的剧本
        with open(script_path, 'r', encoding='utf-8') as f:
            script_content = json.load(f)
        
        return {
            "title": script_content.get("title"),
            "genre": script_content.get("genre"),
            "duration": script_content.get("duration"),
            "setting": script_content.get("setting"),
            "characters": script_content.get("characters"),
            "script_path": script_path,
            "script_content": script_content
        }