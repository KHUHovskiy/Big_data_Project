import time
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import xgboost as xgb

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix, 
    roc_auc_score, roc_curve, f1_score
)

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

    # Создаем признак "Эра"
    def get_era(year):
        if year < 2000: return "old"
        elif year <= 2015: return "medium"
        else: return "new"
    
    df["era"] = df["release_year"].apply(get_era)
    le = LabelEncoder()
    df["era_encoded"] = le.fit_transform(df["era"])

    # --- СОЗДАЕМ БИНАРНЫЙ ПРИЗНАК IS_HIT ---
    # 1 = хит (популярность > 65), 0 = не хит
    df["is_hit"] = (df["track_popularity"] > 50).astype(int)
    
    # Выводим статистику баланса классов
    hit_counts = df["is_hit"].value_counts()
    print(f"\nРаспределение классов (is_hit):")
    print(f"  Не хиты (0): {hit_counts[0]:,} ({hit_counts[0]/len(df)*100:.1f}%)")
    print(f"  Хиты (1):    {hit_counts[1]:,} ({hit_counts[1]/len(df)*100:.1f}%)")

    # Убираем ненужное (включая track_popularity, так как теперь таргет — is_hit)
    df = df.drop(columns=["release_year", "era", "track_popularity"])

    # X и y
    y = df["is_hit"]
    X = df.drop(columns=["is_hit"])

    # Тренировочная и тестовая выборки (stratify сохраняет пропорцию классов)
    return train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)


# ==== 2. ОБУЧЕНИЕ XGBOOST КЛАССИФИКАТОРА ====
def train_xgboost(X_train, X_test, y_train, y_test):
    print("\nОбучение XGBoost Classifier...")
    start_time = time.time()

    # Вычисляем дисбаланс классов (хитов обычно меньше, чем не-хитов)
    # Это заставит модель уделять больше внимания хитам
    scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()

    model = xgb.XGBClassifier(
        n_estimators=1000,
        learning_rate=0.05,
        max_depth=7,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight, # Боремся с дисбалансом классов
        random_state=42,
        n_jobs=-1,
        tree_method="hist",
        eval_metric="auc",                 # Для классификации используем AUC
        early_stopping_rounds=50
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_train, y_train), (X_test, y_test)],
        verbose=100
    )

    print(f"Обучение завершено за {time.time() - start_time:.1f} секунд.")
    return model


# ==== 3. ОЦЕНКА И ВИЗУАЛИЗАЦИЯ ====
def evaluate_and_plot(model, X_test, y_test):
    # Прогноз вероятностей (от 0 до 1) и классов (0 или 1)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    y_pred = model.predict(X_test)

    # Метрики классификации
    acc = accuracy_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_pred_proba)
    f1 = f1_score(y_test, y_pred)

    print("\n=== МЕТРИКИ МОДЕЛИ XGBOOST (КЛАССИФИКАЦИЯ) ===")
    print(f"Accuracy (Точность): {acc:.3f} (доля правильных ответов)")
    print(f"ROC-AUC:             {roc_auc:.3f} (способность отличать хиты от не-хитов)")
    print(f"F1-Score:            {f1:.3f} (баланс между точностью и полнотой)")
    
    print("\nДетальный отчет по классам:")
    print(classification_report(y_test, y_pred, target_names=["Не хит (0)", "Хит (1)"]))

    # Визуализация (2x2)
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    fig.suptitle("Анализ модели XGBoost (Предсказание хита)", fontsize=16, fontweight="bold")

    # 1. Матрица ошибок (Confusion Matrix)
    ax = axes[0, 0]
    cm = confusion_matrix(y_test, y_pred)
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax, 
                xticklabels=["Не хит", "Хит"], yticklabels=["Не хит", "Хит"])
    ax.set_title("Матрица ошибок (Confusion Matrix)")
    ax.set_xlabel("Предсказано моделью")
    ax.set_ylabel("Реальность")

    # 2. Важность признаков
    ax = axes[0, 1]
    importances = model.feature_importances_
    imp_df = pd.DataFrame({
        'feature': X_test.columns,
        'importance': importances
    }).sort_values(by='importance', ascending=False)

    sns.barplot(data=imp_df, y='feature', x='importance', palette="viridis", ax=ax)
    ax.set_title("Важность признаков")
    ax.set_xlabel("Влияние на прогноз")
    ax.set_ylabel("")

    # 3. ROC-кривая
    ax = axes[1, 0]
    fpr, tpr, _ = roc_curve(y_test, y_pred_proba)
    ax.plot(fpr, tpr, color="darkorange", lw=2, label=f"ROC-кривая (AUC = {roc_auc:.3f})")
    ax.plot([0, 1], [0, 1], color="navy", lw=2, linestyle="--") # Случайное угадывание
    ax.set_title("ROC-кривая")
    ax.set_xlabel("False Positive Rate (Ложные срабатывания)")
    ax.set_ylabel("True Positive Rate (Найдено хитов)")
    ax.legend(loc="lower right")
    ax.grid(alpha=0.3)

    # 4. Распределение вероятностей
    ax = axes[1, 1]
    sns.histplot(y_pred_proba[y_test == 0], bins=50, color="blue", label="Реальные не-хиты", alpha=0.5, ax=ax)
    sns.histplot(y_pred_proba[y_test == 1], bins=50, color="red", label="Реальные хиты", alpha=0.5, ax=ax)
    ax.set_title("Распределение предсказанных вероятностей")
    ax.set_xlabel("Вероятность стать хитом (0 = нет, 1 = да)")
    ax.set_ylabel("Количество треков")
    ax.legend()

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