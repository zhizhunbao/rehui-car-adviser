# 后端环境配置

## 环境变量设置

1. 复制环境变量模板文件：
   ```bash
   cp ../env.example .env
   ```

2. 编辑 `.env` 文件，填入实际的配置值：

### 必需的配置项

- `GOOGLE_GEMINI_API_KEY`: Google Gemini API 密钥
- `SUPABASE_URL`: Supabase 项目 URL
- `SUPABASE_ANON_KEY`: Supabase 匿名密钥
- `SUPABASE_SERVICE_ROLE_KEY`: Supabase 服务角色密钥
- `DATABASE_URL`: 数据库连接 URL

### 可选配置项

- `DEBUG`: 调试模式 (默认: True)

## 获取 Supabase 配置

1. 登录 [Supabase Dashboard](https://supabase.com/dashboard)
2. 选择您的项目
3. 在 Settings > API 中找到：
   - Project URL (SUPABASE_URL)
   - anon public key (SUPABASE_ANON_KEY)
   - service_role secret key (SUPABASE_SERVICE_ROLE_KEY)

## 获取 Gemini API 密钥

1. 访问 [Google AI Studio](https://makersuite.google.com/app/apikey)
2. 创建新的 API 密钥
3. 将密钥填入 `GOOGLE_GEMINI_API_KEY`

## 启动应用

```bash
# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
python main.py
```

应用将在 http://localhost:8000 启动
