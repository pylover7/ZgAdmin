# PyTool 

## Version
当前版本: 1.0.1

## Docker 使用

### 方式一：直接运行

#### 拉取镜像

```bash
docker pull docker.cnb.cool/pylover/pytool
```

#### 运行容器

```bash
docker run -d \
  --name pytool-app \
  -p 80:80 \
  -p 7001:7001 \
  docker.cnb.cool/pylover/pytool
```

### 方式二：Docker Compose

#### 启动服务

```bash
docker compose up -d
```

#### 停止服务

```bash
docker compose down
```

#### 查看日志

```bash
docker compose logs -f
```

### 访问应用

- 前端：http://localhost:80
- 后端API：http://localhost:7001
