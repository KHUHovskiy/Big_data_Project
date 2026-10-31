import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from scipy.stats import pearsonr, spearmanr

from database import read
from database import ENGINE as engine


# ==== ЗАГРУЗКА ====
def load_data() -> pd.DataFrame:
    query = read("hyp_loudness.sql", subdir='')
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)

    # Приводим типы и считаем «возраст» трека
    df["release_year"] = df["release_year"].astype(int)
    df["loudness"] = df["loudness"].astype(float)
    df["age_years"] = pd.Timestamp.now().year - df["release_year"]

    # Убираем выбросы: громкость ниже -40 дБ — почти наверняка битые данные
    df = df[(df["loudness"] > -40) & (df["loudness"] < 5)]
    return df.dropna(subset=["loudness", "age_years"])


# ==== СТАТИСТИКА ====
def test_hypothesis(df: pd.DataFrame) -> dict:
    """Проверяет гипотезу: age_years vs loudness."""
    x = df["age_years"].values
    y = df["loudness"].values

    # Пирсон: линейная связь
    r_p, p_p = pearsonr(x, y)
    # Спирмен: монотонная связь (устойчив к выбросам и нелинейности)
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
        "Гипотеза: чем ближе дата выхода к сегодняшнему дню, тем выше громкость",
        fontsize=15, fontweight="bold",
    )

    # ---------- 1. Scatter: возраст vs громкость + регрессия ----------
    ax = axes[0, 0]
    # Подвыборка для читаемости (107M строк на scatter — тяжело)
    sample = df.sample(min(20_000, len(df)), random_state=42)
    ax.scatter(sample["age_years"], sample["loudness"],
               s=6, alpha=0.25, color="steelblue", zorder=2)
    sns.regplot(
        data=sample, x="age_years", y="loudness",
        scatter=False, color="red", ax=ax, line_kws={"lw": 2},
    )
    ax.set_title(
        f"1. Возраст трека vs громкость "
        f"(Pearson r = {stats['pearson_r']:.3f}, p = {stats['pearson_p']:.1e})"
    )
    ax.set_xlabel("Возраст трека (лет, 0 = текущий год)")
    ax.set_ylabel("Громкость (dB)")
    ax.grid(alpha=0.3)

    # ---------- 2. Средняя громкость по годам ----------
    ax = axes[0, 1]
    by_year = (
        df.groupby("release_year")["loudness"]
        .agg(["mean", "median", "count"])
        .reset_index()
    )
    by_year = by_year[by_year["count"] >= 50]  # годы с малым числом треков не рисуем

    ax.plot(by_year["release_year"], by_year["mean"],
            color="darkred", lw=1.8, label="Средняя")
    ax.plot(by_year["release_year"], by_year["median"],
            color="navy", lw=1.5, ls="--", label="Медиана")
    ax.fill_between(by_year["release_year"],
                    by_year["mean"] - 1, by_year["mean"] + 1,
                    color="red", alpha=0.1)
    ax.set_title("2. Средняя и медианная громкость по годам выпуска")
    ax.set_xlabel("Год выпуска")
    ax.set_ylabel("Громкость (dB)")
    ax.legend()
    ax.grid(alpha=0.3)

    # ---------- 3. Распределение громкости по десятилетиям ----------
    ax = axes[1, 0]
    df_decade = df.copy()
    df_decade["decade"] = (df_decade["release_year"] // 10) * 10
    df_decade = df_decade[df_decade["decade"] >= 1950]  # отсекаем шум

    sns.violinplot(
        data=df_decade, x="decade", y="loudness",
        palette="viridis", ax=ax, cut=0,
    )
    ax.set_title("3. Распределение громкости по десятилетиям")
    ax.set_xlabel("Десятилетие")
    ax.set_ylabel("Громкость (dB)")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(alpha=0.3, axis="y")

    # ---------- 4. Корреляция по десятилетиям (Спирмен) ----------
    ax = axes[1, 1]
    rows = []
    for decade, sub in df_decade.groupby("decade"):
        if len(sub) < 100:
            continue
        r, p = spearmanr(sub["age_years"], sub["loudness"])
        rows.append({"decade": int(decade), "n": len(sub),
                     "spearman_r": r, "p": p})
    corr_df = pd.DataFrame(rows)

    colors = ["tab:red" if c > 0 else "tab:blue" for c in corr_df["spearman_r"]]
    ax.bar(corr_df["decade"].astype(str), corr_df["spearman_r"],
           color=colors, edgecolor="black")
    ax.axhline(0, color="black", lw=0.8)
    for i, row in corr_df.iterrows():
        ax.text(i, row["spearman_r"], f"{row['spearman_r']:.3f}",
                ha="center",
                va="bottom" if row["spearman_r"] >= 0 else "top",
                fontsize=9)
    ax.set_title("4. Корреляция (Спирмен) возраста и громкости внутри каждого десятилетия")
    ax.set_xlabel("Десятилетие")
    ax.set_ylabel("Spearman r")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(alpha=0.3, axis="y")

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.show()



if __name__ == "__main__":
    df = load_data()
    stats = test_hypothesis(df)

    print(f"N = {stats['n']:,}")
    print(f"Pearson  r = {stats['pearson_r']:.4f} (p = {stats['pearson_p']:.2e})")
    print(f"Spearman r = {stats['spearman_r']:.4f} (p = {stats['spearman_p']:.2e})")

    if stats["spearman_p"] < 0.05:
        if stats["spearman_r"] < 0:
            print("→ Гипотеза ПОДТВЕРЖДАЕТСЯ: чем моложе трек, тем выше громкость.")
        else:
            print("→ Гипотеза ОПРОВЕРГНУТА: чем старше трек, тем выше громкость.")
    else:
        print("→ Связь статистически незначима (p ≥ 0.05).")

    plot_hypothesis(df, stats)