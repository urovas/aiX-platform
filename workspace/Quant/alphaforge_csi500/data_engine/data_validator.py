# 数据验证工具

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import warnings
from datetime import datetime, timedelta
import re

warnings.filterwarnings('ignore')


class DataValidator:
    """
    数据验证工具
    用于验证数据质量、完整性和一致性
    """
    
    def __init__(self, config: Dict = None):
        """
        初始化数据验证器
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        
        # 验证规则
        self.rules = {
            'tick': self._get_tick_rules(),
            'minute': self._get_minute_rules(),
            'daily': self._get_daily_rules(),
            'financial': self._get_financial_rules(),
            'order_book': self._get_order_book_rules()
        }
        
        # 验证结果
        self.validation_results = {}
        
        print("✅ 数据验证器初始化完成")
    
    def _get_tick_rules(self) -> Dict:
        """获取逐笔数据验证规则"""
        return {
            'required_columns': ['datetime', 'stock_code', 'price', 'volume'],
            'column_types': {
                'datetime': 'datetime64[ns]',
                'stock_code': 'object',
                'price': 'float64',
                'volume': 'int64'
            },
            'value_ranges': {
                'price': (0, 10000),
                'volume': (0, 1e10),
                'amount': (0, 1e15)
            },
            'unique_check': ['datetime', 'stock_code']
        }
    
    def _get_minute_rules(self) -> Dict:
        """获取分钟数据验证规则"""
        return {
            'required_columns': ['datetime', 'stock_code', 'open', 'high', 'low', 'close', 'volume'],
            'column_types': {
                'datetime': 'datetime64[ns]',
                'stock_code': 'object',
                'open': 'float64',
                'high': 'float64',
                'low': 'float64',
                'close': 'float64',
                'volume': 'int64'
            },
            'value_ranges': {
                'open': (0, 10000),
                'high': (0, 10000),
                'low': (0, 10000),
                'close': (0, 10000),
                'volume': (0, 1e10)
            },
            'logical_rules': {
                'high_ge_low': 'high >= low',
                'high_ge_open': 'high >= open',
                'high_ge_close': 'high >= close',
                'low_le_open': 'low <= open',
                'low_le_close': 'low <= close'
            }
        }
    
    def _get_daily_rules(self) -> Dict:
        """获取日线数据验证规则"""
        return {
            'required_columns': ['date', 'stock_code', 'open', 'high', 'low', 'close', 'volume'],
            'column_types': {
                'date': 'datetime64[ns]',
                'stock_code': 'object',
                'open': 'float64',
                'high': 'float64',
                'low': 'float64',
                'close': 'float64',
                'volume': 'float64'
            },
            'value_ranges': {
                'open': (0, 10000),
                'high': (0, 10000),
                'low': (0, 10000),
                'close': (0, 10000),
                'volume': (0, 1e12),
                'turnover': (0, 100)
            },
            'logical_rules': {
                'high_ge_low': 'high >= low',
                'high_ge_open': 'high >= open',
                'high_ge_close': 'high >= close',
                'low_le_open': 'low <= open',
                'low_le_close': 'low <= close'
            }
        }
    
    def _get_financial_rules(self) -> Dict:
        """获取财务数据验证规则"""
        return {
            'required_columns': ['date', 'stock_code', 'revenue', 'net_profit', 'total_assets', 'total_equity'],
            'column_types': {
                'date': 'datetime64[ns]',
                'stock_code': 'object',
                'revenue': 'float64',
                'net_profit': 'float64',
                'total_assets': 'float64',
                'total_equity': 'float64'
            },
            'value_ranges': {
                'revenue': (-1e15, 1e15),
                'net_profit': (-1e14, 1e14),
                'total_assets': (0, 1e16),
                'total_equity': (-1e15, 1e15)
            },
            'logical_rules': {
                'assets_ge_equity': 'total_assets >= total_equity'
            }
        }
    
    def _get_order_book_rules(self) -> Dict:
        """获取订单簿数据验证规则"""
        return {
            'required_columns': ['datetime', 'stock_code', 'mid_price'],
            'column_types': {
                'datetime': 'datetime64[ns]',
                'stock_code': 'object',
                'mid_price': 'float64'
            },
            'value_ranges': {
                'mid_price': (0, 10000),
                'bid_price_1': (0, 10000),
                'ask_price_1': (0, 10000)
            },
            'logical_rules': {
                'ask_ge_bid': 'ask_price_1 >= bid_price_1'
            }
        }
    
    def validate(self, 
                data: pd.DataFrame, 
                data_type: str,
                stock_code: str = None) -> Dict:
        """
        验证数据
        
        Args:
            data: 数据DataFrame
            data_type: 数据类型
            stock_code: 股票代码（可选）
            
        Returns:
            result: 验证结果
        """
        print(f"验证{data_type}数据...")
        
        if data_type not in self.rules:
            print(f"  ⚠️ 未知的数据类型: {data_type}")
            return {'valid': False, 'errors': [f"未知的数据类型: {data_type}"]}
        
        rules = self.rules[data_type]
        errors = []
        warnings_list = []
        
        # 1. 检查数据是否为空
        if data.empty:
            errors.append("数据为空")
            return {'valid': False, 'errors': errors}
        
        # 2. 检查必需列
        missing_cols = self._check_required_columns(data, rules.get('required_columns', []))
        if missing_cols:
            errors.append(f"缺少必需列: {missing_cols}")
        
        # 3. 检查数据类型
        type_errors = self._check_column_types(data, rules.get('column_types', {}))
        if type_errors:
            warnings_list.extend(type_errors)
        
        # 4. 检查值范围
        range_errors = self._check_value_ranges(data, rules.get('value_ranges', {}))
        if range_errors:
            errors.extend(range_errors)
        
        # 5. 检查逻辑规则
        logical_errors = self._check_logical_rules(data, rules.get('logical_rules', {}))
        if logical_errors:
            errors.extend(logical_errors)
        
        # 6. 检查缺失值
        missing_stats = self._check_missing_values(data)
        
        # 7. 检查重复值
        duplicate_count = self._check_duplicates(data, rules.get('unique_check', []))
        if duplicate_count > 0:
            warnings_list.append(f"发现 {duplicate_count} 条重复记录")
        
        # 8. 检查时间连续性
        time_issues = self._check_time_continuity(data, data_type)
        if time_issues:
            warnings_list.extend(time_issues)
        
        # 9. 检查异常值
        outlier_stats = self._check_outliers(data)
        
        # 构建结果
        result = {
            'valid': len(errors) == 0,
            'data_type': data_type,
            'stock_code': stock_code,
            'total_rows': len(data),
            'total_columns': len(data.columns),
            'errors': errors,
            'warnings': warnings_list,
            'missing_stats': missing_stats,
            'duplicate_count': duplicate_count,
            'outlier_stats': outlier_stats,
            'validated_at': datetime.now().isoformat()
        }
        
        # 保存结果
        cache_key = f"{data_type}_{stock_code or 'all'}"
        self.validation_results[cache_key] = result
        
        # 打印结果
        if result['valid']:
            print(f"  ✅ 验证通过")
        else:
            print(f"  ❌ 验证失败: {len(errors)} 个错误")
        
        return result
    
    def _check_required_columns(self, data: pd.DataFrame, required: List[str]) -> List[str]:
        """检查必需列"""
        missing = [col for col in required if col not in data.columns]
        return missing
    
    def _check_column_types(self, data: pd.DataFrame, types: Dict) -> List[str]:
        """检查数据类型"""
        warnings_list = []
        
        for col, expected_type in types.items():
            if col not in data.columns:
                continue
            
            actual_type = str(data[col].dtype)
            
            # 简化类型比较
            if 'datetime' in expected_type and 'datetime' not in actual_type:
                warnings_list.append(f"列 {col} 类型不匹配: 期望 {expected_type}, 实际 {actual_type}")
            elif 'float' in expected_type and 'float' not in actual_type and 'int' not in actual_type:
                warnings_list.append(f"列 {col} 类型不匹配: 期望 {expected_type}, 实际 {actual_type}")
            elif 'int' in expected_type and 'int' not in actual_type:
                warnings_list.append(f"列 {col} 类型不匹配: 期望 {expected_type}, 实际 {actual_type}")
        
        return warnings_list
    
    def _check_value_ranges(self, data: pd.DataFrame, ranges: Dict) -> List[str]:
        """检查值范围"""
        errors = []
        
        for col, (min_val, max_val) in ranges.items():
            if col not in data.columns:
                continue
            
            # 检查最小值
            if data[col].min() < min_val:
                count = (data[col] < min_val).sum()
                errors.append(f"列 {col} 有 {count} 个值小于最小值 {min_val}")
            
            # 检查最大值
            if data[col].max() > max_val:
                count = (data[col] > max_val).sum()
                errors.append(f"列 {col} 有 {count} 个值大于最大值 {max_val}")
        
        return errors
    
    def _check_logical_rules(self, data: pd.DataFrame, rules: Dict) -> List[str]:
        """检查逻辑规则"""
        errors = []
        
        for rule_name, rule_expr in rules.items():
            try:
                # 简单的逻辑规则检查
                if rule_expr == 'high >= low':
                    violations = (data['high'] < data['low']).sum()
                    if violations > 0:
                        errors.append(f"逻辑规则违反 ({rule_expr}): {violations} 条记录")
                
                elif rule_expr == 'high >= open':
                    violations = (data['high'] < data['open']).sum()
                    if violations > 0:
                        errors.append(f"逻辑规则违反 ({rule_expr}): {violations} 条记录")
                
                elif rule_expr == 'high >= close':
                    violations = (data['high'] < data['close']).sum()
                    if violations > 0:
                        errors.append(f"逻辑规则违反 ({rule_expr}): {violations} 条记录")
                
                elif rule_expr == 'low <= open':
                    violations = (data['low'] > data['open']).sum()
                    if violations > 0:
                        errors.append(f"逻辑规则违反 ({rule_expr}): {violations} 条记录")
                
                elif rule_expr == 'low <= close':
                    violations = (data['low'] > data['close']).sum()
                    if violations > 0:
                        errors.append(f"逻辑规则违反 ({rule_expr}): {violations} 条记录")
                
                elif rule_expr == 'total_assets >= total_equity':
                    violations = (data['total_assets'] < data['total_equity']).sum()
                    if violations > 0:
                        errors.append(f"逻辑规则违反 ({rule_expr}): {violations} 条记录")
                
                elif rule_expr == 'ask_price_1 >= bid_price_1':
                    if 'ask_price_1' in data.columns and 'bid_price_1' in data.columns:
                        violations = (data['ask_price_1'] < data['bid_price_1']).sum()
                        if violations > 0:
                            errors.append(f"逻辑规则违反 ({rule_expr}): {violations} 条记录")
                
            except Exception as e:
                errors.append(f"逻辑规则检查失败 ({rule_name}): {e}")
        
        return errors
    
    def _check_missing_values(self, data: pd.DataFrame) -> Dict:
        """检查缺失值"""
        missing = data.isnull().sum()
        total = len(data)
        
        stats = {
            'total_missing': missing.sum(),
            'by_column': {col: {'count': count, 'ratio': count / total} 
                         for col, count in missing.items() if count > 0}
        }
        
        return stats
    
    def _check_duplicates(self, data: pd.DataFrame, unique_cols: List[str]) -> int:
        """检查重复值"""
        if not unique_cols:
            return 0
        
        existing_cols = [col for col in unique_cols if col in data.columns]
        if not existing_cols:
            return 0
        
        return data.duplicated(subset=existing_cols).sum()
    
    def _check_time_continuity(self, data: pd.DataFrame, data_type: str) -> List[str]:
        """检查时间连续性"""
        warnings_list = []
        
        time_cols = ['datetime', 'timestamp', 'date', 'time']
        time_col = None
        
        for col in time_cols:
            if col in data.columns:
                time_col = col
                break
        
        if time_col is None:
            return warnings_list
        
        try:
            # 转换时间列
            data[time_col] = pd.to_datetime(data[time_col])
            
            # 排序
            data_sorted = data.sort_values(time_col)
            
            # 计算时间差
            time_diffs = data_sorted[time_col].diff()
            
            # 根据数据类型检查
            if data_type == 'minute':
                expected_diff = pd.Timedelta(minutes=1)
                max_gap = pd.Timedelta(minutes=5)
            elif data_type == 'daily':
                expected_diff = pd.Timedelta(days=1)
                max_gap = pd.Timedelta(days=7)
            else:
                return warnings_list
            
            # 检查大间隙
            large_gaps = (time_diffs > max_gap).sum()
            if large_gaps > 0:
                warnings_list.append(f"发现 {large_gaps} 个时间间隙大于 {max_gap}")
            
        except Exception as e:
            warnings_list.append(f"时间连续性检查失败: {e}")
        
        return warnings_list
    
    def _check_outliers(self, data: pd.DataFrame) -> Dict:
        """检查异常值"""
        outlier_stats = {}
        
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            Q1 = data[col].quantile(0.25)
            Q3 = data[col].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 3 * IQR
            upper_bound = Q3 + 3 * IQR
            
            outliers = ((data[col] < lower_bound) | (data[col] > upper_bound)).sum()
            
            if outliers > 0:
                outlier_stats[col] = {
                    'count': outliers,
                    'ratio': outliers / len(data),
                    'lower_bound': lower_bound,
                    'upper_bound': upper_bound
                }
        
        return outlier_stats
    
    def validate_batch(self,
                      data_dict: Dict[str, pd.DataFrame],
                      data_type: str) -> Dict[str, Dict]:
        """
        批量验证数据
        
        Args:
            data_dict: 数据字典 {stock_code: DataFrame}
            data_type: 数据类型
            
        Returns:
            results: 验证结果字典
        """
        print(f"\n批量验证 {len(data_dict)} 个数据集...")
        
        results = {}
        
        for stock_code, data in data_dict.items():
            results[stock_code] = self.validate(data, data_type, stock_code)
        
        # 统计结果
        valid_count = sum(1 for r in results.values() if r['valid'])
        print(f"\n验证完成: {valid_count}/{len(results)} 通过")
        
        return results
    
    def validate_stock_code(self, stock_code: str) -> bool:
        """
        验证股票代码格式
        
        Args:
            stock_code: 股票代码
            
        Returns:
            valid: 是否有效
        """
        # A股格式：6位数字.交易所
        pattern = r'^\d{6}\.(SZ|SH|BJ)$'
        
        if re.match(pattern, stock_code):
            return True
        
        # 港股格式：5位数字.HK
        pattern = r'^\d{5}\.HK$'
        if re.match(pattern, stock_code):
            return True
        
        # 美股格式：1-5位大写字母
        pattern = r'^[A-Z]{1,5}$'
        if re.match(pattern, stock_code):
            return True
        
        return False
    
    def validate_date_range(self, 
                           start_date: str, 
                           end_date: str) -> Tuple[bool, str]:
        """
        验证日期范围
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            valid, message: 是否有效和消息
        """
        try:
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            
            if start > end:
                return False, "开始日期不能晚于结束日期"
            
            if end > datetime.now():
                return False, "结束日期不能晚于当前日期"
            
            return True, "日期范围有效"
            
        except Exception as e:
            return False, f"日期格式错误: {e}"
    
    def get_validation_summary(self) -> pd.DataFrame:
        """
        获取验证结果摘要
        
        Returns:
            summary: 摘要DataFrame
        """
        if not self.validation_results:
            return pd.DataFrame()
        
        summary_list = []
        
        for key, result in self.validation_results.items():
            summary_list.append({
                'key': key,
                'valid': result['valid'],
                'data_type': result['data_type'],
                'stock_code': result['stock_code'],
                'total_rows': result['total_rows'],
                'error_count': len(result['errors']),
                'warning_count': len(result['warnings']),
                'missing_count': result['missing_stats']['total_missing'],
                'duplicate_count': result['duplicate_count'],
                'outlier_count': sum(s['count'] for s in result['outlier_stats'].values()),
                'validated_at': result['validated_at']
            })
        
        return pd.DataFrame(summary_list)
    
    def print_validation_report(self, result: Dict = None):
        """
        打印验证报告
        
        Args:
            result: 验证结果，None表示打印所有结果
        """
        if result:
            results = {'single': result}
        else:
            results = self.validation_results
        
        for key, res in results.items():
            print("\n" + "="*60)
            print(f"验证报告: {key}")
            print("="*60)
            
            print(f"数据类型: {res['data_type']}")
            print(f"股票代码: {res['stock_code']}")
            print(f"总行数: {res['total_rows']}")
            print(f"总列数: {res['total_columns']}")
            print(f"验证结果: {'✅ 通过' if res['valid'] else '❌ 失败'}")
            
            if res['errors']:
                print("\n错误:")
                for error in res['errors']:
                    print(f"  ❌ {error}")
            
            if res['warnings']:
                print("\n警告:")
                for warning in res['warnings']:
                    print(f"  ⚠️ {warning}")
            
            if res['missing_stats']['total_missing'] > 0:
                print("\n缺失值统计:")
                for col, stats in res['missing_stats']['by_column'].items():
                    print(f"  {col}: {stats['count']} ({stats['ratio']:.2%})")
            
            if res['outlier_stats']:
                print("\n异常值统计:")
                for col, stats in res['outlier_stats'].items():
                    print(f"  {col}: {stats['count']} ({stats['ratio']:.2%})")
            
            print("="*60)
    
    def export_validation_results(self, file_path: str):
        """
        导出验证结果到文件
        
        Args:
            file_path: 文件路径
        """
        import json
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.validation_results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"✅ 验证结果已导出: {file_path}")
    
    def add_custom_rule(self, 
                       data_type: str, 
                       rule_name: str, 
                       rule_func):
        """
        添加自定义验证规则
        
        Args:
            data_type: 数据类型
            rule_name: 规则名称
            rule_func: 规则函数 (data) -> List[str]
        """
        if data_type not in self.rules:
            self.rules[data_type] = {}
        
        if 'custom_rules' not in self.rules[data_type]:
            self.rules[data_type]['custom_rules'] = {}
        
        self.rules[data_type]['custom_rules'][rule_name] = rule_func
        
        print(f"✅ 已添加自定义规则: {data_type}.{rule_name}")
    
    def check_data_freshness(self, 
                            data: pd.DataFrame, 
                            time_col: str = 'datetime',
                            max_age_hours: int = 24) -> Tuple[bool, str]:
        """
        检查数据新鲜度
        
        Args:
            data: 数据DataFrame
            time_col: 时间列名
            max_age_hours: 最大允许的小时数
            
        Returns:
            fresh, message: 是否新鲜和消息
        """
        if time_col not in data.columns:
            return False, f"时间列 {time_col} 不存在"
        
        try:
            latest_time = pd.to_datetime(data[time_col]).max()
            age = datetime.now() - latest_time.to_pydatetime()
            age_hours = age.total_seconds() / 3600
            
            if age_hours > max_age_hours:
                return False, f"数据已过期 {age_hours:.1f} 小时"
            
            return True, f"数据新鲜，最新时间: {latest_time}"
            
        except Exception as e:
            return False, f"新鲜度检查失败: {e}"
