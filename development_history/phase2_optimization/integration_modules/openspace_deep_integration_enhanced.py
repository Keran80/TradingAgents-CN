#!/usr/bin/env python3
"""
增强的OpenSpace深度集成模块
包含任务中断接续功能
"""

import asyncio
import json
import os
import sys
import time
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import aiohttp

class TaskStateManager:
    """任务状态管理器"""
    
    def __init__(self, state_file: str = "solution_c_state.json"):
        self.state_file = state_file
        self.state = self._load_state()
    
    def _load_state(self) -> Dict[str, Any]:
        """加载状态"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"❌ 加载状态文件失败: {e}")
        
        # 默认状态
        return {
            "project_state": {
                "name": "",
                "current_stage": "",
                "overall_progress": 0,
                "last_checkpoint": "",
                "next_task": "",
                "interrupted": False,
                "recovery_count": 0
            },
            "task_states": {},
            "checkpoints": [],
            "error_log": [],
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "version": "1.0"
            }
        }
    
    def save_state(self):
        """保存状态"""
        try:
            self.state["metadata"]["last_updated"] = datetime.now().isoformat()
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"❌ 保存状态文件失败: {e}")
            return False
    
    def update_task_status(self, task_id: str, status: str, progress: int = 0, 
                          result: Any = None, error: str = None):
        """更新任务状态"""
        if "task_states" not in self.state:
            self.state["task_states"] = {}
        
        task_state = {
            "id": task_id,
            "status": status,  # pending, running, completed, failed, retrying
            "progress": progress,
            "last_updated": datetime.now().isoformat(),
            "result": result,
            "error": error
        }
        
        # 如果是新任务，添加创建时间
        if task_id not in self.state["task_states"]:
            task_state["created_at"] = datetime.now().isoformat()
        
        self.state["task_states"][task_id] = task_state
        
        # 更新项目进度
        self._update_project_progress()
        
        return self.save_state()
    
    def _update_project_progress(self):
        """更新项目进度"""
        if not self.state["task_states"]:
            self.state["project_state"]["overall_progress"] = 0
            return
        
        total_tasks = len(self.state["task_states"])
        completed_tasks = sum(1 for t in self.state["task_states"].values() 
                             if t.get("status") == "completed")
        
        if total_tasks > 0:
            self.state["project_state"]["overall_progress"] = int((completed_tasks / total_tasks) * 100)
    
    def get_next_task(self, tasks: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """获取下一个待执行任务"""
        # 首先查找失败的任务
        for task in tasks:
            task_id = task.get("id")
            if task_id in self.state["task_states"]:
                task_state = self.state["task_states"][task_id]
                if task_state.get("status") in ["failed", "retrying"]:
                    return task
        
        # 然后查找未开始的任务
        for task in tasks:
            task_id = task.get("id")
            if task_id not in self.state["task_states"]:
                return task
            elif self.state["task_states"][task_id].get("status") == "pending":
                return task
        
        return None
    
    def create_checkpoint(self, checkpoint_id: str, data: Dict[str, Any]):
        """创建检查点"""
        checkpoint = {
            "id": checkpoint_id,
            "timestamp": datetime.now().isoformat(),
            "data": data,
            "project_progress": self.state["project_state"]["overall_progress"]
        }
        
        if "checkpoints" not in self.state:
            self.state["checkpoints"] = []
        
        self.state["checkpoints"].append(checkpoint)
        
        # 保留最近10个检查点
        if len(self.state["checkpoints"]) > 10:
            self.state["checkpoints"] = self.state["checkpoints"][-10:]
        
        self.state["project_state"]["last_checkpoint"] = checkpoint_id
        return self.save_state()
    
    def log_error(self, task_id: str, error: str, error_type: str = "runtime"):
        """记录错误"""
        if "error_log" not in self.state:
            self.state["error_log"] = []
        
        error_entry = {
            "task_id": task_id,
            "error": error,
            "error_type": error_type,
            "timestamp": datetime.now().isoformat(),
            "recovered": False
        }
        
        self.state["error_log"].append(error_entry)
        return self.save_state()
    
    def mark_interruption(self):
        """标记中断"""
        self.state["project_state"]["interrupted"] = True
        self.state["project_state"]["recovery_count"] += 1
        return self.save_state()
    
    def clear_interruption(self):
        """清除中断标记"""
        self.state["project_state"]["interrupted"] = False
        return self.save_state()
    
    def get_recovery_info(self) -> Dict[str, Any]:
        """获取恢复信息"""
        return {
            "interrupted": self.state["project_state"]["interrupted"],
            "recovery_count": self.state["project_state"]["recovery_count"],
            "last_checkpoint": self.state["project_state"]["last_checkpoint"],
            "pending_tasks": sum(1 for t in self.state["task_states"].values() 
                               if t.get("status") in ["pending", "failed", "retrying"]),
            "completed_tasks": sum(1 for t in self.state["task_states"].values() 
                                 if t.get("status") == "completed")
        }

class EnhancedOpenSpaceDeepIntegration:
    """增强的OpenSpace深度集成类（包含中断接续功能）"""
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = "qwen-plus"):
        self.api_key = api_key or os.getenv("OPENSPACE_API_KEY", "sk-ce33d912e9e54f419982cfe088e62aba")
        self.base_url = base_url or os.getenv("OPENSPACE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.model = model
        
        # 状态管理器
        self.state_manager = TaskStateManager()
        
        self.integration_status = {
            "openspace_connected": False,
            "agents_registered": False,
            "skills_loaded": False,
            "workflows_configured": False,
            "recovery_enabled": True
        }
        
        self.registered_agents = {}
        self.loaded_skills = {}
        self.workflows = {}
        self.integration_dir = os.path.dirname(os.path.abspath(__file__))
        
    async def initialize(self, recovery_mode: bool = False) -> bool:
        """初始化集成"""
        try:
            print("🔧 初始化增强的OpenSpace深度集成...")
            
            if recovery_mode:
                recovery_info = self.state_manager.get_recovery_info()
                print(f"🔄 恢复模式: 中断次数={recovery_info['recovery_count']}, 待处理任务={recovery_info['pending_tasks']}")
            
            # 测试API连接
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                test_data = {
                    "model": self.model,
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 10
                }
                
                async with session.post(f"{self.base_url}/chat/completions", 
                                       headers=headers, 
                                       json=test_data) as response:
                    if response.status == 200:
                        self.integration_status["openspace_connected"] = True
                        print("✅ OpenSpace API连接成功")
                    else:
                        print(f"❌ OpenSpace API连接失败: {response.status}")
                        return False
            
            # 注册默认智能体
            self._register_default_agents()
            
            # 加载默认技能
            self._load_default_skills()
            
            # 配置默认工作流
            self._configure_default_workflows()
            
            # 清除中断标记（如果存在）
            self.state_manager.clear_interruption()
            
            print("✅ 增强的OpenSpace深度集成初始化成功")
            return True
            
        except Exception as e:
            print(f"❌ 初始化失败: {e}")
            self.state_manager.log_error("initialization", str(e), "initialization")
            return False
    
    def _register_default_agents(self):
        """注册默认智能体"""
        self.registered_agents = {
            "financial_project_manager": {
                "name": "金融项目经理",
                "description": "负责金融项目的规划和管理",
                "capabilities": ["project_planning", "risk_assessment", "timeline_management"],
                "recovery_capable": True
            },
            "financial_code_reviewer": {
                "name": "金融代码审查员",
                "description": "负责金融代码的审查和优化",
                "capabilities": ["code_review", "performance_optimization", "security_audit"],
                "recovery_capable": True
            },
            "quantitative_test_generator": {
                "name": "量化测试生成器",
                "description": "负责生成量化交易的测试用例",
                "capabilities": ["test_generation", "coverage_analysis", "performance_testing"],
                "recovery_capable": True
            }
        }
        self.integration_status["agents_registered"] = True
    
    def _load_default_skills(self):
        """加载默认技能"""
        self.loaded_skills = {
            "financial_analysis": {
                "name": "金融分析",
                "description": "金融数据分析和风险评估",
                "version": "1.0"
            },
            "quantitative_testing": {
                "name": "量化测试",
                "description": "量化交易策略的测试和验证",
                "version": "1.0"
            },
            "performance_optimization": {
                "name": "性能优化",
                "description": "系统性能分析和优化",
                "version": "1.0"
            },
            "recovery_management": {
                "name": "恢复管理",
                "description": "任务中断恢复和状态管理",
                "version": "1.0"
            }
        }
        self.integration_status["skills_loaded"] = True
    
    def _configure_default_workflows(self):
        """配置默认工作流"""
        self.workflows = {
            "financial_project_planning": {
                "name": "金融项目规划工作流",
                "description": "金融项目的智能规划和管理",
                "steps": ["需求分析", "技术设计", "任务分解", "风险评估", "时间线规划"],
                "agents": ["financial_project_manager"],
                "recoverable": True
            },
            "quantitative_development": {
                "name": "量化开发工作流",
                "description": "量化交易策略的开发和测试",
                "steps": ["策略实现", "代码审查", "测试生成", "回测执行", "性能优化"],
                "agents": ["financial_code_reviewer", "quantitative_test_generator"],
                "recoverable": True
            },
            "performance_optimization": {
                "name": "性能优化工作流",
                "description": "系统性能分析和优化",
                "steps": ["性能分析", "瓶颈识别", "优化建议", "实施验证", "效果评估"],
                "agents": ["financial_code_reviewer"],
                "recoverable": True
            },
            "recovery_workflow": {
                "name": "恢复工作流",
                "description": "任务中断恢复和状态重建",
                "steps": ["状态检查", "中断分析", "恢复规划", "任务继续", "状态验证"],
                "agents": ["financial_project_manager"],
                "recoverable": True
            }
        }
        self.integration_status["workflows_configured"] = True
    
    async def execute_workflow_with_recovery(self, workflow_name: str, inputs: Dict[str, Any], 
                                           max_retries: int = 3) -> Dict[str, Any]:
        """执行工作流（带恢复功能）"""
        print(f"🔄 执行工作流（带恢复）: {workflow_name}")
        
        workflow = self.workflows.get(workflow_name)
        if not workflow:
            return {"error": f"工作流不存在: {workflow_name}"}
        
        workflow_id = f"{workflow_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 更新任务状态
        self.state_manager.update_task_status(
            task_id=workflow_id,
            status="running",
            progress=0
        )
        
        try:
            # 创建检查点
            checkpoint_data = {
                "workflow": workflow_name,
                "inputs": inputs,
                "start_time": datetime.now().isoformat(),
                "status": "running"
            }
            self.state_manager.create_checkpoint(f"checkpoint_{workflow_id}", checkpoint_data)
            
            # 执行工作流
            result = await self._execute_workflow_internal(workflow_name, inputs)
            
            # 更新任务状态为完成
            self.state_manager.update_task_status(
                task_id=workflow_id,
                status="completed",
                progress=100,
                result=result
            )
            
            # 更新检查点
            checkpoint_data["end_time"] = datetime.now().isoformat()
            checkpoint_data["status"] = "completed"
            checkpoint_data["result"] = result
            self.state_manager.create_checkpoint(f"checkpoint_{workflow_id}_completed", checkpoint_data)
            
            print(f"✅ 工作流执行完成: {workflow_name}")
            return result
            
        except Exception as e:
            error_msg = f"工作流执行失败: {str(e)}"
            print(f"❌ {error_msg}")
            
            # 记录错误
            self.state_manager.log_error(workflow_id, error_msg, "workflow_execution")
            
            # 更新任务状态为失败
            self.state_manager.update_task_status(
                task_id=workflow_id,
                status="failed",
                progress=50,
                error=error_msg
            )
            
            # 标记中断
            self.state_manager.mark_interruption()
            
            return {"error": error_msg, "workflow_id": workflow_id, "recoverable": True}
    
    async def _execute_workflow_internal(self, workflow_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """内部工作流执行"""
        # 这里根据工作流名称执行不同的逻辑
        if workflow_name == "financial_project_planning":
            return await self.execute_planning_workflow(
                project_name=inputs.get("project_name", "未知项目"),
                current_status=inputs.get("current_status", ""),
                requirements=inputs.get("requirements", ""),
                deadline=inputs.get("deadline", ""),
                priority=inputs.get("priority", "medium")
            )
        elif workflow_name == "quantitative_development":
            return await self.execute_quantitative_development_workflow(
                task_name=inputs.get("task_name", ""),
                task_description=inputs.get("task_description", ""),
                requirements=inputs.get("requirements", ""),
                code_context=inputs.get("code_context", ""),
                test_framework=inputs.get("test_framework", "unittest"),
                deadline=inputs.get("deadline")
            )
        elif workflow_name == "performance_optimization":
            return await self.execute_quantitative_development_workflow(
                task_name="性能优化分析",
                task_description="分析系统性能瓶颈，提出优化建议",
                requirements=inputs.get("requirements", "分析性能瓶颈"),
                code_context=inputs.get("code_context", ""),
                test_framework="performance",
                deadline=inputs.get("deadline")
            )
        else:
            return {"error": f"未知工作流: {workflow_name}"}
    
    async def recover_from_interruption(self) -> Dict[str, Any]:
        """从中断恢复"""
        print("🔄 从中断恢复...")
        
        recovery_info = self.state_manager.get_recovery_info()
        if not recovery_info["interrupted"]:
            return {"status": "no_interruption", "message": "没有检测到中断"}
        
        # 查找失败的任务
        failed_tasks = []
        for task_id, task_state in self.state_manager.state["task_states"].items():
            if task_state.get("status") in ["failed", "retrying"]:
                failed_tasks.append({
                    "task_id": task_id,
                    "status": task_state["status"],
                    "error": task_state.get("error"),
                    "progress": task_state.get("progress", 0)
                })
        
        if not failed_tasks:
            # 查找未完成的任务
            pending_tasks = []
            for task_id, task_state in self.state_manager.state["task_states"].items():
                if task_state.get("status") in ["pending", "running"]:
                    pending_tasks.append({
                        "task_id": task_id,
                        "status": task_state["status"],
                        "progress": task_state.get("progress", 0)
                    })
            
            failed_tasks = pending_tasks