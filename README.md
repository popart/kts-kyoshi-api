# kts-kyoshi-server

## Basic deps
pyenv
poetry

## postgres
```
docker pull postgres:16.2-bookworm

docker run --name my_db -e POSTGRES_PASSWORD=mypassword -p 5432:5432 -d postgres:16.2-bookworm 

psql -h localhost -p 5432 -U postgres

# can stop & restart without losing (e.g. shutting down docker)
docker stop my_db
docker start my_db

# to wipe the db
docker stop my_db
docker rm my_db
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
