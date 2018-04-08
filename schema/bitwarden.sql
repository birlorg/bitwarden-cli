--liquibase formatted sql

--changeset birlorg:1
create table config (
    key STRING primary key,
    value TEXT
);
--rollback drop table config;

--changeset birlorg:2
CREATE TABLE users
        (uuid STRING PRIMARY KEY,
        created_at DATETIME,
        updated_at DATETIME,
        email TEXT UNIQUE,
        email_verified BOOLEAN,
        premium BOOLEAN,
        name TEXT,
        password_hash TEXT,
        password_hint TEXT,
        key TEXT,
        private_key BLOB,
        public_key BLOB,
        totp_secret STRING,
        security_stamp STRING,
        culture STRING);
--rollback drop table users;

--changeset birlorg:3
CREATE TABLE devices
        (uuid STRING PRIMARY KEY,
        created_at DATETIME,
        updated_at DATETIME,
        user_uuid STRING,
        name STRING,
        type INTEGER,
        push_token STRING UNIQUE,
        access_token STRING UNIQUE,
        refresh_token STRING UNIQUE,
        token_expires_at DATETIME);
--rollback drop table devices;

--changeset birlorg:4
CREATE TABLE ciphers (
	uuid STRING PRIMARY KEY,
        created_at DATETIME,
        updated_at DATETIME,
	json STRING,
	card STRING,
        user_uuid STRING,
	collection_ids STRING,
	data STRING,
	edit BOOLEAN,
        favorite BOOLEAN,
        folder_uuid STRING,
	identity STRING,
	login STRING,
	uri STRING,
	name STRING,
	notes STRING,
	object STRING,
	organization_id BOOLEAN,
	organization_use_totp BOOLEAN,
	secure_note STRING,
        type INTEGER,

        attachments BLOB);
--rollback drop table ciphers;

--changeset birlorg:5
CREATE TABLE uris (
	id INTEGER PRIMARY KEY,
	match INTEGER,
	uri STRING,
	cipher_id STRING NOT NULL,
	FOREIGN KEY (cipher_id) REFERENCES ciphers(uuid)
);
--rollback drop table uris;

--changeset birlorg:6
CREATE TABLE fields (
	id INTEGER PRIMARY KEY,
	name STRING,
	type INTEGER,
	value STRING,
	cipher_id STRING NOT NULL,
	FOREIGN KEY (cipher_id) REFERENCES ciphers(uuid)
);

--changeset birlorg:7
CREATE TABLE folders
        (uuid STRING PRIMARY KEY,
        created_at DATETIME,
        updated_at DATETIME,
        user_uuid STRING,
        name BLOB);
--rollback drop table folders;

--changeset birlorg:8
CREATE TABLE attachments (
	id INTEGER PRIMARY KEY,
	data STRING,
	cipher_id STRING NOT NULL,
	FOREIGN KEY (cipher_id) REFERENCES ciphers(uuid)
	);
--rollback drop table attachments;
