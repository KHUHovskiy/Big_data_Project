import pandas as pd
from sqlalchemy import create_engine

# 1. Читаем файл из export
print("Читаем файл export/000000_0...")
df = pd.read_csv('export/000000_0', sep='\t', header=None, quoting=3)

# 2. Даём имена колонкам (в порядке SELECT из Hive)
df.columns = [
    'track_id', 'track_name', 'track_popularity',
    'danceability', 'energy', 'loudness', 'valence', 'tempo',
    'release_date', 'artist_name', 'followers', 'genres', 'artist_popularity'
]

print(f"Строк: {len(df)}")
print(df.head(3))

# 3. Подключаемся к PostgreSQL (порт 5433!)
engine = create_engine('postgresql://postgres:123@localhost:5433/music')

# 4. Заливаем
print("Загружаем в PostgreSQL...")
df.to_sql('tracks_with_artists', engine, if_exists='replace', index=False)
print(f"Загружено: {len(df)} строк")