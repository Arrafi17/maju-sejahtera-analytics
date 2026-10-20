from src import descriptive, diagnostic, predictive, prescriptive
from src.config import (
    DATA_DIR,
    OUT_DIR,
    TARGET_CASHFLOW_CHANGE,
    TARGET_DEBT_CHANGE,
    TARGET_NET_PROFIT_CHANGE,
    ensure_dirs,
    fmt,
)
from src.data_generator import generate_customers, generate_financials, generate_invoices


def validasi_skenario(fin):
    y = fin.groupby("tahun").agg(rev=("revenue", "sum"), np_=("net_profit", "sum"), cf=("cash_flow", "sum"), debt=("debt", "last"))
    a, b = y.index
    cek = {
        "Pendapatan naik": y.loc[b, "rev"] > y.loc[a, "rev"],
        "Laba bersih turun 11%": abs((y.loc[b, "np_"] / y.loc[a, "np_"] - 1) - TARGET_NET_PROFIT_CHANGE) < 1e-3,
        "Utang naik 300%": abs((y.loc[b, "debt"] / y.loc[a, "debt"] - 1) - TARGET_DEBT_CHANGE) < 1e-3,
        "Arus kas turun Rp 1 juta": abs((y.loc[b, "cf"] - y.loc[a, "cf"]) - TARGET_CASHFLOW_CHANGE) < 1e-2,
    }
    print("=== Validasi skenario (sesuai materi) ===")
    for nama, ok in cek.items():
        print(f"  [{'OK' if ok else 'GAGAL'}] {nama}")
    assert all(cek.values()), "Data sintetis tidak sesuai skenario"


def tulis_laporan(fin, ringkasan, jembatan, rasio, penting, metrik, model, ringkas_rek, agg):
    r = ringkasan.set_index(ringkasan.columns[0])
    pct = lambda nama: r.loc[nama, "Perubahan (%)"]
    penekan = jembatan[(jembatan["jenis"] == "delta") & (jembatan["nilai"] < 0)].sort_values("nilai")
    top_penekan = ", ".join(f"{k.replace(chr(10), ' ')} ({v:,.0f})" for k, v in zip(penekan["komponen"], penekan["nilai"]))
    auc = metrik.set_index("Model").loc[model, "ROC-AUC"]
    faktor = ", ".join(penting.sort_values(ascending=False).index[:3])
    md = f"""# Laporan Keputusan - PT. Maju Sejahtera

 {pct('Pendapatan (revenue)'):+.1f}%, laba bersih {pct('Laba bersih (net profit)'):+.1f}%,
 {pct('Utang (akhir tahun)'):+.0f}%, arus kas {pct('Arus kas bersih (cash flow)'):+.1f}%.
 {top_penekan}.
 {rasio.loc[0, 'Margin kotor (%)']:.1f}% ke {rasio.loc[1, 'Margin kotor (%)']:.1f}%,
 {rasio.loc[0, 'DSO rata-rata (hari)']:.0f} ke {rasio.loc[1, 'DSO rata-rata (hari)']:.0f} hari.
 {model} (ROC-AUC {auc:.2f}). Faktor risiko utama: {faktor}.

{ringkas_rek.to_markdown()}

{fmt(agg['manfaat_bersih_juta'].sum(), 1)}
"""
    (OUT_DIR / "laporan_keputusan.md").write_text(md, encoding="utf-8")
    print(f"\nLaporan ringkas ditulis ke {OUT_DIR / 'laporan_keputusan.md'}")


def main():
    ensure_dirs()
    fin = generate_financials()
    pelanggan = generate_customers()
    inv = generate_invoices(pelanggan)

    fin.to_csv(DATA_DIR / "keuangan_bulanan.csv", index=False)
    pelanggan.drop(columns="_laten").to_csv(DATA_DIR / "pelanggan.csv", index=False)
    inv.to_csv(DATA_DIR / "invoice.csv", index=False)
    validasi_skenario(fin)

    ringkasan = descriptive.run(fin)
    jembatan, rasio, _ = diagnostic.run(fin, inv)
    terbuka, metrik, penting, model = predictive.run(inv)
    gm = 1 - fin[fin["tahun"] == 2025]["cogs"].sum() / fin[fin["tahun"] == 2025]["revenue"].sum()
    agg, ringkas_rek = prescriptive.run(terbuka, pelanggan.drop(columns="_laten"), gm)

    tulis_laporan(fin, ringkasan, jembatan, rasio, penting, metrik, model, ringkas_rek, agg)
    print("\nSelesai. Lihat folder 'outputs/'.")


if __name__ == "__main__":
    main()
