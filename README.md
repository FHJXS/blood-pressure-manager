# 血压管家 H5 应用

> 轻量级高血压记录工具，无需登录，快速记录，本地存储。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Vue 3](https://img.shields.io/badge/Vue-3.3.4-42b883)](https://vuejs.org/)
[![Python](https://img.shields.io/badge/Python-3.10-3776ab)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-lightgrey)](https://flask.palletsprojects.com/)

## 📱 功能特点

- **快速录入** - 收缩压、舒张压、心率一键记录
- **历史记录** - 时间流展示，支持编辑和删除
- **数据统计** - 周/月/年视图，血压趋势图表
- **自动定位** - 基于 IP 自动获取测量地点
- **数据导出** - 支持导出 JSON 格式数据
- **无需登录** - 设备 ID 自动识别，开箱即用

## 🛠️ 技术栈

### 后端
- **Python 3.10** - 后端运行环境
- **Flask 3.0** - Web 框架
- **SQLite** - 轻量级数据库
- **Flask-CORS** - 跨域支持

### 前端
- **Vue 3.3** - 渐进式 JavaScript 框架
- **Tailwind CSS 3.3** - 实用优先的 CSS 框架
- **Chart.js 4.4** - 数据可视化图表
- **Font Awesome 6** - 图标库

### 部署
- **Nginx** - Web 服务器和反向代理

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 16+ (可选，仅用于前端构建)
- Nginx (生产环境)

### 后端启动

```bash
# 进入后端目录
cd backend

# 安装依赖
pip3 install -r requirements.txt

# 启动服务
python3 app.py
```

后端服务将在 `http://localhost:5000` 启动。

### 前端访问

前端已集成为单页应用，直接访问：

```
http://localhost:8001
```

> 注意：前端需要通过 Nginx 或直接使用 Python 内置服务器提供。

### 使用 Python 内置服务器（开发环境）

```bash
cd frontend
python3 -m http.server 8001
```

然后访问 `http://localhost:8001`。

## 📦 项目结构

```
blood-pressure-manager/
├── backend/
│   ├── app.py              # Flask 应用入口
│   ├── database.py         # 数据库操作
│   └── requirements.txt    # Python 依赖
├── frontend/
│   ├── index.html          # Vue 单页应用
│   └── assets/             # 前端静态资源
│       ├── tailwind.min.js
│       ├── vue.js
│       ├── chart.umd.min.js
│       ├── fontawesome.css
│       └── webfonts/       # FontAwesome 字体
├── nginx.conf              # Nginx 配置示例
├── deploy.sh               # 部署脚本
└── README.md               # 项目文档
```

## 🌐 API 接口

### 设备管理

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/device` | 创建新设备 |
| GET | `/api/device?id={deviceId}` | 获取设备信息 |

### 记录管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/records?deviceId={deviceId}` | 获取记录列表 |
| POST | `/api/records?deviceId={deviceId}` | 创建新记录 |
| GET | `/api/records/{id}` | 获取单条记录 |
| PUT | `/api/records/{id}` | 更新记录 |
| DELETE | `/api/records/{id}` | 删除记录 |

### 统计数据

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/stats?deviceId={deviceId}&period={week|month|year}` | 获取统计数据 |

### 设置管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/settings?deviceId={deviceId}` | 获取设置 |
| PUT | `/api/settings?deviceId={deviceId}` | 更新设置 |

### 位置记录

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/location-log` | 记录 IP 位置信息 |

## 📊 数据模型

### 血压记录 (records)

```json
{
  "id": "rec_xxx",
  "device_id": "dev_xxx",
  "systolic": 120,
  "diastolic": 80,
  "heart_rate": 70,
  "timestamp": "2026-03-08T14:30:00",
  "location": "中国 广东 深圳",
  "note": "晨起测量",
  "medication": false,
  "status": "normal",
  "ip": "223.73.207.25"
}
```

### 血压状态标准

| 状态 | 收缩压 | 舒张压 | 标识颜色 |
|------|--------|--------|----------|
| 正常 | 90-140 | 60-90 | 🟢 绿色 |
| 偏高 | 140-160 | 90-100 | 🟡 黄色 |
| 危险 | >160 | >100 | 🔴 红色 |

## 🌍 部署

### 云服务器部署

1. **上传代码到服务器**

```bash
scp -r project/ root@your-server:/srv/www/blood-pressure/
```

2. **执行部署脚本**

```bash
ssh root@your-server
cd /srv/www/blood-pressure
./deploy.sh
```

3. **配置 Nginx**

将 `nginx.conf` 复制到 `/etc/nginx/conf.d/` 并重启 Nginx。

```bash
sudo cp nginx.conf /etc/nginx/conf.d/blood-pressure.conf
sudo nginx -t
sudo systemctl restart nginx
```

### Docker 部署（可选）

```bash
docker build -t blood-pressure-manager .
docker run -d -p 8001:80 -p 5000:5000 blood-pressure-manager
```

## 📱 使用指南

### 首次使用

1. 打开应用，系统会自动生成设备 ID
2. 测量地点会自动获取（基于 IP）
3. 输入血压数据并保存

### 查看历史记录

- 点击底部"历史"标签
- 时间流展示所有记录
- 点击记录可查看详情或编辑

### 查看统计

- 点击底部"统计"标签
- 切换周/月/年视图
- 查看血压趋势图表

### 数据导出

- 点击底部"我的"标签
- 点击"导出数据"
- 下载 JSON 格式数据文件

## 🔒 隐私说明

- 所有数据存储在本地（SQLite 数据库）
- 不会上传到任何第三方服务器
- 设备 ID 仅用于本地识别
- 支持数据导出，防止数据丢失

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 License

MIT License

---

**开发时间**: 2026-03-08  
**开发者**: DevOps Worker  
**版本**: 1.0.0
