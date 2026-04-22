# -*- coding: utf-8 -*-
"""
main.py - 主要逻辑

从 builder.py 拆分
"""

# 其余代码保留在此文件
# 建议后续进一步拆分

from dataclasses import dataclass, field
import json
from typing import Any, Dict, List, Optional
import os
from .components import ComponentRegistry
from __future__ import annotations
from pathlib import Path
from .dsl import (
from datetime import datetime
import logging

# 主逻辑代码
