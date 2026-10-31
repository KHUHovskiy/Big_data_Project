import subprocess
import time
import os

def run_cmd(cmd):
    print(f"Выполняю: {cmd}")
    subprocess.run(cmd, shell=True)

# print("1. Ждем, пока контейнеры поднимутся...")
# time.sleep(30)

print("2. Загружаем данные в HDFS...")
run_cmd('docker exec datanode hdfs dfs -mkdir -p /user/hive/warehouse/music.db/tracks /user/hive/warehouse/music.db/artists')
run_cmd('docker exec datanode hdfs dfs -put -f /tmp/init_data/tracks.tsv /user/hive/warehouse/music.db/tracks/data')
run_cmd('docker exec datanode hdfs dfs -put -f /tmp/init_data/artists.tsv /user/hive/warehouse/music.db/artists/data')

print("3. Выполняем JOIN в Hive (это займет около 2 минут)...")
run_cmd('docker exec hive-server hive -f /tmp/init_scripts/init_hive.sql')

print("4. Забираем файл из HDFS и копируем в PostgreSQL...")
run_cmd('docker exec datanode hdfs dfs -get /tmp/export/* /tmp/data.tsv')
run_cmd('docker cp datanode:/tmp/data.tsv ./data.tsv')
run_cmd('docker cp ./data.tsv target_postgres:/tmp/data.tsv')

print("5. Создаем таблицу и заливаем данные...")

# Создаем SQL-скрипт локально, чтобы избежать проблем с кавычками в Windows
sql_content = """CREATE TABLE IF NOT EXISTS tracks_with_artists (
    track_id TEXT, track_name TEXT, track_popularity INT,
    danceability FLOAT, energy FLOAT, loudness FLOAT, valence FLOAT, tempo FLOAT, release_date TEXT,
    artist_name TEXT, followers FLOAT, genres TEXT, artist_popularity INT
);

\\copy tracks_with_artists FROM '/tmp/data.tsv' WITH (FORMAT csv, DELIMITER E'\\t');
"""

with open("load.sql", "w", encoding="utf-8") as f:
    f.write(sql_content)

# Копируем SQL-скрипт в контейнер
run_cmd('docker cp load.sql target_postgres:/tmp/load.sql')

# Выполняем скрипт внутри контейнера
run_cmd('docker exec target_postgres psql -U postgres -d music -f /tmp/load.sql')

# Удаляем временный файл, чтобы не мусорить
if os.path.exists("load.sql"):
    os.remove("load.sql")

print("\n✅ ГОТОВО! Проверь базу:")
print('docker exec -it target_postgres psql -U postgres -d music -c "SELECT COUNT(*) FROM tracks_with_artists;"')