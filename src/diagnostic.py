"""Tingkat 2 - Diagnostic Analytics: MENGAPA hal itu terjadi?"""
import matplotlib.pyplot as plt
import pandas as pd

from .config import FIG_DIR, PALET, TAB_DIR, apply_style


def jembatan_laba(fin: pd.DataFrame) -> pd.DataFrame:
    """Dekomposisi selisih laba bersih Tahun 1 -> Tahun 2 (profit bridge)."""
    y = fin.groupby("tahun")[["revenue", "cogs", "opex", "bad_debt", "interest", "tax", "net_profit"]].sum()
    a, b = y.index.tolist()
    d = y.loc[b] - y.loc[a]
    langkah = [
        (f"Laba bersih\n{a}", y.loc[a, "net_profit"], "total"),
        ("Pendapatan", d["revenue"], "delta"),
        ("HPP", -d["cogs"], "delta"),
        ("Biaya\noperasional", -d["opex"], "delta"),
        ("Piutang\nmacet", -d["bad_debt"], "delta"),
        ("Beban\nbunga", -d["interest"], "delta"),
        ("Pajak", -d["tax"], "delta"),
        (f"Laba bersih\n{b}", y.loc[b, "net_profit"], "total"),
    ]
    df = pd.DataFrame(langkah, columns=["komponen", "nilai", "jenis"])
    cek = df.loc[0, "nilai"] + df.loc[1:6, "nilai"].sum()
    # toleransi kecil karena data dibulatkan 3 desimal
    assert abs(cek - df.loc[7, "nilai"]) < 0.1, "Jembatan laba tidak seimbang"
    return df


def grafik_jembatan(df: pd.DataFrame):
    apply_style()
    fig, ax = plt.subplots(figsize=(10, 5))
    berjalan = 0.0
    puncak = 0.0
    for i, r in df.iterrows():
        if r.jenis == "total":
            ax.bar(i, r.nilai, color=PALET["utama"])
            ax.text(i, r.nilai, f"{r.nilai:,.0f}", ha="center", va="bottom", fontsize=9)
            berjalan = r.nilai
            puncak = max(puncak, r.nilai)
        else:
            warna = PALET["baik"] if r.nilai >= 0 else PALET["buruk"]
            ax.bar(i, r.nilai, bottom=berjalan, color=warna)
            ujung = berjalan + r.nilai
            ax.text(i, max(berjalan, ujung), f"{r.nilai:+,.0f}", ha="center", va="bottom", fontsize=9)
            puncak = max(puncak, berjalan, ujung)
            berjalan = ujung
    ax.set_xticks(range(len(df)))
    ax.set_xticklabels(df["komponen"], fontsize=9)
    ax.set_ylabel("Rp juta")
    ax.set_title("Mengapa laba bersih turun? Dekomposisi Tahun 1 -> Tahun 2")
    ax.set_ylim(0, puncak * 1.15)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "02_diagnostik_jembatan_laba.png")
    plt.close(fig)


def rasio_kunci(fin: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for th, g in fin.groupby("tahun"):
        rev = g["revenue"].sum()
        rows.append(
            {
                "Tahun": th,
                "Margin kotor (%)": (1 - g["cogs"].sum() / rev) * 100,
                "Biaya operasional / pendapatan (%)": g["opex"].sum() / rev * 100,
                "Piutang macet / pendapatan (%)": g["bad_debt"].sum() / rev * 100,
                "Beban bunga / pendapatan (%)": g["interest"].sum() / rev * 100,
                "DSO rata-rata (hari)": g["dso"].mean(),
                "Margin bersih (%)": g["net_profit"].sum() / rev * 100,
            }
        )
    return pd.DataFrame(rows).round(2)


def risiko_per_kelompok(inv: pd.DataFrame) -> dict:
    """Tingkat invoice tidak terbayar menurut kelompok (hanya invoice 'Selesai')."""
    h = inv[inv["status"] == "Selesai"].copy()
    h["kelompok_riwayat_telat"] = pd.qcut(
        h["rasio_telat_historis"], 4, labels=["Q1 rendah", "Q2", "Q3", "Q4 tinggi"]
    )
    hasil = {}
    for kolom in ["segmen", "termin_hari", "kelompok_riwayat_telat"]:
        hasil[kolom] = (
            h.groupby(kolom, observed=True)["tidak_terbayar"].mean().mul(100).round(1).rename("tidak_terbayar_%")
        )
    return hasil


def grafik_risiko(hasil: dict):
    apply_style()
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.8), sharey=True)
    judul = {"segmen": "Segmen", "termin_hari": "Termin (hari)", "kelompok_riwayat_telat": "Riwayat telat bayar"}
    for ax, (kol, serie) in zip(axes, hasil.items()):
        ax.bar(serie.index.astype(str), serie.values, color=PALET["waspada"])
        for i, v in enumerate(serie.values):
            ax.text(i, v, f"{v:.1f}", ha="center", va="bottom", fontsize=8)
        ax.set_title(judul[kol])
        ax.tick_params(axis="x", labelsize=8)
    axes[0].set_ylabel("% invoice tidak terbayar")
    fig.suptitle("Siapa sumber piutang macet? (invoice selesai)", fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "03_diagnostik_risiko_piutang.png")
    plt.close(fig)


def run(fin: pd.DataFrame, inv: pd.DataFrame):
    print("\n=== [2] DIAGNOSTIC: Mengapa terjadi? ===")
    jembatan = jembatan_laba(fin)
    jembatan.to_csv(TAB_DIR / "02_jembatan_laba.csv", index=False)
    grafik_jembatan(jembatan)

    rasio = rasio_kunci(fin)
    rasio.to_csv(TAB_DIR / "02_rasio_kunci.csv", index=False)

    risiko = risiko_per_kelompok(inv)
    pd.concat(risiko, axis=0).to_csv(TAB_DIR / "03_risiko_per_kelompok.csv")
    grafik_risiko(risiko)

    penekan = jembatan[(jembatan["jenis"] == "delta") & (jembatan["nilai"] < 0)].sort_values("nilai")
    print("  Penekan laba terbesar (Rp juta):")
    for _, r in penekan.iterrows():
        print(f"    - {r.komponen.replace(chr(10), ' '):<20} {r.nilai:>10,.1f}")
    print("  Rasio kunci:")
    print(rasio.to_string(index=False))
    return jembatan, rasio, risiko
