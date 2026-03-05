# 量化交易工具函数库

from .utils import (
    DataUtils,
    PlotUtils, 
    PerformanceUtils,
    clean_data,
    calculate_returns,
    normalize_data,
    plot_factor_ic,
    plot_correlation_heatmap,
    plot_backtest_results,
    calculate_performance_metrics,
    generate_performance_report
)

__all__ = [
    'DataUtils',
    'PlotUtils',
    'PerformanceUtils',
    'clean_data',
    'calculate_returns',
    'normalize_data',
    'plot_factor_ic',
    'plot_correlation_heatmap',
    'plot_backtest_results',
    'calculate_performance_metrics',
    'generate_performance_report'
]

__version__ = '1.0.0'
__author__ = 'Clawdbot'
__date__ = '2026-02-14'