from sqlalchemy import Table, Column, Integer, String
from backend.db import metadata

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("username", String, unique=True, index=True, nullable=False),
    Column("password", String, nullable=False),
    Column("role", String, nullable=False, default="viewer"),
)