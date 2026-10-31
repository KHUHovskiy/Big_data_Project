WITH artist_stats AS (
    SELECT
        artist_name,
        COUNT(track_id) AS total_tracks,
        MIN(EXTRACT(YEAR FROM release_date::date)) AS first_year,
        MAX(track_popularity) AS max_track_pop,
        AVG(track_popularity) AS avg_track_pop,
        MAX(artist_popularity) AS artist_pop,
        MAX(followers) AS followers
    FROM tracks_with_artists
    WHERE release_date ~ '^\d{4}-\d{2}-\d{2}$' -- только валидные даты
    GROUP BY artist_name
)
SELECT
    artist_name,
    total_tracks,
    first_year,
    (EXTRACT(YEAR FROM CURRENT_DATE) - first_year) AS experience_years,
    max_track_pop,
    avg_track_pop,
    artist_pop,
    followers
FROM artist_stats
WHERE first_year >= 1900; -- отсекаем мусорные даты