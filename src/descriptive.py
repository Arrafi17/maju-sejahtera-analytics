"""Tingkat 1 - Descriptive Analytics: APA yang terjadi?"""
import matplotlib.pyplot as plt
import pandas as pd

from .config import FIG_DIR, PALET, TAB_DIR, apply_style, fmt


def ringkasan_tahunan(fin: pd.DataFrame) -> pd.DataFrame:
    g = fin.groupby("tahun").agg(
        pendapatan=("revenue", "sum"),
        laba_bersih=("net_profit", "sum"),
        arus_kas=("cash_flow", "sum"),
        utang=("debt", "last"),
    )
    t1, t2 = g.index.tolist()
    label = {
        "pendapatan": "Pendapatan (revenue)",
        "laba_bersih": "Laba bersih (net profit)",
        "utang": "Utang (akhir tahun)",
        "arus_kas": "Arus kas bersih (cash flow)",
    }
    baris = []
    for kol, nama in label.items():
        a, b = g.loc[t1, kol], g.loc[t2, kol]
        baris.append(
            {
                "Metrik (Rp juta)": nama,
                f"Tahun {t1}": a,
                f"Tahun {t2}": b,
                "Selisih": b - a,
                "Perubahan (%)": (b - a) / abs(a) * 100,
            }
        )
    return pd.DataFrame(baris).round(2)


def grafik_tren(fin: pd.DataFrame):
    apply_style()
    fig, axes = plt.subplots(2, 2, figsize=(11, 6.5))
    panel = [
        ("revenue", "Pendapatan bulanan", PALET["utama"]),
        ("net_profit", "Laba bersih bulanan", PALET["baik"]),
        ("debt", "Saldo utang", PALET["buruk"]),
        ("cash_flow", "Arus kas bersih bulanan", PALET["waspada"]),
    ]
    x = range(len(fin))
    for ax, (kol, judul, warna) in zip(axes.ravel(), panel):
        ax.plot(x, fin[kol], color=warna, lw=2)
        ax.axvline(11.5, color="#999999", ls="--", lw=1)
        ax.set_title(judul)
        ax.set_xticks([0, 6, 12, 18, 23])
        ax.set_xticklabels([fin["periode"][i] for i in (0, 6, 12, 18, 23)], fontsize=8)
        ax.set_ylabel("Rp juta")
    fig.suptitle("PT. Maju Sejahtera - Gambaran Deskriptif 2024-2025", fontweight="bold")
    fig.tight_layout()
    path = FIG_DIR / "01_deskriptif_tren.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def run(fin: pd.DataFrame) -> pd.DataFrame:
    tabel = ringkasan_tahunan(fin)
    tabel.to_csv(TAB_DIR / "01_ringkasan_tahunan.csv", index=False)
    grafik_tren(fin)
    print("\n=== [1] DESCRIPTIVE: Apa yang terjadi? ===")
    for _, r in tabel.iterrows():
        print(f"  {r.iloc[0]:<30} {fmt(r.iloc[1], 1):>12} -> {fmt(r.iloc[2], 1):>12}  ({r['Perubahan (%)']:+.1f}%)")
    return tabel
