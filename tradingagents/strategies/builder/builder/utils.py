# -*- coding: utf-8 -*-
"""
utils.py - 工具函数

从 builder.py 拆分
"""

def generate_builder_html() -> str:
    """生成可视化构建器 HTML"""

    html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TradingAgents-CN 可视化策略构建器</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #e0e0e0;
        }

        .header {
            background: rgba(0, 0, 0, 0.3);
            padding: 20px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .header h1 {
            color: #00d4ff;
            font-size: 24px;
        }

        .header-actions {
            display: flex;
            gap: 10px;
        }

        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s;
        }

        .btn-primary {
            background: #00d4ff;
            color: #1a1a2e;
        }

        .btn-primary:hover {
            background: #00b8e6;
            transform: translateY(-2px);
        }

        .btn-secondary {
            background: rgba(255, 255, 255, 0.1);
            color: #e0e0e0;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.2);
        }

        .btn-success {
            background: #00c853;
            color: white;
        }

        .btn-success:hover {
            background: #00a844;
        }

        .btn-danger {
            background: #ff5252;
            color: white;
        }

        .btn-danger:hover {
            background: #e04848;
        }

        .main-container {
            display: grid;
            grid-template-columns: 280px 1fr 320px;
            gap: 0;
            height: calc(100vh - 80px);
        }

        .panel {
            background: rgba(0, 0, 0, 0.2);
            border-right: 1px solid rgba(255, 255, 255, 0.1);
            overflow-y: auto;
            padding: 20px;
        }

        .panel:last-child {
            border-right: none;
            border-left: 1px solid rgba(255, 255, 255, 0.1);
        }

        .panel-header {
            font-size: 16px;
            font-weight: 600;
            color: #00d4ff;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .component-group {
            margin-bottom: 20px;
        }

        .component-group h4 {
            font-size: 13px;
            color: #888;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .component-item {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 12px 15px;
            margin-bottom: 8px;
            cursor: grab;
            transition: all 0.2s;
        }

        .component-item:hover {
            background: rgba(255, 255, 255, 0.1);
            border-color: #00d4ff;
            transform: translateX(5px);
        }

        .component-item.dragging {
            opacity: 0.5;
            cursor: grabbing;
        }

        .component-item .name {
            font-weight: 600;
            color: #fff;
            margin-bottom: 4px;
        }

        .component-item .desc {
            font-size: 12px;
            color: #888;
        }

        .indicator-item {
            border-left: 3px solid #4caf50;
        }

        .condition-item {
            border-left: 3px solid #ff9800;
        }

        .signal-item {
            border-left: 3px solid #2196f3;
        }

        .canvas {
            background: rgba(0, 0, 0, 0.3);
            padding: 20px;
        }

        .strategy-config {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }

        .config-row {
            display: grid;
            grid-template-columns: 120px 1fr;
            gap: 15px;
            margin-bottom: 15px;
            align-items: center;
        }

        .config-label {
            font-size: 13px;
            color: #888;
        }

        .config-input {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 6px;
            padding: 8px 12px;
            color: #fff;
            font-size: 14px;
            width: 100%;
        }

        .config-input:focus {
            outline: none;
            border-color: #00d4ff;
        }

        .drop-zone {
            background: rgba(255, 255, 255, 0.02);
            border: 2px dashed rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            min-height: 200px;
            padding: 20px;
            transition: all 0.3s;
        }

        .drop-zone.drag-over {
            background: rgba(0, 212, 255, 0.1);
            border-color: #00d4ff;
        }

        .drop-zone-title {
            text-align: center;
            color: #666;
            padding: 40px;
            font-size: 14px;
        }

        .strategy-section {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            margin-bottom: 15px;
            overflow: hidden;
        }

        .section-header {
            background: rgba(0, 0, 0, 0.3);
            padding: 12px 15px;
            font-weight: 600;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .section-header.buy {
            color: #ff5252;
            border-left: 3px solid #ff5252;
        }

        .section-header.sell {
            color: #00c853;
            border-left: 3px solid #00c853;
        }

        .section-body {
            padding: 15px;
        }

        .condition-tag {
            display: inline-flex;
            align-items: center;
            background: rgba(255, 152, 0, 0.2);
            border: 1px solid #ff9800;
            border-radius: 20px;
            padding: 6px 12px;
            margin: 5px;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .condition-tag:hover {
            background: rgba(255, 152, 0, 0.4);
        }

        .condition-tag .remove {
            margin-left: 8px;
            cursor: pointer;
            color: #ff9800;
        }

        .template-list {
            margin-top: 20px;
        }

        .template-item {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 10px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .template-item:hover {
            background: rgba(0, 212, 255, 0.1);
            border: 1px solid rgba(0, 212, 255, 0.3);
        }

        .template-item h5 {
            color: #00d4ff;
            margin-bottom: 5px;
        }

        .template-item p {
            font-size: 12px;
            color: #888;
        }

        .preview-section {
            margin-top: 20px;
        }

        .preview-code {
            background: rgba(0, 0, 0, 0.4);
            border-radius: 8px;
            padding: 15px;
            font-family: "Consolas", monospace;
            font-size: 12px;
            max-height: 300px;
            overflow-y: auto;
            white-space: pre-wrap;
            color: #a0e0a0;
        }

        .indicator-list, .condition-list {
            margin-bottom: 15px;
        }

        .indicator-tag {
            background: rgba(76, 175, 80, 0.2);
            border: 1px solid #4caf50;
        }

        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }

        .modal.show {
            display: flex;
        }

        .modal-content {
            background: #1a1a2e;
            border-radius: 12px;
            padding: 30px;
            max-width: 500px;
            width: 90%;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .modal-header {
            font-size: 18px;
            font-weight: 600;
            color: #00d4ff;
            margin-bottom: 20px;
        }

        .modal-body {
            margin-bottom: 20px;
        }

        .modal-footer {
            display: flex;
            justify-content: flex-end;
            gap: 10px;
        }

        .param-row {
            margin-bottom: 15px;
        }

        .param-row label {
            display: block;
            font-size: 13px;
            color: #888;
            margin-bottom: 5px;
        }

        .param-row input, .param-row select {
            width: 100%;
            padding: 10px;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 6px;
            color: #fff;
        }

        .toast {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: #00c853;
            color: white;
            padding: 15px 25px;
            border-radius: 8px;
            display: none;
            z-index: 2000;
            animation: slideIn 0.3s ease;
        }

        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }

        .indicator-preview {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }

        .indicator-preview .tag {
            background: rgba(76, 175, 80, 0.2);
            border: 1px solid #4caf50;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>TradingAgents-CN 可视化策略构建器</h1>
        <div class="header-actions">
            <button class="btn btn-secondary" onclick="loadTemplate()">加载模板</button>
            <button class="btn btn-secondary" onclick="newStrategy()">新建策略</button>
            <button class="btn btn-primary" onclick="compileStrategy()">编译策略</button>
            <button class="btn btn-success" onclick="exportCode()">导出代码</button>
        </div>
    </div>

    <div class="main-container">
        <!-- 组件库面板 -->
        <div class="panel">
            <div class="panel-header">组件库</div>

            <div class="component-group">
                <h4>指标组件</h4>
                <div class="component-item indicator-item" draggable="true" data-type="indicator" data-name="MA" data-params=\'{"period": 5}\'>
                    <div class="name">MA 移动平均</div>
                    <div class="desc">计算N日收盘价均值</div>
                </div>
                <div class="component-item indicator-item" draggable="true" data-type="indicator" data-name="MACD" data-params=\'{"fast_period": 12, "slow_period": 26, "signal_period": 9}\'>
                    <div class="name">MACD</div>
                    <div class="desc">指数平滑异同移动平均线</div>
                </div>
                <div class="component-item indicator-item" draggable="true" data-type="indicator" data-name="RSI" data-params=\'{"period": 14}\'>
                    <div class="name">RSI 相对强弱</div>
                    <div class="desc">衡量价格涨跌动力的指标</div>
                </div>
                <div class="component-item indicator-item" draggable="true" data-type="indicator" data-name="KDJ" data-params=\'{"n": 9, "m1": 3, "m2": 3}\'>
                    <div class="name">KDJ 随机指标</div>
                    <div class="desc">随机指标超买超卖分析</div>
                </div>
                <div class="component-item indicator-item" draggable="true" data-type="indicator" data-name="BOLL" data-params=\'{"period": 20, "std_dev": 2}\'>
                    <div class="name">BOLL 布林带</div>
                    <div class="desc">价格波动范围的指标</div>
                </div>
                <div class="component-item indicator-item" draggable="true" data-type="indicator" data-name="Volume" data-params=\'{"period": 5}\'>
                    <div class="name">Volume 成交量</div>
                    <div class="desc">成交量移动平均</div>
                </div>
            </div>

            <div class="component-group">
                <h4>条件组件</h4>
                <div class="component-item condition-item" draggable="true" data-type="condition" data-name="PriceCondition" data-params=\'{"operator": "gt"}\'>
                    <div class="name">价格条件</div>
                    <div class="desc">价格比较/穿越条件</div>
                </div>
                <div class="component-item condition-item" draggable="true" data-type="condition" data-name="IndicatorCondition" data-params=\'{"indicator_name": "", "operator": "gt"}\'>
                    <div class="name">指标条件</div>
                    <div class="desc">指标值比较/穿越条件</div>
                </div>
                <div class="component-item condition-item" draggable="true" data-type="condition" data-name="MACDCross" data-params=\'{"cross_type": "cross_up"}\'>
                    <div class="name">MACD交叉</div>
                    <div class="desc">MACD金叉/死叉条件</div>
                </div>
                <div class="component-item condition-item" draggable="true" data-type="condition" data-name="VolumeCondition" data-params=\'{"condition": "spike", "ratio": 1.5}\'>
                    <div class="name">成交量条件</div>
                    <div class="desc">放量/缩量/突破条件</div>
                </div>
            </div>

            <div class="component-group">
                <h4>逻辑组合</h4>
                <div class="component-item" draggable="true" data-type="logic" data-name="AND" data-params=\'{}\'>
                    <div class="name">AND 与</div>
                    <div class="desc">所有条件同时满足</div>
                </div>
                <div class="component-item" draggable="true" data-type="logic" data-name="OR" data-params=\'{}\'>
                    <div class="name">OR 或</div>
                    <div class="desc">任一条件满足</div>
                </div>
                <div class="component-item" draggable="true" data-type="logic" data-name="NOT" data-params=\'{}\'>
                    <div class="name">NOT 非</div>
                    <div class="desc">条件取反</div>
                </div>
            </div>
        </div>

        <!-- 画布区域 -->
        <div class="canvas">
            <div class="strategy-config">
                <h3 style="color: #00d4ff; margin-bottom: 15px;">策略配置</h3>
                <div class="config-row">
                    <label class="config-label">策略名称</label>
                    <input type="text" id="strategyName" class="config-input" value="均线交叉策略" placeholder="输入策略名称">
                </div>
                <div class="config-row">
                    <label class="config-label">股票代码</label>
                    <input type="text" id="symbolCode" class="config-input" value="000001.SZ" placeholder="如: 000001.SZ">
                </div>
                <div class="config-row">
                    <label class="config-label">初始资金</label>
                    <input type="number" id="initialCapital" class="config-input" value="1000000" placeholder="初始资金">
                </div>
                <div class="config-row">
                    <label class="config-label">仓位比例</label>
                    <input type="number" id="positionSize" class="config-input" value="30" placeholder="单股最大仓位(%)">
                </div>
            </div>

            <!-- 策略预览 -->
            <div class="strategy-section">
                <div class="section-header" style="color: #4caf50; border-left: 3px solid #4caf50;">
                    指标列表
                </div>
                <div class="section-body">
                    <div class="indicator-preview" id="indicatorList">
                        <span style="color: #666; font-size: 13px;">从左侧拖拽指标组件到这里</span>
                    </div>
                </div>
            </div>

            <div class="strategy-section">
                <div class="section-header buy">
                    <span>买入条件</span>
                    <span style="font-size: 12px; color: #888;">拖拽条件组件</span>
                </div>
                <div class="section-body drop-zone" id="buyDropZone">
                    <div class="drop-zone-title">将条件组件拖拽到此处构建买入信号</div>
                </div>
            </div>

            <div class="strategy-section">
                <div class="section-header sell">
                    <span>卖出条件</span>
                    <span style="font-size: 12px; color: #888;">拖拽条件组件</span>
                </div>
                <div class="section-body drop-zone" id="sellDropZone">
                    <div class="drop-zone-title">将条件组件拖拽到此处构建卖出信号</div>
                </div>
            </div>
        </div>

        <!-- 预览面板 -->
        <div class="panel">
            <div class="panel-header">策略预览</div>

            <div class="preview-section">
                <h4 style="color: #888; margin-bottom: 10px;">策略摘要</h4>
                <div id="strategySummary" style="font-size: 13px; color: #aaa;">
                    暂无策略
                </div>
            </div>

            <div class="preview-section">
                <h4 style="color: #888; margin-bottom: 10px;">生成的代码</h4>
                <div class="preview-code" id="codePreview">
                    // 编译后显示代码
                </div>
            </div>

            <div class="template-list">
                <h4 style="color: #888; margin-bottom: 10px;">快速模板</h4>
                <div class="template-item" onclick="useTemplate('ma_crossover')">
                    <h5>均线交叉策略</h5>
                    <p>MA5/MA20 金叉买入，死叉卖出</p>
                </div>
                <div class="template-item" onclick="useTemplate('macd_crossover')">
                    <h5>MACD 交叉策略</h5>
                    <p>MACD 金叉买入，死叉卖出</p>
                </div>
                <div class="template-item" onclick="useTemplate('rsi_reversion')">
                    <h5>RSI 均值回归</h5>
                    <p>RSI 超卖买入，超买卖出</p>
                </div>
                <div class="template-item" onclick="useTemplate('boll_breakout')">
                    <h5>布林带突破</h5>
                    <p>突破上轨买入，跌破下轨卖出</p>
                </div>
            </div>
        </div>
    </div>

    <!-- 模板选择弹窗 -->
    <div class="modal" id="templateModal">
        <div class="modal-content">
            <div class="modal-header">加载模板</div>
            <div class="modal-body">
                <div class="param-row">
                    <label>选择模板</label>
                    <select id="templateSelect">
                        <option value="ma_crossover">均线交叉策略</option>
                        <option value="macd_crossover">MACD 交叉策略</option>
                        <option value="rsi_reversion">RSI 均值回归</option>
                        <option value="boll_breakout">布林带突破</option>
                    </select>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeModal()">取消</button>
                <button class="btn btn-primary" onclick="confirmLoadTemplate()">加载</button>
            </div>
        </div>
    </div>

    <!-- 提示 -->
    <div class="toast" id="toast">操作成功</div>

    <script>
        // 状态管理
        let state = {
            strategy: {
                name: "均线交叉策略",
                symbols: ["000001.SZ"],
                indicators: [],
                buyConditions: [],
                sellConditions: [],
                initialCapital: 1000000,
                positionSize: 0.3
            }
        };

        // 拖拽初始化
        document.querySelectorAll('.component-item[draggable="true"]').forEach(item => {
            item.addEventListener('dragstart', handleDragStart);
            item.addEventListener('dragend', handleDragEnd);
        });

        // 放置区域
        document.querySelectorAll('.drop-zone').forEach(zone => {
            zone.addEventListener('dragover', handleDragOver);
            zone.addEventListener('dragleave', handleDragLeave);
            zone.addEventListener('drop', handleDrop);
        });

        function handleDragStart(e) {
            e.dataTransfer.setData('text/plain', JSON.stringify({
                type: e.target.dataset.type,
                name: e.target.dataset.name,
                params: JSON.parse(e.target.dataset.params || '{}')
            }));
            e.target.classList.add('dragging');
        }

        function handleDragEnd(e) {
            e.target.classList.remove('dragging');
        }

        function handleDragOver(e) {
            e.preventDefault();
            e.currentTarget.classList.add('drag-over');
        }

        function handleDragLeave(e) {
            e.currentTarget.classList.remove('drag-over');
        }

        function handleDrop(e) {
            e.preventDefault();
            e.currentTarget.classList.remove('drag-over');

            const data = JSON.parse(e.dataTransfer.getData('text/plain'));
            const zoneId = e.currentTarget.id;

            if (zoneId === 'buyDropZone' && data.type === 'condition') {
                addCondition(data, 'buy');
            } else if (zoneId === 'sellDropZone' && data.type === 'condition') {
                addCondition(data, 'sell');
            } else if (data.type === 'indicator') {
                addIndicator(data);
            }

            updatePreview();
        }

        function addIndicator(data) {
            const exists = state.strategy.indicators.some(i => i.name === data.name);
            if (!exists) {
                state.strategy.indicators.push({
                    name: data.name,
                    type: data.name,
                    params: data.params
                });
                showToast(`已添加指标: ${data.name}`);
            } else {
                showToast('指标已存在', 'info');
            }
            renderIndicators();
        }

        function addCondition(data, signalType) {
            const conditions = signalType === 'buy' ? state.strategy.buyConditions : state.strategy.sellConditions;
            conditions.push({
                name: data.name,
                type: data.name,
                params: data.params
            });
            showToast(`已添加${signalType === 'buy' ? '买入' : '卖出'}条件: ${data.name}`);
            renderConditions();
        }

        function removeCondition(name, signalType) {
            const conditions = signalType === 'buy' ? state.strategy.buyConditions : state.strategy.sellConditions;
            const index = conditions.findIndex(c => c.name === name);
            if (index > -1) {
                conditions.splice(index, 1);
            }
            renderConditions();
            updatePreview();
        }

        function renderIndicators() {
            const container = document.getElementById('indicatorList');
            if (state.strategy.indicators.length === 0) {
                container.innerHTML = '<span style="color: #666; font-size: 13px;">从左侧拖拽指标组件到这里</span>';
                return;
            }
            container.innerHTML = state.strategy.indicators.map(i =>
                `<span class="tag">${i.name}</span>`
            ).join('');
        }

        function renderConditions() {
            // 买入
            const buyZone = document.getElementById('buyDropZone');
            if (state.strategy.buyConditions.length === 0) {
                buyZone.innerHTML = '<div class="drop-zone-title">将条件组件拖拽到此处构建买入信号</div>';
            } else {
                buyZone.innerHTML = state.strategy.buyConditions.map(c =>
                    `<span class="condition-tag">${c.name}<span class="remove" onclick="removeCondition('${c.name}', 'buy')">x</span></span>`
                ).join('');
            }

            // 卖出
            const sellZone = document.getElementById('sellDropZone');
            if (state.strategy.sellConditions.length === 0) {
                sellZone.innerHTML = '<div class="drop-zone-title">将条件组件拖拽到此处构建卖出信号</div>';
            } else {
                sellZone.innerHTML = state.strategy.sellConditions.map(c =>
                    `<span class="condition-tag">${c.name}<span class="remove" onclick="removeCondition('${c.name}', 'sell')">x</span></span>`
                ).join('');
            }
        }

        function updatePreview() {
            // 更新摘要
            document.getElementById('strategySummary').innerHTML = `
                <p><strong>名称:</strong> ${state.strategy.name}</p>
                <p><strong>股票:</strong> ${state.strategy.symbols.join(', ')}</p>
                <p><strong>指标:</strong> ${state.strategy.indicators.length}个</p>
                <p><strong>买入条件:</strong> ${state.strategy.buyConditions.length}个</p>
                <p><strong>卖出条件:</strong> ${state.strategy.sellConditions.length}个</p>
            `;
        }

        function compileStrategy() {
            // 收集配置
            state.strategy.name = document.getElementById('strategyName').value;
            state.strategy.symbols = [document.getElementById('symbolCode').value];
            state.strategy.initialCapital = parseFloat(document.getElementById('initialCapital').value);
            state.strategy.positionSize = parseFloat(document.getElementById('positionSize').value) / 100;

            // 生成代码预览（这里简化处理，实际应调用后端）
            const code = generateCodePreview();
            document.getElementById('codePreview').textContent = code;

            showToast('策略编译成功');
        }

        function generateCodePreview() {
            const { name, symbols, indicators, buyConditions, sellConditions, initialCapital } = state.strategy;

            return `# ${name}
# Generated by Visual Strategy Builder

class ${name.replace(/\\s+/g, '')}Strategy:
    def __init__(self):
        self.name = "${name}"
        self.symbols = ${JSON.stringify(symbols)}
        self.initial_capital = ${initialCapital}

    def on_bar(self, bar):
        # Indicators: ${indicators.map(i => i.name).join(', ')}
        # Buy Conditions: ${buyConditions.map(c => c.name).join(', ')}
        # Sell Conditions: ${sellConditions.map(c => c.name).join(', ')}
        pass
`;
        }

        function exportCode() {
            compileStrategy();
            const code = document.getElementById('codePreview').textContent;
            const blob = new Blob([code], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${state.strategy.name.replace(/\\s+/g, '_')}_strategy.py`;
            a.click();
            URL.revokeObjectURL(url);
            showToast('代码已导出');
        }

        function useTemplate(templateName) {
            const templates = {
                'ma_crossover': {
                    name: '均线交叉策略',
                    indicators: [
                        { name: 'MA5', type: 'MA', params: { period: 5 } },
                        { name: 'MA20', type: 'MA', params: { period: 20 } }
                    ],
                    buyConditions: [{ name: '金叉', type: 'IndicatorCondition', params: {} }],
                    sellConditions: [{ name: '死叉', type: 'IndicatorCondition', params: {} }]
                }
            };

            const template = templates[templateName];
            if (template) {
                Object.assign(state.strategy, template);
                document.getElementById('strategyName').value = template.name;
                renderIndicators();
                renderConditions();
                updatePreview();
                showToast(`已加载模板: ${template.name}`);
            }
        }

        function loadTemplate() {
            document.getElementById('templateModal').classList.add('show');
        }

        function closeModal() {
            document.getElementById('templateModal').classList.remove('show');
        }

        function confirmLoadTemplate() {
            const templateName = document.getElementById('templateSelect').value;
            useTemplate(templateName);
            closeModal();
        }

        function newStrategy() {
            state.strategy = {
                name: "新策略",
                symbols: ["000001.SZ"],
                indicators: [],
                buyConditions: [],
                sellConditions: [],
                initialCapital: 1000000,
                positionSize: 0.3
            };
            document.getElementById('strategyName').value = '';
            document.getElementById('symbolCode').value = '000001.SZ';
            document.getElementById('initialCapital').value = '1000000';
            document.getElementById('positionSize').value = '30';
            renderIndicators();
            renderConditions();
            updatePreview();
            showToast('已创建新策略');
        }

        function showToast(message, type = 'success') {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.style.display = 'block';
            setTimeout(() => {
                toast.style.display = 'none';
            }, 2000);
        }

        // 初始化
        renderIndicators();
        renderConditions();
        updatePreview();
    </script>
</body>
</html>
'''

    return html


def save_builder_html(filepath: str = None) -> str:
    """保存可视化构建器 HTML"""
    if filepath is None:
        filepath = os.path.join(
            Path(__file__).parent.parent.parent,
            "examples",
            "strategy_builder.html"
        )

    html = generate_builder_html()
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    logger.info(f"Saved strategy builder HTML to: {filepath}")
    return filepath
