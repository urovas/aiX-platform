# 数据缓存管理器

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
import os
import pickle
import hashlib
import json
import time
from datetime import datetime, timedelta
from collections import OrderedDict
import threading
import warnings

warnings.filterwarnings('ignore')


class DataCache:
    """
    数据缓存管理器
    支持内存缓存、磁盘缓存、LRU淘汰策略
    """
    
    def __init__(self, config: Dict = None):
        """
        初始化数据缓存管理器
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        
        # 内存缓存
        self.memory_cache = OrderedDict()
        
        # 缓存配置
        self.max_memory_items = self.config.get('max_memory_items', 100)
        self.max_memory_size_mb = self.config.get('max_memory_size_mb', 1024)
        self.default_ttl = self.config.get('default_ttl', 3600)  # 默认过期时间（秒）
        
        # 磁盘缓存目录
        self.disk_cache_dir = self.config.get('disk_cache_dir', './cache/')
        os.makedirs(self.disk_cache_dir, exist_ok=True)
        
        # 缓存元数据
        self.cache_metadata = {}
        
        # 缓存统计
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'disk_reads': 0,
            'disk_writes': 0
        }
        
        # 线程锁
        self.lock = threading.RLock()
        
        # 加载缓存元数据
        self._load_metadata()
        
        print("✅ 数据缓存管理器初始化完成")
        print(f"  内存缓存上限: {self.max_memory_items} 项 / {self.max_memory_size_mb} MB")
        print(f"  磁盘缓存目录: {self.disk_cache_dir}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取缓存数据
        
        Args:
            key: 缓存键
            default: 默认值
            
        Returns:
            data: 缓存数据
        """
        with self.lock:
            # 检查内存缓存
            if key in self.memory_cache:
                # 检查是否过期
                if self._is_expired(key):
                    self._remove(key)
                    self.stats['misses'] += 1
                    return default
                
                # 移动到末尾（LRU）
                self.memory_cache.move_to_end(key)
                self.stats['hits'] += 1
                return self.memory_cache[key]['data']
            
            # 检查磁盘缓存
            disk_data = self._load_from_disk(key)
            if disk_data is not None:
                # 检查是否过期
                if self._is_expired(key):
                    self._remove_from_disk(key)
                    self.stats['misses'] += 1
                    return default
                
                # 加载到内存缓存
                self._set_memory_cache(key, disk_data)
                self.stats['hits'] += 1
                self.stats['disk_reads'] += 1
                return disk_data
            
            self.stats['misses'] += 1
            return default
    
    def set(self, 
            key: str, 
            data: Any, 
            ttl: int = None,
            persist: bool = False) -> bool:
        """
        设置缓存数据
        
        Args:
            key: 缓存键
            data: 缓存数据
            ttl: 过期时间（秒）
            persist: 是否持久化到磁盘
            
        Returns:
            success: 是否成功
        """
        with self.lock:
            try:
                # 设置内存缓存
                self._set_memory_cache(key, data, ttl)
                
                # 持久化到磁盘
                if persist:
                    self._save_to_disk(key, data, ttl)
                
                return True
                
            except Exception as e:
                print(f"❌ 缓存设置失败: {e}")
                return False
    
    def _set_memory_cache(self, key: str, data: Any, ttl: int = None):
        """设置内存缓存"""
        # 检查是否需要淘汰
        self._evict_if_needed()
        
        # 计算数据大小
        data_size = self._estimate_size(data)
        
        # 设置缓存
        self.memory_cache[key] = {
            'data': data,
            'size': data_size,
            'created_at': time.time(),
            'ttl': ttl or self.default_ttl
        }
        
        # 更新元数据
        self.cache_metadata[key] = {
            'created_at': datetime.now().isoformat(),
            'size': data_size,
            'ttl': ttl or self.default_ttl
        }
    
    def _evict_if_needed(self):
        """如果需要，执行缓存淘汰"""
        # 按数量淘汰
        while len(self.memory_cache) >= self.max_memory_items:
            self._evict_lru()
        
        # 按大小淘汰
        while self._get_total_size() > self.max_memory_size_mb * 1024 * 1024:
            self._evict_lru()
    
    def _evict_lru(self):
        """淘汰最近最少使用的缓存"""
        if not self.memory_cache:
            return
        
        # 移除第一个元素（最久未使用）
        key, _ = self.memory_cache.popitem(last=False)
        self.stats['evictions'] += 1
        
        # 更新元数据
        if key in self.cache_metadata:
            del self.cache_metadata[key]
    
    def _is_expired(self, key: str) -> bool:
        """检查缓存是否过期"""
        if key not in self.memory_cache:
            # 检查磁盘缓存元数据
            if key in self.cache_metadata:
                created_at = datetime.fromisoformat(self.cache_metadata[key]['created_at'])
                ttl = self.cache_metadata[key]['ttl']
                return datetime.now() > created_at + timedelta(seconds=ttl)
            return True
        
        cache_item = self.memory_cache[key]
        elapsed = time.time() - cache_item['created_at']
        return elapsed > cache_item['ttl']
    
    def _remove(self, key: str):
        """移除缓存"""
        if key in self.memory_cache:
            del self.memory_cache[key]
        
        if key in self.cache_metadata:
            del self.cache_metadata[key]
    
    def _estimate_size(self, data: Any) -> int:
        """估算数据大小（字节）"""
        if isinstance(data, pd.DataFrame):
            return data.memory_usage(deep=True).sum()
        elif isinstance(data, np.ndarray):
            return data.nbytes
        elif isinstance(data, (list, dict)):
            return len(pickle.dumps(data))
        else:
            return len(str(data))
    
    def _get_total_size(self) -> int:
        """获取缓存总大小"""
        return sum(item['size'] for item in self.memory_cache.values())
    
    def _save_to_disk(self, key: str, data: Any, ttl: int = None):
        """保存到磁盘"""
        try:
            # 生成文件路径
            file_path = self._get_disk_path(key)
            
            # 保存数据
            if isinstance(data, pd.DataFrame):
                data.to_parquet(file_path)
            else:
                with open(file_path, 'wb') as f:
                    pickle.dump(data, f)
            
            # 更新元数据
            self.cache_metadata[key]['disk_path'] = file_path
            
            # 保存元数据
            self._save_metadata()
            
            self.stats['disk_writes'] += 1
            
        except Exception as e:
            print(f"❌ 磁盘缓存保存失败: {e}")
    
    def _load_from_disk(self, key: str) -> Any:
        """从磁盘加载"""
        try:
            file_path = self._get_disk_path(key)
            
            if not os.path.exists(file_path):
                return None
            
            # 加载数据
            if file_path.endswith('.parquet'):
                data = pd.read_parquet(file_path)
            else:
                with open(file_path, 'rb') as f:
                    data = pickle.load(f)
            
            return data
            
        except Exception as e:
            print(f"❌ 磁盘缓存加载失败: {e}")
            return None
    
    def _remove_from_disk(self, key: str):
        """从磁盘移除"""
        try:
            file_path = self._get_disk_path(key)
            
            if os.path.exists(file_path):
                os.remove(file_path)
            
            if key in self.cache_metadata:
                del self.cache_metadata[key]
            
            self._save_metadata()
            
        except Exception as e:
            print(f"❌ 磁盘缓存移除失败: {e}")
    
    def _get_disk_path(self, key: str) -> str:
        """获取磁盘缓存路径"""
        # 使用哈希作为文件名
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.disk_cache_dir, f"{key_hash}.cache")
    
    def _save_metadata(self):
        """保存元数据"""
        metadata_path = os.path.join(self.disk_cache_dir, 'metadata.json')
        
        try:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.cache_metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 元数据保存失败: {e}")
    
    def _load_metadata(self):
        """加载元数据"""
        metadata_path = os.path.join(self.disk_cache_dir, 'metadata.json')
        
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    self.cache_metadata = json.load(f)
            except Exception as e:
                print(f"⚠️ 元数据加载失败: {e}")
                self.cache_metadata = {}
    
    def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            success: 是否成功
        """
        with self.lock:
            self._remove(key)
            self._remove_from_disk(key)
            return True
    
    def clear_memory(self):
        """清除内存缓存"""
        with self.lock:
            self.memory_cache.clear()
            print("✅ 内存缓存已清除")
    
    def clear_disk(self):
        """清除磁盘缓存"""
        with self.lock:
            try:
                for filename in os.listdir(self.disk_cache_dir):
                    if filename.endswith('.cache'):
                        file_path = os.path.join(self.disk_cache_dir, filename)
                        os.remove(file_path)
                
                self.cache_metadata.clear()
                self._save_metadata()
                
                print("✅ 磁盘缓存已清除")
                
            except Exception as e:
                print(f"❌ 磁盘缓存清除失败: {e}")
    
    def clear_all(self):
        """清除所有缓存"""
        self.clear_memory()
        self.clear_disk()
        print("✅ 所有缓存已清除")
    
    def cleanup_expired(self):
        """清理过期缓存"""
        with self.lock:
            expired_keys = []
            
            # 检查内存缓存
            for key in list(self.memory_cache.keys()):
                if self._is_expired(key):
                    expired_keys.append(key)
            
            # 检查磁盘缓存
            for key in list(self.cache_metadata.keys()):
                if self._is_expired(key):
                    expired_keys.append(key)
            
            # 删除过期缓存
            for key in expired_keys:
                self._remove(key)
                self._remove_from_disk(key)
            
            print(f"✅ 清理过期缓存: {len(expired_keys)} 项")
    
    def get_stats(self) -> Dict:
        """
        获取缓存统计信息
        
        Returns:
            stats: 统计信息
        """
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = self.stats['hits'] / total_requests if total_requests > 0 else 0
        
        stats = {
            'memory_items': len(self.memory_cache),
            'memory_size_mb': self._get_total_size() / 1024 / 1024,
            'disk_items': len([f for f in os.listdir(self.disk_cache_dir) if f.endswith('.cache')]),
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'hit_rate': hit_rate,
            'evictions': self.stats['evictions'],
            'disk_reads': self.stats['disk_reads'],
            'disk_writes': self.stats['disk_writes']
        }
        
        return stats
    
    def print_stats(self):
        """打印缓存统计"""
        stats = self.get_stats()
        
        print("\n" + "="*60)
        print("缓存统计")
        print("="*60)
        print(f"内存缓存项数: {stats['memory_items']}")
        print(f"内存缓存大小: {stats['memory_size_mb']:.2f} MB")
        print(f"磁盘缓存项数: {stats['disk_items']}")
        print(f"缓存命中率: {stats['hit_rate']:.2%}")
        print(f"命中次数: {stats['hits']}")
        print(f"未命中次数: {stats['misses']}")
        print(f"淘汰次数: {stats['evictions']}")
        print(f"磁盘读取次数: {stats['disk_reads']}")
        print(f"磁盘写入次数: {stats['disk_writes']}")
        print("="*60)
    
    def get_cache_keys(self) -> List[str]:
        """
        获取所有缓存键
        
        Returns:
            keys: 缓存键列表
        """
        all_keys = set(self.memory_cache.keys())
        all_keys.update(self.cache_metadata.keys())
        return list(all_keys)
    
    def get_cache_info(self, key: str) -> Dict:
        """
        获取缓存项信息
        
        Args:
            key: 缓存键
            
        Returns:
            info: 缓存信息
        """
        info = {
            'key': key,
            'exists': key in self.memory_cache or key in self.cache_metadata,
            'in_memory': key in self.memory_cache,
            'on_disk': key in self.cache_metadata and 'disk_path' in self.cache_metadata.get(key, {})
        }
        
        if key in self.memory_cache:
            cache_item = self.memory_cache[key]
            info['size'] = cache_item['size']
            info['created_at'] = datetime.fromtimestamp(cache_item['created_at']).isoformat()
            info['ttl'] = cache_item['ttl']
            info['is_expired'] = self._is_expired(key)
        
        if key in self.cache_metadata:
            metadata = self.cache_metadata[key]
            info['metadata'] = metadata
        
        return info
    
    def warmup(self, 
               data_loader,
               stock_codes: List[str],
               data_types: List[str],
               start_date: str,
               end_date: str):
        """
        预热缓存
        
        Args:
            data_loader: 数据加载器
            stock_codes: 股票代码列表
            data_types: 数据类型列表
            start_date: 开始日期
            end_date: 结束日期
        """
        print("预热缓存...")
        
        load_method_map = {
            'tick': data_loader.load_tick_data,
            'minute': data_loader.load_minute_data,
            'daily': data_loader.load_daily_data,
            'financial': data_loader.load_financial_data,
            'order_book': data_loader.load_order_book_data
        }
        
        for stock_code in stock_codes:
            for data_type in data_types:
                if data_type in load_method_map:
                    try:
                        key = f"{data_type}_{stock_code}_{start_date}_{end_date}"
                        
                        # 检查是否已缓存
                        if self.get(key) is not None:
                            continue
                        
                        # 加载数据
                        data = load_method_map[data_type](stock_code, start_date, end_date)
                        
                        # 缓存数据
                        if data is not None and len(data) > 0:
                            self.set(key, data, persist=True)
                            
                    except Exception as e:
                        print(f"  ⚠️ 预热失败 {stock_code} {data_type}: {e}")
        
        print("✅ 缓存预热完成")
    
    def export_cache_info(self, file_path: str):
        """
        导出缓存信息到文件
        
        Args:
            file_path: 文件路径
        """
        info = {
            'stats': self.get_stats(),
            'metadata': self.cache_metadata,
            'keys': self.get_cache_keys()
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 缓存信息已导出: {file_path}")
