from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.APP_ENV == "development",
    pool_size=5,
    max_overflow=0,
    pool_timeout=30,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Không tự động làm mới dữ liệu sau commit
)

# Base class cho các model SQLAlchemy
class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()  # Commit nếu không có lỗi
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()
