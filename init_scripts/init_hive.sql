CREATE DATABASE IF NOT EXISTS music;
USE music;

CREATE EXTERNAL TABLE IF NOT EXISTS tracks (
    id STRING, name STRING, popularity INT, duration_ms INT, explicit INT,
    artists STRING, id_artists STRING, release_date STRING, danceability DOUBLE,
    energy DOUBLE, key INT, loudness DOUBLE, mode INT, speechiness DOUBLE,
    acousticness DOUBLE, instrumentalness DOUBLE, liveness DOUBLE, valence DOUBLE,
    tempo DOUBLE, time_signature INT
) ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' STORED AS TEXTFILE
LOCATION '/user/hive/warehouse/music.db/tracks';

CREATE EXTERNAL TABLE IF NOT EXISTS artists (
    id STRING, followers DOUBLE, genres STRING, name STRING, popularity INT
) ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' STORED AS TEXTFILE
LOCATION '/user/hive/warehouse/music.db/artists';

-- 1. Создаем промежуточную таблицу, где разворачиваем артистов
DROP TABLE IF EXISTS tracks_exploded;
CREATE TABLE tracks_exploded AS
SELECT 
    t.id AS track_id, t.name AS track_name, t.popularity AS track_popularity,
    t.danceability, t.energy, t.loudness, t.valence, t.tempo, t.release_date,
    exploded.artist_id
FROM tracks t
LATERAL VIEW explode(split(t.id_artists, ',')) exploded AS artist_id;

-- 2. Теперь делаем JOIN с таблицей артистов (без LATERAL VIEW)
DROP TABLE IF EXISTS tracks_with_artists;
CREATE TABLE tracks_with_artists AS
SELECT 
    te.track_id, te.track_name, te.track_popularity,
    te.danceability, te.energy, te.loudness, te.valence, te.tempo, te.release_date,
    a.name AS artist_name, a.followers, a.genres, a.popularity AS artist_popularity
FROM tracks_exploded te
JOIN artists a ON te.artist_id = a.id;

-- 3. Выгружаем результат в текстовый файл для передачи в PostgreSQL
INSERT OVERWRITE DIRECTORY '/tmp/export' ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
SELECT * FROM tracks_with_artists;