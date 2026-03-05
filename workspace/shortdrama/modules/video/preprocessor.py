"""
视频预处理模块
负责视频解码、关键帧提取、音频分离
"""
import os
import cv2
import subprocess
import numpy as np
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class VideoPreprocessor:
    """视频预处理器"""
    
    def __init__(self, output_dir: str = "./output/temp"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def extract_keyframes(
        self, 
        video_path: str, 
        method: str = "uniform",
        num_frames: int = 32,
        scene_threshold: float = 30.0
    ) -> List[Dict]:
        """
        提取关键帧
        
        Args:
            video_path: 视频路径
            method: 提取方法 (uniform/scene/hybrid)
            num_frames: 目标帧数
            scene_threshold: 场景切换阈值
            
        Returns:
            关键帧信息列表
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频: {video_path}")
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = total_frames / fps if fps > 0 else 0
        
        logger.info(f"视频信息: {total_frames}帧, {fps}fps, {duration:.2f}秒")
        
        keyframes = []
        
        if method == "uniform":
            # 均匀采样
            indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)
            for idx in indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                if ret:
                    timestamp = idx / fps
                    keyframes.append({
                        "frame_idx": int(idx),
                        "timestamp": timestamp,
                        "image": frame,
                        "method": "uniform"
                    })
                    
        elif method == "scene":
            # 基于场景检测
            keyframes = self._scene_detection(cap, fps, scene_threshold)
            
        elif method == "hybrid":
            # 混合策略：场景切换点 + 均匀采样填充
            scene_frames = self._scene_detection(cap, fps, scene_threshold)
            if len(scene_frames) < num_frames:
                # 补充均匀采样
                remaining = num_frames - len(scene_frames)
                uniform_indices = np.linspace(0, total_frames - 1, remaining, dtype=int)
                for idx in uniform_indices:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                    ret, frame = cap.read()
                    if ret:
                        timestamp = idx / fps
                        keyframes.append({
                            "frame_idx": int(idx),
                            "timestamp": timestamp,
                            "image": frame,
                            "method": "uniform_fill"
                        })
            keyframes.extend(scene_frames)
            keyframes.sort(key=lambda x: x["frame_idx"])
            
        cap.release()
        logger.info(f"提取了 {len(keyframes)} 个关键帧")
        return keyframes
    
    def _scene_detection(
        self, 
        cap: cv2.VideoCapture, 
        fps: float, 
        threshold: float
    ) -> List[Dict]:
        """场景检测算法"""
        keyframes = []
        prev_frame = None
        frame_idx = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            if prev_frame is not None:
                # 计算帧间差异
                diff = cv2.absdiff(prev_frame, frame)
                diff_mean = np.mean(diff)
                
                if diff_mean > threshold:
                    timestamp = frame_idx / fps
                    keyframes.append({
                        "frame_idx": frame_idx,
                        "timestamp": timestamp,
                        "image": frame.copy(),
                        "method": "scene",
                        "diff_score": float(diff_mean)
                    })
                    
            prev_frame = frame.copy()
            frame_idx += 1
            
        return keyframes
    
    def extract_audio(
        self, 
        video_path: str, 
        output_format: str = "wav"
    ) -> str:
        """
        提取音频
        
        Args:
            video_path: 视频路径
            output_format: 输出格式
            
        Returns:
            音频文件路径
        """
        video_name = Path(video_path).stem
        audio_path = self.output_dir / f"{video_name}_audio.{output_format}"
        
        cmd = [
            "ffmpeg", "-i", video_path,
            "-vn",  # 不处理视频
            "-acodec", "pcm_s16le" if output_format == "wav" else "libmp3lame",
            "-ar", "16000",  # 16kHz采样率
            "-ac", "1",  # 单声道
            str(audio_path),
            "-y"  # 覆盖已存在文件
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"音频提取完成: {audio_path}")
            return str(audio_path)
        except subprocess.CalledProcessError as e:
            logger.error(f"音频提取失败: {e}")
            raise
    
    def get_video_info(self, video_path: str) -> Dict:
        """
        获取视频基本信息
        
        Args:
            video_path: 视频路径
            
        Returns:
            视频信息字典
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频: {video_path}")
        
        info = {
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": cap.get(cv2.CAP_PROP_FPS),
            "total_frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            "duration": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) / cap.get(cv2.CAP_PROP_FPS)
        }
        
        cap.release()
        return info
    
    def save_keyframes(self, keyframes: List[Dict], output_dir: str) -> List[str]:
        """
        保存关键帧到磁盘
        
        Args:
            keyframes: 关键帧列表
            output_dir: 输出目录
            
        Returns:
            保存的文件路径列表
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        saved_paths = []
        for i, kf in enumerate(keyframes):
            filename = f"frame_{kf['frame_idx']:06d}_{kf['timestamp']:.3f}s.jpg"
            filepath = output_path / filename
            cv2.imwrite(str(filepath), kf["image"])
            saved_paths.append(str(filepath))
            
        logger.info(f"保存了 {len(saved_paths)} 个关键帧到 {output_dir}")
        return saved_paths
    
    def create_video_segments(
        self, 
        video_path: str, 
        segments: List[Tuple[float, float]], 
        output_dir: str
    ) -> List[str]:
        """
        将视频切分为多个片段
        
        Args:
            video_path: 视频路径
            segments: 时间段列表 [(start, end), ...]
            output_dir: 输出目录
            
        Returns:
            片段文件路径列表
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        segment_paths = []
        for i, (start, end) in enumerate(segments):
            output_file = output_path / f"segment_{i:03d}_{start:.1f}_{end:.1f}.mp4"
            
            cmd = [
                "ffmpeg", "-i", video_path,
                "-ss", str(start),
                "-t", str(end - start),
                "-c", "copy",
                str(output_file),
                "-y"
            ]
            
            try:
                subprocess.run(cmd, check=True, capture_output=True)
                segment_paths.append(str(output_file))
            except subprocess.CalledProcessError as e:
                logger.error(f"片段 {i} 切割失败: {e}")
                
        return segment_paths
