# kts-kyoshi-server

## Basic deps
pyenv
poetry

## postgres
```
docker pull postgres:16.2-bookworm

export DB_NAME="kyoshi_db"

docker run --name $DB_NAME -e POSTGRES_PASSWORD=mypassword -e POSTGRES_INITDB_ARGS="--encoding=UTF8" -p 5432:5432 -d postgres:16.2-bookworm

psql -h localhost -p 5432 -U postgres

# can stop & restart without losing (e.g. shutting down docker)
docker stop $DB_NAME
docker start $DB_NAME

# to wipe the db
docker stop $DB_NAME
docker rm $DB_NAME
```
need to create database manually
`CREATE DATABASE kyoshi`

## alembic
(had to update alembic/env.py for autogeneration)
`target_metadata = declarative_base.Base.metadata`

```
poetry run alembic revision --autogenerate -m "create User table"
poetry run alembic upgrade head
```

DB design:
- avoid nulls (default values better if they make sense, e.g. 0 on a column you'll sum)
- no foreign key constraints (slows the db down)
- uuids instead of ints for PKs (enables sharding later)

Drop all alembic tables:
`poetry run python -m scripts.drop_all_tables`

## llm providers
### 2024-05-11
gpt-4 definitely works
claude sonnet (3x cheaper) can't get pronunciations right
claude opus (3x expensive)
