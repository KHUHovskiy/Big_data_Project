SELECT
    track_popularity,
    danceability,
    energy,
    loudness,
    valence,
    tempo,
    EXTRACT(YEAR FROM release_date::date)::int AS release_year,
    artist_popularity,
    followers
FROM tracks_with_artists
WHERE release_date ~ '^\d{4}-\d{2}-\d{2}$'
  AND tempo BETWEEN 40 AND 220
  AND loudness BETWEEN -40 AND 5
  AND track_popularity IS NOT NULL
LIMIT 1000000;