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

