"""
Скрипт для загрузки объединённой таблицы tracks_with_artists
из TSV-файла в PostgreSQL.

Использование:
1. Положить файл tracks_with_artists.tsv в папку export/
2. Запустить: python load_from_tsv.py
"""

import pandas as pd
from sqlalchemy import create_engine
import os

# --- НАСТРОЙКИ ---
TSV_FILE = 'export/tracks_with_artists.tsv'
DB_URL = 'postgresql+psycopg2://postgres:123@localhost:5433/music'

def main():
    # 1. Проверка, что файл существует
    if not os.path.exists(TSV_FILE):
        print(f"❌ ОШИБКА: Файл {TSV_FILE} не найден.")
        print("Пожалуйста, распакуйте архив tracks_with_artists.zip и положите файл в папку export/")
        return

    print(f"⏳ Читаем файл {TSV_FILE}...")
    
    # 2. Чтение TSV
    # sep='\t' — разделитель табуляция
    # header=None — в файле нет заголовков
    # quoting=3 — игнорировать кавычки (на всякий случай)
    try:
        df = pd.read_csv(TSV_FILE, sep='\t', header=None, quoting=3)
    except Exception as e:
        print(f"❌ Ошибка при чтении файла: {e}")
        return

    # 3. Задаем имена колонкам (ровно в том порядке, как они шли в Hive)
    df.columns = [
        'track_id', 'track_name', 'track_popularity',
        'danceability', 'energy', 'loudness', 'valence', 'tempo',
        'release_date', 'artist_name', 'followers', 'genres', 'artist_popularity'
    ]

    print(f"✅ Прочитано строк: {len(df)}")
    print("Первые 3 строки для проверки:")
    print(df.head(3).to_string())

    # 4. Подключение к PostgreSQL и загрузка
    print("\n⏳ Подключаемся к PostgreSQL (localhost:5433, db=music)...")
    try:
        engine = create_engine(DB_URL)
        
        # Записываем данные в таблицу. 
        # if_exists='replace' — если таблица была, она перезапишется.
        print("⏳ Загружаем данные в таблицу tracks_with_artists...")
        df.to_sql('tracks_with_artists', engine, if_exists='replace', index=False)
        
        print(f"\n✅ УСПЕХ! Загружено {len(df)} строк в PostgreSQL.")
        print("Теперь можно подключаться в DBeaver (localhost:5433, база music).")
        
    except Exception as e:
        print(f"\n❌ Ошибка при подключении к БД или загрузке: {e}")
        print("Проверьте, что Docker-контейнер music_pg запущен и работает на порту 5433.")

if __name__ == "__main__":
    main()