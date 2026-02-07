#!/usr/bin/env python3
"""
百度AI客户端 - 封装百度AI各种服务
支持语音合成(TTS)、OCR识别、文心一格等
"""

import os
import json
import base64
import requests
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class BaiduAIService(Enum):
    """百度AI服务类型"""
    TTS = "tts"           # 语音合成
    OCR = "ocr"          # 文字识别
    WENXIN = "wenxin"    # 文心一格
    NLP = "nlp"          # 自然语言处理
    IMAGE = "image"      # 图像识别

@dataclass
class TTSConfig:
    """TTS配置"""
    text: str
    speed: int = 5        # 语速 0-15
    pitch: int = 5        # 音调 0-15
    volume: int = 5       # 音量 0-15
    person: int = 0       # 发音人 0-女声 1-男声 3-情感男声 4-情感女声
    format: str = "mp3"   # 音频格式 mp3/pcm/wav

@dataclass
class OCRConfig:
    """OCR配置"""
    image_data: bytes
    language_type: str = "CHN_ENG"  # 语言类型
    detect_direction: bool = False  # 检测图像朝向
    detect_language: bool = False   # 检测语言
    paragraph: bool = False         # 输出段落信息

@dataclass
class WenxinConfig:
    """文心一格配置"""
    prompt: str
    style: str = "默认"
    size: str = "1024x1024"
    steps: int = 30
    guidance: float = 7.5

