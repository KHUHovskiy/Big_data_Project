CREATE DATABASE IF NOT EXISTS music;
USE music;

DROP TABLE IF EXISTS tracks;
CREATE TABLE tracks (
    id STRING,
    name STRING,
    popularity INT,
    duration_ms INT,
    explicit INT,
    artists STRING,
    id_artists STRING,
    release_date STRING,
    danceability DOUBLE,
    energy DOUBLE,
    key INT,
    loudness DOUBLE,
    mode INT,
    speechiness DOUBLE,
    acousticness DOUBLE,
    instrumentalness DOUBLE,
    liveness DOUBLE,
    valence DOUBLE,
    tempo DOUBLE,
    time_signature INT
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE;

DROP TABLE IF EXISTS artists;
CREATE TABLE artists (
    id STRING,
    followers DOUBLE,
    genres STRING,
    name STRING,
    popularity INT
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE;