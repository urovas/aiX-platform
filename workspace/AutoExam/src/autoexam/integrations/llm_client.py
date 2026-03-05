#!/usr/bin/env python3
"""
LLM客户端模块
用于调用Qwen-72B等大模型生成场景控制脚本
"""

import json
import logging
import requests
from typing import Dict, Optional

logger = logging.getLogger('LLMClient')


class LLMClient:
    """LLM客户端"""
    
    def __init__(self, config: Optional[Dict] = None):
        """初始化LLM客户端
        
        参数:
            config: 配置字典，包含模型API信息
        """
        self.config = config or {
            'provider': 'ollama',
            'model': 'qwen:72b',
            'base_url': 'http://localhost:11434',
            'timeout': 600
        }
        
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict:
        """生成文本
        
        参数:
            prompt: 用户提示词
            system_prompt: 系统提示词
            
        返回:
            生成结果
        """
        try:
            if self.config['provider'] == 'ollama':
                return self._call_ollama(prompt, system_prompt)
            else:
                logger.error(f"不支持的提供商: {self.config['provider']}")
                return {'success': False, 'error': f"不支持的提供商: {self.config['provider']}"}
                
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def _call_ollama(self, prompt: str, system_prompt: Optional[str] = None) -> Dict:
        """调用Ollama API
        
        参数:
            prompt: 用户提示词
            system_prompt: 系统提示词
            
        返回:
            生成结果
        """
        try:
            url = f"{self.config['base_url']}/api/generate"
            
            payload = {
                'model': self.config['model'],
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'num_predict': 4096
                }
            }
            
            if system_prompt:
                payload['system'] = system_prompt
            
            response = requests.post(
                url,
                json=payload,
                timeout=self.config.get('timeout', 120)
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'text': result.get('response', ''),
                    'model': self.config['model']
                }
            else:
                logger.error(f"Ollama API错误: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f"API错误: {response.status_code}"
                }
                
        except requests.exceptions.Timeout:
            logger.error("Ollama API超时")
            return {'success': False, 'error': 'API超时'}
        except Exception as e:
            logger.error(f"调用Ollama失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_scenario_control_script(self, scenario_params: Dict) -> Dict:
        """生成场景控制脚本
        
        参数:
            scenario_params: 场景参数
            
        返回:
            控制脚本
        """
        system_prompt = """你是一个自动驾驶场景控制脚本生成专家。你需要根据场景参数生成Python控制脚本，用于CARLA仿真环境。

生成的脚本必须：
1. 使用carla Python API
2. 包含完整的车辆控制逻辑（加速、减速、转向）
3. 实现无保护左转场景：
   - 主车接近路口
   - 观察对向来车
   - 选择合适时机左转
   - 避免碰撞
4. 输出格式为JSON，包含：
   - "script": 完整的Python代码字符串
   - "description": 脚本功能描述
   - "key_functions": 关键函数列表"""

        prompt = f"""请生成一个无保护左转场景的CARLA控制脚本。

场景参数：
- 主车速度: {scenario_params.get('ego_speed', 15)} km/h
- 对向车速: {scenario_params.get('oncoming_speed', 50)} km/h  
- 时间间隙: {scenario_params.get('time_gap', 4)} 秒
- 对向车型: {scenario_params.get('oncoming_vehicle_type', 'sedan')}
- 天气: {scenario_params.get('weather', 'clear')}
- 视野遮挡: {scenario_params.get('occlusion', False)}
- 交通流量: {scenario_params.get('traffic_flow', 'low')}
- 有行人: {scenario_params.get('has_pedestrian', False)}

要求：
1. 主车从路口前方50米处开始，以给定速度接近路口
2. 到达路口时，检测对向来车距离和速度
3. 计算安全左转时机（基于时间间隙）
4. 执行左转：先减速、观察、然后加速左转
5. 如果对向来车太近，应该停车等待
6. 左转完成后继续行驶

请输出JSON格式的控制脚本。"""

        result = self.generate(prompt, system_prompt)
        
        if result['success']:
            try:
                text = result['text']
                if '```json' in text:
                    json_str = text.split('```json')[1].split('```')[0].strip()
                elif '```' in text:
                    json_str = text.split('```')[1].split('```')[0].strip()
                else:
                    json_str = text.strip()
                
                script_data = json.loads(json_str)
                return {
                    'success': True,
                    'script': script_data.get('script', ''),
                    'description': script_data.get('description', ''),
                    'key_functions': script_data.get('key_functions', [])
                }
            except json.JSONDecodeError as e:
                logger.error(f"解析脚本JSON失败: {e}")
                return {
                    'success': False,
                    'error': f"JSON解析失败: {e}",
                    'raw_text': result['text']
                }
        else:
            return result
    
    def generate_vehicle_control_logic(self, scenario_params: Dict) -> Dict:
        """生成车辆控制逻辑
        
        参数:
            scenario_params: 场景参数
            
        返回:
            控制逻辑
        """
        system_prompt = """你是自动驾驶决策专家。根据场景参数生成车辆控制决策逻辑。

输出JSON格式：
{
  "phases": [
    {
      "name": "阶段名称",
      "trigger": "触发条件",
      "actions": ["动作列表"],
      "duration": 持续时间秒
    }
  ],
  "decision_points": [
    {
      "location": "决策位置描述",
      "condition": "判断条件",
      "if_true": "条件成立时的动作",
      "if_false": "条件不成立时的动作"
    }
  ],
  "safety_rules": ["安全规则列表"]
}"""

        prompt = f"""为无保护左转场景生成车辆控制决策逻辑。

场景参数：
{json.dumps(scenario_params, indent=2, ensure_ascii=False)}

决策要点：
1. 何时开始减速接近路口？
2. 如何判断对向来车的距离和到达时间？
3. 何时可以安全左转？
4. 何时应该停车等待？
5. 左转过程中如何监控安全？

请输出JSON格式的决策逻辑。"""

        result = self.generate(prompt, system_prompt)
        
        if result['success']:
            try:
                text = result['text']
                if '```json' in text:
                    json_str = text.split('```json')[1].split('```')[0].strip()
                elif '```' in text:
                    json_str = text.split('```')[1].split('```')[0].strip()
                else:
                    json_str = text.strip()
                
                logic = json.loads(json_str)
                return {
                    'success': True,
                    'logic': logic
                }
            except json.JSONDecodeError as e:
                logger.error(f"解析决策逻辑JSON失败: {e}")
                return {
                    'success': False,
                    'error': f"JSON解析失败: {e}",
                    'raw_text': result['text']
                }
        else:
            return result
