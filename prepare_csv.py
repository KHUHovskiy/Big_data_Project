import pandas as pd
import os

os.makedirs('dataset_prepared', exist_ok=True)

# === TRACKS ===
print("Обработка tracks.csv...")
tracks = pd.read_csv('dataset/tracks.csv')

# Преобразуем id_artists в нормальный вид (убираем [' '] и кавычки)
tracks['id_artists'] = tracks['id_artists'].astype(str).str.replace(r"[\[\]']", "", regex=True)
tracks['artists'] = tracks['artists'].astype(str).str.replace(r"[\[\]']", "", regex=True)

# Сохраняем как TSV (tab-separated) — Hive примет без проблем
tracks.to_csv('dataset_prepared/tracks.tsv', sep='\t', index=False, header=False)
print(f"  tracks.tsv: {len(tracks)} строк")

# === ARTISTS ===
print("Обработка artists.csv...")
artists = pd.read_csv('dataset/artists.csv')

# Убираем квадратные скобки и кавычки из жанров
artists['genres'] = artists['genres'].astype(str).str.replace(r"[\[\]']", "", regex=True)

# TSV
artists.to_csv('dataset_prepared/artists.tsv', sep='\t', index=False, header=False)
print(f"  artists.tsv: {len(artists)} строк")

print("\nГотово. Файлы в dataset_prepared/")