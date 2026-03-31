# notifiers/file_notifier.py
"""
文件通知器
将告警写入日志文件
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..triggers.base import TriggerResult
from .base import AlertNotifier, NotificationResult


class FileNotifier(AlertNotifier):
    """
    文件通知器

    将告警信息写入日志文件

    使用方式:
    ```python
    notifier = FileNotifier(
        name="file",
        log_dir="./logs/monitoring",
        max_file_size=10*1024*1024,  # 10MB
        backup_count=5
    )
    notifier.notify(trigger_result)
    ```
    """

    def __init__(
        self,
        name: str = "file",
        log_dir: str = "./logs/monitoring",
        filename_template: str = "alert_{date}.log",
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        **kwargs
    ):
        super().__init__(name=name, **kwargs)
        self.log_dir = Path(log_dir)
        self.filename_template = filename_template
        self.max_file_size = max_file_size
        self.backup_count = backup_count

        # 确保目录存在
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _send_impl(self, result: TriggerResult) -> NotificationResult:
        """发送文件通知"""
        try:
            log_file = self._get_log_file()
            message = self._format_message(result)

            # 写入文件
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(message + '\n')

            # 检查文件大小，必要时轮转
            if log_file.stat().st_size > self.max_file_size:
                self._rotate_log(log_file)

            return self._create_result(
                success=True,
                message=f"Written to {log_file}"
            )
        except Exception as e:
            return self._create_result(
                success=False,
                error=str(e)
            )

    def _get_log_file(self) -> Path:
        """获取当前日志文件路径"""
        date_str = datetime.now().strftime("%Y%m%d")
        filename = self.filename_template.format(date=date_str)
        return self.log_dir / filename

    def _rotate_log(self, log_file: Path):
        """轮转日志文件"""
        for i in range(self.backup_count - 1, 0, -1):
            src = log_file.with_suffix(f'.{i}')
            dst = log_file.with_suffix(f'.{i + 1}')
            if src.exists():
                src.rename(dst)

        # 移动当前日志
        backup = log_file.with_suffix('.1')
        if backup.exists():
            backup.unlink()
        log_file.rename(backup)
