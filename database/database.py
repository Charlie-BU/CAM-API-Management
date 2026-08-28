from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

engine = create_engine(
    url=os.getenv("DATABASE_URI") or "",
    echo=False,  # 关闭SQL语句输出
    pool_size=20,  # 默认连接池大小
    max_overflow=30,  # 最大溢出连接数
    pool_timeout=60,  # 连接超时时间
    pool_recycle=3600,  # 连接回收时间，防止连接被数据库关闭
    pool_pre_ping=True,  # 每次借出连接前 ping 一下，防止取到断开的连接
)
session = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def initialize_database():
    database_uri = os.getenv("DATABASE_URI")
    if not database_uri:
        raise RuntimeError("DATABASE_URI is not configured")

    # 显式验证数据库可达，避免应用启动后才在首个请求时报错。
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    # 若 models 中定义的表在库中不存在，则自动创建。
    from .models import Base

    Base.metadata.create_all(bind=engine)