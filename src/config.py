"""Konfigurasi, parameter skenario, dan gaya grafik."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # aman dijalankan tanpa layar
import matplotlib.pyplot as plt

SEED = 42

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "outputs"
FIG_DIR = OUT_DIR / "figures"
TAB_DIR = OUT_DIR / "tables"

# --- Fakta skenario dari materi (target kalibrasi data sintetis) ---
TAX_RATE = 0.22                    # tarif PPh badan
TARGET_NET_PROFIT_CHANGE = -0.11   # laba bersih turun 11%
TARGET_DEBT_CHANGE = 3.00          # utang naik 300%
TARGET_CASHFLOW_CHANGE = -1.0      # arus kas berkurang Rp 1 juta

# --- Ambang kebijakan preskriptif (probabilitas gagal bayar) ---
BATAS_TINGGI = 0.30
BATAS_SEDANG = 0.15

# Asumsi dampak kebijakan (dapat diubah untuk analisis what-if)
EFEK_KEBIJAKAN = {
    "BATASI": {"kurangi_rugi": 0.70, "kehilangan_penjualan": 0.25},
    "WASPADA": {"kurangi_rugi": 0.35, "kehilangan_penjualan": 0.10},
    "AMAN": {"kurangi_rugi": 0.0, "kehilangan_penjualan": 0.0},
}

PALET = {
    "utama": "#1F4E79",
    "baik": "#2A9D8F",
    "buruk": "#D1495B",
    "waspada": "#E9A23B",
    "netral": "#8D99ae".upper(),
    "teks": "#2B2D42",
}


def ensure_dirs():
    for d in (DATA_DIR, FIG_DIR, TAB_DIR):
        d.mkdir(parents=True, exist_ok=True)


def apply_style():
    plt.rcParams.update(
        {
            "figure.dpi": 130,
            "savefig.dpi": 130,
            "savefig.bbox": "tight",
            "font.size": 10,
            "axes.titlesize": 11,
            "axes.titleweight": "bold",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "axes.edgecolor": "#555555",
            "text.color": PALET["teks"],
            "axes.labelcolor": PALET["teks"],
        }
    )


def fmt(x, desimal=0):
    """Format angka gaya Indonesia: 1.234,5"""
    s = f"{x:,.{desimal}f}"
    return s.replace(",", "_").replace(".", ",").replace("_", ".")
