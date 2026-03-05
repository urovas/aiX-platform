# AutoExam 部署文档

**版本**: v1.0.0  
**日期**: 2026-03-02  
**状态**: 已发布

---

## 目录

1. [系统要求](#系统要求)
2. [环境准备](#环境准备)
3. [安装步骤](#安装步骤)
4. [配置说明](#配置说明)
5. [启动服务](#启动服务)
6. [验证部署](#验证部署)
7. [CARLA集成](#carla集成)
8. [Apollo集成](#apollo集成)
9. [生产环境部署](#生产环境部署)
10. [故障排除](#故障排除)

---

## 系统要求

### 硬件要求

| 组件 | 最低配置 | 推荐配置 | 说明 |
|------|----------|----------|------|
| CPU | 4核 | 8核+ | 场景生成和测试执行需要计算资源 |
| 内存 | 8GB | 16GB+ | 大规模场景生成需要更多内存 |
| 磁盘 | 20GB | 50GB+ | 场景库和测试结果存储 |
| GPU | 可选 | NVIDIA GTX 1060+ | CARLA仿真需要 |

### 软件要求

| 软件 | 版本 | 说明 |
|------|------|------|
| 操作系统 | Ubuntu 20.04+ | Linux系统 |
| Python | 3.9+ | 核心运行环境 |
| Conda | 4.10+ | 环境管理 |
| CARLA | 0.9.13+ | 仿真环境（可选） |
| Apollo | 10.0 | 真实系统（可选） |

---

## 环境准备

### 1. 系统更新

```bash
# 更新系统包
sudo apt-get update
sudo apt-get upgrade -y

# 安装基础依赖
sudo apt-get install -y \
    git \
    wget \
    curl \
    build-essential \
    python3-dev \
    python3-pip
```

### 2. Conda安装

```bash
# 下载Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

# 安装
bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda3

# 初始化
$HOME/miniconda3/bin/conda init bash
source ~/.bashrc

# 验证
conda --version
```

---

## 安装步骤

### 方法一：使用安装脚本（推荐）

```bash
# 1. 克隆项目
git clone <repository-url>
cd AutoExam

# 2. 运行安装脚本
bash install_env.sh

# 3. 激活环境
conda activate autoexam
```

### 方法二：手动安装

```bash
# 1. 创建Conda环境
conda create -n autoexam python=3.9 -y

# 2. 激活环境
conda activate autoexam

# 3. 安装依赖
pip install -r requirements.txt

# 4. 创建必要目录
mkdir -p scenarios results reports openscenario
```

### 依赖列表

**requirements.txt**:
```
flask>=2.0.0
numpy>=1.20.0
matplotlib>=3.3.0
scikit-learn>=0.24.0
pytest>=7.0.0
pytest-cov>=3.0.0
```

---

## 配置说明

### 1. 配置文件

创建 `config.yaml`:

```yaml
# AutoExam 配置文件

# 系统配置
system:
  debug: false
  host: "0.0.0.0"
  port: 5000
  secret_key: "your-secret-key-here"

# 场景库配置
library:
  base_path: "./scenarios"
  max_scenarios: 10000

# CARLA配置
carla:
  enabled: false
  host: "localhost"
  port: 2000
  timeout: 10.0
  map: "Town03"

# Apollo配置
apollo:
  enabled: false
  host: "localhost"
  port: 8888
  bridge_port: 9090

# 生成器配置
generator:
  default_count: 10
  max_count: 500
  use_llm: false

# 导出配置
exporter:
  output_dir: "./openscenario"
  format: "xosc"

# 日志配置
logging:
  level: "INFO"
  file: "./logs/autoexam.log"
  max_size: "10MB"
  backup_count: 5
```

### 2. 环境变量

```bash
# 添加到 ~/.bashrc
export AUTOEXAM_CONFIG="/path/to/config.yaml"
export AUTOEXAM_ENV="production"
export CARLA_ROOT="/path/to/carla"
export APOLLO_ROOT="/path/to/apollo"
```

---

## 启动服务

### 开发环境

```bash
# 1. 激活环境
conda activate autoexam

# 2. 启动Web服务
python ui/app.py

# 服务将在 http://localhost:5000 启动
```

### 生产环境

```bash
# 使用Gunicorn启动
conda activate autoexam
gunicorn -w 4 -b 0.0.0.0:5000 ui.app:app

# 或使用启动脚本
bash start.sh
```

### 后台运行

```bash
# 使用nohup
nohup python ui/app.py > logs/autoexam.log 2>&1 &

# 或使用systemd（推荐）
sudo systemctl start autoexam
```

---

## 验证部署

### 1. 服务状态检查

```bash
# 检查端口
netstat -tlnp | grep 5000

# 或
curl http://localhost:5000/api/statistics
```

### 2. 功能验证

```bash
# 测试场景生成
curl -X POST http://localhost:5000/api/unprotected_left_turn/generate \
  -H "Content-Type: application/json" \
  -d '{"count": 5, "difficulty": "medium"}'

# 测试场景列表
curl http://localhost:5000/api/unprotected_left_turn/scenarios
```

### 3. 日志检查

```bash
# 查看日志
tail -f logs/autoexam.log

# 检查错误
grep "ERROR" logs/autoexam.log
```

---

## CARLA集成

### 1. CARLA安装

```bash
# 下载CARLA
cd /path/to/carla
wget https://carla-releases.s3.eu-west-3.amazonaws.com/Linux/CARLA_0.9.13.tar.gz
tar -xvzf CARLA_0.9.13.tar.gz

# 安装Python API
cd PythonAPI/carla/dist
pip install carla-0.9.13-py3.7-linux-x86_64.egg
```

### 2. 启动CARLA

```bash
# 启动CARLA服务器
cd /path/to/carla
./CarlaUE4.sh -RenderOffScreen -nosound

# 或使用显示模式
./CarlaUE4.sh -quality-level=Low
```

### 3. 配置AutoExam

```yaml
# config.yaml
carla:
  enabled: true
  host: "localhost"
  port: 2000
  timeout: 10.0
  map: "Town03"
```

### 4. 验证连接

```bash
# 测试CARLA连接
python -c "
import carla
client = carla.Client('localhost', 2000)
client.set_timeout(10.0)
world = client.get_world()
print('CARLA连接成功:', world.get_map().name)
"
```

---

## Apollo集成

### 1. Apollo安装

参考 [Apollo官方文档](https://apollo.auto/)

```bash
# 克隆Apollo
git clone https://github.com/ApolloAuto/apollo.git
cd apollo

# 启动Docker环境
bash docker/scripts/dev_start.sh
bash docker/scripts/dev_into.sh

# 编译
./apollo.sh config
./apollo.sh build
```

### 2. 启动Apollo

```bash
# 在Docker内
bash scripts/bootstrap.sh

# 启动Dreamview
bash scripts/bootstrap.sh start
```

### 3. 配置AutoExam

```yaml
# config.yaml
apollo:
  enabled: true
  host: "localhost"
  port: 8888
  bridge_port: 9090
```

---

## 生产环境部署

### 1. 使用Docker部署

**Dockerfile**:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 创建目录
RUN mkdir -p scenarios results reports openscenario logs

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "ui.app:app"]
```

**构建和运行**:
```bash
# 构建镜像
docker build -t autoexam:v1.0.0 .

# 运行容器
docker run -d \
  -p 5000:5000 \
  -v $(pwd)/scenarios:/app/scenarios \
  -v $(pwd)/results:/app/results \
  -v $(pwd)/reports:/app/reports \
  --name autoexam \
  autoexam:v1.0.0
```

### 2. 使用Docker Compose

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  autoexam:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./scenarios:/app/scenarios
      - ./results:/app/results
      - ./reports:/app/reports
      - ./logs:/app/logs
    environment:
      - AUTOEXAM_ENV=production
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - autoexam
    restart: unless-stopped
```

**启动**:
```bash
docker-compose up -d
```

### 3. 使用Systemd

**autoexam.service**:
```ini
[Unit]
Description=AutoExam Web Service
After=network.target

[Service]
Type=simple
User=autoexam
WorkingDirectory=/home/autoexam/AutoExam
Environment="PATH=/home/autoexam/miniconda3/envs/autoexam/bin"
Environment="AUTOEXAM_ENV=production"
ExecStart=/home/autoexam/miniconda3/envs/autoexam/bin/gunicorn -w 4 -b 0.0.0.0:5000 ui.app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**启用服务**:
```bash
sudo cp autoexam.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable autoexam
sudo systemctl start autoexam
```

---

## 故障排除

### 常见问题

#### 1. 端口被占用

```bash
# 检查端口占用
sudo lsof -i :5000

# 终止进程
sudo kill -9 <PID>

# 或修改端口
export AUTOEXAM_PORT=5001
```

#### 2. 权限问题

```bash
# 修复目录权限
chmod -R 755 scenarios results reports openscenario logs

# 修改所有者
sudo chown -R $USER:$USER scenarios results reports openscenario logs
```

#### 3. Conda环境问题

```bash
# 重新创建环境
conda env remove -n autoexam
conda create -n autoexam python=3.9
conda activate autoexam
pip install -r requirements.txt
```

#### 4. CARLA连接失败

```bash
# 检查CARLA是否运行
ps aux | grep CarlaUE4

# 检查端口
netstat -tlnp | grep 2000

# 测试连接
python -c "import carla; client = carla.Client('localhost', 2000); print(client.get_server_version())"
```

#### 5. 内存不足

```bash
# 减少工作进程数
gunicorn -w 2 -b 0.0.0.0:5000 ui.app:app

# 或限制批量生成数量
# 修改 config.yaml
generator:
  max_count: 200
```

### 日志分析

```bash
# 查看最近错误
tail -n 100 logs/autoexam.log | grep ERROR

# 查看性能日志
tail -n 100 logs/autoexam.log | grep "Performance"

# 统计请求数
grep "POST" logs/autoexam.log | wc -l
```

---

## 备份和恢复

### 备份策略

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/autoexam/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# 备份场景库
cp -r scenarios $BACKUP_DIR/

# 备份结果
cp -r results $BACKUP_DIR/

# 备份配置
cp config.yaml $BACKUP_DIR/

# 压缩
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
rm -rf $BACKUP_DIR

echo "备份完成: $BACKUP_DIR.tar.gz"
```

### 恢复数据

```bash
#!/bin/bash
# restore.sh

BACKUP_FILE=$1
tar -xzf $BACKUP_FILE

# 恢复场景库
cp -r scenarios/* ./scenarios/

# 恢复结果
cp -r results/* ./results/

echo "恢复完成"
```

---

## 监控和告警

### 使用Prometheus + Grafana

**prometheus.yml**:
```yaml
scrape_configs:
  - job_name: 'autoexam'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/metrics'
```

### 关键监控指标

| 指标 | 告警阈值 | 说明 |
|------|----------|------|
| 请求延迟 | > 2s | API响应时间 |
| 错误率 | > 5% | 请求错误比例 |
| 内存使用 | > 80% | 系统内存使用 |
| 磁盘使用 | > 85% | 磁盘空间使用 |
| 场景数量 | > 9000 | 场景库容量 |

---

## 附录

### 目录结构

```
AutoExam/
├── config.yaml           # 配置文件
├── requirements.txt      # Python依赖
├── install_env.sh       # 安装脚本
├── start.sh             # 启动脚本
├── docker-compose.yml   # Docker配置
├── autoexam.service     # Systemd服务
├── ui/                  # Web界面
├── generators/          # 场景生成器
├── analyzers/           # 分析器
├── library/             # 场景库
├── exporters/           # 导出器
├── scenarios/           # 场景存储
├── results/             # 测试结果
├── reports/             # 测试报告
├── openscenario/        # OpenSCENARIO导出
└── logs/                # 日志文件
```

### 环境变量清单

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| AUTOEXAM_CONFIG | ./config.yaml | 配置文件路径 |
| AUTOEXAM_ENV | development | 运行环境 |
| AUTOEXAM_PORT | 5000 | 服务端口 |
| CARLA_ROOT | - | CARLA安装路径 |
| APOLLO_ROOT | - | Apollo安装路径 |

---

**文档维护**: AutoExam Team  
**最后更新**: 2026-03-02
