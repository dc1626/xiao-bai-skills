---
name: dingtalk-assistant
description: 钉钉机器人集成助手 - 提供钉钉机器人配置、消息发送、语音识别等完整解决方案。针对中国企业的钉钉平台优化。
metadata: {"openclaw":{"emoji":"🦞","requires":{"config":["channels.dingtalk"]}}}
---

# 钉钉助手技能

## 概述

本技能提供完整的钉钉机器人集成解决方案，特别针对中国企业钉钉平台优化。包含配置指南、API使用经验、常见问题解决和最佳实践。

## 快速开始

### 安装钉钉插件
```bash
openclaw plugins install https://github.com/soimy/clawdbot-channel-dingtalk.git
```

### 配置钉钉凭证
在OpenClaw配置中添加钉钉通道配置。

### 发送测试消息
```python
from dingtalk_assistant import DingTalkAssistant

assistant = DingTalkAssistant()
assistant.send_text("31261924402207", "测试消息")
```

## 完整文档

详细文档请查看 [DOCUMENTATION.md](./DOCUMENTATION.md)

## 示例

查看 [examples/](./examples/) 目录中的使用示例。

## 许可证

MIT License