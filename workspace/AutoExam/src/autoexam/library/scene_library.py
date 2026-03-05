#!/usr/bin/env python3
"""
场景库管理模块
负责场景的存储、加载和管理
"""

import os
import json
import logging
from datetime import datetime

logger = logging.getLogger('SceneLibrary')

class SceneLibrary:
    """场景库"""
    
    def __init__(self, base_dir):
        """初始化场景库
        
        参数:
            base_dir: 场景存储目录
        """
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)
        
        # 创建场景类型子目录
        self.scenario_types = [
            'cut-in', 'emergency-brake', 'occlusion', 
            'pedestrian-crossing', 'multi-vehicle', 'adverse-weather'
        ]
        
        for scenario_type in self.scenario_types:
            scenario_dir = os.path.join(self.base_dir, scenario_type)
            os.makedirs(scenario_dir, exist_ok=True)
        
        logger.info(f"初始化场景库，存储目录: {self.base_dir}")
    
    def save_scenario(self, scenario):
        """保存场景
        
        参数:
            scenario: 场景字典
        """
        scenario_id = scenario.get('id')
        scenario_type = scenario.get('type', 'default')
        
        if not scenario_id:
            logger.error("场景ID不能为空")
            return False
        
        # 确保场景类型目录存在
        scenario_dir = os.path.join(self.base_dir, scenario_type)
        os.makedirs(scenario_dir, exist_ok=True)
        
        # 保存场景文件
        scenario_path = os.path.join(scenario_dir, f"{scenario_id}.json")
        
        try:
            with open(scenario_path, 'w', encoding='utf-8') as f:
                json.dump(scenario, f, indent=2, ensure_ascii=False)
            logger.info(f"场景保存成功: {scenario_id}")
            return True
        except Exception as e:
            logger.error(f"保存场景失败: {e}")
            return False
    
    def load_scenario(self, scenario_id):
        """加载场景
        
        参数:
            scenario_id: 场景ID
            
        返回:
            场景字典，如果不存在返回None
        """
        # 搜索所有场景类型目录
        for scenario_type in self.scenario_types + ['default']:
            scenario_path = os.path.join(self.base_dir, scenario_type, f"{scenario_id}.json")
            if os.path.exists(scenario_path):
                try:
                    with open(scenario_path, 'r', encoding='utf-8') as f:
                        scenario = json.load(f)
                    logger.info(f"场景加载成功: {scenario_id}")
                    return scenario
                except Exception as e:
                    logger.error(f"加载场景失败: {e}")
                    return None
        
        logger.warning(f"场景不存在: {scenario_id}")
        return None
    
    def list_scenarios(self, scenario_type=None, risk_level=None):
        """列出场景
        
        参数:
            scenario_type: 场景类型，None表示所有类型
            risk_level: 风险等级，None表示所有等级
            
        返回:
            场景ID列表
        """
        scenarios = []
        
        # 确定要搜索的目录
        if scenario_type:
            search_dirs = [os.path.join(self.base_dir, scenario_type)]
        else:
            search_dirs = [os.path.join(self.base_dir, st) for st in self.scenario_types + ['default']]
        
        # 搜索场景文件
        for search_dir in search_dirs:
            if not os.path.exists(search_dir):
                continue
            
            for filename in os.listdir(search_dir):
                if filename.endswith('.json'):
                    scenario_id = filename[:-5]  # 去掉.json后缀
                    scenario = self.load_scenario(scenario_id)
                    if scenario:
                        # 过滤风险等级
                        if risk_level and scenario.get('risk_level') != risk_level:
                            continue
                        scenarios.append(scenario_id)
        
        return scenarios
    
    def get_scenario_metadata(self, scenario_id):
        """获取场景元数据
        
        参数:
            scenario_id: 场景ID
            
        返回:
            元数据字典
        """
        scenario = self.load_scenario(scenario_id)
        if not scenario:
            return None
        
        metadata = {
            'id': scenario.get('id'),
            'type': scenario.get('type'),
            'risk_level': scenario.get('risk_level'),
            'created_at': scenario.get('created_at'),
            'parameters': scenario.get('parameters', {}),
            'environment': scenario.get('environment', {})
        }
        
        return metadata
    
    def update_scenario(self, scenario_id, updates):
        """更新场景
        
        参数:
            scenario_id: 场景ID
            updates: 更新的字段字典
            
        返回:
            是否更新成功
        """
        scenario = self.load_scenario(scenario_id)
        if not scenario:
            return False
        
        # 更新字段
        scenario.update(updates)
        scenario['updated_at'] = datetime.now().isoformat()
        
        # 保存更新后的场景
        return self.save_scenario(scenario)
    
    def delete_scenario(self, scenario_id):
        """删除场景
        
        参数:
            scenario_id: 场景ID
            
        返回:
            是否删除成功
        """
        # 搜索场景文件
        for scenario_type in self.scenario_types + ['default']:
            scenario_path = os.path.join(self.base_dir, scenario_type, f"{scenario_id}.json")
            if os.path.exists(scenario_path):
                try:
                    os.remove(scenario_path)
                    logger.info(f"场景删除成功: {scenario_id}")
                    return True
                except Exception as e:
                    logger.error(f"删除场景失败: {e}")
                    return False
        
        logger.warning(f"场景不存在: {scenario_id}")
        return False
    
    def export_scenarios(self, output_file, scenario_ids=None):
        """导出场景
        
        参数:
            output_file: 输出文件路径
            scenario_ids: 场景ID列表，None表示导出所有场景
            
        返回:
            是否导出成功
        """
        try:
            if scenario_ids:
                # 导出指定场景
                scenarios = []
                for scenario_id in scenario_ids:
                    scenario = self.load_scenario(scenario_id)
                    if scenario:
                        scenarios.append(scenario)
            else:
                # 导出所有场景
                scenarios = []
                for scenario_type in self.scenario_types + ['default']:
                    scenario_dir = os.path.join(self.base_dir, scenario_type)
                    if not os.path.exists(scenario_dir):
                        continue
                    
                    for filename in os.listdir(scenario_dir):
                        if filename.endswith('.json'):
                            scenario_id = filename[:-5]
                            scenario = self.load_scenario(scenario_id)
                            if scenario:
                                scenarios.append(scenario)
            
            # 保存到文件
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(scenarios, f, indent=2, ensure_ascii=False)
            
            logger.info(f"成功导出 {len(scenarios)} 个场景到 {output_file}")
            return True
        except Exception as e:
            logger.error(f"导出场景失败: {e}")
            return False
    
    def import_scenarios(self, input_file):
        """导入场景
        
        参数:
            input_file: 输入文件路径
            
        返回:
            导入的场景数量
        """
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                scenarios = json.load(f)
            
            if not isinstance(scenarios, list):
                scenarios = [scenarios]
            
            imported_count = 0
            for scenario in scenarios:
                if self.save_scenario(scenario):
                    imported_count += 1
            
            logger.info(f"成功导入 {imported_count} 个场景")
            return imported_count
        except Exception as e:
            logger.error(f"导入场景失败: {e}")
            return 0
    
    def get_statistics(self):
        """获取场景库统计信息
        
        返回:
            统计信息字典
        """
        stats = {
            'total_scenarios': 0,
            'scenarios_by_type': {},
            'scenarios_by_risk': {},
            'last_updated': datetime.now().isoformat()
        }
        
        # 统计场景
        for scenario_type in self.scenario_types + ['default']:
            scenario_dir = os.path.join(self.base_dir, scenario_type)
            if not os.path.exists(scenario_dir):
                continue
            
            type_count = 0
            for filename in os.listdir(scenario_dir):
                if filename.endswith('.json'):
                    type_count += 1
                    scenario_id = filename[:-5]
                    scenario = self.load_scenario(scenario_id)
                    if scenario:
                        risk_level = scenario.get('risk_level', 'unknown')
                        stats['scenarios_by_risk'][risk_level] = stats['scenarios_by_risk'].get(risk_level, 0) + 1
            
            if type_count > 0:
                stats['scenarios_by_type'][scenario_type] = type_count
                stats['total_scenarios'] += type_count
        
        return stats
