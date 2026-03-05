# 多频段信号融合策略 - 实时监控使用示例

import pandas as pd
import numpy as np
from models.multi_frequency_fusion import MultiFrequencySignalFusionStrategy

# 配置参数
config = {
    # 模型路径
    'model_path': './models/saved/',
    
    # 监控配置
    'enable_monitoring': True,          # 启用监控
    'monitoring_interval': 60,           # 监控间隔（秒）
    
    # 报警阈值
    'alert_signal_threshold': 0.05,      # 信号强度报警阈值
    'alert_confidence': 0.8,             # 置信度报警阈值
    'alert_risk_level': 'high',          # 风险等级报警阈值
    'alert_signal_reversal': True,       # 是否启用信号反转报警
    'max_alerts_per_hour': 10,           # 每小时最大报警数
    
    # 钉钉报警配置（可选）
    'dingtalk_webhook_url': 'https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN',
    
    # 邮件报警配置（可选）
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'smtp_username': 'your_email@gmail.com',
    'smtp_password': 'your_password',
    'alert_recipient': 'recipient@example.com'
}

# 初始化策略
strategy = MultiFrequencySignalFusionStrategy(config)

# 准备训练数据
train_data = {
    'tick': [pd.DataFrame()],
    'minute': [pd.DataFrame()],
    'financial': [pd.DataFrame()],
    'price': [pd.DataFrame()]
}

val_data = {
    'tick': [pd.DataFrame()],
    'minute': [pd.DataFrame()],
    'financial': [pd.DataFrame()],
    'price': [pd.DataFrame()],
    'actual_returns': []
}

# 训练策略
strategy.train(train_data, val_data)

# 启动实时监控
strategy.start_monitoring()

# 获取监控状态
status = strategy.get_monitoring_status()
print(f"监控状态: {status}")

# 获取最近的报警
recent_alerts = strategy.get_recent_alerts(10)
print(f"最近报警: {recent_alerts}")

# 设置报警阈值
strategy.set_alert_threshold('signal_strength', 0.08)

# 获取所有报警阈值
thresholds = strategy.get_alert_thresholds()
print(f"报警阈值: {thresholds}")

# 生成监控报告
report = strategy.generate_monitoring_report()
print(f"监控报告: {report}")

# 停止监控
strategy.stop_monitoring()

# 清除报警
strategy.clear_alerts()

# 自定义数据获取方法
class CustomStrategy(MultiFrequencySignalFusionStrategy):
    def _fetch_latest_data(self):
        """
        自定义数据获取方法
        从数据库或API获取最新数据
        """
        # 示例：从数据库获取最新数据
        # import sqlite3
        # conn = sqlite3.connect('market_data.db')
        # 
        # tick_data = pd.read_sql("SELECT * FROM tick_data ORDER BY timestamp DESC LIMIT 1000", conn)
        # minute_data = pd.read_sql("SELECT * FROM minute_data ORDER BY timestamp DESC LIMIT 60", conn)
        # financial_data = pd.read_sql("SELECT * FROM financial_data ORDER BY date DESC LIMIT 20", conn)
        # price_data = pd.read_sql("SELECT * FROM price_data ORDER BY date DESC LIMIT 20", conn)
        # market_data = pd.read_sql("SELECT * FROM market_data ORDER BY timestamp DESC LIMIT 1", conn)
        # 
        # conn.close()
        # 
        # return {
        #     'tick': tick_data,
        #     'minute': minute_data,
        #     'financial': financial_data,
        #     'price': price_data,
        #     'market_data': market_data
        # }
        
        # 示例：从API获取最新数据
        # import requests
        # 
        # tick_response = requests.get('https://api.example.com/tick')
        # minute_response = requests.get('https://api.example.com/minute')
        # 
        # return {
        #     'tick': pd.DataFrame(tick_response.json()),
        #     'minute': pd.DataFrame(minute_response.json()),
        #     'financial': pd.DataFrame(),
        #     'price': pd.DataFrame(),
        #     'market_data': pd.DataFrame()
        # }
        
        # 暂时返回None
        return None

# 使用自定义策略
custom_strategy = CustomStrategy(config)
custom_strategy.train(train_data, val_data)
custom_strategy.start_monitoring()

# 报警类型说明：
# 1. strong_signal: 强信号出现（信号强度超过阈值）
# 2. high_confidence: 高置信度信号（置信度超过阈值）
# 3. high_risk: 高风险信号（风险等级为high）
# 4. signal_reversal: 信号反转（信号方向改变）

# 监控状态字段说明：
# - is_monitoring: 是否正在监控
# - monitoring_enabled: 监控是否启用
# - monitoring_interval: 监控间隔（秒）
# - last_signal: 最后一次信号
# - signal_history_count: 信号历史数量
# - alerts_count: 报警数量
# - alert_stats: 报警统计信息