class BaiduAIClient:
    """百度AI客户端"""
    
    def __init__(self, api_key: str = None, secret_key: str = None, 
                 proxy: str = None, cache_tokens: bool = True):
        """
        初始化百度AI客户端
        
        Args:
            api_key: 百度AI API Key
            secret_key: 百度AI Secret Key
            proxy: 代理服务器
            cache_tokens: 是否缓存Access Token
        """
        self.api_key = api_key or os.getenv('BAIDU_API_KEY')
        self.secret_key = secret_key or os.getenv('BAIDU_SECRET_KEY')
        self.proxy = proxy
        self.cache_tokens = cache_tokens
        
        # Token缓存
        self._tokens = {}
        self._token_expiry = {}
        
        # 创建会话
        self.session = self._create_session()
        
        # 服务端点
        self.endpoints = {
            BaiduAIService.TTS: "https://tsn.baidubce.com/text2audio",
            BaiduAIService.OCR_GENERAL: "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic",
            BaiduAIService.OCR_ACCURATE: "https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic",
            BaiduAIService.WENXIN: "https://aip.baidubce.com/rpc/2.0/ernievilg/v1/txt2img",
            BaiduAIService.TOKEN: "https://aip.baidubce.com/oauth/2.0/token"
        }
    
    def _create_session(self):
        """创建HTTP会话"""
        session = requests.Session()
        if self.proxy:
            session.proxies = {
                'http': self.proxy,
                'https': self.proxy
            }
        
        # 设置通用请求头
        session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        return session
    
    def get_access_token(self, service: BaiduAIService = None) -> str:
        """
        获取Access Token
        
        Args:
            service: 服务类型，用于不同服务的Token
            
        Returns:
            Access Token
        """
        # 检查缓存
        cache_key = service.value if service else 'default'
        if (self.cache_tokens and cache_key in self._tokens and 
            cache_key in self._token_expiry and 
            time.time() < self._token_expiry[cache_key]):
            return self._tokens[cache_key]
        
        # 获取新Token
        params = {
            'grant_type': 'client_credentials',
            'client_id': self.api_key,
            'client_secret': self.secret_key
        }
        
        # 添加服务范围（如果需要）
        if service == BaiduAIService.TTS:
            params['scope'] = 'audio_tts_post'
        elif service == BaiduAIService.OCR:
            params['scope'] = 'brain_ocr_general_basic'
        elif service == BaiduAIService.WENXIN:
            params['scope'] = 'brain_all_scope'
        
        response = self.session.post(self.endpoints[BaiduAIService.TOKEN], data=params)
        
        if response.status_code != 200:
            raise ValueError(f"获取Token失败: {response.status_code} - {response.text}")
        
        data = response.json()
        
        if 'error' in data:
            raise ValueError(f"百度AI错误: {data.get('error_description', '未知错误')}")
        
        access_token = data['access_token']
        expires_in = data['expires_in']
        
        # 缓存Token（提前5分钟过期）
        if self.cache_tokens:
            self._tokens[cache_key] = access_token
            self._token_expiry[cache_key] = time.time() + expires_in - 300
        
        return access_token
    
    def text_to_speech(self, config: TTSConfig) -> Tuple[bytes, str]:
        """
        文本转语音
        
        Args:
            config: TTS配置
            
        Returns:
            (音频数据, 使用的提示词)
        """
        access_token = self.get_access_token(BaiduAIService.TTS)
        
        params = {
            'tex': config.text,
            'tok': access_token,
            'cuid': 'baidu_tts_client',
            'ctp': '1',
            'lan': 'zh',
            'spd': str(config.speed),
            'pit': str(config.pitch),
            'vol': str(config.volume),
            'per': str(config.person)
        }
        
        # 设置音频格式
        if config.format == 'mp3':
            params['aue'] = '3'
        elif config.format == 'pcm':
            params['aue'] = '4'
        elif config.format == 'wav':
            params['aue'] = '5'
        
        response = self.session.post(self.endpoints[BaiduAIService.TTS], data=params)
        
        # 检查是否是错误响应
        if response.headers.get('Content-Type', '').startswith('application/json'):
            error_data = response.json()
            raise ValueError(f"TTS错误: {error_data.get('err_msg', '未知错误')}")
        
        return response.content, config.text
    
    def ocr_general(self, config: OCRConfig) -> List[str]:
        """
        通用文字识别
        
        Args:
            config: OCR配置
            
        Returns:
            识别出的文字列表
        """
        access_token = self.get_access_token(BaiduAIService.OCR)
        
        # 编码图片
        image_base64 = base64.b64encode(config.image_data).decode('utf-8')
        
        params = {
            'access_token': access_token,
            'image': image_base64,
            'language_type': config.language_type,
            'detect_direction': 'true' if config.detect_direction else 'false',
            'detect_language': 'true' if config.detect_language else 'false',
            'paragraph': 'true' if config.paragraph else 'false'
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        response = self.session.post(
            self.endpoints[BaiduAIService.OCR_GENERAL],
            data=params,
            headers=headers
        )
        
        data = response.json()
        
        if 'error_code' in data:
            raise ValueError(f"OCR错误 {data['error_code']}: {data.get('error_msg', '未知错误')}")
        
        # 提取文字
        words = []
        for item in data.get('words_result', []):
            words.append(item.get('words', ''))
        
        return words
    
    def ocr_accurate(self, config: OCRConfig) -> List[str]:
        """
        高精度文字识别
        
        Args:
            config: OCR配置
            
        Returns:
            识别出的文字列表
        """
        access_token = self.get_access_token(BaiduAIService.OCR)
        
        # 编码图片
        image_base64 = base64.b64encode(config.image_data).decode('utf-8')
        
        params = {
            'access_token': access_token,
            'image': image_base64,
            'language_type': config.language_type,
            'detect_direction': 'true' if config.detect_direction else 'false',
            'detect_language': 'true' if config.detect_language else 'false',
            'paragraph': 'true' if config.paragraph else 'false'
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        response = self.session.post(
            self.endpoints[BaiduAIService.OCR_ACCURATE],
            data=params,
            headers=headers
        )
        
        data = response.json()
        
        if 'error_code' in data:
            raise ValueError(f"OCR高精度错误 {data['error_code']}: {data.get('error_msg', '未知错误')}")
        
        # 提取文字
        words = []
        for item in data.get('words_result', []):
            words.append(item.get('words', ''))
        
        return words
    
    def wenxin_image_generate(self, config: WenxinConfig) -> bytes:
        """
        文心一格图片生成
        
        Args:
            config: 文心一格配置
            
        Returns:
            生成的图片数据
        """
        access_token = self.get_access_token(BaiduAIService.WENXIN)
        
        params = {
            'access_token': access_token,
            'text': config.prompt,
            'style': config.style,
            'resolution': config.size,
            'num': 1,
            'steps': config.steps,
            'guidance_scale': config.guidance
        }
        
        response = self.session.post(self.endpoints[BaiduAIService.WENXIN], json=params)
        data = response.json()
        
        if 'error_code' in data:
            raise ValueError(f"文心一格错误 {data['error_code']}: {data.get('error_msg', '未知错误')}")
        
        # 解码Base64图片
        if 'data' in data and 'image' in data['data']:
            image_data = base64.b64decode(data['data']['image'])
            return image_data
        else:
            raise ValueError("文心一格响应格式错误")
    
    def test_connection(self) -> bool:
        """
        测试连接
        
        Returns:
            连接是否成功
        """
        try:
            # 尝试获取Token
            token = self.get_access_token()
            return bool(token)
        except Exception as e:
            print(f"连接测试失败: {e}")
            return False


# 命令行接口
if __name__ == "__main__":
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='百度AI客户端命令行工具')
    parser.add_argument('--api-key', help='百度AI API Key')
    parser.add_argument('--secret-key', help='百度AI Secret Key')
    parser.add_argument('--proxy', help='代理服务器')
    
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # TTS命令
    tts_parser = subparsers.add_parser('tts', help='文本转语音')
    tts_parser.add_argument('--text', required=True, help='要转换的文本')
    tts_parser.add_argument('--output', default='output.mp3', help='输出文件')
    tts_parser.add_argument('--speed', type=int, default=5, help='语速 0-15')
    tts_parser.add_argument('--person', type=int, default=0, help='发音人 0-女声 1-男声')
    
    # OCR命令
    ocr_parser = subparsers.add_parser('ocr', help='文字识别')
    ocr_parser.add_argument('--image', required=True, help='图片文件路径')
    ocr_parser.add_argument('--accurate', action='store_true', help='使用高精度识别')
    
    # 文心一格命令
    wenxin_parser = subparsers.add_parser('wenxin', help='文心一格图片生成')
    wenxin_parser.add_argument('--prompt', required=True, help='提示词')
    wenxin_parser.add_argument('--output', default='output.png', help='输出文件')
    wenxin_parser.add_argument('--size', default='1024x1024', help='图片尺寸')
    
    args = parser.parse_args()
    
    # 创建客户端
    client = BaiduAIClient(
        api_key=args.api_key,
        secret_key=args.secret_key,
        proxy=args.proxy
    )
    
    try:
        if args.command == 'tts':
            print("执行TTS...")
            config = TTSConfig(
                text=args.text,
                speed=args.speed,
                person=args.person
            )
            audio_data, _ = client.text_to_speech(config)
            with open(args.output, 'wb') as f:
                f.write(audio_data)
            print(f"语音文件已保存: {args.output}")
            
        elif args.command == 'ocr':
            print("执行OCR...")
            with open(args.image, 'rb') as f:
                image_data = f.read()
            config = OCRConfig(image_data=image_data)
            
            if args.accurate:
                words = client.ocr_accurate(config)
                print("高精度OCR结果:")
            else:
                words = client.ocr_general(config)
                print("通用OCR结果:")
            
            for i, word in enumerate(words, 1):
                print(f"{i}. {word}")
                
        elif args.command == 'wenxin':
            print("执行文心一格...")
            config = WenxinConfig(
                prompt=args.prompt,
                size=args.size
            )
            image_data = client.wenxin_image_generate(config)
            with open(args.output, 'wb') as f:
                f.write(image_data)
            print(f"图片已保存: {args.output}")
            
        else:
            # 测试连接
            print("测试百度AI连接...")
            if client.test_connection():
                print("✅ 连接成功!")
            else:
                print("❌ 连接失败")
                
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)