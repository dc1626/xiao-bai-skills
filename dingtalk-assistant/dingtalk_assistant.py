#!/usr/bin/env python3
"""
钉钉助手 - 钉钉机器人集成工具
提供钉钉消息发送、用户管理、API调用等功能
"""

import os
import json
import requests
from typing import Dict, List, Optional
from datetime import datetime

class DingTalkAssistant:
    """钉钉机器人助手类"""
    
    def __init__(self, access_token: str = None, proxy: str = None):
        """
        初始化钉钉助手
        
        Args:
            access_token: 钉钉Access Token，如果为None则从环境变量读取
            proxy: 代理服务器地址，格式: http://host:port
        """
        self.access_token = access_token or os.getenv('DINGTALK_ACCESS_TOKEN')
        self.base_url = "https://api.dingtalk.com/v1.0"
        self.proxy = proxy
        self.session = self._create_session()
        
    def _create_session(self):
        """创建HTTP会话"""
        session = requests.Session()
        if self.proxy:
            session.proxies = {
                'http': self.proxy,
                'https': self.proxy
            }
        return session
    
    def get_access_token(self, client_id: str, client_secret: str) -> str:
        """
        获取钉钉Access Token
        
        Args:
            client_id: 钉钉应用Client ID
            client_secret: 钉钉应用Client Secret
            
        Returns:
            Access Token字符串
        """
        url = f"{self.base_url}/oauth2/accessToken"
        data = {
            "appKey": client_id,
            "appSecret": client_secret
        }
        
        response = self.session.post(url, json=data)
        response.raise_for_status()
        
        result = response.json()
        self.access_token = result.get('accessToken')
        return self.access_token
    
    def send_text_message(self, user_id: str, content: str, 
                         robot_code: str = None) -> Dict:
        """
        发送文本消息
        
        Args:
            user_id: 钉钉用户ID（员工数字ID）
            content: 消息内容
            robot_code: 机器人Code，如果为None则从环境变量读取
            
        Returns:
            发送结果
        """
        if not self.access_token:
            raise ValueError("Access Token未设置，请先调用get_access_token或设置环境变量")
            
        robot_code = robot_code or os.getenv('DINGTALK_ROBOT_CODE')
        if not robot_code:
            raise ValueError("机器人Code未设置")
        
        url = f"{self.base_url}/robot/oToMessages/batchSend"
        
        headers = {
            "x-acs-dingtalk-access-token": self.access_token,
            "Content-Type": "application/json"
        }
        
        data = {
            "robotCode": robot_code,
            "userIds": [user_id],
            "msgKey": "sampleText",
            "msgParam": json.dumps({"content": content}, ensure_ascii=False)
        }
        
        response = self.session.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        return response.json()
    
    def send_markdown_message(self, user_id: str, title: str, text: str,
                             robot_code: str = None) -> Dict:
        """
        发送Markdown格式消息
        
        Args:
            user_id: 钉钉用户ID
            title: 消息标题
            text: Markdown格式内容
            robot_code: 机器人Code
            
        Returns:
            发送结果
        """
        robot_code = robot_code or os.getenv('DINGTALK_ROBOT_CODE')
        
        url = f"{self.base_url}/robot/oToMessages/batchSend"
        
        headers = {
            "x-acs-dingtalk-access-token": self.access_token,
            "Content-Type": "application/json"
        }
        
        data = {
            "robotCode": robot_code,
            "userIds": [user_id],
            "msgKey": "sampleMarkdown",
            "msgParam": json.dumps({
                "title": title,
                "text": text
            }, ensure_ascii=False)
        }
        
        response = self.session.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        return response.json()
    
    def send_link_message(self, user_id: str, title: str, text: str,
                         message_url: str, pic_url: str = None,
                         robot_code: str = None) -> Dict:
        """
        发送链接消息
        
        Args:
            user_id: 钉钉用户ID
            title: 链接标题
            text: 链接描述
            message_url: 链接地址
            pic_url: 图片地址（可选）
            robot_code: 机器人Code
            
        Returns:
            发送结果
        """
        robot_code = robot_code or os.getenv('DINGTALK_ROBOT_CODE')
        
        url = f"{self.base_url}/robot/oToMessages/batchSend"
        
        headers = {
            "x-acs-dingtalk-access-token": self.access_token,
            "Content-Type": "application/json"
        }
        
        msg_param = {
            "title": title,
            "text": text,
            "messageUrl": message_url
        }
        
        if pic_url:
            msg_param["picUrl"] = pic_url
        
        data = {
            "robotCode": robot_code,
            "userIds": [user_id],
            "msgKey": "sampleLink",
            "msgParam": json.dumps(msg_param, ensure_ascii=False)
        }
        
        response = self.session.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        return response.json()
    
    def get_user_info(self, user_id: str) -> Dict:
        """
        获取用户信息
        
        Args:
            user_id: 钉钉用户ID
            
        Returns:
            用户信息
        """
        url = f"{self.base_url}/contact/users/{user_id}"
        
        headers = {
            "x-acs-dingtalk-access-token": self.access_token
        }
        
        response = self.session.get(url, headers=headers)
        response.raise_for_status()
        
        return response.json()
    
    def batch_send(self, user_ids: List[str], msg_key: str, 
                  msg_param: Dict, robot_code: str = None) -> Dict:
        """
        批量发送消息
        
        Args:
            user_ids: 用户ID列表
            msg_key: 消息类型key
            msg_param: 消息参数
            robot_code: 机器人Code
            
        Returns:
            发送结果
        """
        robot_code = robot_code or os.getenv('DINGTALK_ROBOT_CODE')
        
        url = f"{self.base_url}/robot/oToMessages/batchSend"
        
        headers = {
            "x-acs-dingtalk-access-token": self.access_token,
            "Content-Type": "application/json"
        }
        
        data = {
            "robotCode": robot_code,
            "userIds": user_ids,
            "msgKey": msg_key,
            "msgParam": json.dumps(msg_param, ensure_ascii=False)
        }
        
        response = self.session.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        return response.json()
    
    def test_connection(self) -> bool:
        """
        测试连接是否正常
        
        Returns:
            连接是否成功
        """
        try:
            # 尝试获取当前用户信息
            url = f"{self.base_url}/oauth2/userinfo"
            headers = {
                "x-acs-dingtalk-access-token": self.access_token
            }
            
            response = self.session.get(url, headers=headers)
            return response.status_code == 200
        except:
            return False


