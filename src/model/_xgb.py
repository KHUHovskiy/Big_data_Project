import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import xgboost as xgb

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from database import read
from database import ENGINE as engine


# ==== 1. ЗАГРУЗКА И ПОДГОТОВКА ====
def load_and_preprocess() -> tuple:
    print("Загрузка данных из БД...")
    query = read("ml_query_xgb.sql")
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    print(f"Загружено строк: {len(df):,}")

    # Заполняем пропуски
    df["followers"] = df["followers"].fillna(0)
    df["artist_popularity"] = df["artist_popularity"].fillna(df["artist_popularity"].median())

    # Создаем признак "Эра" (old, medium, new)
    def get_era(year):
        if year < 2000: return "old"
        elif year <= 2015: return "medium"
        else: return "new"
    
    df["era"] = df["release_year"].apply(get_era)
    le = LabelEncoder()
    df["era_encoded"] = le.fit_transform(df["era"])

    # Убираем ненужное
    df = df.drop(columns=["release_year", "era"])

    # X и y
    y = df["track_popularity"]
    X = df.drop(columns=["track_popularity"])

    # Тренировочная и тестовая выборки
    return train_test_split(X, y, test_size=0.2, random_state=42)


# ==== 2. ОБУЧЕНИЕ XGBOOST ====
def train_xgboost(X_train, X_test, y_train, y_test):
    print("\nОбучение XGBoost...")
    start_time = time.time()

    # Настройки XGBoost
    # early_stopping_rounds останавливает обучение, если модель перестала улучшаться на тесте
    model = xgb.XGBRegressor(
        n_estimators=1000,          # Максимум деревьев
        learning_rate=0.05,         # Скорость обучения (меньше = точнее, но дольше)
        max_depth=7,                # Глубина деревьев
        subsample=0.8,              # Использовать 80% данных для каждого дерева (защита от переобучения)
        colsample_bytree=0.8,       # Использовать 80% признаков для каждого дерева
        random_state=42,
        n_jobs=-1,                  # Использовать все ядра процессора
        tree_method="hist",         # Самый быстрый метод для больших данных
        early_stopping_rounds=50    # Остановиться, если 50 итераций нет улучшений
    )

    # Обучаем с валидацией на тестовой выборке
    model.fit(
        X_train, y_train,
        eval_set=[(X_train, y_train), (X_test, y_test)],
        verbose=100 # Печатать прогресс каждые 100 деревьев
    )

    print(f"Обучение завершено за {time.time() - start_time:.1f} секунд.")
    return model


# ==== 3. ОЦЕНКА И ВИЗУАЛИЗАЦИЯ ====
def evaluate_and_plot(model, X_test, y_test):
    # Прогноз
    y_pred = model.predict(X_test)

    # Метрики
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    print("\n=== МЕТРИКИ МОДЕЛИ XGBOOST ===")
    print(f"MAE:  {mae:.2f} (средняя ошибка в баллах)")
    print(f"RMSE: {rmse:.2f}")
    print(f"R²:   {r2:.3f} (объясненная дисперсия)")

    # Визуализация
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle("Анализ модели XGBoost", fontsize=16, fontweight="bold")

    # 1. График: Реальная vs Предсказанная популярность
    ax = axes[0]
    # Берем подвыборку для читаемости графика
    sample_idx = np.random.choice(len(y_test), size=min(10000, len(y_test)), replace=False)
    ax.scatter(y_test.iloc[sample_idx], y_pred[sample_idx], alpha=0.2, s=10, color="teal")
    
    # Идеальная линия
    ax.plot([0, 100], [0, 100], color="red", linestyle="--", lw=2)
    ax.set_title("Реальная vs Предсказанная")
    ax.set_xlabel("Реальная популярность (0-100)")
    ax.set_ylabel("Предсказанная популярность")
    ax.grid(alpha=0.3)

    # 2. Важность признаков
    ax = axes[1]
    importances = model.feature_importances_
    imp_df = pd.DataFrame({
        'feature': X_test.columns,
        'importance': importances
    }).sort_values(by='importance', ascending=False)

    sns.barplot(data=imp_df, y='feature', x='importance', palette="viridis", ax=ax)
    ax.set_title("Важность признаков (Feature Importance)")
    ax.set_xlabel("Влияние на прогноз")
    ax.set_ylabel("")

    # 3. Распределение ошибок (Residuals)
    ax = axes[2]
    residuals = y_test - y_pred
    sns.histplot(residuals, bins=50, kde=True, color="purple", ax=ax)
    ax.axvline(0, color="red", linestyle="--")
    ax.set_title("Распределение ошибок (Residuals)")
    ax.set_xlabel("Ошибка (Реальность - Прогноз)")
    ax.set_ylabel("Количество треков")
    ax.set_xlim(-50, 50)

    plt.tight_layout()
    plt.show()

    return imp_df


# ==== MAIN ====
if __name__ == "__main__":
    # 1. Подготовка
    X_train, X_test, y_train, y_test = load_and_preprocess()
    
    # 2. Обучение
    model = train_xgboost(X_train, X_test, y_train, y_test)
    
    # 3. Оценка
    imp_df = evaluate_and_plot(model, X_test, y_test)
    
    print("\nТоп-5 самых важных признаков:")
    print(imp_df.head(5).to_string(index=False))