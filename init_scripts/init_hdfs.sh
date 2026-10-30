#!/bin/bash
echo "Ожидание запуска NameNode..."

# Ждем, пока namenode станет доступен (пытаемся подключиться в цикле)
until hdfs dfs -ls / > /dev/null 2>&1; do
  echo "Ждем, пока NameNode поднимется..."
  sleep 5
done

echo "Загрузка данных в HDFS..."
hdfs dfs -mkdir -p /user/hive/warehouse/music.db/tracks
hdfs dfs -mkdir -p /user/hive/warehouse/music.db/artists

hdfs dfs -put -f /tmp/init_data/tracks.tsv /user/hive/warehouse/music.db/tracks/data
hdfs dfs -put -f /tmp/init_data/artists.tsv /user/hive/warehouse/music.db/artists/data

echo "Данные в HDFS загружены!"