import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import pearsonr, spearmanr

from database import read
from database import ENGINE as engine


# ==== ЗАГРУЗКА ====
def load_data() -> pd.DataFrame:
    # Читаем агрегированные данные по артистам
    query = read("hyp_experience.sql")
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)

    # Убираем выбросы (например, артисты с 1 треком сильно искажают картину)
    # Оставим только тех, у кого есть хотя бы 3 трека в базе
    df = df[df["total_tracks"] >= 3].copy()
    
    # Ограничиваем опыт адекватными рамками (например, до 70 лет)
    df = df[(df["experience_years"] >= 0) & (df["experience_years"] <= 70)]
    
    return df.dropna(subset=["experience_years", "max_track_pop", "artist_pop"])


# ==== СТАТИСТИКА ====
def test_hypothesis(df: pd.DataFrame) -> dict:
    # Проверяем связь: Опыт (годы) vs Успех (макс. популярность трека)
    x = df["experience_years"].values
    y = df["max_track_pop"].values

    r_p, p_p = pearsonr(x, y)
    r_s, p_s = spearmanr(x, y)

    return {
        "n": len(df),
        "pearson_r": r_p, "pearson_p": p_p,
        "spearman_r": r_s, "spearman_p": p_s,
    }


# ==== ГРАФИКИ ====
def plot_hypothesis(df: pd.DataFrame, stats: dict) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(16, 11))
    fig.suptitle(
        "Гипотеза 3: Влияет ли опыт исполнителя на успех?",
        fontsize=15, fontweight="bold",
    )

    # ---------- 1. Scatter: Опыт (годы) vs Макс. популярность трека ----------
    ax = axes[0, 0]
    sample = df.sample(min(15_000, len(df)), random_state=42)
    
    sns.regplot(
        data=sample, x="experience_years", y="max_track_pop",
        scatter_kws={"s": 10, "alpha": 0.3, "color": "teal"},
        line_kws={"color": "red", "lw": 2}, ax=ax,
    )
    ax.set_title(
        f"1. Опыт (лет) vs Макс. популярность трека "
        f"(Spearman r = {stats['spearman_r']:.3f})"
    )
    ax.set_xlabel("Опыт исполнителя (лет с первого трека)")
    ax.set_ylabel("Популярность трека (0-100)")
    ax.grid(alpha=0.3)

    # ---------- 2. Количество треков vs Популярность артиста ----------
    ax = axes[0, 1]
    # Логарифмическая шкала по X, так как разброс огромен (от 3 до 1000+)
    sns.scatterplot(
        data=sample, x="total_tracks", y="artist_pop",
        alpha=0.3, s=15, color="purple", ax=ax
    )
    ax.set_xscale("log")
    ax.set_title("2. Количество треков (log) vs Популярность артиста")
    ax.set_xlabel("Всего треков (логарифмическая шкала)")
    ax.set_ylabel("Популярность артиста (0-100)")
    ax.grid(alpha=0.3)

    # ---------- 3. Распределение популярности по группам опыта ----------
    ax = axes[1, 0]
    df_bins = df.copy()
    
    # Группируем опыт: 0-5 лет (новички), 6-15 (средние), 15+ (ветераны)
    conditions = [
        (df_bins["experience_years"] <= 5),
        (df_bins["experience_years"] > 5) & (df_bins["experience_years"] <= 15),
        (df_bins["experience_years"] > 15)
    ]
    choices = ["Новички (0-5 лет)", "Средний опыт (6-15 лет)", "Ветераны (15+ лет)"]
    df_bins["exp_group"] = np.select(conditions, choices, default="Unknown")
    
    sns.boxplot(
        data=df_bins, x="exp_group", y="max_track_pop",
        palette="Set2", ax=ax, showfliers=False
    )
    ax.set_title("3. Популярность треков в зависимости от стажа")
    ax.set_xlabel("Группа опыта")
    ax.set_ylabel("Макс. популярность трека")
    ax.grid(alpha=0.3, axis="y")

    # ---------- 4. Подписчики vs Популярность артиста ----------
    ax = axes[1, 1]
    sns.regplot(
        data=sample, x="followers", y="artist_pop",
        scatter_kws={"s": 10, "alpha": 0.2, "color": "orange"},
        line_kws={"color": "red", "lw": 2}, ax=ax,
    )
    ax.set_xscale("log") # Логарифмируем подписчиков, чтобы уместить на графике
    ax.set_title("4. Подписчики (log) vs Популярность артиста")
    ax.set_xlabel("Количество подписчиков (log)")
    ax.set_ylabel("Популярность артиста (0-100)")
    ax.grid(alpha=0.3)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.show()


# ==== MAIN ====
if __name__ == "__main__":
    df = load_data()
    stats = test_hypothesis(df)

    print(f"Артистов в выборке (>= 3 треков): {stats['n']:,}")
    print(f"Spearman r (Опыт vs Успех) = {stats['spearman_r']:.4f} (p = {stats['spearman_p']:.2e})")

    if stats["spearman_p"] < 0.05:
        print("→ Связь статистически значима.")
        if stats["spearman_r"] > 0:
            print("   Опыт ПОЛОЖИТЕЛЬНО влияет на успех (чем больше стаж, тем выше популярность).")
        else:
            print("   Опыт ОТРИЦАТЕЛЬНО влияет на успех (новички популярнее ветеранов).")
    else:
        print("→ Статистически значимой связи не обнаружено.")

    plot_hypothesis(df, stats)