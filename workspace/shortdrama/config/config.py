import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    # API密钥
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")  # 阿里千问API密钥
    OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    
    # 模型配置
    OPENAI_MODEL = "gpt-4"
    ANTHROPIC_MODEL = "claude-3-opus-20240229"
    DASHSCOPE_MODEL = "qwen-max"  # 阿里千问模型
    DALLE_MODEL = "dall-e-3"
    ELEVENLABS_VOICE = "21m00Tcm4TlvDq8ikWAM"  # 默认语音
    
    # 生成配置
    SCRIPT_MAX_TOKENS = 4000
    SCRIPT_TEMPERATURE = 0.7
    IMAGE_SIZE = "1024x1024"
    IMAGE_QUALITY = "hd"
    AUDIO_SAMPLE_RATE = 22050
    VIDEO_FPS = 24
    
    # 工作目录
    WORK_DIR = os.getenv("WORK_DIR", "./output")
    SCRIPT_DIR = os.path.join(WORK_DIR, "scripts")
    CHARACTER_DIR = os.path.join(WORK_DIR, "characters")
    SCENE_DIR = os.path.join(WORK_DIR, "scenes")
    AUDIO_DIR = os.path.join(WORK_DIR, "audio")
    VIDEO_DIR = os.path.join(WORK_DIR, "video")
    FINAL_DIR = os.path.join(WORK_DIR, "final")
    
    # 确保目录存在
    os.makedirs(SCRIPT_DIR, exist_ok=True)
    os.makedirs(CHARACTER_DIR, exist_ok=True)
    os.makedirs(SCENE_DIR, exist_ok=True)
    os.makedirs(AUDIO_DIR, exist_ok=True)
    os.makedirs(VIDEO_DIR, exist_ok=True)
    os.makedirs(FINAL_DIR, exist_ok=True)
    
    # 应用配置
    UPLOAD_FOLDER = WORK_DIR
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "5000"))
    
    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "app.log")