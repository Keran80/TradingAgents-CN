#!/usr/bin/env python3
"""
智能监控策略引擎
实现动态监控间隔调整
"""

import datetime
import json
import os
import time
from typing import Dict, Any

class SmartMonitorEngine:
    """智能监控引擎"""
    
    def __init__(self):
        self.config_file = "/tmp/CODING_agent/smart_monitor_config.json"
        self.load_config()
        
    def load_config(self):
        """加载配置"""
        default_config = {
            "monitor_intervals": {
                "critical_phase": 15,      # 关键阶段: 15分钟
                "normal_phase": 30,        # 正常阶段: 30分钟
                "stable_phase": 60,        # 稳定阶段: 60分钟
                "night_time": 120,         # 夜间: 120分钟
                "early_morning": 180       # 凌晨: 180分钟
            },
            "time_ranges": {
                "daytime": ["08:00", "22:00"],
                "night": ["22:00", "08:00"],
                "early_morning": ["00:00", "06:00"]
            },
            "phase_definitions": {
                "critical": ["progress_rate < 0.3", "quality_score < 90"],
                "normal": ["progress_rate >= 0.3", "progress_rate <= 0.8"],
                "stable": ["progress_rate > 0.8", "quality_score >= 95"]
            },
            "adjustment_factors": {
                "quality_high_multiplier": 1.5,    # 质量高时延长50%
                "quality_low_multiplier": 0.7,     # 质量低时缩短30%
                "max_interval": 180,               # 最大间隔180分钟
                "min_interval": 10                 # 最小间隔10分钟
            }
        }
        
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = default_config
            self.save_config()
    
    def save_config(self):
        """保存配置"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get_current_phase(self, progress_rate: float, quality_score: float) -> str:
        """获取当前项目阶段"""
        if progress_rate < 0.3 or quality_score < 90:
            return "critical"
        elif progress_rate >= 0.3 and progress_rate <= 0.8:
            return "normal"
        else:
            return "stable"
    
    def get_time_of_day(self) -> str:
        """获取当前时间段"""
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M")
        
        # 检查时间段
        for time_range, (start, end) in self.config["time_ranges"].items():
            if start <= current_time <= end:
                return time_range
        
        return "daytime"  # 默认白天
    
    def calculate_interval(self, progress_rate: float, quality_score: float) -> int:
        """计算监控间隔(分钟)"""
        # 获取当前阶段和时间段
        current_phase = self.get_current_phase(progress_rate, quality_score)
        time_of_day = self.get_time_of_day()
        
        # 基础间隔
        base_interval = self.config["monitor_intervals"].get(current_phase, 30)
        
        # 时间调整
        if time_of_day == "night":
            base_interval = max(base_interval, self.config["monitor_intervals"]["night_time"])
        elif time_of_day == "early_morning":
            base_interval = max(base_interval, self.config["monitor_intervals"]["early_morning"])
        
        # 质量调整 (质量越高，监控间隔可适当延长)
        adjustment = self.config["adjustment_factors"]
        if quality_score >= 95:
            base_interval = min(base_interval * adjustment["quality_high_multiplier"], 
                              adjustment["max_interval"])
        elif quality_score < 85:
            base_interval = max(base_interval * adjustment["quality_low_multiplier"],
                              adjustment["min_interval"])
        
        return int(base_interval)
    
    def get_monitor_schedule(self) -> Dict[str, Any]:
        """获取监控计划"""
        # 模拟当前状态 (实际应从系统获取)
        current_progress = 0.92  # 92%
        current_quality = 95     # 95/100
        
        interval_minutes = self.calculate_interval(current_progress, current_quality)
        
        return {
            "current_progress": current_progress,
            "current_quality": current_quality,
            "current_phase": self.get_current_phase(current_progress, current_quality),
            "time_of_day": self.get_time_of_day(),
            "monitor_interval_minutes": interval_minutes,
            "next_check_time": (datetime.datetime.now() + datetime.timedelta(minutes=interval_minutes)).strftime("%Y-%m-%d %H:%M"),
            "reasoning": f"基于进度{current_progress*100}%、质量{current_quality}/100、时间{self.get_time_of_day()}计算"
        }

def main():
    """主函数"""
    engine = SmartMonitorEngine()
    schedule = engine.get_monitor_schedule()
    
    print("🤖 智能监控策略引擎")
    print("=" * 50)
    print(f"当前进度: {schedule['current_progress']*100:.1f}%")
    print(f"当前质量: {schedule['current_quality']}/100")
    print(f"项目阶段: {schedule['current_phase']}")
    print(f"时间段: {schedule['time_of_day']}")
    print(f"监控间隔: {schedule['monitor_interval_minutes']}分钟")
    print(f"下次检查: {schedule['next_check_time']}")
    print(f"决策依据: {schedule['reasoning']}")
    print("=" * 50)
    
    # 返回间隔分钟数供脚本使用
    return schedule['monitor_interval_minutes']

if __name__ == "__main__":
    interval = main()
    # 输出间隔供shell脚本捕获
    print(f"INTERVAL:{interval}")