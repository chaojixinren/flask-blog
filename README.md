# MySQL Blog

一个基于 Flask 和 MySQL 的轻量级博客系统，支持用户注册、登录和文章管理功能。

## 项目简介

这是一个使用 Python Flask 框架开发的博客应用，具有完整的用户认证系统和文章管理功能。用户可以通过注册账号并登录后创建、编辑和删除文章，未登录用户只能浏览文章内容。

## 功能特性

- 用户注册与登录（JWT Token 认证）
- 用户名和邮箱唯一性验证
- 文章创建、查看、编辑和删除（仅限登录用户）
- 响应式界面设计（基于 Bootstrap）
- 数据持久化（MySQL 数据库）

## 技术栈

- 后端：Python + Flask
- 前端：Bootstrap + Jinja2 模板引擎
- 数据库：MySQL
- 认证：JWT (JSON Web Tokens)

## 安装与运行

### 环境要求

- Python 3.x
- MySQL 数据库
- pip 包管理工具

### 安装步骤

1. 克隆项目到本地：
   ```
   git clone <项目地址>
   cd mysql-blog
   ```

2. 安装依赖：
   ```
   pip install flask PyJWT werkzeug pymysql
   ```

3. 配置数据库：
   在 `config.py` 文件中修改数据库配置信息：
   ```python
   class Config:
       # MySQL配置
       MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
       MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
       MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'your_password')
       MYSQL_DB = os.environ.get('MYSQL_DB', 'xinrendatabase')
       MYSQL_CHARSET = 'utf8mb4'
   ```

4. 初始化数据库：
   ```
   python init_db.py
   ```

5. 运行应用：
   ```
   python blog.py
   ```

6. 访问应用：
   在浏览器中打开 `http://127.0.0.1:5000`

## 使用说明

1. 首次使用需要注册账号
2. 注册后使用邮箱和密码登录
3. 登录后可以创建新文章
4. 可以编辑和删除自己创建的文章
5. 未登录用户只能浏览文章内容

## 项目结构

```
mysql-blog/
├── static/                 # 静态资源文件
│   ├── css/
│   │   └── bootstrap.min.css
│   └── js/
│       ├── bootstrap.min.js
│       ├── jquery.slim.min.js
│       ├── popper.min.js
│       └── titleanimation.js
├── templates/              # HTML 模板文件
│   ├── about.html
│   ├── base.html
│   ├── edit.html
│   ├── index.html
│   ├── login.html
│   ├── new.html
│   ├── post.html
│   ├── signup.html
│   └── unlogin.html
├── blog.py                 # 主应用文件
├── config.py               # 配置文件
├── db.sql                  # 数据库结构定义
├── init_db.py              # 数据库初始化脚本
└── README.md               # 项目说明文件
```

## 安全说明

- 密码使用哈希算法加密存储
- 使用 JWT Token 进行用户身份验证
- 敏感操作（创建、编辑、删除文章）需要用户登录
