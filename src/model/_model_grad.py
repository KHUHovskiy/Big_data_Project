import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.inspection import permutation_importance

from database import read
from database import ENGINE as engine


# ==== 1. ЗАГРУЗКА ДАННЫХ ====
def load_data() -> pd.DataFrame:
    print("Загрузка данных из БД...")
    query = read("ml_query_grad.sql")
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    print(f"Загружено строк: {len(df):,}")
    return df


# ==== 2. ПОДГОТОВКА ПРИЗНАКОВ ====
def preprocess(df: pd.DataFrame):
    # Заполняем пропуски
    df["main_genre"] = df["main_genre"].fillna("unknown")
    df["followers"] = df["followers"].fillna(0)
    df["artist_popularity"] = df["artist_popularity"].fillna(df["artist_popularity"].median())

    # Кодируем жанры (One-Hot Encoding)
    # Оставляем только топ-20 жанров, остальные объединяем в 'other'
    top_genres = df["main_genre"].value_counts().head(20).index
    df["main_genre"] = df["main_genre"].where(df["main_genre"].isin(top_genres), "other")

    df_encoded = pd.get_dummies(df, columns=["main_genre"], drop_first=True, dtype=int)

    # Отделяем целевую переменную от признаков
    X = df_encoded.drop(columns=["track_popularity"])
    y = df_encoded["track_popularity"]

    return X, y


# ==== 3. ОБУЧЕНИЕ МОДЕЛИ ====
def train_model(X, y):
    # Разделяем на train и test (80% / 20%)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print("Обучение модели (Gradient Boosting)...")
    # Используем HistGradientBoostingRegressor — он быстрый и мощный
    model = HistGradientBoostingRegressor(
        max_iter=200, 
        learning_rate=0.1, 
        max_depth=10, 
        random_state=42
    )
    model.fit(X_train, y_train)

    # Прогноз
    y_pred = model.predict(X_test)

    # Оценка качества
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    print("\n=== МЕТРИКИ КАЧЕСТВА ===")
    print(f"MAE (Средняя абсолютная ошибка): {mae:.2f} баллов")
    print(f"RMSE (Квадратичная ошибка):      {rmse:.2f} баллов")
    print(f"R² (Объясненная дисперсия):      {r2:.3f}")

    return model, X_test, y_test, y_pred


# ==== 4. ВИЗУАЛИЗАЦИЯ И ВАЖНОСТЬ ПРИЗНАКОВ ====
def plot_results(model, X_test, y_test, y_pred):
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # --- График 1: Реальная vs Предсказанная популярность ---
    ax = axes[0]
    # Берем подвыборку для графика, чтобы точки не слиплись
    sample_idx = np.random.choice(len(y_test), size=min(5000, len(y_test)), replace=False)
    ax.scatter(y_test.iloc[sample_idx], y_pred[sample_idx], alpha=0.2, s=10, color="teal")
    
    # Идеальная линия (если бы модель предсказывала идеально)
    ax.plot([0, 100], [0, 100], color="red", linestyle="--", lw=2)
    
    ax.set_title("Реальная vs Предсказанная популярность")
    ax.set_xlabel("Реальная популярность")
    ax.set_ylabel("Предсказанная популярность")
    ax.grid(alpha=0.3)

    # --- График 2: Важность признаков (Permutation Importance) ---
    ax = axes[1]
    print("\nРасчет важности признаков (может занять минуту)...")
    # Считаем важность на небольшой подвыборке, чтобы не ждать долго
    X_sample = X_test.iloc[:5000]
    y_sample = y_test.iloc[:5000]
    
    result = permutation_importance(
        model, X_sample, y_sample, n_repeats=5, random_state=42, n_jobs=-1
    )
    
    # Собираем в DataFrame и сортируем
    importance_df = pd.DataFrame({
        'feature': X_test.columns,
        'importance': result.importances_mean
    }).sort_values('importance', ascending=False).head(10)

    sns.barplot(
        data=importance_df, y="feature", x="importance", 
        palette="viridis", ax=ax, edgecolor="black"
    )
    ax.set_title("Топ-10 самых важных признаков")
    ax.set_xlabel("Влияние на прогноз (Permutation Importance)")
    ax.set_ylabel("")

    plt.tight_layout()
    plt.show()


# ==== MAIN ====
if __name__ == "__main__":
    df = load_data()
    X, y = preprocess(df)
    
    model, X_test, y_test, y_pred = train_model(X, y)
    plot_results(model, X_test, y_test, y_pred)