
.PHONY: start help hdfs-dirs upload-hdfs hive-join export-hdfs \
        create-pg-table copy-to-pg verify-pg clean status


start:
	@echo "Проверка необходимых зависимостей"
	poetry install
	@sleep 3

	@echo "0. Поднимаем контейнеры через docker compose up -d..."
	docker compose up -d
	
	@echo "Запуск содержимого контейнеров"
	@sleep 5
	@echo "Контейнеры запущены. Переходим к пайплайну..."
	
	$(MAKE) upload-hdfs
	$(MAKE) hive-join
	$(MAKE) export-hdfs
	$(MAKE) copy-to-pg
	@echo "Пайплайн пройден успешно"

stop:
	docker compose down -v

help:
	@echo "Доступные цели:"
	@echo "  make start         - поднять контейнеры и прогнать весь пайплайн (по умолчанию)"
	@echo "  make stop          - остановить все запущенные контейнеры"
	@echo "  make hdfs-dirs     - создать директории в HDFS"
	@echo "  make upload-hdfs   - загрузить TSV в HDFS"
	@echo "  make hive-join     - выполнить JOIN в Hive"
	@echo "  make export-hdfs   - забрать результат из HDFS на хост"
	@echo "  make copy-to-pg    - создать таблицу и залить данные в PostgreSQL"
	@echo "  make verify-pg     - проверить, что данные залились"
	@echo "  make status        - показать статус контейнеров"
	@echo "  make clean         - удалить временные файлы"

status:
	@echo "Статус контейнеров:"
	@docker ps --format "table {{.Names}}\t{{.Status}}"

clean:
	@echo "Удаляем временные файлы..."
	-rm -f /tmp/joined_data.csv
	-rm -f load.sql
	-docker exec datanode rm -f /tmp/joined_data.csv 2>/dev/null || true
	-docker exec datanode hdfs dfs -rm -r -f /user/hive/warehouse/music.db/tracks_with_artists 2>/dev/null || true
	-docker exec target_postgres rm -f /tmp/data.tsv /tmp/load.sql 2>/dev/null || true





hdfs-dirs:
	@echo "2a. Создаём директории в HDFS..."
	docker exec datanode hdfs dfs -mkdir -p \
		/user/hive/warehouse/music.db/tracks \
		/user/hive/warehouse/music.db/artists

upload-hdfs: hdfs-dirs
	@echo "2b. Загружаем данные в HDFS..."
	docker exec datanode hdfs dfs -put -f \
		/tmp/init_data/tracks.tsv \
		/user/hive/warehouse/music.db/tracks/data
	docker exec datanode hdfs dfs -put -f \
		/tmp/init_data/artists.tsv \
		/user/hive/warehouse/music.db/artists/data


hive-join:
	@echo "3. Выполняем JOIN в Hive (около 2 минут)..."
	docker exec hive-server hive -f /tmp/init_scripts/init_hive.sql

hive-join:
	@echo "3. Выполняем JOIN в Hive (около 2 минут)..."
	docker exec hive-server hive -f /tmp/init_scripts/init_hive.sql

export-hdfs:
	@echo "4. Забираем файл из HDFS и копируем в PostgreSQL..."
	docker exec datanode hdfs dfs -get /tmp/export/* /tmp/data.tsv
	docker cp datanode:/tmp/data.tsv ./data.tsv
	docker cp ./data.tsv target_postgres:/tmp/data.tsv

copy-to-pg:
	@echo "5. Создаем таблицу и заливаем данные..."
	@printf '%s\n' \
		'CREATE TABLE IF NOT EXISTS tracks_with_artists (' \
		'    track_id TEXT, track_name TEXT, track_popularity INT,' \
		'    danceability FLOAT, energy FLOAT, loudness FLOAT, valence FLOAT, tempo FLOAT, release_date TEXT,' \
		'    artist_name TEXT, followers FLOAT, genres TEXT, artist_popularity INT' \
		');' \
		'' \
		"\\copy tracks_with_artists FROM '/tmp/data.tsv' WITH (FORMAT csv, DELIMITER E'\\t');" \
		> load.sql
	docker cp load.sql target_postgres:/tmp/load.sql
	docker exec target_postgres psql -U postgres -d music -f /tmp/load.sql
	-rm -f load.sql
	@echo "5. Проверяем, что данные залились..."
	$(MAKE) verify-pg