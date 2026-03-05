#!/usr/bin/env python3
"""
OpenSCENARIO格式导出器
将场景导出为OpenSCENARIO标准格式
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List

logger = logging.getLogger('OpenScenarioExporter')

class OpenScenarioExporter:
    """OpenSCENARIO导出器"""
    
    def __init__(self):
        """初始化导出器"""
        logger.info("OpenSCENARIO导出器初始化完成")
    
    def export(self, scenario: Dict, output_path: str = None) -> str:
        """导出场景为OpenSCENARIO格式
        
        参数:
            scenario: 场景字典
            output_path: 输出文件路径
            
        返回:
            OpenSCENARIO XML字符串
        """
        # 生成XML字符串
        xml_str = self._generate_xml(scenario)
        
        # 保存到文件
        if output_path:
            self._save_to_file(xml_str, output_path)
            logger.info(f"场景已导出到: {output_path}")
        
        return xml_str
    
    def _generate_xml(self, scenario: Dict) -> str:
        """生成XML字符串"""
        lines = []
        
        # XML声明
        lines.append('<?xml version="1.0" encoding="UTF-8"?>')
        lines.append('<OpenSCENARIO xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.w3.org/2001/XMLSchema OpenSCENARIO.xsd">')
        
        # 文件头
        lines.append(self._generate_file_header(scenario))
        
        # 参数声明
        lines.append(self._generate_parameter_declarations(scenario))
        
        # 实体
        lines.append(self._generate_entities(scenario))
        
        # 初始化
        lines.append(self._generate_init(scenario))
        
        # 故事
        lines.append(self._generate_story(scenario))
        
        # 结束标签
        lines.append('</OpenSCENARIO>')
        
        return '\n'.join(lines)
    
    def _generate_file_header(self, scenario: Dict) -> str:
        """生成文件头"""
        return f"""  <FileHeader author="AutoExam" date="{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}" description="{scenario.get('description', '')}" revMajor="1" revMinor="0" />"""
    
    def _generate_parameter_declarations(self, scenario: Dict) -> str:
        """生成参数声明"""
        lines = ['  <ParameterDeclarations>']
        
        params = scenario.get('parameters', {})
        for key, value in params.items():
            param_type = 'double' if isinstance(value, (int, float)) else 'string'
            lines.append(f'    <ParameterDeclaration name="{key}" parameterType="{param_type}" value="{value}" />')
        
        lines.append('  </ParameterDeclarations>')
        return '\n'.join(lines)
    
    def _generate_entities(self, scenario: Dict) -> str:
        """生成实体"""
        lines = ['  <Entities>']
        
        # 主车
        ego_vehicle = scenario.get('ego_vehicle', {})
        lines.append(self._generate_entity(ego_vehicle, 'ego_vehicle'))
        
        # 对向来车
        for vehicle in scenario.get('oncoming_vehicles', []):
            lines.append(self._generate_entity(vehicle, vehicle['id']))
        
        # 横向交通
        for vehicle in scenario.get('cross_traffic', []):
            lines.append(self._generate_entity(vehicle, vehicle['id']))
        
        # 行人
        for pedestrian in scenario.get('pedestrians', []):
            lines.append(self._generate_entity(pedestrian, pedestrian['id']))
        
        lines.append('  </Entities>')
        return '\n'.join(lines)
    
    def _generate_entity(self, entity: Dict, entity_id: str) -> str:
        """生成单个实体"""
        return f"""    <Entity name="{entity_id}">
      <Object>
        <CatalogReference entryName="{entity.get('model', 'vehicle.tesla.model3')}" />
      </Object>
      <Role>{entity.get('role', 'obstacle')}</Role>
    </Entity>"""
    
    def _generate_init(self, scenario: Dict) -> str:
        """生成初始化"""
        environment = scenario.get('environment', {})
        
        return f"""  <Init>
    <Actions>
      <GlobalAction name="Environment">
        <Environment>
          <Weather cloudState="free" precipitationType="{self._get_precipitation_type(scenario)}" precipitationIntensity="0.5" sunIntensity="0.5" sunAzimuth="0" sunElevation="45" />
          <RoadCondition frictionScale="1.0" />
          <TimeOfDay animation="false" dateTime="{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}" />
        </Environment>
      </GlobalAction>
      <PrivateAction entityRef="ego_vehicle">
        <TeleportAction>
          <Position>
            <WorldPosition x="{scenario.get('ego_vehicle', {}).get('position', {}).get('x', -50)}" y="{scenario.get('ego_vehicle', {}).get('position', {}).get('y', 0)}" z="0.5" />
          </Position>
        </TeleportAction>
      </PrivateAction>
    </Actions>
  </Init>"""
    
    def _generate_story(self, scenario: Dict) -> str:
        """生成故事"""
        return """  <Storyboard>
    <Init>
      <Actions>
        <GlobalAction name="InitAction">
          <EnvironmentAction />
        </GlobalAction>
      </Actions>
    </Init>
    <Story name="UnprotectedLeftTurnStory">
      <Act name="LeftTurnAct">
        <ManeuverGroup name="LeftTurnManeuverGroup" maximumExecutionCount="1">
          <Actors selectActorRoles="true">
            <ActorRef entityRef="ego_vehicle" />
          </Actors>
          <Maneuver name="LeftTurnManeuver">
            <Event name="LeftTurnEvent" priority="overwrite">
              <Action name="LeftTurnAction">
                <PrivateAction entityRef="ego_vehicle">
                  <LongitudinalAction>
                    <SpeedAction>
                      <SpeedActionTarget>
                        <AbsoluteTargetSpeed value="13.89" />
                      </SpeedActionTarget>
                      <SpeedActionDynamics>
                        <Dynamics shape="linear" rate="2.0" time="0" />
                      </SpeedActionDynamics>
                    </SpeedAction>
                  </LongitudinalAction>
                  <LateralAction>
                    <LaneChangeAction targetLaneOffset="1">
                      <LaneChangeActionDynamics>
                        <Dynamics shape="linear" time="3.0" />
                      </LaneChangeActionDynamics>
                      <LaneChangeTarget>
                        <RelativeTargetLane entityRef="ego_vehicle" value="1" />
                      </LaneChangeTarget>
                    </LaneChangeAction>
                  </LateralAction>
                </PrivateAction>
              </Action>
              <StartTrigger>
                <ConditionGroup>
                  <Condition name="StartCondition" delay="2.0" conditionEdge="rising">
                    <ByValueCondition>
                      <SimulationTimeCondition rule="greaterThan" value="0" />
                    </ByValueCondition>
                  </Condition>
                </ConditionGroup>
              </StartTrigger>
            </Event>
          </Maneuver>
        </ManeuverGroup>
      </Act>
    </Story>
    <StopTrigger>
      <ConditionGroup>
        <Condition name="StopCondition" delay="10.0" conditionEdge="rising">
          <ByValueCondition>
            <SimulationTimeCondition rule="greaterThan" value="10" />
          </ByValueCondition>
        </Condition>
      </ConditionGroup>
    </StopTrigger>
  </Storyboard>"""
    
    def _get_precipitation_type(self, scenario: Dict) -> str:
        """获取降水类型"""
        weather = scenario.get('environment', {}).get('weather', 'clear')
        
        weather_map = {
            'clear': 'none',
            'rain': 'rain',
            'fog': 'fog',
            'night': 'none',
            'rain_night': 'rain'
        }
        
        return weather_map.get(weather, 'none')
    
    def _save_to_file(self, xml_str: str, file_path: str):
        """保存到文件"""
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(xml_str)
    
    def export_batch(self, scenarios: List[Dict], output_dir: str):
        """批量导出场景
        
        参数:
            scenarios: 场景列表
            output_dir: 输出目录
        """
        os.makedirs(output_dir, exist_ok=True)
        
        for scenario in scenarios:
            scenario_id = scenario.get('id', 'unknown')
            output_path = os.path.join(output_dir, f"{scenario_id}.xosc")
            
            try:
                self.export(scenario, output_path)
                logger.info(f"导出场景: {scenario_id}")
            except Exception as e:
                logger.error(f"导出场景失败 {scenario_id}: {e}")
        
        logger.info(f"批量导出完成，共 {len(scenarios)} 个场景")
