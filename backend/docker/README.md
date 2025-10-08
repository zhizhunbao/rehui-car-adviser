# Docker 配置说明

这个目录包含了用于运行车型数据收集脚本的Docker配置文件。

## 文件说明

- `Dockerfile` - Docker镜像构建文件
- `docker-compose.yml` - Docker Compose配置文件
- `entrypoint.sh` - 容器启动入口脚本
- `.dockerignore` - Docker构建时忽略的文件
- `README.md` - 本说明文件

## 使用方法

### 1. 构建镜像

```bash
# 在backend目录下执行
cd backend
docker build -f docker/Dockerfile -t rehui-car-models-collector .
```

### 2. 使用Docker Compose运行

```bash
# 在backend目录下执行
cd backend
docker-compose -f docker/docker-compose.yml up
```

### 3. 运行特定命令

```bash
# 查看帮助
docker-compose -f docker/docker-compose.yml run --rm car-models-collector python scripts/collect_models.py --help

# 收集特定品牌的数据
docker-compose -f docker/docker-compose.yml run --rm car-models-collector python scripts/collect_models.py --brand toyota

# 进入容器调试
docker-compose -f docker/docker-compose.yml run --rm car-models-collector bash
```

### 4. 开发模式

```bash
# 启动开发环境
docker-compose -f docker/docker-compose.yml --profile dev up car-models-collector-dev
```

## 环境变量

确保在`.env`文件中设置以下环境变量：

```env
GOOGLE_GEMINI_API_KEY=your_gemini_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
DEBUG=false
ENVIRONMENT=production
```

## 数据持久化

容器会将以下目录挂载到宿主机：

- `./data` - 收集的数据文件
- `./logs` - 日志文件
- `./chrome_profiles` - Chrome用户配置文件
- `./tmp` - 临时文件

## 故障排除

### 1. Chrome启动失败
确保容器有足够的内存（建议至少1GB）和正确的权限。

### 2. 网络问题
如果遇到网络连接问题，可以尝试使用`--network host`模式。

### 3. 权限问题
确保挂载的目录有正确的读写权限。

## 资源限制

默认配置：
- 内存限制：2GB
- CPU限制：1核心
- 内存预留：1GB
- CPU预留：0.5核心

可以根据需要调整`docker-compose.yml`中的资源限制。
