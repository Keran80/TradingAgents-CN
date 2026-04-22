async def _analyze_feedback(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """分析反馈信息"""
        analysis = {
            "feedback_type": feedback.get("type", "general"),
            "issues_found": feedback.get("issues", []),
            "suggestions": feedback.get("suggestions", []),
            "severity": feedback.get("severity", "medium"),
            "changes_needed": [],
            "priority": "high" if feedback.get("severity") == "high" else "medium"
        }
        
        # 根据反馈类型确定需要的变化
        if analysis["feedback_type"] == "technical":
            analysis["changes_needed"].append("技术方案调整")
        elif analysis["feedback_type"] == "requirement":
            analysis["changes_needed"].append("需求澄清或调整")
        elif analysis["feedback_type"] == "resource":
            analysis["changes_needed"].append("资源分配优化")
        elif analysis["feedback_type"] == "schedule":
            analysis["changes_needed"].append("时间安排调整")
        
        return analysis
    
    async def _optimize_based_on_feedback(self, original_plan: Dict[str, Any],
                                         feedback_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """基于反馈优化方案"""
        optimized_plan = original_plan.copy()
        
        # 标记为优化版本
        optimized_plan["optimized"] = True
        optimized_plan["optimized_at"] = datetime.now().isoformat()
        optimized_plan["feedback_analysis"] = feedback_analysis
        
        # 根据反馈类型进行优化
        if feedback_analysis["feedback_type"] == "technical":
            # 优化技术方案
            if "技术方案调整" in feedback_analysis["changes_needed"]:
                optimized_plan["technical_plan"] = self._optimize_technical_plan(
                    optimized_plan.get("technical_plan", {}),
                    feedback_analysis
                )
        
        elif feedback_analysis["feedback_type"] == "requirement":
            # 优化需求分析
            if "需求澄清或调整" in feedback_analysis["changes_needed"]:
                optimized_plan["requirements_analysis"] = self._optimize_requirements_analysis(
                    optimized_plan.get("requirements_analysis", {}),
                    feedback_analysis
                )
        
        elif feedback_analysis["feedback_type"] == "resource":
            # 优化资源分配
            if "资源分配优化" in feedback_analysis["changes_needed"]:
                optimized_plan["task_decomposition"] = self._optimize_resource_allocation(
                    optimized_plan.get("task_decomposition", {}),
                    feedback_analysis
                )
        
        elif feedback_analysis["feedback_type"] == "schedule":
            # 优化时间安排
            if "时间安排调整" in feedback_analysis["changes_needed"]:
                optimized_plan["task_decomposition"] = self._optimize_schedule(
                    optimized_plan.get("task_decomposition", {}),
                    feedback_analysis
                )
        
        # 重新验证优化后的方案
        optimized_plan["validation_report"] = await self._validate_plan(
            optimized_plan.get("task_decomposition", {})
        )
        
        optimized_plan["status"] = "optimized"
        
        return optimized_plan
    
    def _optimize_technical_plan(self, technical_plan: Dict[str, Any],
                                feedback_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """优化技术方案"""
        optimized = technical_plan.copy()
        
        # 添加优化标记
        optimized["optimization_notes"] = feedback_analysis.get("suggestions", [])
        optimized["last_optimized"] = datetime.now().isoformat()
        
        return optimized
    
    def _optimize_requirements_analysis(self, requirements_analysis: Dict[str, Any],
                                       feedback_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """优化需求分析"""
        optimized = requirements_analysis.copy()
        
        # 添加反馈信息
        optimized["feedback_incorporated"] = True
        optimized["feedback_details"] = feedback_analysis
        
        return optimized
    
    def _optimize_resource_allocation(self, task_decomposition: Dict[str, Any],
                                     feedback_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """优化资源分配"""
        optimized = task_decomposition.copy()
        
        # 这里可以添加资源分配优化逻辑
        optimized["resource_optimized"] = True
        optimized["optimization_time"] = datetime.now().isoformat()
        
        return optimized
    
    def _optimize_schedule(self, task_decomposition: Dict[str, Any],
                          feedback_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """优化时间安排"""
        optimized = task_decomposition.copy()
        
        # 这里可以添加时间安排优化逻辑
        optimized["schedule_optimized"] = True
        optimized["optimization_time"] = datetime.now().isoformat()
        
        return optimized
    
    async def _generate_optimization_report(self, plan_id: str, original_plan: Dict[str, Any],
                                           optimized_plan: Dict[str, Any],
                                           feedback_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """生成优化报告"""
        report = {
            "plan_id": plan_id,
            "optimization_time": datetime.now().isoformat(),
            "feedback_analysis": feedback_analysis,
            "changes_made": feedback_analysis.get("changes_needed", []),
            "original_validation": original_plan.get("validation_report", {}).get("passed", False),
            "optimized_validation": optimized_plan.get("validation_report", {}).get("passed", False),
            "improvement_summary": self._generate_improvement_summary(original_plan, optimized_plan),
            "next_steps": [
                "执行优化后的方案",
                "监控优化效果",
                "持续收集反馈"
            ]
        }
        
        # 保存报告
        report_file = self.project_dir / "reports" / f"optimization_report_{plan_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report
    
    def _generate_improvement_summary(self, original_plan: Dict[str, Any],
                                     optimized_plan: Dict[str, Any]) -> Dict[str, Any]:
        """生成改进摘要"""
        original_tasks = len(original_plan.get("task_decomposition", {}).get("tasks", []))
        optimized_tasks = len(optimized_plan.get("task_decomposition", {}).get("tasks", []))
        
        original_validation = original_plan.get("validation_report", {}).get("passed", False)
        optimized_validation = optimized_plan.get("validation_report", {}).get("passed", False)
        
        return {
            "task_count_change": optimized_tasks - original_tasks,
            "validation_improvement": optimized_validation and not original_validation,
            "status_change": f"{original_plan.get('status', 'unknown')} → {optimized_plan.get('status', 'unknown')}",
            "optimization_applied": True
        }
    
    async def get_status(self) -> Dict[str, Any]:
        """获取 Agent 状态"""
        return {
            **self.status,
            "current_time": datetime.now().isoformat(),
            "project_directory": str(self.project_dir),
            "sub_agents_enabled": [agent_id for agent_id, config in self.sub_agents.items() if config.get("enabled", False)],
            "openspace_online": self.openspace_config.get("online", False),
            "active_workflows": await self._get_active_workflows()
        }
    
    async def _get_active_workflows(self) -> List[str]:
        """获取活跃的工作流程"""
        # 这里可以检查正在执行的工作流程
        return ["planning", "execution_monitoring"]
    
    async def stop(self):
        """停止 Agent"""
        logger.info("CODING Agent 正在停止...")
        self.status["stopped_at"] = datetime.now().isoformat()
        logger.info("CODING Agent 已停止")


async def main():
    """主函数"""
    print("=" * 60)
    print("CODING Agent - TradingAgents-CN 项目开发管理")
    print("=" * 60)
    
    # 创建 Agent
    agent = CODINGAgent(project_name="TradingAgents-CN")
    
    try:
        # 初始化
        print("\n[1/4] 初始化 CODING Agent...")
        if not await agent.initialize():
            print("❌ 初始化失败")
            return
        
        print("✅ CODING Agent 初始化成功")
        
        # 获取状态
        print("\n[2/4] 获取系统状态...")
        status = await agent.get_status()
        print(f"   项目: {status['project']}")
        print(f"   状态: {'已初始化' if status['initialized'] else '未初始化'}")
        print(f"   OpenSpace: {'在线' if status.get('openspace_online', False) else '离线'}")
        print(f"   子Agent: {len(status['sub_agents_enabled'])} 个已启用")
        
        # 演示创建项目方案
        print("\n[3/4] 演示创建项目开发方案...")
        requirements = {
            "functional": [
                "优化回测引擎性能",
                "集成A股数据源",
                "实现多因子模型",
                "添加风险管理模块"
            ],
            "performance": {
                "backtest_speed": "10000条数据 < 0.1秒",
                "memory_usage": "< 500MB",
                "accuracy": "> 95%"
            },
            "quality": {
                "test_coverage": "> 80%",
                "code_style": "符合PEP8",
                "documentation": "完整API文档"
            },
            "constraints": {
                "time": "2周",
                "resources": "单机部署",
                "technology": "Python 3.11+"
            }
        }
        
        plan_result = await agent.create_project_plan(requirements)
        
        if plan_result["success"]:
            print(f"✅ 项目开发方案创建成功")
            print(f"   方案ID: {plan_result['plan_id']}")
            print(f"   验证结果: {'通过' if plan_result['validation_passed'] else '未通过'}")
            print(f"   报告文件: {plan_result.get('report', {}).get('summary', {})}")
            
            # 演示调用 OpenSpace 执行
            print("\n[4/4] 演示调用 OpenSpace 执行...")
            if status.get("openspace_online", False):
                execution_result = await agent.execute_with_openspace(plan_result["plan_id"])
                
                if execution_result["success"]:
                    print(f"✅ OpenSpace 执行成功")
                    print(f"   执行ID: {execution_result['execution_id']}")
                    print(f"   使用子Agent: {', '.join(execution_result['sub_agents_used'])}")
                    print(f"   任务完成率: {execution_result['results'].get('success_rate', 0)*100:.1f}%")
                else:
                    print(f"⚠️  OpenSpace 执行失败: {execution_result.get('error', '未知错误')}")
            else:
                print("⚠️  OpenSpace 离线，跳过执行演示")
        else:
            print(f"❌ 项目开发方案创建失败: {plan_result.get('error', '未知错误')}")
        
        print("\n" + "=" * 60)
        print("演示完成！")
        print("=" * 60)
        
        # 显示下一步建议
        print("\n📋 下一步建议:")
        print("1. 配置 OpenSpace API 连接")
        print("2. 完善需求分析（集成LLM）")
        print("3. 优化任务分配算法")
        print("4. 实现实时监控面板")
        print("5. 集成版本控制系统")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  用户中断")
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 停止 Agent
        await agent.stop()


if __name__ == "__main__":
    # 运行主函数
    asyncio.run(main())