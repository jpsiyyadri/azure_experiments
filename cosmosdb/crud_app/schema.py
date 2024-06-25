from sqlalchemy import text

from db import SessionLocal

with SessionLocal() as session:
    users = session.query(text("select * from pg_database")).all()
    print(
        users
    )
