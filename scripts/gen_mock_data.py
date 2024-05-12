import configparser
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from db_models import User

config = configparser.ConfigParser()
config.read("alembic.ini")

db_url = config.get("alembic", "sqlalchemy.url")


if __name__ == "__main__":
    engine = create_engine(db_url)

    with Session(engine) as session:
        god = User(email="god@tsunderegeniuslabs.com")
        session.add(god)
        session.commit()
