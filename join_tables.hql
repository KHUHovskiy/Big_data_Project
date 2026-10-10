USE music;

-- 1. Разворачиваем список ID исполнителей
DROP TABLE IF EXISTS tracks_exploded;
CREATE TABLE tracks_exploded AS
SELECT 
    t.id AS track_id,
    t.name AS track_name,
    t.popularity AS track_popularity,
    t.danceability,
    t.energy,
    t.loudness,
    t.valence,
    t.tempo,
    t.release_date,
    exploded_id AS artist_id
FROM tracks t
LATERAL VIEW explode(split(t.id_artists, ',')) exploded_table AS exploded_id;

-- 2. JOIN с artists
DROP TABLE IF EXISTS tracks_with_artists;
CREATE TABLE tracks_with_artists AS
SELECT 
    te.track_id,
    te.track_name,
    te.track_popularity,
    te.danceability,
    te.energy,
    te.loudness,
    te.valence,
    te.tempo,
    te.release_date,
    a.name AS artist_name,
    a.followers,
    a.genres,
    a.popularity AS artist_popularity
FROM tracks_exploded te
JOIN artists a ON te.artist_id = a.id;