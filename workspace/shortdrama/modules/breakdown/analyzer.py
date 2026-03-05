"""
拆片分析核心模块
基于Qwen2-VL-72B的视频理解与分析
"""
import os
import json
import torch
import logging
from typing import List, Dict, Optional, Union
from pathlib import Path
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)


class VideoBreakdownAnalyzer:
    """视频拆片分析器"""
    
    def __init__(
        self,
        model_path: str = "Qwen/Qwen2-VL-72B-Instruct",
        device_map: str = "auto",
        load_in_4bit: bool = True,
        max_memory: Optional[Dict] = None
    ):
        """
        初始化分析器
        
        Args:
            model_path: 模型路径或HuggingFace模型名
            device_map: 设备分配策略
            load_in_4bit: 是否使用4bit量化
            max_memory: 每GPU最大显存限制
        """
        self.model_path = model_path
        self.device_map = device_map
        self.load_in_4bit = load_in_4bit
        self.max_memory = max_memory or {
            0: "22GiB", 1: "22GiB", 2: "22GiB", 3: "22GiB"
        }
        
        self.model = None
        self.processor = None
        self._load_model()
    
    def _load_model(self):
        """加载Qwen2-VL模型"""
        try:
            from transformers import (
                Qwen2VLForConditionalGeneration, 
                AutoProcessor,
                BitsAndBytesConfig
            )
            
            logger.info(f"正在加载模型: {self.model_path}")
            
            # 4bit量化配置
            quantization_config = None
            if self.load_in_4bit:
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.bfloat16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )
            
            # 加载处理器
            self.processor = AutoProcessor.from_pretrained(
                self.model_path,
                trust_remote_code=True
            )
            
            # 加载模型
            self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                self.model_path,
                torch_dtype=torch.bfloat16,
                device_map=self.device_map,
                max_memory=self.max_memory,
                quantization_config=quantization_config,
                trust_remote_code=True
            )
            
            logger.info("模型加载完成")
            
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            raise
    
    def analyze_video_structure(
        self, 
        video_path: str,
        keyframes: Optional[List[Dict]] = None
    ) -> Dict:
        """
        分析视频结构
        
        Args:
            video_path: 视频路径
            keyframes: 预提取的关键帧列表
            
        Returns:
            视频结构分析结果
        """
        if keyframes is None:
            from modules.video.preprocessor import VideoPreprocessor
            preprocessor = VideoPreprocessor()
            keyframes = preprocessor.extract_keyframes(
                video_path, 
                method="hybrid", 
                num_frames=32
            )
        
        # 构建提示词
        prompt = self._build_structure_prompt()
        
        # 准备输入
        images = [kf["image"] for kf in keyframes]
        timestamps = [kf["timestamp"] for kf in keyframes]
        
        # 调用模型分析
        result = self._inference(images, prompt)
        
        # 解析结果
        analysis = self._parse_structure_result(result, timestamps)
        
        return analysis
    
    def analyze_shot_language(
        self,
        video_segments: List[str],
        segment_info: List[Dict]
    ) -> Dict:
        """
        分析镜头语言
        
        Args:
            video_segments: 视频片段路径列表
            segment_info: 片段信息列表
            
        Returns:
            镜头语言分析结果
        """
        results = []
        
        for i, (segment_path, info) in enumerate(zip(video_segments, segment_info)):
            # 提取片段关键帧
            from modules.video.preprocessor import VideoPreprocessor
            preprocessor = VideoPreprocessor()
            frames = preprocessor.extract_keyframes(
                segment_path,
                method="uniform",
                num_frames=8
            )
            
            prompt = self._build_shot_language_prompt(info)
            images = [f["image"] for f in frames]
            
            result = self._inference(images, prompt)
            results.append({
                "segment_id": i,
                "info": info,
                "analysis": result
            })
        
        # 汇总分析
        summary = self._summarize_shot_analysis(results)
        return summary
    
    def analyze_audio_visual(
        self,
        video_path: str,
        audio_path: str,
        transcript: Optional[str] = None
    ) -> Dict:
        """
        分析音视频内容
        
        Args:
            video_path: 视频路径
            audio_path: 音频路径
            transcript: 转录文本（可选）
            
        Returns:
            音视频分析结果
        """
        # 提取关键帧
        from modules.video.preprocessor import VideoPreprocessor
        preprocessor = VideoPreprocessor()
        keyframes = preprocessor.extract_keyframes(
            video_path,
            method="uniform",
            num_frames=16
        )
        
        # 构建提示词
        prompt = self._build_audio_visual_prompt(transcript)
        images = [kf["image"] for kf in keyframes]
        
        result = self._inference(images, prompt)
        
        return {
            "audio_visual_analysis": result,
            "transcript": transcript
        }
    
    def comprehensive_analysis(
        self,
        video_path: str,
        include_audio: bool = True
    ) -> Dict:
        """
        综合拆片分析
        
        Args:
            video_path: 视频路径
            include_audio: 是否包含音频分析
            
        Returns:
            完整分析报告
        """
        logger.info(f"开始综合分析: {video_path}")
        
        # 1. 视频预处理
        from modules.video.preprocessor import VideoPreprocessor
        preprocessor = VideoPreprocessor()
        
        video_info = preprocessor.get_video_info(video_path)
        keyframes = preprocessor.extract_keyframes(
            video_path,
            method="hybrid",
            num_frames=32
        )
        
        # 2. 结构分析
        structure = self.analyze_video_structure(video_path, keyframes)
        
        # 3. 镜头语言分析
        segments = structure.get("segments", [])
        segment_files = preprocessor.create_video_segments(
            video_path,
            [(s["start"], s["end"]) for s in segments],
            "./output/segments"
        )
        shot_language = self.analyze_shot_language(segment_files, segments)
        
        # 4. 音视频分析
        audio_visual = {}
        if include_audio:
            audio_path = preprocessor.extract_audio(video_path)
            # TODO: 调用Whisper进行语音识别
            transcript = None
            audio_visual = self.analyze_audio_visual(
                video_path, audio_path, transcript
            )
        
        # 5. 汇总报告
        report = {
            "video_info": video_info,
            "structure_analysis": structure,
            "shot_language": shot_language,
            "audio_visual": audio_visual,
            "keyframes_count": len(keyframes)
        }
        
        logger.info("综合分析完成")
        return report
    
    def _inference(
        self, 
        images: List[np.ndarray], 
        prompt: str,
        max_new_tokens: int = 2048
    ) -> str:
        """
        模型推理
        
        Args:
            images: 图像列表
            prompt: 提示词
            max_new_tokens: 最大生成token数
            
        Returns:
            模型输出文本
        """
        # 转换图像格式
        pil_images = []
        for img in images:
            if isinstance(img, np.ndarray):
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                pil_images.append(Image.fromarray(img))
            else:
                pil_images.append(img)
        
        # 构建对话
        messages = [
            {
                "role": "user",
                "content": [
                    *[{"type": "image", "image": img} for img in pil_images],
                    {"type": "text", "text": prompt}
                ]
            }
        ]
        
        # 准备输入
        text = self.processor.apply_chat_template(
            messages, 
            tokenize=False, 
            add_generation_prompt=True
        )
        
        inputs = self.processor(
            text=[text],
            images=pil_images,
            return_tensors="pt",
            padding=True
        ).to(self.model.device)
        
        # 生成
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=0.7,
                top_p=0.9
            )
        
        # 解码输出
        generated_ids = outputs[:, inputs.input_ids.shape[1]:]
        result = self.processor.batch_decode(
            generated_ids, 
            skip_special_tokens=True
        )[0]
        
        return result
    
    def _build_structure_prompt(self) -> str:
        """构建视频结构分析提示词"""
        return """分析这个视频的结构，输出以下信息：

1. 视频分段：按时间线列出主要段落（格式：开始时间-结束时间 内容描述）
2. 场景识别：每个场景的主要内容和作用
3. 叙事节奏：标注高潮、转折、铺垫等节点的时间点
4. 情感曲线：描述情感基调的变化趋势

请以JSON格式输出：
{
  "segments": [
    {"start": 0.0, "end": 30.5, "description": "开场介绍", "type": "intro"}
  ],
  "scenes": [...],
  "pacing": [...],
  "emotion_curve": [...]
}"""
    
    def _build_shot_language_prompt(self, segment_info: Dict) -> str:
        """构建镜头语言分析提示词"""
        return f"""分析这个视频片段的镜头语言：

片段信息：{json.dumps(segment_info, ensure_ascii=False)}

请分析：
1. 景别分布（特写/近景/中景/全景/远景的比例）
2. 镜头运动（推/拉/摇/移/跟/升降）
3. 构图特点（对称/三分法/框架构图等）
4. 转场方式（硬切/淡入淡出/叠化/特效）
5. 视觉风格（色调/光影/滤镜效果）

以JSON格式输出。"""
    
    def _build_audio_visual_prompt(self, transcript: Optional[str]) -> str:
        """构建音视频分析提示词"""
        transcript_text = f"\n转录文本：{transcript}" if transcript else ""
        return f"""分析这个视频的音视频内容：{transcript_text}

请分析：
1. 人物分析：出场人物、表情变化、动作特征
2. 物体识别：关键道具、场景元素
3. 音频情绪：背景音乐氛围、音效使用
4. 声画关系：音画同步、对位、对比等手法
5. 内容主题：核心主题、关键词、叙事逻辑

以JSON格式输出。"""
    
    def _parse_structure_result(
        self, 
        result: str, 
        timestamps: List[float]
    ) -> Dict:
        """解析结构分析结果"""
        try:
            # 尝试直接解析JSON
            data = json.loads(result)
            return data
        except json.JSONDecodeError:
            # 如果模型输出不是标准JSON，进行后处理
            logger.warning("模型输出不是标准JSON，进行后处理")
            return {
                "raw_output": result,
                "timestamps": timestamps,
                "parsed": False
            }
    
    def _summarize_shot_analysis(self, results: List[Dict]) -> Dict:
        """汇总镜头语言分析"""
        summary = {
            "total_segments": len(results),
            "shot_types": {},
            "movements": {},
            "transitions": {}
        }
        
        for r in results:
            # 统计各类指标
            analysis = r.get("analysis", "")
            # TODO: 更精细的解析逻辑
            
        return summary
