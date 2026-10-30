#!/bin/bash
echo "Ожидание запуска Hive Metastore..."
sleep 40

echo "Выполнение HQL-скрипта..."
hive -f /tmp/init_scripts/init_hive.sql
echo "JOIN выполнен, данные готовы к экспорту!"