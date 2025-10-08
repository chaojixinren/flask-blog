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

# 获取文章的所有评论
def get_post_comments(post_id):
    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute('''SELECT c.id, c.created, c.content, c.author_id, u.name as author_name 
                                 FROM comments c 
                                 LEFT JOIN user u ON c.author_id = u.id 
                                 WHERE c.post_id = %s 
                                 ORDER BY c.created ASC''', (post_id,))
                comments = cursor.fetchall()
                return comments
        finally:
            conn.close()
    except Exception as e:
        print(f"获取评论时出错: {e}")
        return []

# 检查用户是否已经点赞了某篇文章
def has_user_liked_post(user_id, post_id):
    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute('SELECT COUNT(*) as count FROM likes WHERE user_id = %s AND post_id = %s', (user_id, post_id))
                result = cursor.fetchone()
                return result['count'] > 0
        finally:
            conn.close()
    except Exception as e:
        print(f"检查点赞状态时出错: {e}")
        return False

# 获取文章点赞数
def get_post_likes_count(post_id):
    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute('SELECT COUNT(*) as count FROM likes WHERE post_id = %s', (post_id,))
                result = cursor.fetchone()
                return result['count']
        finally:
            conn.close()
    except Exception as e:
        print(f"获取点赞数时出错: {e}")
        return 0

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
                # 为每篇文章获取评论数和点赞数
                for post in posts:
                    cursor.execute('SELECT COUNT(*) as comment_count FROM comments WHERE post_id = %s', (post['id'],))
                    comment_result = cursor.fetchone()
                    post['comment_count'] = comment_result['comment_count']
                    
                    cursor.execute('SELECT COUNT(*) as like_count FROM likes WHERE post_id = %s', (post['id'],))
                    like_result = cursor.fetchone()
                    post['like_count'] = like_result['like_count']
                
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
        
        # 获取评论
        comments = get_post_comments(post_id)
        
        # 获取点赞信息
        like_count = get_post_likes_count(post_id)
        
        # 检查当前用户是否已点赞（如果已登录）
        user_has_liked = False
        user_id = request.cookies.get('user_id')
        if user_id:
            user_has_liked = has_user_liked_post(int(user_id), post_id)
        
        return render_template('post.html', post=post, comments=comments, 
                              like_count=like_count, user_has_liked=user_has_liked)
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

# 添加评论路由
@app.route('/posts/<int:post_id>/comment', methods=['POST'])
@token_required
def add_comment(current_user, post_id):
    content = request.form.get('content')
    
    if not content:
        flash('评论内容不能为空!')
        return redirect(url_for('post', post_id=post_id))
    
    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute('INSERT INTO comments (content, author_id, post_id) VALUES (%s, %s, %s)',
                             (content, current_user['id'], post_id))
                conn.commit()
            flash('评论成功!')
        finally:
            conn.close()
    except Exception as e:
        flash(f'评论失败: {e}')
    
    return redirect(url_for('post', post_id=post_id))

# 点赞/取消点赞路由
@app.route('/posts/<int:post_id>/like', methods=['POST'])
@token_required
def toggle_like(current_user, post_id):
    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # 检查是否已经点赞
                cursor.execute('SELECT id FROM likes WHERE user_id = %s AND post_id = %s', 
                             (current_user['id'], post_id))
                existing_like = cursor.fetchone()
                
                if existing_like:
                    # 如果已经点赞，则取消点赞
                    cursor.execute('DELETE FROM likes WHERE id = %s', (existing_like['id'],))
                    conn.commit()
                    flash('已取消点赞!')
                else:
                    # 如果尚未点赞，则添加点赞
                    cursor.execute('INSERT INTO likes (user_id, post_id) VALUES (%s, %s)', 
                                 (current_user['id'], post_id))
                    conn.commit()
                    flash('点赞成功!')
        finally:
            conn.close()
    except Exception as e:
        flash(f'操作失败: {e}')
    
    return redirect(url_for('post', post_id=post_id))


# 删除评论路由
@app.route('/posts/<int:post_id>/comments/<int:comment_id>/delete', methods=['POST'])
@token_required
def delete_comment(current_user, post_id, comment_id):
    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # 获取评论信息，包括作者和关联的文章
                cursor.execute('''SELECT c.id, c.author_id, c.post_id, p.author_id as post_author_id
                                 FROM comments c 
                                 JOIN posts p ON c.post_id = p.id
                                 WHERE c.id = %s AND c.post_id = %s''', (comment_id, post_id))
                comment = cursor.fetchone()
                
                if comment is None:
                    flash('评论不存在!')
                    return redirect(url_for('post', post_id=post_id))
                
                # 检查权限：只有评论作者或文章作者可以删除评论
                if comment['author_id'] != current_user['id'] and comment['post_author_id'] != current_user['id']:
                    flash('您没有权限删除此评论!')
                    return redirect(url_for('post', post_id=post_id))
                
                # 删除评论
                cursor.execute('DELETE FROM comments WHERE id = %s', (comment_id,))
                conn.commit()
                flash('评论删除成功!')
        finally:
            conn.close()
    except Exception as e:
        flash(f'删除评论失败: {e}')
    
    return redirect(url_for('post', post_id=post_id))


if __name__ == '__main__':
    app.run(debug=True)
