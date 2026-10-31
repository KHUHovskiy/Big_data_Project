import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from scipy.stats import pearsonr, spearmanr

from database import read
from database import ENGINE as engine


# ==== ЗАГРУЗКА ====
def load_data() -> pd.DataFrame:
    query = read("hyp_energy_tempo.sql")
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)

    # Приводим типы
    df["tempo"] = df["tempo"].astype(float)
    df["energy"] = df["energy"].astype(float)

    # Убираем физические выбросы темпа (обычно от 40 до 220 BPM)
    df = df[(df["tempo"] >= 40) & (df["tempo"] <= 220)]
    # Энергия по шкале Spotify всегда от 0.0 до 1.0
    df = df[(df["energy"] >= 0) & (df["energy"] <= 1)]

    return df.dropna(subset=["tempo", "energy"])


# ==== СТАТИСТИКА ====
def test_hypothesis(df: pd.DataFrame) -> dict:
    x = df["tempo"].values
    y = df["energy"].values

    # Пирсон: линейная связь
    r_p, p_p = pearsonr(x, y)
    # Спирмен: монотонная связь (устойчив к выбросам)
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
        "Гипотеза: Темп (tempo) и Энергия (energy) трека коррелируют",
        fontsize=15, fontweight="bold",
    )

    # ---------- 1. Scatter: Tempo vs Energy + линия регрессии ----------
    ax = axes[0, 0]
    # Подвыборка для читаемости (если строк миллионы)
    sample = df.sample(min(20_000, len(df)), random_state=42)
    
    ax.scatter(
        sample["tempo"], sample["energy"],
        s=6, alpha=0.2, color="steelblue", zorder=2
    )
    sns.regplot(
        data=sample, x="tempo", y="energy",
        scatter=False, color="red", ax=ax, line_kws={"lw": 2},
    )
    ax.set_title(
        f"1. Темп vs Энергия "
        f"(Pearson r = {stats['pearson_r']:.3f}, p = {stats['pearson_p']:.1e})"
    )
    ax.set_xlabel("Темп (BPM)")
    ax.set_ylabel("Энергия (0..1)")
    ax.grid(alpha=0.3)

    # ---------- 2. 2D-гистограмма (Hexbin) ----------
    ax = axes[0, 1]
    hb = ax.hexbin(
        df["tempo"], df["energy"], 
        gridsize=50, cmap="YlOrRd", mincnt=1
    )
    fig.colorbar(hb, ax=ax, label="Количество треков")
    ax.set_title("2. Плотность распределения треков")
    ax.set_xlabel("Темп (BPM)")
    ax.set_ylabel("Энергия (0..1)")

    # ---------- 3. Распределение темпа (KDE) ----------
    ax = axes[1, 0]
    sns.kdeplot(data=df, x="tempo", fill=True, color="teal", ax=ax)
    ax.axvline(df["tempo"].median(), color="red", ls="--", 
               label=f"Медиана: {df['tempo'].median():.1f} BPM")
    ax.set_title("3. Распределение темпа (BPM)")
    ax.set_xlabel("Темп (BPM)")
    ax.set_ylabel("Плотность")
    ax.legend()
    ax.grid(alpha=0.3)

    # ---------- 4. Средняя энергия по группам BPM ----------
    ax = axes[1, 1]
    # Разбиваем темп на корзины по 20 BPM
    df_bins = df.copy()
    df_bins["tempo_bin"] = (df_bins["tempo"] // 20) * 20
    # Оставляем только те корзины, где достаточно данных
    counts = df_bins["tempo_bin"].value_counts()
    valid_bins = counts[counts >= 100].index
    df_bins = df_bins[df_bins["tempo_bin"].isin(valid_bins)]

    sns.barplot(
        data=df_bins, x="tempo_bin", y="energy",
        errorbar="ci", palette="crest", ax=ax, edgecolor="black"
    )
    ax.set_title("4. Средняя энергия по диапазонам BPM (с 95% доверительным интервалом)")
    ax.set_xlabel("Темп (BPM)")
    ax.set_ylabel("Средняя энергия")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(alpha=0.3, axis="y")

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.show()


# ==== MAIN ====
if __name__ == "__main__":
    df = load_data()
    stats = test_hypothesis(df)

    print(f"N = {stats['n']:,}")
    print(f"Pearson  r = {stats['pearson_r']:.4f} (p = {stats['pearson_p']:.2e})")
    print(f"Spearman r = {stats['spearman_r']:.4f} (p = {stats['spearman_p']:.2e})")

    # Интерпретация
    r = stats['pearson_r']
    if stats["pearson_p"] < 0.05:
        if r > 0:
            print("→ Гипотеза ПОДТВЕРЖДАЕТСЯ: связь есть, она прямая (чем выше темп, тем выше энергия).")
        else:
            print("→ Гипотеза ПОДТВЕРЖДАЕТСЯ: связь есть, но она обратная (чем выше темп, тем НИЖЕ энергия).")
        
        # Оценка силы связи (по шкале Чеддока)
        abs_r = abs(r)
        if abs_r < 0.3:
            print("   Сила связи: слабая.")
        elif abs_r < 0.5:
            print("   Сила связи: умеренная.")
        elif abs_r < 0.7:
            print("   Сила связи: заметная.")
        else:
            print("   Сила связи: высокая.")
    else:
        print("→ Связь статистически незначима (p >= 0.05). Гипотеза не подтверждается.")

    plot_hypothesis(df, stats)