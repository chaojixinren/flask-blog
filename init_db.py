import pymysql
from config import Config

def init_db():
    try:
        # 创建数据库链接
        connection = pymysql.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            charset=Config.MYSQL_CHARSET
        )

        with connection.cursor() as cursor:
            # 创建数据库
            cursor.execute(f'DROP DATABASE IF EXISTS {Config.MYSQL_DB}')
            cursor.execute(f'CREATE DATABASE {Config.MYSQL_DB} DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
            cursor.execute(f'USE {Config.MYSQL_DB}')
            
            # 执行db.sql中的SQL语句
            with open('db.sql') as f:
                sql_statements = f.read().split(';')
                for statement in sql_statements:
                    if statement.strip():
                        cursor.execute(statement)
        
        # 提交前面的数据操作
        connection.commit()
        print("数据库初始化成功！")
        print(f"已创建数据库: {Config.MYSQL_DB}")
        
    except pymysql.err.OperationalError as e:
        print(f"MySQL连接错误: {e}")
    except FileNotFoundError:
        print("错误: 找不到 db.sql 文件")
    except Exception as e:
        print(f"初始化数据库时发生错误: {e}")
    finally:
        try:
            connection.close()
        except:
            pass

if __name__ == '__main__':
    init_db()