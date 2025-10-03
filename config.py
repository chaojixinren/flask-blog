import os

class Config:
    # MySQL配置
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'tinki2307')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'xinrendatabase')
    MYSQL_CHARSET = 'utf8mb4'