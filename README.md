# kts-kyoshi-server

## Basic deps
uv

## setup
```
uv sync
```

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
uv run alembic revision --autogenerate -m "create User table"
uv run alembic upgrade head
```

DB design:
- avoid nulls (default values better if they make sense, e.g. 0 on a column you'll sum)
- no foreign key constraints (slows the db down)
- uuids instead of ints for PKs (enables sharding later)

Drop all alembic tables:
`uv run python -m scripts.drop_all_tables`

# docker build
```
docker build -t kyoshi:dev .

docker run -d --name kyoshi_api -p 5555:5555 -e MY_SECRET_KEY=$(gcloud secrets versions access latest --secret="YOUR_SECRET_NAME") kyoshi:dev
```
secrets configured in cloud run. pulled at instance startup
then they'll only live in running instances env.
and not be saved in the docker build.

# docker network
Getting all the docker containers to talk to each other
(`docker-compose up` does all of this)
```
docker network create kyoshi_network
docker network connect kyoshi_network kyoshi_db
docker network connect kysohi_network kyoshi_api # <-- container_id alias

docker run {kyosh api} --network -e DB_HOST=my_postgres -e DB_USER=postgres -e DB_PASSWORD=mysecretpassword kyoshi_network
```


## llm providers
### 2024-05-11
gpt-4 definitely works
claude sonnet (3x cheaper) can't get pronunciations right
claude opus (3x expensive)

