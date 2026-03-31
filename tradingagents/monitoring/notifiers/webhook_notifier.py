# notifiers/webhook_notifier.py
"""
Webhook通知器
通过HTTP POST发送告警到远程服务器
"""

import json
import urllib.request
import urllib.error
from typing import Any, Dict, Optional

from ..triggers.base import TriggerResult
from .base import AlertNotifier, NotificationResult


class WebhookNotifier(AlertNotifier):
    """
    Webhook通知器

    通过HTTP POST发送告警到远程服务器

    使用方式:
    ```python
    # 飞书Webhook
    notifier = WebhookNotifier(
        name="feishu",
        url="https://open.feishu.cn/open-apis/bot/v2/hook/xxx",
        headers={"Content-Type": "application/json"}
    )

    # 企业微信Webhook
    notifier = WebhookNotifier(
        name="wecom",
        url="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx",
        formatter=wecom_formatter  # 自定义格式化器
    )

    # 自定义Webhook
    notifier = WebhookNotifier(
        name="custom",
        url="https://your-server.com/webhook",
        formatter=custom_formatter
    )
    ```

    内置格式化器:
    - feishu_formatter: 飞书消息卡片
    - wecom_formatter: 企业微信消息
    - discord_formatter: Discord webhook
    - dingtalk_formatter: 钉钉机器人
    """

    def __init__(
        self,
        name: str = "webhook",
        url: str = "",
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 10,
        formatter: Optional[callable] = None,
        **kwargs
    ):
        super().__init__(name=name, **kwargs)
        self.url = url
        self.method = method.upper()
        self.headers = headers or {"Content-Type": "application/json"}
        self.timeout = timeout
        self.formatter = formatter or self._default_formatter

    def _send_impl(self, result: TriggerResult) -> NotificationResult:
        """发送Webhook通知"""
        if not self.url:
            return self._create_result(
                success=False,
                error="Webhook URL not configured"
            )

        try:
            # 格式化消息
            payload = self.formatter(result)

            # 发送请求
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                self.url,
                data=data,
                headers=self.headers,
                method=self.method
            )

            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                response_body = response.read().decode('utf-8')

            return self._create_result(
                success=True,
                message=f"Webhook sent, response: {response_body[:100]}"
            )

        except urllib.error.URLError as e:
            return self._create_result(
                success=False,
                error=f"URL error: {e}"
            )
        except Exception as e:
            return self._create_result(
                success=False,
                error=str(e)
            )

    def _default_formatter(self, result: TriggerResult) -> Dict[str, Any]:
        """默认JSON格式化器"""
        return {
            'trigger_name': result.trigger_name,
            'alert_level': result.alert_level.value,
            'title': result.title,
            'message': result.message,
            'data': result.data,
            'timestamp': result.timestamp.isoformat(),
        }

    def _feishu_formatter(self, result: TriggerResult) -> Dict[str, Any]:
        """飞书消息卡片格式化器"""
        return {
            'msg_type': 'interactive',
            'card': {
                'config': {'wide_screen_mode': True},
                'header': {
                    'title': {'tag': 'plain_text', 'content': result.title},
                    'template': self._get_feishu_color(result.alert_level)
                },
                'elements': [
                    {
                        'tag': 'div',
                        'text': {
                            'tag': 'lark_md',
                            'content': result.message
                        }
                    },
                    {
                        'tag': 'note',
                        'fields': [
                            {'label': '告警级别', 'value': result.alert_level.value},
                            {'label': '触发器', 'value': result.trigger_name},
                            {'label': '时间', 'value': result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
                        ]
                    }
                ]
            }
        }

    def _wecom_formatter(self, result: TriggerResult) -> Dict[str, Any]:
        """企业微信消息格式化器"""
        return {
            'msgtype': 'markdown',
            'markdown': {
                'content': f"### {result.title}\n\n{result.message}\n\n> 级别: {result.alert_level.value}\n> 触发器: {result.trigger_name}\n> 时间: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
            }
        }

    def _get_feishu_color(self, level) -> str:
        """获取飞书卡片颜色"""
        colors = {
            'info': 'blue',
            'warning': 'yellow',
            'critical': 'red',
            'urgent': 'purple',
        }
        return colors.get(level.value, 'blue')


# 便捷格式化器函数
def feishu_formatter(result: TriggerResult) -> Dict[str, Any]:
    """飞书消息卡片格式化"""
    return {
        'msg_type': 'interactive',
        'card': {
            'config': {'wide_screen_mode': True},
            'header': {
                'title': {'tag': 'plain_text', 'content': result.title},
                'template': 'red' if result.alert_level.value in ['critical', 'urgent'] else 'orange'
            },
            'elements': [
                {'tag': 'div', 'text': {'tag': 'lark_md', 'content': result.message}},
                {'tag': 'hr'},
                {
                    'tag': 'note',
                    'fields': [
                        {'label': '级别', 'value': result.alert_level.value.upper()},
                        {'label': '时间', 'value': result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
                    ]
                }
            ]
        }
    }


def wecom_formatter(result: TriggerResult) -> Dict[str, Any]:
    """企业微信格式化"""
    emoji = {'info': '', 'warning': 'warning', 'critical': 'fire', 'urgent': 'sos'}
    return {
        'msgtype': 'markdown',
        'markdown': {
            'content': f"### {result.title}\n>{result.message}\n>{emoji.get(result.alert_level.value, '')} 级别: **{result.alert_level.value}**"
        }
    }


def dingtalk_formatter(result: TriggerResult) -> Dict[str, Any]:
    """钉钉格式化"""
    return {
        'msgtype': 'markdown',
        'markdown': {
            'title': result.title,
            'text': f"## {result.title}\n\n{result.message}\n\n---\n**级别**: {result.alert_level.value}\n**时间**: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        }
    }
