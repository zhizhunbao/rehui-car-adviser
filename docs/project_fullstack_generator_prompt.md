# 🧠 Claude 全项目生成提示模板

## 1. 项目定义

面向加拿大用户的智能搜车顾问，用户通过自然语言输入购车需求，系统返回匹配的车源卡片。

### 1.1 项目生成说明
**请按照以下步骤自动创建完整的项目结构**：
1. 创建 `frontend/` 和 `backend/` 两个主目录
2. 根据技术栈和模块规划自动生成合理的目录结构
3. 创建所有必要的配置文件和依赖文件
4. 实现完整的前后端代码，确保项目可直接运行

### 1.2 功能边界

#### 1.2.1 必须实现
- **自然语言输入**：支持中英文查询
- **AI解析**：使用 Gemini API 解析用户意图
- **车源搜索**：仅从 Cargurus 获取数据
- **结果展示**：返回车源信息卡片
- **响应时间**：< 10秒

#### 1.2.2 明确排除
- 用户注册/登录系统
- 多平台数据聚合（仅Cargurus）
- 高级分析功能（价格趋势、推荐理由等）
- 用户偏好存储
- 复杂的数据缓存策略

## 2. 技术约束

### 2.1 前端技术栈
**必须使用**：
- React + TypeScript
- Vite 构建工具
- Tailwind CSS 样式框架
- React Context API（状态管理）
- Axios（HTTP 客户端）

### 2.2 后端技术栈
**必须使用**：
- Python FastAPI 框架
- Gemini API（自然语言处理）
- Selenium + Chrome WebDriver（网页抓取）
- Supabase PostgreSQL（数据库）
- BeautifulSoup（HTML 解析）
- Pydantic（数据验证）
- python-dotenv（环境变量管理）

### 2.3 数据库约束
**必须使用**：
- Supabase PostgreSQL
- 提供的连接信息

**环境变量**：
```
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
DATABASE_URL=your_database_url

GOOGLE_GEMINI_API_KEY=your_gemini_api_key
```

### 2.4 数据源约束
**唯一数据源**：Cargurus 网站
**抓取方式**：网页爬虫（Selenium）
**数据范围**：公开的车源信息

## 3. 功能规范

### 3.1 接口要求
**必须实现**：
- POST /api/search 接口
- 接收自然语言查询
- 返回车源信息列表
- 统一错误处理格式

### 3.2 数据要求
**车源信息必须包含**：
- 标题
- 价格
- 年份
- 里程
- 城市
- 详情链接

### 3.3 界面要求
**必须包含**：
- 搜索输入框
- 加载状态显示
- 车源结果展示
- 响应式设计

## 4. 项目结构要求

### 4.1 目录结构
**必须创建**：
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
├── .env                      # 环境变量
├── render.yaml              # Render 部署配置
└── README.md                 # 项目说明
```

### 4.2 文件要求
**必须包含**：
- `package.json`（前端依赖）
- `requirements.txt`（后端依赖）
- `vite.config.ts`（前端配置）
- `index.html`（前端模板）
- `App.tsx`（主应用组件）
- `main.tsx`（应用入口）
- `main.py`（后端入口）
- `__init__.py`（Python 包初始化）
- `.env`（环境变量）
- `render.yaml`（部署配置）
- `README.md`（使用说明）

## 5. 代码质量要求

### 5.1 代码规范
**必须遵循**：
- TypeScript 严格模式
- Python PEP 8 规范
- 统一的错误处理
- 完整的类型注解
- 清晰的注释说明

### 5.2 性能要求
**必须满足**：
- 前端首屏加载 < 3秒
- API 响应时间 < 10秒
- 内存使用合理
- 无内存泄漏

## 6. 部署要求

### 6.1 本地开发
**必须支持**：
- `npm run dev`（前端开发）
- `python main.py`（后端开发）
- 热重载功能
- 跨域配置

### 6.2 生产部署
**部署平台**：Render
**必须准备**：
- Render 配置文件（render.yaml）
- 环境变量配置
- 数据库迁移脚本
- 部署文档
- 前后端分离部署配置
