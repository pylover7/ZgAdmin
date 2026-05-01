#!/bin/bash -e

# 记录脚本开始时间
start_time=$(date +%s)

# 从 VERSION 文件读取版本号
if [ -f "VERSION" ]; then
    export IMAGE_VERSION=$(cat VERSION)
    echo "从 VERSION 文件读取版本号: $IMAGE_VERSION"
else
    export IMAGE_VERSION="1.0.0"
    echo "VERSION 文件不存在，使用默认版本号: $IMAGE_VERSION"
fi

# 显示开始时间（可选）
echo "脚本开始执行时间: $(date -d @$start_time '+%Y-%m-%d %H:%M:%S')"

# 执行Docker构建
docker build -t ${CNB_DOCKER_REGISTRY}/${CNB_REPO_SLUG_LOWERCASE}:${IMAGE_VERSION} .

# 打 tag
docker tag ${CNB_DOCKER_REGISTRY}/${CNB_REPO_SLUG_LOWERCASE}:${IMAGE_VERSION} ${CNB_DOCKER_REGISTRY}/${CNB_REPO_SLUG_LOWERCASE}:latest

# 执行Docker推送
docker push ${CNB_DOCKER_REGISTRY}/${CNB_REPO_SLUG_LOWERCASE}:${IMAGE_VERSION}
docker push ${CNB_DOCKER_REGISTRY}/${CNB_REPO_SLUG_LOWERCASE}:latest

# 记录脚本结束时间
end_time=$(date +%s)

# 计算总用时（秒）
total_time=$((end_time - start_time))

# 转换为更易读的格式
hours=$((total_time / 3600))
minutes=$(( (total_time % 3600) / 60 ))
seconds=$((total_time % 60))

# 输出总用时
echo "===================================="
echo "脚本执行完成"
echo "总用时: ${total_time}秒 (${hours}小时 ${minutes}分钟 ${seconds}秒)"
echo "脚本结束时间: $(date -d @$end_time '+%Y-%m-%d %H:%M:%S')"
echo "===================================="
