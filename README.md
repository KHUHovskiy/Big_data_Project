# Групповой проект по дисциплине «Архитектура больших данных»

## Тема
Анализ датасета Spotify (600k+ треков)

## Авторы
- [Твоё ФИО] — Data Engineer (архитектура, ETL)
- [ФИО друга] — Data Analyst (гипотезы, визуализация)

## Архитектура

CSV → HDFS → Hive → PostgreSQL → Superset/Grafana

- **HDFS** — распределённое хранилище данных
- **Hive** — обработка данных (SQL поверх Hadoop)
- **PostgreSQL** — БД для аналитики и визуализации
- **Python** — ETL (обработка и загрузка)

## Данные

- **Источник:** Kaggle — Spotify Dataset 1921–2020 (600k tracks)
- **Размер:** ~495 МБ (tracks.csv + artists.csv)
- **Ссылка:** https://www.kaggle.com/datasets/yamaerenay/spotify-dataset-19212020-600k-tracks

⚠️ **Данные не хранятся в репозитории** (слишком большие). Скачайте их по ссылке и положите в папку `dataset/`.

## Запуск

1. Запустить контейнеры:
   ```bash
   docker-compose up -d