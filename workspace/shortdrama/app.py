from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import sys
import logging
import traceback
from config.config import Config

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
from workflow.workflow import ShortDramaWorkflow
from modules.script.generator import ScriptGenerator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 初始化应用
app = Flask(__name__)

# 加载配置
config = Config()
app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
app.config['SECRET_KEY'] = config.SECRET_KEY

# 确保输出目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    """首页路由"""
    try:
        return render_template('interface_v2.html')
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        logger.error(traceback.format_exc())
        return render_template('error.html', error_message="服务器内部错误")

@app.route('/generate', methods=['POST'])
def generate():
    """生成短剧路由"""
    try:
        # 获取表单数据
        topic = request.form.get('topic')
        genre = request.form.get('genre')
        duration = request.form.get('duration')
        characters = request.form.get('characters', '').split(',')
        setting = request.form.get('setting')
        
        # 验证输入
        if not all([topic, genre, duration, characters, setting]):
            return render_template('error.html', error_message="请填写所有必填字段")
        
        # 去除空白字符
        characters = [char.strip() for char in characters if char.strip()]
        
        if not characters:
            return render_template('error.html', error_message="请至少填写一个角色")
        
        logger.info(f"开始生成短剧: 主题={topic}, 类型={genre}, 时长={duration}, 角色={characters}, 场景={setting}")
        
        # 运行工作流
        workflow = ShortDramaWorkflow()
        final_video_path = workflow.run_workflow(
            topic=topic,
            genre=genre,
            duration=duration,
            characters=characters,
            setting=setting
        )
        
        # 获取生成的文件信息
        script_path = os.path.join(app.config['UPLOAD_FOLDER'], 'scripts')
        character_path = os.path.join(app.config['UPLOAD_FOLDER'], 'characters')
        scene_path = os.path.join(app.config['UPLOAD_FOLDER'], 'scenes')
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], 'audio')
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], 'video')
        final_path = os.path.join(app.config['UPLOAD_FOLDER'], 'final')
        
        # 获取文件列表
        script_files = os.listdir(script_path) if os.path.exists(script_path) else []
        character_files = os.listdir(character_path) if os.path.exists(character_path) else []
        scene_files = os.listdir(scene_path) if os.path.exists(scene_path) else []
        audio_files = os.listdir(audio_path) if os.path.exists(audio_path) else []
        video_files = os.listdir(video_path) if os.path.exists(video_path) else []
        final_files = os.listdir(final_path) if os.path.exists(final_path) else []
        
        # 读取剧本内容
        script_content = None
        script_file_path = None
        if script_files:
            script_file_path = os.path.join(script_path, script_files[0])
            with open(script_file_path, 'r', encoding='utf-8') as f:
                script_content = json.load(f)
        
        logger.info(f"短剧生成完成: {final_video_path}")
        
        return render_template('result.html', 
                             topic=topic,
                             genre=genre,
                             duration=duration,
                             characters=characters,
                             setting=setting,
                             final_video_path=final_video_path,
                             script_files=script_files,
                             character_files=character_files,
                             scene_files=scene_files,
                             audio_files=audio_files,
                             video_files=video_files,
                             final_files=final_files,
                             script_content=script_content,
                             script_path=script_file_path)
    except Exception as e:
        logger.error(f"Error in generate route: {str(e)}")
        logger.error(traceback.format_exc())
        return render_template('error.html', error_message="生成过程中出错")

@app.route('/edit-script/<script_file>', methods=['GET'])
def edit_script(script_file):
    """编辑剧本路由"""
    try:
        # 构建剧本文件路径
        script_path = os.path.join(app.config['UPLOAD_FOLDER'], 'scripts', script_file)
        
        # 验证文件存在
        if not os.path.exists(script_path):
            return render_template('error.html', error_message="剧本文件不存在")
        
        # 读取剧本内容
        with open(script_path, 'r', encoding='utf-8') as f:
            script_content = json.load(f)
        
        return render_template('edit_script.html', 
                             script_content=script_content,
                             script_path=script_path)
    except Exception as e:
        logger.error(f"Error in edit_script route: {str(e)}")
        logger.error(traceback.format_exc())
        return render_template('error.html', error_message="编辑剧本时出错")

