"""Tingkat 4 - Prescriptive Analytics: APA yang harus dilakukan?

Mengubah probabilitas gagal bayar menjadi rekomendasi tindakan per pelanggan.
"""
import matplotlib.pyplot as plt
import pandas as pd

from .config import BATAS_SEDANG, BATAS_TINGGI, EFEK_KEBIJAKAN, FIG_DIR, PALET, TAB_DIR, apply_style

TINDAKAN = {
    "BATASI": "Batasi pembelian: wajib bayar di muka (DP 50%), tanpa kredit baru",
    "WASPADA": "Turunkan limit kredit 30% dan pendekkan termin maksimal 30 hari",
    "AMAN": "Pertahankan kebijakan kredit saat ini",
}


def kategori(p: float) -> str:
    if p >= BATAS_TINGGI:
        return "BATASI"
    if p >= BATAS_SEDANG:
        return "WASPADA"
    return "AMAN"


def run(terbuka: pd.DataFrame, pelanggan: pd.DataFrame, margin_kotor: float) -> pd.DataFrame:
    print("\n=== [4] PRESCRIPTIVE: Apa yang harus dilakukan? ===")
    t = terbuka.assign(rugi_diharapkan=terbuka["jumlah_juta"] * terbuka["prob_tidak_bayar"])
    agg = (
        t.groupby("id_pelanggan")
        .agg(jumlah_invoice=("id_invoice", "count"), eksposur_juta=("jumlah_juta", "sum"), rugi_diharapkan_juta=("rugi_diharapkan", "sum"))
        .reset_index()
    )
    agg["prob_rata2"] = agg["rugi_diharapkan_juta"] / agg["eksposur_juta"]
    agg["rekomendasi"] = agg["prob_rata2"].map(kategori)
    agg["tindakan"] = agg["rekomendasi"].map(TINDAKAN)

    efek = agg["rekomendasi"].map(EFEK_KEBIJAKAN)
    agg["rugi_dihindari_juta"] = agg["rugi_diharapkan_juta"] * efek.map(lambda e: e["kurangi_rugi"])
    agg["margin_hilang_juta"] = agg["eksposur_juta"] * efek.map(lambda e: e["kehilangan_penjualan"]) * margin_kotor
    agg["manfaat_bersih_juta"] = agg["rugi_dihindari_juta"] - agg["margin_hilang_juta"]

    agg = agg.merge(pelanggan[["id_pelanggan", "segmen", "wilayah", "limit_kredit_juta"]], on="id_pelanggan", how="left")
    agg = agg.sort_values("rugi_diharapkan_juta", ascending=False).round(3)
    agg.to_csv(TAB_DIR / "06_rekomendasi_pelanggan.csv", index=False)

    ringkas = (
        agg.groupby("rekomendasi")
        .agg(pelanggan=("id_pelanggan", "count"), eksposur=("eksposur_juta", "sum"), rugi=("rugi_diharapkan_juta", "sum"), manfaat=("manfaat_bersih_juta", "sum"))
        .round(1)
    )
    ringkas.to_csv(TAB_DIR / "06_ringkasan_rekomendasi.csv")
    print(ringkas.to_string())
    print(f"  Estimasi manfaat bersih kebijakan: Rp {agg['manfaat_bersih_juta'].sum():,.1f} juta")

    apply_style()
    top = agg.head(10).iloc[::-1]
    warna = {"BATASI": PALET["buruk"], "WASPADA": PALET["waspada"], "AMAN": PALET["baik"]}
    fig, ax = plt.subplots(figsize=(9, 4.6))
    ax.barh(top["id_pelanggan"] + " (" + top["segmen"] + ")", top["rugi_diharapkan_juta"], color=top["rekomendasi"].map(warna))
    ax.set(xlabel="Kerugian diharapkan (Rp juta)", title="10 pelanggan dengan potensi rugi terbesar")
    from matplotlib.patches import Patch

    ax.legend(handles=[Patch(color=c, label=k) for k, c in warna.items()], loc="lower right")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "05_preskriptif_top_pelanggan.png")
    plt.close(fig)
    return agg, ringkas
