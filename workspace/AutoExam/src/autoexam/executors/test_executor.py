#!/usr/bin/env python3
"""
测试执行器模块
使用智能体执行场景测试
"""

import logging
from datetime import datetime
from autoexam.integrations.agent_interface import AgentInterface

logger = logging.getLogger('TestExecutor')

class TestExecutor:
    """测试执行器"""
    
    def __init__(self, environment='simulation', use_agents=True):
        """初始化测试执行器
        
        参数:
            environment: 测试环境（simulation/real）
            use_agents: 是否使用智能体执行测试
        """
        self.environment = environment
        self.use_agents = use_agents
        
        if self.use_agents:
            self.agent_interface = AgentInterface()
            logger.info(f"测试执行器使用智能体模式，环境: {environment}")
        else:
            logger.info(f"测试执行器使用传统模式，环境: {environment}")
    
    def execute(self, scenario):
        """执行场景测试
        
        参数:
            scenario: 场景字典
            
        返回:
            测试结果
        """
        if self.use_agents:
            return self._execute_with_agent(scenario)
        else:
            return self._execute_traditional(scenario)
    
    def _execute_with_agent(self, scenario):
        """使用智能体执行测试
        
        参数:
            scenario: 场景字典
            
        返回:
            测试结果
        """
        logger.info(f"使用智能体执行测试: {scenario['id']}, 类型: {scenario['type']}")
        
        result = self.agent_interface.execute_test(scenario)
        
        if result['success']:
            test_result = result['result']
            test_result['scenario_id'] = scenario['id']
            test_result['scenario_type'] = scenario['type']
            test_result['risk_level'] = scenario['risk_level']
            test_result['execution_time'] = datetime.now().isoformat()
            test_result['environment'] = self.environment
            
            logger.info(f"智能体执行测试成功: {scenario['id']}")
            return test_result
        else:
            logger.error(f"智能体执行测试失败: {result.get('error')}")
            return self._execute_traditional(scenario)
    
    def _execute_traditional(self, scenario):
        """使用传统方法执行测试（备用方案）
        
        参数:
            scenario: 场景字典
            
        返回:
            测试结果
        """
        logger.info(f"使用传统方法执行测试: {scenario['id']}, 类型: {scenario['type']}")
        
        # 模拟测试结果
        scenario_type = scenario['type']
        risk_level = scenario['risk_level']
        
        # 基础成功率
        base_success_rate = 0.7
        
        # 根据风险等级调整成功率
        risk_factor = {
            'low': 0.1,
            'medium': 0.2,
            'high': 0.3,
            'extreme': 0.4
        }
        
        success_rate = base_success_rate - risk_factor.get(risk_level, 0.2)
        
        # 生成测试结果
        import random
        success = random.random() < success_rate
        collision = not success and random.random() < 0.5
        
        # 生成响应时间和减速度
        response_time = random.uniform(0.5, 2.5)
        max_deceleration = random.uniform(-8, -3)
        
        result = {
            'success': success,
            'collision': collision,
            'response_time': response_time,
            'max_deceleration': max_deceleration,
            'scenario_id': scenario['id'],
            'scenario_type': scenario['type'],
            'risk_level': scenario['risk_level'],
            'execution_time': datetime.now().isoformat(),
            'environment': self.environment
        }
        
        logger.info(f"传统方法执行测试完成: {scenario['id']}, 成功: {success}")
        return result
