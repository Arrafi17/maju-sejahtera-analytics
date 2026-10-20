"""Tingkat 3 - Predictive Analytics: APA yang akan terjadi?

Memprediksi invoice mana yang berpotensi tidak terbayar.
"""
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, confusion_matrix, roc_auc_score, roc_curve
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import FIG_DIR, PALET, SEED, TAB_DIR, apply_style

NUMERIK = ["lama_langganan_bln", "jumlah_juta", "termin_hari", "rasio_telat_historis", "utilisasi_limit"]
KATEGORI = ["segmen", "wilayah"]
FITUR = NUMERIK + KATEGORI
AMBANG = 0.30  # ambang klasifikasi "berisiko" (lebih rendah dari 0,5 karena kelas minoritas)

NAMA_FITUR = {
    "lama_langganan_bln": "Lama berlangganan",
    "jumlah_juta": "Nilai invoice",
    "termin_hari": "Termin pembayaran",
    "rasio_telat_historis": "Riwayat telat bayar",
    "utilisasi_limit": "Pemakaian limit kredit",
    "segmen": "Segmen pelanggan",
    "wilayah": "Wilayah",
}


def _pipeline(model, skala: bool):
    pre = ColumnTransformer(
        [
            ("num", StandardScaler() if skala else "passthrough", NUMERIK),
            ("cat", OneHotEncoder(handle_unknown="ignore"), KATEGORI),
        ]
    )
    return Pipeline([("pre", pre), ("model", model)])


def run(inv: pd.DataFrame):
    print("\n=== [3] PREDICTIVE: Apa yang akan terjadi? ===")
    hist = inv[inv["status"] == "Selesai"]
    terbuka = inv[inv["status"] == "Berjalan"].copy()

    X, y = hist[FITUR], hist["tidak_terbayar"].astype(int)
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, stratify=y, random_state=SEED)

    kandidat = {
        "Regresi Logistik": _pipeline(LogisticRegression(max_iter=1000), skala=True),
        "Random Forest": _pipeline(
            RandomForestClassifier(n_estimators=300, min_samples_leaf=5, random_state=SEED), skala=False
        ),
    }

    metrik, kurva = [], {}
    for nama, pipe in kandidat.items():
        pipe.fit(X_tr, y_tr)
        p = pipe.predict_proba(X_te)[:, 1]
        fpr, tpr, _ = roc_curve(y_te, p)
        kurva[nama] = (fpr, tpr)
        tn, fp, fn, tp = confusion_matrix(y_te, p >= AMBANG).ravel()
        metrik.append(
            {
                "Model": nama,
                "ROC-AUC": roc_auc_score(y_te, p),
                "Avg Precision": average_precision_score(y_te, p),
                "Precision": tp / (tp + fp) if tp + fp else 0.0,
                "Recall": tp / (tp + fn) if tp + fn else 0.0,
            }
        )
    metrik = pd.DataFrame(metrik).round(3)
    metrik.to_csv(TAB_DIR / "04_evaluasi_model.csv", index=False)
    terbaik = metrik.sort_values("ROC-AUC", ascending=False).iloc[0]["Model"]
    model = kandidat[terbaik]
    print(metrik.to_string(index=False))
    print(f"  Model terpilih: {terbaik} (ambang risiko = {AMBANG:.2f})")

    # Fitur paling berpengaruh (permutation importance pada data uji)
    pi = permutation_importance(model, X_te, y_te, scoring="roc_auc", n_repeats=15, random_state=SEED)
    penting = (
        pd.Series(pi.importances_mean, index=FITUR).rename(index=NAMA_FITUR).sort_values().rename("penurunan_AUC")
    )
    penting.round(4).to_csv(TAB_DIR / "04_pengaruh_fitur.csv")

    apply_style()
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))
    for nama, (fpr, tpr) in kurva.items():
        auc = metrik.set_index("Model").loc[nama, "ROC-AUC"]
        a1.plot(fpr, tpr, lw=2, label=f"{nama} (AUC {auc:.2f})")
    a1.plot([0, 1], [0, 1], "--", color="#999999")
    a1.set(xlabel="False positive rate", ylabel="True positive rate", title="Kurva ROC")
    a1.legend(loc="lower right")
    a2.barh(penting.index, penting.values, color=PALET["utama"])
    a2.set(xlabel="Penurunan AUC jika fitur diacak", title=f"Faktor risiko ({terbaik})")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "04_prediktif_model.png")
    plt.close(fig)

    # Prediksi untuk invoice yang masih berjalan
    terbuka["prob_tidak_bayar"] = model.predict_proba(terbuka[FITUR])[:, 1].round(4)
    keluaran = terbuka[["id_invoice", "tanggal", "id_pelanggan", "segmen", "jumlah_juta", "termin_hari", "prob_tidak_bayar"]]
    keluaran.sort_values("prob_tidak_bayar", ascending=False).to_csv(TAB_DIR / "05_prediksi_invoice_berjalan.csv", index=False)
    berisiko = int((terbuka["prob_tidak_bayar"] >= AMBANG).sum())
    print(f"  Invoice berjalan: {len(terbuka)} | berisiko (>= {AMBANG:.2f}): {berisiko}")
    return terbuka, metrik, penting, terbaik
