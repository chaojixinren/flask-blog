import pymysql
from flask import Flask, render_template, request, url_for, flash, redirect
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = 'tooyoungtoosimple'

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

def get_post(post_id):
    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute('SELECT * FROM posts WHERE id = %s', (post_id,))
                post = cursor.fetchone()
                return post
        finally:
            conn.close()
    except Exception as e:
        print(f"获取文章时出错: {e}")
        return None


@app.route('/') 
def index():
    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute('SELECT * FROM posts ORDER BY created DESC')
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
def new():
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
                        cursor.execute('INSERT INTO posts (title, content) VALUES (%s, %s)',
                                     (title, content))
                        conn.commit()
                    return redirect(url_for('index'))
                finally:
                    conn.close()
            except Exception as e:
                flash(f"数据库错误: {e}")

    return render_template('new.html')


@app.route('/posts/<int:id>/edit', methods=('GET', 'POST'))
def edit(id):
    try:
        post = get_post(id)
        
        if post is None:
            flash('文章不存在!')
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
def delete(id):
    try:
        post = get_post(id)
        
        if post is None:
            flash('文章不存在!')
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

if __name__ == '__main__':
    app.run(debug=True)