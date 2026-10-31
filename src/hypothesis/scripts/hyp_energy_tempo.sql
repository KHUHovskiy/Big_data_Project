SELECT
    track_id,
    tempo,
    energy,
    genres
FROM tracks_with_artists
WHERE tempo > 0            
  AND energy IS NOT NULL
  AND tempo IS NOT NULL;