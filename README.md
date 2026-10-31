# Групповой проект по дисциплине «Архитектура больших данных»

## Тема
Анализ датасета Spotify (600k+ треков)\
### Выбранные гипотезы
1. Чем ближе дата выхода трека к текущему дню, тем больше будет громкость 

2. Темп и енергия трека коррелируют между собой

3. Опыт исполнителя влияет на популярность его песни

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

## Запуск
### Вариант 1 — через Makefile

Требуется [Poetry](https://python-poetry.org/docs/#installation)

```bash
make start   # запуск пайплайна
make stop    # остановка программы
make help    # список дополнительных команд
```
### Вариант 2 — ручная установка
1. Загрузка зависимостей (любой из способов):
```
- poetry install
# или
- pip install -r requirements.txt
```
2. Запуск контейнеров:
```
docker compose up -d
```
3. Запуск пайплайна:
```
python run_pipeline.py
```

### 4. Подключение к БД
| Параметр | Значение |
|---|---|
| Host | `localhost` |
| Port | `5433` |
| Database | `music` |
| Username | `postgres` |
| Password | `123` |

**Рабочая таблица:** `tracks_with_artists` — 514 352 строки.