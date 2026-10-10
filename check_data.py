import pandas as pd

# Загружаем CSV
tracks = pd.read_csv('dataset/tracks.csv')
artists = pd.read_csv('dataset/artists.csv')

print("=== tracks ===")
print("Форма:", tracks.shape)
print("Колонки:", tracks.columns.tolist())
print(tracks[['name', 'popularity', 'danceability', 'energy']].head())
print("\nПропусков:", tracks.isnull().sum().sum())

print("\n=== artists ===")
print("Форма:", artists.shape)
print("Колонки:", artists.columns.tolist())
print(artists[['name', 'followers', 'genres']].head())
print("\nПропусков:", artists.isnull().sum().sum())