# 命令行接口
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='钉钉助手命令行工具')
    parser.add_argument('--user-id', required=True, help='钉钉用户ID')
    parser.add_argument('--message', required=True, help='消息内容')
    parser.add_argument('--type', default='text', choices=['text', 'markdown', 'link'],
                       help='消息类型')
    parser.add_argument('--title', help='消息标题（markdown/link类型需要）')
    parser.add_argument('--url', help='链接地址（link类型需要）')
    parser.add_argument('--proxy', help='代理服务器')
    
    args = parser.parse_args()
    
    # 从环境变量获取配置
    client_id = os.getenv('DINGTALK_CLIENT_ID')
    client_secret = os.getenv('DINGTALK_CLIENT_SECRET')
    robot_code = os.getenv('DINGTALK_ROBOT_CODE')
    
    if not all([client_id, client_secret, robot_code]):
        print("错误: 请设置环境变量:")
        print("  DINGTALK_CLIENT_ID: 钉钉应用Client ID")
        print("  DINGTALK_CLIENT_SECRET: 钉钉应用Client Secret")
        print("  DINGTALK_ROBOT_CODE: 钉钉机器人Code")
        exit(1)
    
    # 创建助手实例
    assistant = DingTalkAssistant(proxy=args.proxy)
    
    try:
        # 获取Access Token
        print("正在获取Access Token...")
        token = assistant.get_access_token(client_id, client_secret)
        print(f"Access Token获取成功")
        
        # 发送消息
        if args.type == 'text':
            result = assistant.send_text_message(args.user_id, args.message, robot_code)
        elif args.type == 'markdown':
            if not args.title:
                print("错误: markdown消息需要--title参数")
                exit(1)
            result = assistant.send_markdown_message(args.user_id, args.title, args.message, robot_code)
        elif args.type == 'link':
            if not all([args.title, args.url]):
                print("错误: link消息需要--title和--url参数")
                exit(1)
            result = assistant.send_link_message(args.user_id, args.title, args.message, args.url, robot_code=robot_code)
        
        print(f"消息发送成功: {result}")
        
    except Exception as e:
        print(f"错误: {e}")
        exit(1)