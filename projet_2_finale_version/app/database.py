import os
from sqlmodel import SQLModel, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL, echo=True, future=True)

async def init_db():
    import asyncio
    retries = 5
    for i in range(retries):
        try:
            async with engine.begin() as conn:
                # await conn.run_sync(SQLModel.metadata.drop_all)
                await conn.run_sync(SQLModel.metadata.create_all)
            print("Database initialized successfully.")
            return
        except Exception as e:
            if i == retries - 1:
                raise e
            print(f"Database not ready, retrying in 2s... ({i+1}/{retries}) Error: {e}")
            await asyncio.sleep(2)

async def get_session() -> AsyncSession:
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
