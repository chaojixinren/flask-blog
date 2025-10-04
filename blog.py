import pymysql
import os
import uuid
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, url_for, flash, redirect, make_response, jsonify
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = 'tooyoungtoosimple'

#数据库连接函数
def get_db_connection():
    try:
        conn = pymysql.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            database=app.config['MYSQL_DB'],
            charset=app.config['MYSQL_CHARSET'],
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    
    except pymysql.err.OperationalError as e:
        print(f"数据库连接错误: {e}")
        raise e

# 获取文章函数
def get_post(post_id):
    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute('SELECT p.id, p.created, p.title, p.content, p.author_id, u.name as author_name FROM posts p LEFT JOIN user u ON p.author_id = u.id WHERE p.id = %s', (post_id,))
                post = cursor.fetchone()
                return post
        finally:
            conn.close()
    except Exception as e:
        print(f"获取文章时出错: {e}")
        return None

# JWT认证装饰器
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('token')
        
        if not token:
            flash('请先登录!')
            return redirect(url_for('login'))
        
        try:
            data = jwt.decode(token, app.secret_key, algorithms=['HS256'])
            # 获取当前用户信息
            conn = get_db_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute('SELECT id, public_id, name, email FROM user WHERE public_id = %s', (data['public_id'],))
                    current_user = cursor.fetchone()
            finally:
                conn.close()
                
            if not current_user:
                flash('用户不存在，请重新登录!')
                response = make_response(redirect(url_for('login')))
                response.set_cookie('token', '', expires=0)
                return response
        except jwt.ExpiredSignatureError:
            flash('登录已过期，请重新登录!')
            return redirect(url_for('login'))
        except jwt.InvalidTokenError:
            flash('无效的登录信息，请重新登录!')
            return redirect(url_for('login'))
        
        # 将用户ID添加到请求上下文中
        request.current_user_id = current_user['id']
        return f(current_user, *args, **kwargs)
    
    return decorated

@app.route('/') 
def index():
    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute('SELECT p.id, p.created, p.title, p.content, p.author_id, u.name as author_name FROM posts p LEFT JOIN user u ON p.author_id = u.id ORDER BY created DESC')
                posts = cursor.fetchall()
                return render_template('index.html', posts=posts)
        finally:
            conn.close()
    except Exception as e:
        flash(f"数据库错误: {e}")
        return render_template('index.html', posts=[])


@app.route('/posts/<int:post_id>')
def post(post_id):
    try:
        post = get_post(post_id)
        if post is None:
            flash('文章不存在!')
            return redirect(url_for('index'))
        return render_template('post.html', post=post)
    except Exception as e:
        flash(f"数据库错误: {e}")
        return redirect(url_for('index'))


@app.route('/posts/new', methods=('GET', 'POST'))
@token_required
def new(current_user):
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('标题不能为空!')
        elif not content:
            flash('内容不能为空')
        else:
            try:
                conn = get_db_connection()
                try:
                    with conn.cursor() as cursor:
                        cursor.execute('INSERT INTO posts (title, content, author_id) VALUES (%s, %s, %s)',
                                     (title, content, current_user['id']))
                        conn.commit()
                    return redirect(url_for('index'))
                finally:
                    conn.close()
            except Exception as e:
                flash(f"数据库错误: {e}")

    return render_template('new.html')


@app.route('/posts/<int:id>/edit', methods=('GET', 'POST'))
@token_required
def edit(current_user, id):
    try:
        post = get_post(id)
        
        if post is None:
            flash('文章不存在!')
            return redirect(url_for('index'))
        
        # 检查当前用户是否是文章作者
        if post['author_id'] != current_user['id']:
            flash('您没有权限编辑这篇文章!')
            return redirect(url_for('index'))
    except Exception as e:
        flash(f"数据库错误: {e}")
        return redirect(url_for('index'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('标题不能为空!')
        else:
            try:
                conn = get_db_connection()
                try:
                    with conn.cursor() as cursor:
                        cursor.execute('UPDATE posts SET title = %s, content = %s'
                                       ' WHERE id = %s',
                                       (title, content, id))
                        conn.commit()
                    return redirect(url_for('index'))
                finally:
                    conn.close()
            except Exception as e:
                flash(f"数据库错误: {e}")

    return render_template('edit.html', post=post)


@app.route('/posts/<int:id>/delete', methods=('POST',))
@token_required
def delete(current_user, id):
    try:
        post = get_post(id)
        
        if post is None:
            flash('文章不存在!')
            return redirect(url_for('index'))
        
        # 检查当前用户是否是文章作者
        if post['author_id'] != current_user['id']:
            flash('您没有权限删除这篇文章!')
            return redirect(url_for('index'))
            
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute('DELETE FROM posts WHERE id = %s', (id,))
                conn.commit()
            flash('"{}" 删除成功!'.format(post['title']))
        finally:
            conn.close()
    except Exception as e:
        flash(f"数据库错误: {e}")
    return redirect(url_for('index'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/signup', methods=('GET', 'POST'))
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        if not name or not email or not password:
            flash('所有字段都必须填写!')
        else:
            try:
                conn = get_db_connection()
                try:
                    with conn.cursor() as cursor:
                        # 检查用户名是否已存在
                        cursor.execute('SELECT id FROM user WHERE name = %s', (name,))
                        existing_name = cursor.fetchone()
                        
                        if existing_name:
                            flash('该用户名已被使用!')
                        else:
                            # 检查邮箱是否已存在
                            cursor.execute('SELECT id FROM user WHERE email = %s', (email,))
                            existing_email = cursor.fetchone()
                            
                            if existing_email:
                                flash('该邮箱已被注册!')
                            else:
                                # 创建新用户
                                hashed_password = generate_password_hash(password)
                                public_id = str(uuid.uuid4())
                                cursor.execute(
                                    'INSERT INTO user (public_id, name, email, password) VALUES (%s, %s, %s, %s)',
                                    (public_id, name, email, hashed_password)
                                )
                                conn.commit()
                                flash('注册成功，请登录!')
                                return redirect(url_for('login'))
                finally:
                    conn.close()
            except Exception as e:
                flash(f'注册失败: {e}')
    
    return render_template('signup.html')

@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        try:
            conn = get_db_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute('SELECT * FROM user WHERE email = %s', (email,))
                    user = cursor.fetchone()
            finally:
                conn.close()
                
            if user and check_password_hash(user['password'], password):
                # 生成JWT Token
                token = jwt.encode({
                    'public_id': user['public_id'],
                    'exp': datetime.utcnow() + timedelta(days=30)
                }, app.secret_key, algorithm='HS256')
                
                response = make_response(redirect(url_for('index')))
                response.set_cookie('token', token, httponly=True, max_age=30*24*60*60)
                response.set_cookie('user_id', str(user['id']), max_age=30*24*60*60)  # 添加用户ID到cookie
                return response
            else:
                flash('邮箱或密码错误!')
        except Exception as e:
            flash(f"登录时发生错误: {e}")
            
    return render_template('login.html')


@app.route('/logout')
def logout():
    response = make_response(redirect(url_for('index')))
    response.set_cookie('token', '', expires=0)
    response.set_cookie('user_id', '', expires=0)  # 清除用户ID cookie
    flash('您已成功退出登录!')
    return response

if __name__ == '__main__':
    app.run(debug=True)
