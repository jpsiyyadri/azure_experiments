import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()


host = os.getenv("host")
port = os.getenv("port")
user = os.getenv("user")
password = os.getenv("password")
dbname = os.getenv("dbname")

print(
    f"host: {host}, port: {port}, user: {user}, password: {password}, dbname: {dbname}"
)

SQLALCHEMY_DATABASE_URL = "postgresql://citus:Pass#123@c-cosmosclusterforedd.2kjehug7sx75bl.postgres.cosmos.azure.com:5432/citus?sslmode=require"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


