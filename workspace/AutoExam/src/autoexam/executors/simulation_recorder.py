#!/usr/bin/env python3
"""
仿真结果采集和记录模块
负责采集CARLA仿真过程中的各种数据并记录
"""

import os
import json
import logging
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import io
import base64

logger = logging.getLogger('SimulationRecorder')

class SimulationRecorder:
    """仿真结果采集和记录器"""
    
    def __init__(self, results_dir: str = './data/results'):
        """初始化仿真结果记录器
        
        参数:
            results_dir: 结果存储目录
        """
        self.results_dir = results_dir
        os.makedirs(results_dir, exist_ok=True)
        
        self.current_session = None
        self.session_data = []
    
    def start_session(self, session_name: str = None):
        """开始新的记录会话
        
        参数:
            session_name: 会话名称
        """
        if session_name is None:
            session_name = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.current_session = session_name
        self.session_data = []
        
        logger.info(f"开始新的记录会话: {session_name}")
    
    def record_result(self, result: Dict):
        """记录仿真结果
        
        参数:
            result: 仿真结果字典
        """
        if self.current_session is None:
            self.start_session()
        
        result['session'] = self.current_session
        result['recorded_at'] = datetime.now().isoformat()
        
        self.session_data.append(result)
        
        logger.info(f"记录结果: scenario_id={result.get('scenario_id')}, collision={result.get('collision')}")
    
    def save_session(self, filename: str = None):
        """保存当前会话数据
        
        参数:
            filename: 文件名（可选）
        """
        if self.current_session is None:
            logger.warning("没有活动的会话")
            return None
        
        if filename is None:
            filename = f"{self.current_session}.json"
        
        filepath = os.path.join(self.results_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.session_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"会话数据已保存: {filepath}")
        
        return filepath
    
    def load_session(self, filename: str) -> List[Dict]:
        """加载会话数据
        
        参数:
            filename: 文件名
            
        返回:
            会话数据列表
        """
        filepath = os.path.join(self.results_dir, filename)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"加载会话数据: {filepath}, 共{len(data)}条记录")
        
        return data
    
    def analyze_session(self, data: List[Dict] = None) -> Dict:
        """分析会话数据
        
        参数:
            data: 会话数据（可选，默认使用当前会话）
            
        返回:
            分析结果
        """
        if data is None:
            data = self.session_data
        
        if not data:
            return {}
        
        total = len(data)
        collisions = sum(1 for r in data if r.get('collision', False))
        successes = total - collisions
        
        execution_times = [r.get('execution_time', 0) for r in data if 'execution_time' in r]
        avg_execution_time = np.mean(execution_times) if execution_times else 0
        
        collision_rate = collisions / total if total > 0 else 0
        success_rate = successes / total if total > 0 else 0
        
        analysis = {
            'total_scenarios': total,
            'collision_count': collisions,
            'success_count': successes,
            'collision_rate': collision_rate,
            'success_rate': success_rate,
            'avg_execution_time': avg_execution_time,
            'analysis_time': datetime.now().isoformat()
        }
        
        logger.info(f"会话分析: 总数={total}, 碰撞={collisions}, 成功={successes}, "
                   f"碰撞率={collision_rate:.2%}, 平均耗时={avg_execution_time:.2f}s")
        
        return analysis
    
    def get_trajectory_data(self, result: Dict) -> List[Dict]:
        """获取轨迹数据
        
        参数:
            result: 仿真结果
            
        返回:
            轨迹数据列表
        """
        return result.get('trajectory_data', [])
    
    def plot_trajectory(self, trajectory_data: List[Dict], save_path: str = None) -> str:
        """绘制轨迹图
        
        参数:
            trajectory_data: 轨迹数据
            save_path: 保存路径（可选）
            
        返回:
            图片的base64编码
        """
        if not trajectory_data:
            logger.warning("没有轨迹数据")
            return None
        
        try:
            fig, ax = plt.subplots(figsize=(10, 8))
            
            x = [point['location']['x'] for point in trajectory_data]
            y = [point['location']['y'] for point in trajectory_data]
            
            ax.plot(x, y, 'b-', linewidth=2, label='主车轨迹')
            ax.scatter(x[0], y[0], c='g', s=100, marker='o', label='起点')
            ax.scatter(x[-1], y[-1], c='r', s=100, marker='s', label='终点')
            
            ax.set_xlabel('X (m)')
            ax.set_ylabel('Y (m)')
            ax.set_title('车辆轨迹')
            ax.legend()
            ax.grid(True)
            ax.axis('equal')
            
            if save_path:
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                plt.savefig(save_path, dpi=150, bbox_inches='tight')
                logger.info(f"轨迹图已保存: {save_path}")
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            
            plt.close(fig)
            
            return img_base64
            
        except Exception as e:
            logger.error(f"绘制轨迹图失败: {e}")
            return None
    
    def plot_velocity_profile(self, trajectory_data: List[Dict], save_path: str = None) -> str:
        """绘制速度曲线
        
        参数:
            trajectory_data: 轨迹数据
            save_path: 保存路径（可选）
            
        返回:
            图片的base64编码
        """
        if not trajectory_data:
            logger.warning("没有轨迹数据")
            return None
        
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            times = [point['time'] for point in trajectory_data]
            velocities = [
                np.sqrt(point['velocity']['x']**2 + point['velocity']['y']**2) * 3.6
                for point in trajectory_data
            ]
            
            ax.plot(times, velocities, 'b-', linewidth=2)
            ax.set_xlabel('时间 (s)')
            ax.set_ylabel('速度 (km/h)')
            ax.set_title('速度曲线')
            ax.grid(True)
            
            if save_path:
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                plt.savefig(save_path, dpi=150, bbox_inches='tight')
                logger.info(f"速度曲线已保存: {save_path}")
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            
            plt.close(fig)
            
            return img_base64
            
        except Exception as e:
            logger.error(f"绘制速度曲线失败: {e}")
            return None
    
    def plot_statistics(self, data: List[Dict], save_path: str = None) -> str:
        """绘制统计图表
        
        参数:
            data: 会话数据
            save_path: 保存路径（可选）
            
        返回:
            图片的base64编码
        """
        if not data:
            logger.warning("没有数据")
            return None
        
        try:
            fig, axes = plt.subplots(2, 2, figsize=(14, 10))
            
            collisions = sum(1 for r in data if r.get('collision', False))
            successes = len(data) - collisions
            
            axes[0, 0].pie([successes, collisions], 
                          labels=['成功', '碰撞'],
                          autopct='%1.1f%%',
                          colors=['green', 'red'],
                          startangle=90)
            axes[0, 0].set_title('结果分布')
            
            execution_times = [r.get('execution_time', 0) for r in data if 'execution_time' in r]
            if execution_times:
                axes[0, 1].hist(execution_times, bins=20, color='blue', alpha=0.7)
                axes[0, 1].set_xlabel('执行时间 (s)')
                axes[0, 1].set_ylabel('频次')
                axes[0, 1].set_title('执行时间分布')
                axes[0, 1].grid(True)
            
            weather_counts = {}
            for r in data:
                weather = r.get('parameters', {}).get('weather', 'unknown')
                weather_counts[weather] = weather_counts.get(weather, 0) + 1
            
            if weather_counts:
                axes[1, 0].bar(weather_counts.keys(), weather_counts.values(), color='orange')
                axes[1, 0].set_xlabel('天气')
                axes[1, 0].set_ylabel('场景数')
                axes[1, 0].set_title('天气分布')
                axes[1, 0].grid(True)
            
            difficulty_counts = {}
            for r in data:
                difficulty = r.get('difficulty', 'unknown')
                difficulty_counts[difficulty] = difficulty_counts.get(difficulty, 0) + 1
            
            if difficulty_counts:
                axes[1, 1].bar(difficulty_counts.keys(), difficulty_counts.values(), color='purple')
                axes[1, 1].set_xlabel('难度')
                axes[1, 1].set_ylabel('场景数')
                axes[1, 1].set_title('难度分布')
                axes[1, 1].grid(True)
            
            plt.tight_layout()
            
            if save_path:
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                plt.savefig(save_path, dpi=150, bbox_inches='tight')
                logger.info(f"统计图表已保存: {save_path}")
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            
            plt.close(fig)
            
            return img_base64
            
        except Exception as e:
            logger.error(f"绘制统计图表失败: {e}")
            return None
    
    def export_to_csv(self, data: List[Dict], filename: str):
        """导出数据到CSV
        
        参数:
            data: 会话数据
            filename: 文件名
        """
        try:
            import csv
            
            filepath = os.path.join(self.results_dir, filename)
            
            if not data:
                logger.warning("没有数据可导出")
                return
            
            fieldnames = [
                'scenario_id', 'scenario_type', 'collision', 'execution_time',
                'success', 'timestamp', 'environment'
            ]
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in data:
                    row = {
                        'scenario_id': result.get('scenario_id'),
                        'scenario_type': result.get('scenario_type'),
                        'collision': result.get('collision', False),
                        'execution_time': result.get('execution_time', 0),
                        'success': result.get('success', False),
                        'timestamp': result.get('timestamp'),
                        'environment': result.get('environment')
                    }
                    writer.writerow(row)
            
            logger.info(f"数据已导出到CSV: {filepath}")
            
        except Exception as e:
            logger.error(f"导出CSV失败: {e}")
    
    def generate_report(self, data: List[Dict] = None) -> str:
        """生成测试报告
        
        参数:
            data: 会话数据（可选，默认使用当前会话）
            
        返回:
            报告内容
        """
        if data is None:
            data = self.session_data
        
        if not data:
            return "没有数据可生成报告"
        
        analysis = self.analyze_session(data)
        
        report = f"""
# 仿真测试报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 统计概览

- **总场景数**: {analysis['total_scenarios']}
- **碰撞数**: {analysis['collision_count']}
- **成功数**: {analysis['success_count']}
- **碰撞率**: {analysis['collision_rate']:.2%}
- **成功率**: {analysis['success_rate']:.2%}
- **平均执行时间**: {analysis['avg_execution_time']:.2f}s

## 详细结果

"""
        
        for i, result in enumerate(data, 1):
            report += f"""
### 场景 {i}: {result.get('scenario_id', 'unknown')}

- **类型**: {result.get('scenario_type', 'unknown')}
- **碰撞**: {'是' if result.get('collision') else '否'}
- **执行时间**: {result.get('execution_time', 0):.2f}s
- **时间**: {result.get('timestamp', 'unknown')}
"""
        
        return report
