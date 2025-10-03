# MySQL Blog

一个使用 Flask + MySQL 构建的轻量级博客系统，提供用户注册登录、文章管理与基本页面展示功能。该仓库包含完整的后端应用、HTML 模板和初始化数据库所需的 SQL 脚本。

## 功能概览

- 用户注册、登录与登出（基于 JWT，保存在浏览器 Cookie 中）
- 文章的创建、查看、编辑与删除（需登录）
- 基于 Bootstrap 的响应式界面模板
- MySQL 持久化存储，提供初始化脚本一键建表
- 错误提示与表单校验的基础交互体验

## 技术栈

- 后端：Flask、PyMySQL、PyJWT、Werkzeug Security
- 前端：Bootstrap、Jinja2 模板渲染
- 数据库：MySQL 5.7+/8.x
- 运行环境：Python 3.8+（已在 Windows 环境验证）

## 目录结构

```
mysql-blog/
├── blog.py             # Flask 应用入口，包含路由与业务逻辑
├── config.py           # 数据库配置（支持环境变量覆盖）
├── init_db.py          # 初始化/重建数据库脚本（会删除同名数据库）
├── db.sql              # 建表与初始数据 SQL
├── templates/          # Jinja2 模板文件
├── static/             # CSS/JS 等静态资源
└── README.md
```

## 环境准备

- 安装 Python 3
- 安装并启动 MySQL 数据库，创建具备建库与建表权限的账号
- 建议使用虚拟环境隔离依赖：
  ```bash
  python -m venv .venv
  source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
  ```

## 安装依赖

在项目根目录执行：
```bash
pip install flask PyJWT werkzeug pymysql
```
如果已启用虚拟环境，请确保在激活状态下安装依赖。

## 数据库配置

应用默认从 `config.Config` 读取下列配置，可通过环境变量覆盖：

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `MYSQL_HOST` | `localhost` | 数据库主机 |
| `MYSQL_USER` | `root` | 数据库用户 |
| `MYSQL_PASSWORD` | `your_password` | 数据库密码（请在生产环境中更改） |
| `MYSQL_DB` | `xinrendatabase` | 运行时使用的数据库名 |

`init_db.py` 会执行 `DROP DATABASE IF EXISTS`，运行前请确认不会误删生产数据。

根据需要，可以直接修改 `config.py` 或在运行命令前临时设置环境变量，例如：
```bash
set MYSQL_PASSWORD=your_password
# PowerShell: $env:MYSQL_PASSWORD = "your_password"
```

## 初始化数据库

```bash
python init_db.py
```
该脚本会：
- 使用 `Config` 中的连接信息连接 MySQL
- 删除同名数据库并重新创建
- 执行 `db.sql` 中的建表语句

首次运行后数据库中不会有默认用户，请在网页端自行注册。

## 启动应用

```bash
python blog.py
```
应用默认以 `debug=True` 方式启动本地开发服务器：<http://127.0.0.1:5000>

## 使用说明

1. 访问首页浏览公开文章
2. 首次使用通过“注册”页面创建账号
3. 注册成功后在“登录”页面输入邮箱和密码获取登录状态
4. 登录后可创建新文章、编辑已有文章或删除文章
5. 点击“退出”可清除浏览器中的 JWT Cookie

## 常见问题

- 无法连接数据库：检查 MySQL 是否启动、账号密码是否正确，以及 `Config` 配置是否与实际匹配。
- 依赖缺失：确认虚拟环境已激活并执行过 `pip install` 命令。
- 模板或静态资源加载失败：确保以项目根目录为工作路径启动应用，Flask 会自动定位 `templates` 与 `static`。