@app.route('/update-script', methods=['POST'])
def update_script():
    """更新剧本路由"""
    try:
        # 获取表单数据
        script_path = request.form.get('script_path')
        updated_content = request.form.get('script_content')
        
        # 验证输入
        if not script_path or not updated_content:
            return render_template('error.html', error_message="缺少必要参数")
        
        # 验证文件存在
        if not os.path.exists(script_path):
            return render_template('error.html', error_message="剧本文件不存在")
        
        # 解析更新后的内容
        try:
            updated_content = json.loads(updated_content)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {str(e)}")
            return render_template('error.html', error_message="剧本内容格式错误")
        
        # 更新剧本
        script_generator = ScriptGenerator()
        updated_script = script_generator.update_script(script_path, updated_content)
        
        logger.info(f"剧本更新完成: {script_path}")
        
        # 重定向到结果页面
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error in update_script route: {str(e)}")
        logger.error(traceback.format_exc())
        return render_template('error.html', error_message="更新剧本时出错")

# ==================== 拆片分析API ====================

# 全局分析器实例（延迟加载）
_breakdown_analyzer = None

def get_breakdown_analyzer():
    """获取拆片分析器实例（单例模式）"""
    global _breakdown_analyzer
    if _breakdown_analyzer is None:
        from modules.breakdown.analyzer import VideoBreakdownAnalyzer
        logger.info("初始化拆片分析器...")
        _breakdown_analyzer = VideoBreakdownAnalyzer(
            model_path="Qwen/Qwen2-VL-72B-Instruct",
            load_in_4bit=True
        )
    return _breakdown_analyzer

