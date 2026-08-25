-- Runs once on first Postgres startup (docker-entrypoint-initdb.d).
-- Creates one database per service; each service owns its own schema, matching
-- the "services share no code / no shared DB access" boundary.
CREATE DATABASE usersdb;
CREATE DATABASE dynamiccontentdb;
CREATE DATABASE profiledb;
CREATE DATABASE messagingdb;
