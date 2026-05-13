from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

# Database connection url for PostgreSQL database
# with asyncpg driver for asynchronous operations.
DATABASE_URL = "...+...:///"

# Async engine for database.
engine = create_async_engine(DATABASE_URL)

# Session for engine.
# Expire_on_commit is set to False to prevent automatic 
# expiration of objects after commit.
session = async_sessionmaker(engine, expire_on_commit=False)

# Parent class for project chart/sheet classes.
class Model(MappedAsDataclass, DeclarativeBase):
    pass

# Dependency function to get a database session.
async def get_db():
    async with session() as session:
        yield session

# Database session dependency. Automatically provides
# a session to database and closes it after.
SessionDep = Annotated[AsyncSession, Depends(get_db)]