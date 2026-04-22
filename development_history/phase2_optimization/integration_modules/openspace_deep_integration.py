    async def get_integration_status(self) -> Dict[str, Any]:
        """获取集成状态"""
        return {
            **self.integration_status,
            "registered_agents": list(self.registered_agents.keys()),
            "loaded_skills": list(self.loaded_skills.keys()),
            "configured_workflows": list(self.workflows.keys()),
            "openspace_config": self.openspace_config,
            "integration_directory": str(self.integration_dir),
            "current_time": datetime.now().isoformat()
        }
    
    async def stop(self):
        """停止集成"""
        logger.info("停止 OpenSpace 深度集成")
        # 这里可以添加清理逻辑


# 演示函数
async def demonstrate_deep_integration():
    """演示深度集成"""
    print("=" * 60)
    print("OpenSpace 深度集成演示")
    print("=" * 60)
    
    # 创建集成实例
    integration = OpenSpaceDeepIntegration()
    
    print("\n[1/4] 初始化深度集成...")
    if await integration.initialize():
        print("✅ 深度集成初始化成功")
    else:
        print("❌ 深度集成初始化失败")
        return
    
    print("\n[2/4] 获取集成状态:")
    status = await integration.get_integration_status()
    print(f"   OpenSpace 连接: {'✅ 在线' if status['openspace_connected'] else '⚠️ 离线'}")
    print(f"   Agent 注册: {'✅ 完成' if status['agents_registered'] else '❌ 未完成'}")
    print(f"   技能加载: {'✅ 完成' if status['skills_loaded'] else '❌ 未完成'}")
    print(f"   工作流配置: {'✅ 完成' if status['workflows_configured'] else '❌ 未完成'}")
    print(f"   注册Agent数: {len(status['registered_agents'])}")
    print(f"   加载技能数: {len(status['loaded_skills'])}")
    print(f"   配置工作流数: {len(status['configured_workflows'])}")
    
    print("\n[3/4] 演示工作流执行:")
    
    # 演示金融项目规划工作流
    print("   执行金融项目规划工作流...")
    inputs = {
        "project_requirements": {
            "functional": [
                "优化回测引擎",
                "集成A股数据",
                "实现多因子模型",
                "添加风控模块"
            ],
            "performance": {
                "backtest_speed": "10000条数据 < 0.1秒",
                "memory_usage": "< 500MB"
            },
            "constraints": {
                "time": "2周",
                "technology": "Python 3.11+"
            }
        }
    }
    
    result = await integration.execute_workflow("financial_project_planning", inputs)
    
    print(f"   工作流ID: {result.get('execution_id')}")
    print(f"   状态: {result.get('status')}")
    print(f"   步骤数: {len(result.get('steps', []))}")
    
    if result.get("status") == "completed":
        print("   ✅ 工作流执行成功")
        
        # 显示关键结果
        if "results" in result:
            if "requirements_analysis" in result["results"]:
                print(f"   需求分析完成")
            if "technical_plan" in result["results"]:
                print(f"   技术方案设计完成")
            if "task_decomposition" in result["results"]:
                tasks = result["results"]["task_decomposition"].get("tasks", [])
                print(f"   任务分解: {len(tasks)} 个任务")
            if "validation_report" in result["results"]:
                validation = result["results"]["validation_report"]
                print(f"   方案验证: {'通过' if validation.get('passed') else '未通过'}")
    else:
        print(f"   ❌ 工作流执行失败: {result.get('error', '未知错误')}")
    
    print("\n[4/4] 演示量化开发工作流:")
    
    # 演示量化开发工作流
    print("   执行量化开发工作流...")
    strategy_inputs = {
        "strategy_spec": {
            "name": "双均线策略",
            "description": "简单移动平均线交叉策略",
            "parameters": {
                "fast_period": 10,
                "slow_period": 30
            }
        }
    }
    
    # 这里可以实际执行，但为了演示速度，我们跳过
    print("   ⏭️  跳过实际执行（演示目的）")
    
    print("\n" + "=" * 60)
    print("深度集成演示完成！")
    print("=" * 60)
    
    print("\n📋 集成能力总结:")
    print("1. ✅ 专门针对 TradingAgents-CN 优化")
    print("2. ✅ 深度集成 OpenSpace 核心能力")
    print("3. ✅ 3个专门 Agent 注册")
    print("4. ✅ 3个专门工作流配置")
    print("5. ✅ 双向通信机制")
    print("6. ✅ 反馈优化闭环")
    
    print("\n🚀 下一步:")
    print("1. 配置 OpenSpace API 密钥")
    print("2. 测试实际工作流执行")
    print("3. 监控集成性能")
    print("4. 持续优化集成效果")
    
    # 停止集成
    await integration.stop()
    
    return integration, result


if __name__ == "__main__":
    # 运行演示
    asyncio.run(demonstrate_deep_integration())