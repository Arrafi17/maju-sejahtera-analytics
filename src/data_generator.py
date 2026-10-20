"""Pembangkit data sintetis PT. Maju Sejahtera.

Semua angka SIMULASI (satuan: Rp juta) yang dikalibrasi agar sesuai dengan
fakta pada materi: pendapatan naik, laba bersih turun 11%, utang naik 300%,
dan arus kas berkurang Rp 1 juta antara Tahun 1 dan Tahun 2.
"""
import numpy as np
import pandas as pd

from .config import (
    SEED,
    TARGET_CASHFLOW_CHANGE,
    TARGET_NET_PROFIT_CHANGE,
    TAX_RATE,
)


def generate_financials(seed: int = SEED) -> pd.DataFrame:
    """Laporan keuangan bulanan selama 24 bulan (2024-2025)."""
    rng = np.random.default_rng(seed)
    t = np.arange(24)

    revenue = (
        1000 * (1.012**t) * (1 + 0.05 * np.sin(2 * np.pi * t / 12)) * rng.normal(1, 0.015, 24)
    )
    cogs = revenue * (np.linspace(0.70, 0.76, 24) + rng.normal(0, 0.003, 24))
    opex = 120 + 1.2 * t + rng.normal(0, 3, 24)

    # Utang: akhir Tahun 1 = 600, akhir Tahun 2 = 2.400 (naik 300%)
    debt = np.concatenate([np.linspace(520, 600, 12), np.linspace(600, 2400, 13)[1:]])
    interest = debt * 0.010  # bunga 1% per bulan

    # Piutang makin lama tertagih -> DSO naik -> piutang macet naik
    dso = np.linspace(35, 55, 24)
    piutang = revenue / 30 * dso
    bad_debt = revenue * (0.002 + 0.0006 * (dso - 35))

    def laba(opex_arr):
        pbt = revenue - cogs - opex_arr - bad_debt - interest
        tax = TAX_RATE * np.maximum(pbt, 0)
        return pbt, tax, pbt - tax

    # Kalibrasi biaya operasional Tahun 2 agar laba bersih turun tepat 11%
    _, _, net0 = laba(opex)
    np1 = net0[:12].sum()
    pbt_sekarang = laba(opex)[0][12:].sum()
    pbt_target = (1 + TARGET_NET_PROFIT_CHANGE) * np1 / (1 - TAX_RATE)
    k = 1 + (pbt_sekarang - pbt_target) / opex[12:].sum()
    opex = opex.copy()
    opex[12:] *= k
    pbt, tax, net = laba(opex)

    # Arus kas bersih = laba - kenaikan piutang + tambahan utang - investasi
    d_piutang = np.diff(piutang, prepend=piutang[0])
    d_debt = np.diff(debt, prepend=500.0)
    invest = np.full(24, 60.0)
    cf_pra = net - d_piutang + d_debt
    cf1 = (cf_pra[:12] - invest[:12]).sum()
    target_cf2 = cf1 + TARGET_CASHFLOW_CHANGE
    invest[12:] = (cf_pra[12:].sum() - target_cf2) / 12  # plug investasi Tahun 2
    cash_flow = cf_pra - invest

    return pd.DataFrame(
        {
            "periode": pd.period_range("2024-01", periods=24, freq="M").astype(str),
            "tahun": np.repeat([2024, 2025], 12),
            "revenue": revenue,
            "cogs": cogs,
            "opex": opex,
            "bad_debt": bad_debt,
            "interest": interest,
            "pbt": pbt,
            "tax": tax,
            "net_profit": net,
            "piutang": piutang,
            "dso": dso,
            "debt": debt,
            "investasi": invest,
            "cash_flow": cash_flow,
        }
    ).round(3)


AMOUNT_MEAN = {"Retail": 8, "Grosir": 30, "Korporat": 90}
LIMIT_RANGE = {"Retail": (50, 150), "Grosir": (150, 400), "Korporat": (400, 1000)}


def generate_customers(n: int = 60, seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed + 1)
    segmen = rng.choice(["Retail", "Grosir", "Korporat"], n, p=[0.45, 0.35, 0.20])
    limit = [rng.integers(*LIMIT_RANGE[s]) for s in segmen]
    return pd.DataFrame(
        {
            "id_pelanggan": [f"C{i + 1:03d}" for i in range(n)],
            "segmen": segmen,
            "wilayah": rng.choice(
                ["Sumatra", "Jawa", "Kalimantan", "Sulawesi"], n, p=[0.30, 0.35, 0.20, 0.15]
            ),
            "lama_langganan_bln": rng.integers(3, 96, n),
            "limit_kredit_juta": limit,
            "_laten": rng.beta(2, 6, n),  # kecenderungan telat bayar (tak teramati)
        }
    )


def generate_invoices(customers: pd.DataFrame, n: int = 2200, seed: int = SEED) -> pd.DataFrame:
    """Invoice 2024-2025. Invoice >= 1 Nov 2025 berstatus 'Berjalan' (hasil belum diketahui)."""
    rng = np.random.default_rng(seed + 2)
    idx = rng.integers(0, len(customers), n)
    c = customers.iloc[idx].reset_index(drop=True)

    start = pd.Timestamp("2024-01-01")
    hari = np.sort(rng.integers(0, 730, n))
    tanggal = start + pd.to_timedelta(hari, unit="D")
    progres = hari / 730

    rasio_telat = np.clip(c["_laten"] + 0.10 * progres + rng.normal(0, 0.04, n), 0, 1)
    utilisasi = np.clip(rng.beta(2, 4, n) + 0.15 * progres, 0, 1.2)
    rata2 = c["segmen"].map(AMOUNT_MEAN).to_numpy()
    jumlah = rata2 * rng.lognormal(0, 0.5, n)
    termin = rng.choice([14, 30, 45, 60], n, p=[0.15, 0.45, 0.25, 0.15])

    logit = (
        -3.9
        + 4.5 * rasio_telat
        + 1.6 * utilisasi
        + 0.025 * (termin - 30)
        + 0.3 * np.log(jumlah / rata2)
        + 0.5 * (c["segmen"] == "Retail").to_numpy()
        - 0.4 * (c["segmen"] == "Korporat").to_numpy()
        - 0.004 * c["lama_langganan_bln"].to_numpy()
    )
    p = 1 / (1 + np.exp(-logit))
    gagal = (rng.random(n) < p).astype(float)

    status = np.where(tanggal >= pd.Timestamp("2025-11-01"), "Berjalan", "Selesai")
    gagal = np.where(status == "Berjalan", np.nan, gagal)

    return pd.DataFrame(
        {
            "id_invoice": [f"INV-{i + 1:05d}" for i in range(n)],
            "tanggal": tanggal,
            "id_pelanggan": c["id_pelanggan"],
            "segmen": c["segmen"],
            "wilayah": c["wilayah"],
            "lama_langganan_bln": c["lama_langganan_bln"],
            "jumlah_juta": jumlah.round(2),
            "termin_hari": termin,
            "rasio_telat_historis": rasio_telat.round(3),
            "utilisasi_limit": utilisasi.round(3),
            "status": status,
            "tidak_terbayar": gagal,
        }
    )