@app.route('/api/breakdown/analyze', methods=['POST'])
def breakdown_analyze():
    """
    视频拆片分析API
    
    请求参数:
    - video_url: 视频URL或本地路径
    - analysis_type: 分析类型 (structure/shot/audio/comprehensive)
    - include_audio: 是否包含音频分析
    
    返回:
    - JSON格式的分析报告
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求体不能为空"}), 400
        
        video_url = data.get('video_url')
        analysis_type = data.get('analysis_type', 'comprehensive')
        include_audio = data.get('include_audio', True)
        
        if not video_url:
            return jsonify({"error": "video_url不能为空"}), 400
        
        logger.info(f"开始拆片分析: {video_url}, 类型: {analysis_type}")
        
        # 获取分析器
        analyzer = get_breakdown_analyzer()
        
        # 根据分析类型执行不同分析
        if analysis_type == 'comprehensive':
            result = analyzer.comprehensive_analysis(
                video_url, 
                include_audio=include_audio
            )
        elif analysis_type == 'structure':
            result = analyzer.analyze_video_structure(video_url)
        elif analysis_type == 'shot':
            # 需要先进行结构分析获取片段
            structure = analyzer.analyze_video_structure(video_url)
            segments = structure.get('segments', [])
            from modules.video.preprocessor import VideoPreprocessor
            preprocessor = VideoPreprocessor()
            segment_files = preprocessor.create_video_segments(
                video_url,
                [(s['start'], s['end']) for s in segments],
                './output/segments'
            )
            result = analyzer.analyze_shot_language(segment_files, segments)
        else:
            return jsonify({"error": f"未知的分析类型: {analysis_type}"}), 400
        
        return jsonify({
            "success": True,
            "analysis_type": analysis_type,
            "result": result
        })
        
    except Exception as e:
        logger.error(f"拆片分析失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/api/breakdown/status', methods=['GET'])
def breakdown_status():
    """检查拆片分析服务状态"""
    global _breakdown_analyzer
    return jsonify({
        "status": "ready" if _breakdown_analyzer is not None else "not_loaded",
        "model": "Qwen2-VL-72B-Instruct",
        "gpu_available": torch.cuda.is_available(),
        "gpu_count": torch.cuda.device_count() if torch.cuda.is_available() else 0
    })

# 短剧制作API接口
@app.route('/api/shortdrama/script', methods=['POST'])
def generate_script():
    """生成剧本"""
    try:
        data = request.get_json()
        theme = data.get('theme', '')
        genre = data.get('genre', '')
        duration = data.get('duration', '2分钟')
        style = data.get('style', '现代都市')
        
        script_generator = ScriptGenerator()
        script = script_generator.generate(
            theme=theme,
            genre=genre,
            duration=duration,
            style=style
        )
        
        return jsonify({
            "success": True,
            "script": script
        })
    except Exception as e:
        logger.error(f"剧本生成失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/api/shortdrama/storyboard', methods=['POST'])
def generate_storyboard():
    """生成分镜"""
    try:
        data = request.get_json()
        script = data.get('script', '')
        style = data.get('style', '电影感')
        
        workflow = ShortDramaWorkflow()
        storyboard = workflow.generate_storyboard(
            script=script,
            style=style
        )
        
        return jsonify({
            "success": True,
            "storyboard": storyboard
        })
    except Exception as e:
        logger.error(f"分镜生成失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/api/shortdrama/characters', methods=['POST'])
def generate_characters():
    """生成角色"""
    try:
        data = request.get_json()
        script = data.get('script', '')
        model = data.get('model', 'doubao')
        style = data.get('style', 'realistic')
        views = data.get('views', ['front'])
        expressions = data.get('expressions', 'none')
        
        workflow = ShortDramaWorkflow()
        characters = workflow.generate_characters(
            script=script,
            model=model,
            style=style,
            views=views,
            expressions=expressions
        )
        
        return jsonify({
            "success": True,
            "characters": characters
        })
    except Exception as e:
        logger.error(f"角色生成失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/api/shortdrama/video', methods=['POST'])
def generate_video():
    """生成视频"""
    try:
        data = request.get_json()
        storyboard = data.get('storyboard', '')
        characters = data.get('characters', [])
        mode = data.get('mode', 'standard')
        resolution = data.get('resolution', '1080p')
        
        workflow = ShortDramaWorkflow()
        video = workflow.generate_video(
            storyboard=storyboard,
            characters=characters,
            mode=mode,
            resolution=resolution
        )
        
        return jsonify({
            "success": True,
            "video": video
        })
    except Exception as e:
        logger.error(f"视频生成失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/api/shortdrama/voice', methods=['POST'])
def generate_voice():
    """生成语音"""
    try:
        data = request.get_json()
        script = data.get('script', '')
        preset = data.get('preset', 'natural')
        language = data.get('language', 'zh')
        
        workflow = ShortDramaWorkflow()
        voice = workflow.generate_voice(
            script=script,
            preset=preset,
            language=language
        )
        
        return jsonify({
            "success": True,
            "voice": voice
        })
    except Exception as e:
        logger.error(f"语音生成失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/api/shortdrama/production', methods=['POST'])
def manage_production():
    """生产调度"""
    try:
        data = request.get_json()
        action = data.get('action', 'finalize')
        assets = data.get('assets', {})
        
        workflow = ShortDramaWorkflow()
        result = workflow.manage_production(
            action=action,
            assets=assets
        )
        
        return jsonify({
            "success": True,
            "result": result
        })
    except Exception as e:
        logger.error(f"生产调度失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/api/shortdrama/status', methods=['GET'])
def shortdrama_status():
    """检查短剧制作服务状态"""
    return jsonify({
        "status": "ready",
        "models": {
            "script": "Qwen-72B",
            "storyboard": "Qwen-VL-72B",
            "characters": ["豆包", "SkyReels-V3"],
            "video": "LTX-2",
            "voice": "Qwen3-TTS",
            "production": "Huobao Drama"
        },
        "gpu_available": torch.cuda.is_available(),
        "gpu_count": torch.cuda.device_count() if torch.cuda.is_available() else 0
    })

# 对标分析API
@app.route('/api/competitive/industry', methods=['GET'])
def get_industry_data():
    # 模拟行业数据
    data = {
        'trend': {
            'labels': ['1月', '2月', '3月', '4月', '5月', '6月'],
            'data': [12000, 19000, 15000, 25000, 22000, 30000]
        },
        'topics': {
            'labels': ['爱情', '喜剧', '悬疑', '科幻', '职场', '校园'],
            'data': [90, 85, 75, 65, 60, 55]
        },
        'platforms': {
            'labels': ['抖音', '快手', 'B站', '视频号'],
            'data': [45, 25, 20, 10]
        },
        'audience': {
            'labels': ['18-24岁', '25-34岁', '35-44岁', '45岁以上', '男性', '女性'],
            'data': [30, 40, 20, 10, 45, 55]
        }
    }
    return jsonify(data)

@app.route('/api/competitive/platform', methods=['GET'])
def get_platform_data():
    platform = request.args.get('platform', 'all')
    # 模拟平台数据
    data = {
        'features': {
            'all': {
                'name': '全部平台',
                'users': '5亿+',
                'content': '短视频、短剧、直播',
                'algorithm': '基于用户兴趣推荐',
                'advantages': '覆盖面广，用户基数大',
                'disadvantages': '竞争激烈，内容同质化'
            },
            'douyin': {
                'name': '抖音',
                'users': '3亿+',
                'content': '15-60秒短视频，短剧',
                'algorithm': '强个性化推荐，注重完播率',
                'advantages': '流量大，算法成熟',
                'disadvantages': '内容更新快，留存难度大'
            },
            'kuaishou': {
                'name': '快手',
                'users': '2亿+',
                'content': '生活分享，短剧',
                'algorithm': '社区氛围，关注推荐',
                'advantages': '用户粘性高，互动性强',
                'disadvantages': '内容质量参差不齐'
            },
            'bilibili': {
                'name': 'B站',
                'users': '1.5亿+',
                'content': '中长视频，番剧，短剧',
                'algorithm': '兴趣圈层，弹幕文化',
                'advantages': '用户质量高，内容深度',
                'disadvantages': '用户群体相对小众'
            },
            'wechat': {
                'name': '视频号',
                'users': '2.5亿+',
                'content': '社交分享，短剧',
                'algorithm': '社交关系链，朋友推荐',
                'advantages': '社交属性强，转化率高',
                'disadvantages': '内容分发依赖社交关系'
            }
        },
        'content': {
            'all': {
                'labels': ['爱情', '喜剧', '悬疑', '科幻', '职场', '校园'],
                'data': [90, 85, 75, 65, 60, 55]
            },
            'douyin': {
                'labels': ['爱情', '喜剧', '悬疑', '科幻', '职场', '校园'],
                'data': [95, 90, 80, 60, 55, 50]
            },
            'kuaishou': {
                'labels': ['爱情', '喜剧', '悬疑', '科幻', '职场', '校园'],
                'data': [85, 90, 70, 55, 60, 65]
            },
            'bilibili': {
                'labels': ['爱情', '喜剧', '悬疑', '科幻', '职场', '校园'],
                'data': [75, 80, 85, 90, 70, 75]
            },
            'wechat': {
                'labels': ['爱情', '喜剧', '悬疑', '科幻', '职场', '校园'],
                'data': [85, 75, 70, 60, 80, 65]
            }
        }
    }
    return jsonify(data)

@app.route('/api/competitive/domain', methods=['GET'])
def get_domain_data():
    domain = request.args.get('domain', 'all')
    # 模拟领域数据
    data = {
        'trends': {
            'all': {
                'name': '全部领域',
                'trend': '持续增长',
                'growth': '15%/月',
                'hotTopics': '都市情感、职场奋斗、悬疑推理',
                'opportunities': '垂直领域深耕，内容专业化',
                'challenges': '内容同质化，竞争激烈'
            },
            'love': {
                'name': '爱情',
                'trend': '稳定增长',
                'growth': '12%/月',
                'hotTopics': '都市爱情、校园初恋、异地恋',
                'opportunities': '情感共鸣，高互动性',
                'challenges': '题材同质化，创新难度大'
            },
            'comedy': {
                'name': '喜剧',
                'trend': '快速增长',
                'growth': '20%/月',
                'hotTopics': '家庭幽默、职场趣事、社会热点',
                'opportunities': '解压需求大，传播性强',
                'challenges': '笑点创新，持续输出难度'
            },
            'sci-fi': {
                'name': '科幻',
                'trend': '新兴增长',
                'growth': '25%/月',
                'hotTopics': '未来科技、时空穿越、外星文明',
                'opportunities': '视觉效果吸引，粉丝粘性高',
                'challenges': '制作成本高，创意要求高'
            },
            'suspense': {
                'name': '悬疑',
                'trend': '爆发增长',
                'growth': '30%/月',
                'hotTopics': '犯罪推理、密室逃脱、心理悬疑',
                'opportunities': '情节紧凑，观众粘性强',
                'challenges': '剧情逻辑要求高，制作复杂'
            },
            'workplace': {
                'name': '职场',
                'trend': '稳定增长',
                'growth': '10%/月',
                'hotTopics': '职场奋斗、办公室文化、职业发展',
                'opportunities': '贴近现实，共鸣感强',
                'challenges': '题材局限，创新难度'
            },
            'campus': {
                'name': '校园',
                'trend': '稳步增长',
                'growth': '8%/月',
                'hotTopics': '校园生活、青春爱情、友情故事',
                'opportunities': '年轻受众多，市场潜力大',
                'challenges': '题材重复，差异化难'
            }
        },
        'audience': {
            'all': {
                'labels': ['18-24岁', '25-34岁', '35-44岁', '45岁以上', '男性', '女性'],
                'data': [30, 40, 20, 10, 45, 55]
            },
            'love': {
                'labels': ['18-24岁', '25-34岁', '35-44岁', '45岁以上', '男性', '女性'],
                'data': [35, 45, 15, 5, 35, 65]
            },
            'comedy': {
                'labels': ['18-24岁', '25-34岁', '35-44岁', '45岁以上', '男性', '女性'],
                'data': [40, 35, 15, 10, 50, 50]
            },
            'sci-fi': {
                'labels': ['18-24岁', '25-34岁', '35-44岁', '45岁以上', '男性', '女性'],
                'data': [45, 40, 10, 5, 65, 35]
            },
            'suspense': {
                'labels': ['18-24岁', '25-34岁', '35-44岁', '45岁以上', '男性', '女性'],
                'data': [30, 40, 25, 5, 55, 45]
            },
            'workplace': {
                'labels': ['18-24岁', '25-34岁', '35-44岁', '45岁以上', '男性', '女性'],
                'data': [20, 45, 25, 10, 48, 52]
            },
            'campus': {
                'labels': ['18-24岁', '25-34岁', '35-44岁', '45岁以上', '男性', '女性'],
                'data': [50, 30, 15, 5, 45, 55]
            }
        }
    }
    return jsonify(data)

@app.route('/api/competitive/bloggers', methods=['GET'])
def get_bloggers():
    search = request.args.get('search', '')
    # 模拟博主数据
    bloggers = [
        { 'name': '藏经人', 'platform': '抖音', 'followers': '1000万+', 'category': '悬疑', 'style': '烧脑推理', 'representative': '《致命ID》系列' },
        { 'name': '毒舌电影', 'platform': 'B站', 'followers': '800万+', 'category': '影评', 'style': '犀利点评', 'representative': '《毒舌影评》系列' },
        { 'name': 'papi酱', 'platform': '抖音', 'followers': '3000万+', 'category': '喜剧', 'style': '幽默搞笑', 'representative': '《papi酱的周一放送》' },
        { 'name': '罗翔说刑法', 'platform': 'B站', 'followers': '2000万+', 'category': '知识', 'style': '法律科普', 'representative': '《罗翔说刑法》系列' },
        { 'name': '李子柒', 'platform': '视频号', 'followers': '2500万+', 'category': '生活', 'style': '田园生活', 'representative': '《李子柒的生活》系列' },
        { 'name': '李佳琦', 'platform': '抖音', 'followers': '4000万+', 'category': '美妆', 'style': '直播带货', 'representative': '《李佳琦直播》' },
        { 'name': '冯提莫', 'platform': 'B站', 'followers': '1500万+', 'category': '音乐', 'style': '甜美歌声', 'representative': '《佛系少女》' },
        { 'name': '张大仙', 'platform': 'B站', 'followers': '2000万+', 'category': '游戏', 'style': '游戏解说', 'representative': '《张大仙王者荣耀》系列' }
    ]
    
    if search:
        bloggers = [b for b in bloggers if search.lower() in b['name'].lower() or search.lower() in b['platform'].lower() or search.lower() in b['category'].lower()]
    
    return jsonify(bloggers)

@app.route('/api/competitive/blogger/<name>', methods=['GET'])
def get_blogger_analysis(name):
    # 模拟博主分析数据
    bloggers = {
        '藏经人': {
            'name': '藏经人',
            'platform': '抖音',
            'followers': '1000万+',
            'category': '悬疑',
            'style': '烧脑推理',
            'representative': '《致命ID》系列',
            'contentFeatures': '高质量原创内容，粉丝互动性强',
            'successFactors': '独特的个人风格，持续的内容输出',
            'suggestions': '学习其内容创作方法和粉丝运营策略'
        },
        '毒舌电影': {
            'name': '毒舌电影',
            'platform': 'B站',
            'followers': '800万+',
            'category': '影评',
            'style': '犀利点评',
            'representative': '《毒舌影评》系列',
            'contentFeatures': '专业的电影分析，独特的观点',
            'successFactors': '深入浅出的讲解，幽默的语言风格',
            'suggestions': '学习其内容深度和表达技巧'
        },
        'papi酱': {
            'name': 'papi酱',
            'platform': '抖音',
            'followers': '3000万+',
            'category': '喜剧',
            'style': '幽默搞笑',
            'representative': '《papi酱的周一放送》',
            'contentFeatures': '贴近生活的内容，真实的表达',
            'successFactors': '独特的个人魅力，持续的创意输出',
            'suggestions': '学习其内容创意和表达风格'
        },
        '罗翔说刑法': {
            'name': '罗翔说刑法',
            'platform': 'B站',
            'followers': '2000万+',
            'category': '知识',
            'style': '法律科普',
            'representative': '《罗翔说刑法》系列',
            'contentFeatures': '专业的法律知识，生动的案例分析',
            'successFactors': '深入浅出的讲解，人格魅力',
            'suggestions': '学习其知识传播方式和个人品牌建设'
        },
        '李子柒': {
            'name': '李子柒',
            'platform': '视频号',
            'followers': '2500万+',
            'category': '生活',
            'style': '田园生活',
            'representative': '《李子柒的生活》系列',
            'contentFeatures': '精美的画面，传统的生活方式',
            'successFactors': '独特的内容定位，高质量的制作',
            'suggestions': '学习其内容美学和品牌定位'
        },
        '李佳琦': {
            'name': '李佳琦',
            'platform': '抖音',
            'followers': '4000万+',
            'category': '美妆',
            'style': '直播带货',
            'representative': '《李佳琦直播》',
            'contentFeatures': '专业的产品知识，热情的直播风格',
            'successFactors': '勤奋的工作态度，强大的销售能力',
            'suggestions': '学习其直播技巧和粉丝运营'
        },
        '冯提莫': {
            'name': '冯提莫',
            'platform': 'B站',
            'followers': '1500万+',
            'category': '音乐',
            'style': '甜美歌声',
            'representative': '《佛系少女》',
            'contentFeatures': '优美的歌声，可爱的形象',
            'successFactors': '持续的音乐输出，粉丝互动',
            'suggestions': '学习其音乐内容创作和粉丝互动'
        },
        '张大仙': {
            'name': '张大仙',
            'platform': 'B站',
            'followers': '2000万+',
            'category': '游戏',
            'style': '游戏解说',
            'representative': '《张大仙王者荣耀》系列',
            'contentFeatures': '专业的游戏技巧，幽默的解说',
            'successFactors': '独特的解说风格，持续的内容输出',
            'suggestions': '学习其游戏内容创作和解说技巧'
        }
    }
    
    blogger = bloggers.get(name, None)
    if not blogger:
        return jsonify({'error': 'Blogger not found'}), 404
    
    return jsonify(blogger)

# 错误处理
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_message="页面不存在"), 404

@app.errorhandler(500)
def internal_server_error(e):
    logger.error(f"500 Error: {str(e)}")
    logger.error(traceback.format_exc())
    return render_template('error.html', error_message="服务器内部错误"), 500

if __name__ == '__main__':
    logger.info("Starting Short Drama Generator Application")
    app.run(debug=config.DEBUG, host=config.HOST, port=config.PORT)