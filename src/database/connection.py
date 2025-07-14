"""
資料庫連接管理
"""
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from ..config.settings import settings
from .models import Base


class DatabaseManager:
    """資料庫管理器"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._setup_database()
    
    def _setup_database(self):
        """設置資料庫連接"""
        # 創建資料庫引擎
        self.engine = create_engine(
            settings.database_url,
            echo=settings.database_echo,
            pool_pre_ping=True,
            pool_recycle=300,
            connect_args={
                "options": "-c timezone=utc"
            }
        )
        
        # 創建會話工廠
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False
        )
        
        # 設置事件監聽器
        self._setup_event_listeners()
    
    def _setup_event_listeners(self):
        """設置資料庫事件監聽器"""
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """SQLite 特定設定（如果使用 SQLite）"""
            if 'sqlite' in settings.database_url:
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
    
    def create_tables(self):
        """創建所有資料表"""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """刪除所有資料表"""
        Base.metadata.drop_all(bind=self.engine)
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """獲取資料庫會話（上下文管理器）"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_session_direct(self) -> Session:
        """直接獲取資料庫會話"""
        return self.SessionLocal()
    
    def close(self):
        """關閉資料庫連接"""
        if self.engine:
            self.engine.dispose()


# 全域資料庫管理器實例
db_manager = DatabaseManager()


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依賴注入用的資料庫會話獲取器"""
    with db_manager.get_session() as session:
        yield session


def init_database():
    """初始化資料庫"""
    db_manager.create_tables()


def reset_database():
    """重設資料庫"""
    db_manager.drop_tables()
    db_manager.create_tables()


# 便捷函數
def execute_query(query_func, *args, **kwargs):
    """執行資料庫查詢"""
    with db_manager.get_session() as session:
        return query_func(session, *args, **kwargs)