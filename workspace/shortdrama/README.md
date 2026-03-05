# 短剧制作自动化工具

## 项目概述

短剧制作自动化工具是一个AI驱动的短剧创作与分发平台，旨在简化短剧制作的全流程，从剧本创作到视频生成、发布管理和数据分析。

## 核心功能

- **对标分析**：分析热门博主和题材，提供数据支持
- **拆片分析**：分析视频结构、镜头和音效
- **脚本创作**：基于AI生成短剧脚本
- **拍摄管理**：生成拍摄计划和注意事项
- **剪辑制作**：自动化视频剪辑和编辑
- **发布管理**：多平台发布和管理
- **数据分析**：内容表现和受众分析
- **创作者社区**：资源共享和经验交流

## 技术栈

- **前端**：HTML5, CSS3, JavaScript
- **后端**：Python, Flask
- **AI 模型**：OpenAI GPT-4, Claude, Qwen
- **视频处理**：FFmpeg, MoviePy
- **音频处理**：PyDub

## 快速开始

### 环境要求

- Python 3.8+
- FFmpeg
- 依赖库：见 requirements.txt

### 安装步骤

1. 克隆项目
2. 安装依赖：`pip install -r requirements.txt`
3. 配置环境变量：复制 .env.example 为 .env 并填写相关配置
4. 启动应用：`python app.py`
5. 访问：http://localhost:5000

## 项目结构

```
shortdrama/
├── config/          # 配置文件
├── modules/         # 核心功能模块
│   ├── audio/       # 音频生成
│   ├── character/   # 角色生成
│   ├── post/        # 发布管理
│   ├── scene/       # 场景生成
│   ├── script/      # 脚本生成
│   └── video/       # 视频生成
├── output/          # 输出文件
├── templates/       # HTML 模板
├── workflow/        # 工作流管理
├── app.py           # 主应用
├── interface_v2.html # 主界面
├── script.js        # 前端脚本
├── style.css        # 样式文件
└── requirements.txt # 依赖库
```

## 使用指南

### 对标分析
1. 选择平台和视频类型
2. 输入对标账号或选择热门博主
3. 点击「开始分析」查看结果

### 脚本创作
1. 填写短剧主题、类型、时长等信息
2. 选择艺术表现力选项
3. 点击「生成脚本」获取AI生成的脚本

### 拍摄管理
1. 选择脚本
2. 填写拍摄地点、日期等信息
3. 点击「生成拍摄计划」获取详细计划

### 剪辑制作
1. 导入素材
2. 选择脚本和剪辑风格
3. 点击「开始剪辑」自动生成视频

### 发布管理
1. 选择视频文件
2. 填写标题、描述和标签
3. 选择发布平台
4. 点击「发布视频」完成发布

## 配置说明

### 环境变量

在 `.env` 文件中配置以下环境变量：

- `OPENAI_API_KEY`：OpenAI API 密钥
- `ANTHROPIC_API_KEY`：Anthropic API 密钥
- `ELEVENLABS_API_KEY`：ElevenLabs API 密钥
- `DASHSCOPE_API_KEY`：阿里千问 API 密钥
- `SECRET_KEY`：Flask 应用密钥
- `DEBUG`：是否开启调试模式
- `HOST`：服务器主机
- `PORT`：服务器端口

## 开发指南

### 运行开发服务器

```bash
python app.py
```

### 代码风格

- 遵循 PEP 8 编码规范
- 使用有意义的变量和函数命名
- 添加适当的注释
- 保持代码简洁明了

### 测试

运行测试：

```bash
pytest
```

## 部署指南

### 生产环境部署

1. 安装依赖：`pip install -r requirements.txt`
2. 配置环境变量：在 `.env` 文件中设置生产环境配置
3. 启动应用：使用 Gunicorn 或其他 WSGI 服务器

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 许可证

MIT License
