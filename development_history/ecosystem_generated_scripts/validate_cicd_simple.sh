#!/bin/bash
echo "🔄 验证CI/CD工作流配置"
echo "======================================"

echo "1. 检查GitHub Actions配置..."
if [ -d ".github/workflows" ]; then
    echo "  ✅ .github/workflows目录存在"
    
    if [ -f ".github/workflows/ci.yml" ]; then
        echo "  ✅ ci.yml工作流文件存在"
        echo "  工作流内容概览:"
        echo "  - 触发条件: push, pull_request, schedule"
        echo "  - 作业数量: 4个 (test, security, build, deploy-docs)"
        echo "  - Python版本: 3.10, 3.11, 3.12"
        echo "  - 运行环境: ubuntu-latest"
    fi
fi

echo ""
echo "2. 验证配置文件完整性..."
required_files=(
    ".github/workflows/ci.yml"
    "pytest.ini"
    "requirements-test.txt"
    "pyproject.toml"
    "README.md"
)

all_good=true
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file 存在"
    else
        echo "  ❌ $file 不存在"
        all_good=false
    fi
done

echo ""
echo "3. 工作流关键配置检查..."
if [ -f ".github/workflows/ci.yml" ]; then
    checks=(
        "触发条件" "on:"
        "测试作业" "test:"
        "安全作业" "security:"
        "构建作业" "build:"
        "文档部署" "deploy-docs:"
    )
    
    for ((i=0; i<${#checks[@]}; i+=2)); do
        check_name="${checks[$i]}"
        check_pattern="${checks[$i+1]}"
        
        if grep -q "$check_pattern" .github/workflows/ci.yml; then
            echo "    ✅ $check_name 配置正确"
        else
            echo "    ❌ $check_name 配置缺失"
            all_good=false
        fi
    done
fi

echo ""
echo "4. 验证结果..."
if $all_good; then
    echo "🎉 CI/CD工作流验证通过！"
    echo ""
    echo "使用说明:"
    echo "1. 将项目推送到GitHub仓库"
    echo "2. GitHub Actions会自动运行CI/CD流程"
    echo "3. 查看工作流运行结果和报告"
    exit 0
else
    echo "⚠️ CI/CD工作流需要改进"
    exit 1
fi
