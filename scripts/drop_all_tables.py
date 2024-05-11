import configparser
from sqlalchemy import create_engine, text
from db_models import declarative_base

config = configparser.ConfigParser()
config.read("alembic.ini")

db_url = config.get("alembic", "sqlalchemy.url")


if __name__ == "__main__":
    engine = create_engine(db_url)
    target_metadata = declarative_base.Base.metadata

    print(f"Drop tables from {db_url}")
    confirm = input(
        "Are you sure you want to drop all tables? Type 'yes' to continue: "
    )
    if confirm.lower() == "yes":
        # Drop all tables defined in Base.metadata
        target_metadata.drop_all(engine)

        # Drop alembic_version table explicitly
        with engine.connect() as connection:
            connection.execute(text("DROP TABLE IF EXISTS alembic_version;"))
            connection.commit()

        print("All tables have been dropped.")
    else:
        print("Operation canceled.")
