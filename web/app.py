#!/usr/bin/env python3
"""
Openclaw Web Interface
简单的Openclaw网页界面，提供智能体聊天功能
"""

from flask import Flask, render_template, request, jsonify, Response
import requests
import json
import os

app = Flask(__name__)

OLLAMA_BASE_URL = "http://127.0.0.1:11434"
OPENCLAW_DIR = "/home/xcc/.openclaw"

def load_agents():
    """加载所有智能体配置"""
    agents = []
    agents_dir = os.path.join(OPENCLAW_DIR, "agents")
    
    if os.path.exists(agents_dir):
        for agent_id in os.listdir(agents_dir):
            agent_json_path = os.path.join(agents_dir, agent_id, "agent.json")
            if os.path.exists(agent_json_path):
                try:
                    with open(agent_json_path, 'r', encoding='utf-8') as f:
                        agent_config = json.load(f)
                        agents.append({
                            'id': agent_id,
                            'name': agent_config.get('name', agent_id),
                            'description': agent_config.get('description', ''),
                            'model': agent_config.get('model', {}).get('primary', 'ollama/qwen:72b'),
                            'skills': agent_config.get('skills', [])
                        })
                except Exception as e:
                    print(f"加载智能体 {agent_id} 失败: {e}")
    
    return agents

def load_models():
    """加载可用模型"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = [model['name'] for model in data.get('models', [])]
            return models
    except Exception as e:
        print(f"加载模型失败: {e}")
    
    return ['qwen:72b', 'qwen:7b']

@app.route('/')
def index():
    """主页"""
    agents = load_agents()
    models = load_models()
    return render_template('index.html', agents=agents, models=models)

@app.route('/api/chat', methods=['POST'])
def chat():
    """聊天接口"""
    data = request.json
    message = data.get('message', '')
    agent_id = data.get('agent', '')
    model = data.get('model', 'qwen:72b')
    
    if not message:
        return jsonify({'error': '消息不能为空'}), 400
    
    # 加载智能体系统提示
    system_prompt = "你是一个AI助手，帮助用户解决问题。"
    if agent_id:
        agent_json_path = os.path.join(OPENCLAW_DIR, "agents", agent_id, "agent.json")
        if os.path.exists(agent_json_path):
            try:
                with open(agent_json_path, 'r', encoding='utf-8') as f:
                    agent_config = json.load(f)
                    system_prompt = agent_config.get('systemPrompt', system_prompt)
            except Exception as e:
                print(f"加载智能体提示失败: {e}")
    
    # 调用Ollama API
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                'model': model,
                'prompt': message,
                'system': system_prompt,
                'stream': True,
                'options': {
                    'num_ctx': 4096,
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'num_predict': 1024
                }
            },
            stream=True,
            timeout=600
        )
        
        def generate():
            try:
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if 'response' in data:
                                yield data['response']
                        except:
                            pass
            except GeneratorExit:
                print("客户端断开连接")
            except Exception as e:
                print(f"生成错误: {e}")
        
        return Response(generate(), mimetype='text/plain')
    
    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}")
        return jsonify({'error': '请求被中断'}), 200
    except Exception as e:
        print(f"服务器错误: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/agents')
def get_agents():
    """获取智能体列表"""
    agents = load_agents()
    return jsonify(agents)

@app.route('/api/models')
def get_models():
    """获取模型列表"""
    models = load_models()
    return jsonify(models)

@app.route('/api/agent/<agent_id>')
def get_agent(agent_id):
    """获取智能体详情"""
    agent_json_path = os.path.join(OPENCLAW_DIR, "agents", agent_id, "agent.json")
    if os.path.exists(agent_json_path):
        try:
            with open(agent_json_path, 'r', encoding='utf-8') as f:
                agent_config = json.load(f)
                return jsonify(agent_config)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': '智能体不存在'}), 404

if __name__ == '__main__':
    print("启动Openclaw Web界面...")
    print("访问地址: http://127.0.0.1:5000")
    print("按 Ctrl+C 停止服务")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)