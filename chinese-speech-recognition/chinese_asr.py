#!/usr/bin/env python3
"""
中文语音识别 - 支持Google Speech API和Vosk离线识别
针对中文优化，支持钉钉OGG格式自动转换
"""

import os
import json
import time
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import speech_recognition as sr

class RecognitionMode(Enum):
    """识别模式"""
    GOOGLE = "google"      # Google Speech API (在线，高精度)
    VOSK = "vosk"         # Vosk离线识别 (本地，无需网络)
    HYBRID = "hybrid"     # 混合模式，自动选择

@dataclass
class RecognitionResult:
    """识别结果"""
    text: str
    confidence: float
    mode: RecognitionMode
    processing_time: float
    language: str = "zh-CN"
    error: Optional[str] = None

@dataclass
class ASRConfig:
    """ASR配置"""
    mode: RecognitionMode = RecognitionMode.HYBRID
    language: str = "zh-CN"
    proxy: Optional[str] = None
    vosk_model_path: Optional[str] = None
    google_api_key: Optional[str] = None
    auto_convert_formats: bool = True
    sample_rate: int = 16000
    channels: int = 1

class ChineseSpeechRecognizer:
    """中文语音识别器"""
    
    def __init__(self, config: ASRConfig = None):
        """
        初始化中文语音识别器
        
        Args:
            config: ASR配置，如果为None使用默认配置
        """
        self.config = config or ASRConfig()
        self.recognizer = sr.Recognizer()
        
        # 初始化Vosk模型（如果配置了）
        self.vosk_model = None
        if (self.config.mode in [RecognitionMode.VOSK, RecognitionMode.HYBRID] and 
            self.config.vosk_model_path):
            self._init_vosk_model()
        
        # 设置代理（如果配置了）
        if self.config.proxy:
            self._setup_proxy()
    
    def _init_vosk_model(self):
        """初始化Vosk模型"""
        try:
            import vosk
            if os.path.exists(self.config.vosk_model_path):
                self.vosk_model = vosk.Model(self.config.vosk_model_path)
                print(f"✅ Vosk模型加载成功: {self.config.vosk_model_path}")
            else:
                print(f"⚠️ Vosk模型路径不存在: {self.config.vosk_model_path}")
        except ImportError:
            print("⚠️ Vosk未安装，离线识别不可用")
            print("安装: pip install vosk")
        except Exception as e:
            print(f"❌ Vosk模型加载失败: {e}")
    
    def _setup_proxy(self):
        """设置代理"""
        os.environ['HTTP_PROXY'] = self.config.proxy
        os.environ['HTTPS_PROXY'] = self.config.proxy
        print(f"✅ 代理设置: {self.config.proxy}")
    
    def convert_audio_format(self, input_path: str, output_format: str = "wav") -> str:
        """
        转换音频格式
        
        Args:
            input_path: 输入文件路径
            output_format: 输出格式 (wav, flac等)
            
        Returns:
            转换后的文件路径
        """
        # 检查是否需要转换
        input_ext = Path(input_path).suffix.lower()
        if input_ext in ['.wav', '.flac'] and not self.config.auto_convert_formats:
            return input_path
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix=f'.{output_format}', delete=False) as tmp:
            output_path = tmp.name
        
        # 使用ffmpeg转换
        cmd = [
            'ffmpeg', '-i', input_path,
            '-ar', str(self.config.sample_rate),
            '-ac', str(self.config.channels),
            '-y', output_path
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"✅ 音频格式转换: {input_path} -> {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            print(f"❌ 音频转换失败: {e}")
            # 如果转换失败，返回原文件
            return input_path
        except FileNotFoundError:
            print("❌ ffmpeg未安装，无法转换音频格式")
            return input_path
    
    def recognize_with_google(self, audio_path: str) -> RecognitionResult:
        """
        使用Google Speech API识别
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            识别结果
        """
        start_time = time.time()
        
        try:
            # 加载音频文件
            with sr.AudioFile(audio_path) as source:
                audio = self.recognizer.record(source)
            
            # 识别
            text = self.recognizer.recognize_google(
                audio,
                language=self.config.language,
                key=self.config.google_api_key
            )
            
            processing_time = time.time() - start_time
            
            return RecognitionResult(
                text=text,
                confidence=0.9,  # Google API不返回置信度
                mode=RecognitionMode.GOOGLE,
                processing_time=processing_time,
                language=self.config.language
            )
            
        except sr.UnknownValueError:
            processing_time = time.time() - start_time
            return RecognitionResult(
                text="",
                confidence=0.0,
                mode=RecognitionMode.GOOGLE,
                processing_time=processing_time,
                language=self.config.language,
                error="无法识别音频"
            )
        except sr.RequestError as e:
            processing_time = time.time() - start_time
            return RecognitionResult(
                text="",
                confidence=0.0,
                mode=RecognitionMode.GOOGLE,
                processing_time=processing_time,
                language=self.config.language,
                error=f"Google API请求失败: {e}"
            )
        except Exception as e:
            processing_time = time.time() - start_time
            return RecognitionResult(
                text="",
                confidence=0.0,
                mode=RecognitionMode.GOOGLE,
                processing_time=processing_time,
                language=self.config.language,
                error=f"识别过程错误: {e}"
            )
    
    def recognize_with_vosk(self, audio_path: str) -> RecognitionResult:
        """
        使用Vosk离线识别
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            识别结果
        """
        start_time = time.time()
        
        if not self.vosk_model:
            processing_time = time.time() - start_time
            return RecognitionResult(
                text="",
                confidence=0.0,
                mode=RecognitionMode.VOSK,
                processing_time=processing_time,
                language=self.config.language,
                error="Vosk模型未加载"
            )
        
        try:
            import vosk
            import wave
            import json as json_lib
            
            # 读取音频文件
            wf = wave.open(audio_path, "rb")
            
            # 检查音频格式
            if wf.getnchannels() != self.config.channels:
                print(f"⚠️ 音频声道数不匹配: {wf.getnchannels()} != {self.config.channels}")
            
            if wf.getframerate() != self.config.sample_rate:
                print(f"⚠️ 采样率不匹配: {wf.getframerate()} != {self.config.sample_rate}")
            
            # 创建识别器
            rec = vosk.KaldiRecognizer(self.vosk_model, wf.getframerate())
            rec.SetWords(True)
            
            # 识别
            results = []
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    result = json_lib.loads(rec.Result())
                    results.append(result.get("text", ""))
            
            # 获取最终结果
            final_result = json_lib.loads(rec.FinalResult())
            final_text = final_result.get("text", "")
            
            # 合并所有结果
            all_text = " ".join(results + [final_text])
            all_text = all_text.strip()
            
            processing_time = time.time() - start_time
            
            return RecognitionResult(
                text=all_text,
                confidence=0.8,  # Vosk置信度估算
                mode=RecognitionMode.VOSK,
                processing_time=processing_time,
                language=self.config.language
            )
            
        except ImportError:
            processing_time = time.time() - start_time
            return RecognitionResult(
                text="",
                confidence=0.0,
                mode=RecognitionMode.VOSK,
                processing_time=processing_time,
                language=self.config.language,
                error="Vosk未安装"
            )
        except Exception as e:
            processing_time = time.time() - start_time
            return RecognitionResult(
                text="",
                confidence=0.0,
                mode=RecognitionMode.VOSK,
                processing_time=processing_time,
                language=self.config.language,
                error=f"Vosk识别失败: {e}"
            )
    
    def recognize_audio(self, audio_path: str) -> RecognitionResult:
        """
        识别音频文件
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            识别结果
        """
        print(f"🔍 开始识别: {audio_path}")
        
        # 检查文件是否存在
        if not os.path.exists(audio_path):
            return RecognitionResult(
                text="",
                confidence=0.0,
                mode=self.config.mode,
                processing_time=0.0,
                language=self.config.language,
                error=f"文件不存在: {audio_path}"
            )
        
        # 自动转换格式（如果需要）
        if self.config.auto_convert_formats:
            converted_path = self.convert_audio_format(audio_path, "wav")
            # 如果是临时文件，需要后续清理
            is_temp = converted_path != audio_path
        else:
            converted_path = audio_path
            is_temp = False
        
        try:
            # 根据模式选择识别方法
            if self.config.mode == RecognitionMode.GOOGLE:
                result = self.recognize_with_google(converted_path)
            elif self.config.mode == RecognitionMode.VOSK:
                result = self.recognize_with_vosk(converted_path)
            elif self.config.mode == RecognitionMode.HYBRID:
                # 尝试Google，失败则使用Vosk
                google_result = self.recognize_with_google(converted_path)
                if google_result.error or not google_result.text:
                    print("Google识别失败，尝试Vosk...")
                    result = self.recognize_with_vosk(converted_path)
                    result.mode = RecognitionMode.HYBRID
                else:
                    result = google_result
                    result.mode = RecognitionMode.HYBRID
            else:
                result = RecognitionResult(
                    text="",
                    confidence=0.0,
                    mode=self.config.mode,
                    processing_time=0.0,
                    language=self.config.language,
                    error=f"未知识别模式: {self.config.mode}"
                )
            
            # 清理临时文件
            if is_temp and os.path.exists(converted_path):
                os.remove(converted_path)
            
            # 输出结果
            if result.text:
                print(f"✅ 识别成功 [{result.mode.value}]: {result.text}")
                print(f"   置信度: {result.confidence:.2f}, 耗时: {result.processing_time:.2f}s")
            elif result.error:
                print(f"❌ 识别失败: {result.error}")
            
            return result
            
        except Exception as e:
            # 清理临时文件
            if is_temp and os.path.exists(converted_path):
                os.remove(converted_path)
            
            return RecognitionResult(
                text="",
                confidence=0.0,
                mode=self.config.mode,
                processing_time=time.time() - start_time,
                language=self.config.language,
                error=f"识别过程异常: {e}"
            )
    
    def recognize_dingtalk_voice(self, ogg_path: str) -> RecognitionResult:
        """
        专门处理钉钉语音文件
        
        Args:
            ogg_path: 钉钉OGG文件路径
            
        Returns:
            识别结果
        """
        print(f"🎯 处理钉钉语音: {ogg_path}")
        
        # 钉钉语音通常是OGG/Opus格式，需要转换
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            wav_path = tmp.name
        
        # 转换OGG到WAV
        cmd = [
            'ffmpeg', '-i', ogg_path,
            '-ar', '16000',
            '-ac', '1',
            '-acodec', 'pcm_s16le',
            '-y', wav_path
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"✅ 钉钉OGG转换完成: {ogg_path} -> {wav_path}")
            
            # 识别转换后的文件
            result = self.recognize_audio(wav_path)
            
            # 清理临时文件
            os.remove(wav_path)
            
            return result
            
        except subprocess.CalledProcessError as e:
            print(f"❌ 钉钉OGG转换失败: {e}")
            # 尝试直接识别（可能失败）
            return self.recognize_audio(ogg_path)
        except Exception as e:
            print(f"❌ 钉钉语音处理异常: {e}")
            if os.path.exists(wav_path):
                os.remove(wav_path)
            return RecognitionResult(
                text="",
                confidence=0.0,
                mode=self.config.mode,
                processing_time=0.0,
                language=self.config.language,
                error=f"钉钉语音处理失败: {e}"
            )


# 命令行接口
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='中文语音识别工具')
    parser.add_argument('--audio', required=True, help='音频文件路径')
    parser.add_argument('--mode', choices=['google', 'vosk', 'hybrid'], 
                       default='hybrid', help='识别模式')
    parser.add_argument('--proxy', help='代理服务器')
    parser.add_argument('--vosk-model', help='Vosk模型路径')
    parser.add_argument('--google-key', help='Google API Key')
    parser.add_argument('--dingtalk', action='store_true', help='处理钉钉OGG格式')
    
    args = parser.parse_args()
    
    # 创建配置
    config = ASRConfig(
        mode=RecognitionMode(args.mode),
        proxy=args.proxy,
        vosk_model_path=args.vosk_model,
        google_api_key=args.google_key
    )
    
    # 创建识别器
    recognizer = ChineseSpeechRecognizer(config)
    
    # 识别
    if args.dingtalk:
        result = recognizer.recognize_dingtalk_voice(args.audio)
    else:
        result = recognizer.recognize_audio(args.audio)
    
    # 输出结果
    if result.text:
        print("\n" + "="*50)
        print("识别结果:")
        print(f"  文本: {result.text}")
        print(f"  模式: {result.mode.value}")
        print(f"  置信度: {result.confidence:.2f}")
        print(f"  耗时: {result.processing_time:.2f}秒")
        print(f"  语言: {result.language}")
        print("="*50)
        
        # 保存结果到文件
        output_file = Path(args.audio).with_suffix('.txt')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.text)
        print(f"✅ 结果已保存: {output_file}")
    else:
        print(f"❌ 识别失败: {result.error}")