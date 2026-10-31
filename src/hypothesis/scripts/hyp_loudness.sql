SELECT
    track_id,
    release_date,
    EXTRACT(YEAR FROM release_date::date)::int AS release_year,
    loudness,
    track_popularity,
    genres
FROM tracks_with_artists
WHERE release_date ~ '^\d{4}-\d{2}-\d{2}$'   -- только корректные даты
  AND loudness IS NOT NULL;