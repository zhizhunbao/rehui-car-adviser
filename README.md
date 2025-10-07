# Rehui Car Adviser

智能搜车顾问 - 面向加拿大用户的智能搜车服务，用户通过自然语言输入购车需求，系统返回匹配的车源卡片。

## 🚀 功能特点

- **自然语言搜索**：支持中英文查询
- **AI 智能解析**：使用 Gemini API 解析用户意图
- **实时车源搜索**：从 CarGurus 获取最新车源信息
- **响应式界面**：现代化的用户界面设计
- **快速响应**：搜索响应时间 < 10秒

## 🛠 技术栈

### 前端
- React 18 + TypeScript
- Vite 构建工具
- Tailwind CSS 样式框架
- React Context API 状态管理
- Axios HTTP 客户端

### 后端
- Python FastAPI 框架
- Gemini API 自然语言处理
- Selenium + Chrome WebDriver 网页抓取
- Supabase PostgreSQL 数据库
- BeautifulSoup HTML 解析
- Pydantic 数据验证

## 📁 项目结构

```
rehui-car-adviser/
├── frontend/                 # React 前端
│   ├── src/
│   │   ├── components/      # 组件
│   │   ├── contexts/        # Context 状态管理
│   │   ├── services/        # API 服务
│   │   ├── types/           # TypeScript 类型
│   │   ├── utils/           # 工具函数
│   │   ├── App.tsx          # 主应用组件
│   │   └── main.tsx         # 应用入口
│   ├── index.html           # HTML 模板
│   ├── package.json
│   └── vite.config.ts
├── backend/                  # FastAPI 后端
│   ├── app/
│   │   ├── __init__.py      # 包初始化
│   │   ├── api/             # API 路由
│   │   ├── models/          # 数据模型
│   │   ├── services/        # 业务逻辑
│   │   └── utils/           # 工具函数
│   ├── requirements.txt
│   └── main.py
├── env.example              # 环境变量示例
├── render.yaml              # Render 部署配置
└── README.md                # 项目说明
```

## 🚀 快速开始

### 环境要求

- Node.js 18+
- Python 3.9+
- Chrome 浏览器（用于网页抓取）

### 1. 克隆项目

```bash
git clone <repository-url>
cd rehui-car-adviser
```

### 2. 配置环境变量

复制 `env.example` 为 `.env` 并填入真实的配置值：

```bash
cp env.example .env
```

编辑 `.env` 文件，填入以下配置：

```env
# Gemini API 配置
GOOGLE_GEMINI_API_KEY=your_gemini_api_key

# Supabase 配置（可选）
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
DATABASE_URL=your_database_url

# 应用配置
DEBUG=True
VITE_API_URL=http://localhost:8000
```

### 3. 安装依赖

#### 前端依赖
```bash
cd frontend
npm install
```

#### 后端依赖
```bash
cd backend
pip install -r requirements.txt
```

### 4. 启动开发服务器

#### 启动后端服务
```bash
cd backend
python main.py
```
后端服务将在 http://localhost:8000 启动

#### 启动前端服务
```bash
cd frontend
npm run dev
```
前端服务将在 http://localhost:3000 启动

### 5. 访问应用

打开浏览器访问 http://localhost:3000

## 🔧 开发指南

### 前端开发

```bash
cd frontend

# 开发模式
npm run dev

# 构建生产版本
npm run build

# 预览构建结果
npm run preview

# 代码检查
npm run lint
```

### 后端开发

```bash
cd backend

# 启动开发服务器
python main.py

# 或使用 uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### API 文档

后端服务启动后，可以访问以下地址查看 API 文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🚀 部署

### Render 部署

1. 将代码推送到 GitHub 仓库
2. 在 Render 中创建新服务
3. 选择 "Blueprint" 部署方式
4. 上传 `render.yaml` 配置文件
5. 配置环境变量
6. 部署服务

### 环境变量配置

在 Render 中配置以下环境变量：

- `GOOGLE_GEMINI_API_KEY`: Gemini API 密钥
- `SUPABASE_URL`: Supabase 项目 URL
- `SUPABASE_ANON_KEY`: Supabase 匿名密钥
- `SUPABASE_SERVICE_ROLE_KEY`: Supabase 服务角色密钥
- `DATABASE_URL`: 数据库连接 URL

## 📝 API 接口

### POST /api/search

搜索车源接口

**请求体：**
```json
{
  "query": "2020年后的丰田凯美瑞，预算3万加元"
}
```

**响应：**
```json
{
  "success": true,
  "data": [
    {
      "id": "cg_123456",
      "title": "2021 Toyota Camry LE",
      "price": "$28,500",
      "year": 2021,
      "mileage": "45,000 km",
      "city": "Toronto",
      "link": "https://www.cargurus.ca/..."
    }
  ],
  "message": "找到 5 辆车源",
  "total_count": 5
}
```

## 🤝 贡献

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🆘 支持

如果您遇到任何问题或有任何建议，请：

1. 查看 [Issues](https://github.com/your-repo/issues) 页面
2. 创建新的 Issue
3. 联系开发团队

## 🔮 未来计划

- [ ] 支持更多车源网站
- [ ] 添加价格趋势分析
- [ ] 实现用户偏好存储
- [ ] 添加车源比较功能
- [ ] 支持图片搜索
- [ ] 移动端应用开发
