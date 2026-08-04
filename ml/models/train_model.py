"""
train_model.py
===============
Script untuk melatih model deteksi phishing URL menggunakan XGBoost
(model utama) dan LightGBM (pembanding), lengkap dengan evaluasi dan
SHAP explainability.

CARA PAKAI:
1. Pastikan ml/data/processed/dataset_features.csv sudah ada (hasil Fase 3)
2. Jalankan: python ml/models/train_model.py
3. Model terbaik akan disimpan ke ml/models/*.pkl
4. Laporan evaluasi (teks + grafik) tersimpan di ml/models/evaluation/
"""

import sys
import os
import json
import pickle
import time

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score,
    precision_recall_curve
)
import xgboost as xgb
import lightgbm as lgb
import shap
import matplotlib
matplotlib.use("Agg")  # non-interactive backend, aman dijalankan tanpa GUI
import matplotlib.pyplot as plt


# ============================================================
# KONFIGURASI PATH
# ============================================================

_current_file = os.path.abspath(__file__)
_project_root = os.path.abspath(os.path.join(_current_file, "..", "..", ".."))

DATASET_PATH = os.path.join(_project_root, "ml", "data", "processed", "dataset_features.csv")
MODELS_DIR = os.path.join(_project_root, "ml", "models")
EVAL_DIR = os.path.join(MODELS_DIR, "evaluation")

RANDOM_SEED = 42
TEST_SIZE = 0.2


def load_data():
    print("Memuat dataset...")
    df = pd.read_csv(DATASET_PATH)
    # 'url' cuma untuk referensi manusia, bukan fitur numerik -> dibuang saat training
    feature_cols = [c for c in df.columns if c not in ("is_phishing", "url")]
    X = df[feature_cols]
    y = df["is_phishing"]
    print(f"Total data: {len(df)} baris, {len(feature_cols)} fitur")
    return X, y, feature_cols


def evaluate_model(name, model, X_test, y_test):
    """Evaluasi lengkap: accuracy, precision, recall, F1, ROC-AUC, confusion matrix"""
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred),
        "recall": recall_score(y_test, y_pred),
        "f1_score": f1_score(y_test, y_pred),
        "roc_auc": roc_auc_score(y_test, y_proba),
    }

    cm = confusion_matrix(y_test, y_pred)

    print(f"\n{'='*60}")
    print(f"HASIL EVALUASI: {name}")
    print(f"{'='*60}")
    for k, v in metrics.items():
        print(f"  {k:12s}: {v*100:.2f}%")
    print(f"\nConfusion Matrix:")
    print(f"                  Prediksi Safe   Prediksi Phishing")
    print(f"  Aktual Safe          {cm[0][0]:6d}          {cm[0][1]:6d}")
    print(f"  Aktual Phishing      {cm[1][0]:6d}          {cm[1][1]:6d}")
    print(f"\n{classification_report(y_test, y_pred, target_names=['Safe', 'Phishing'])}")

    return metrics, y_proba, cm


def plot_precision_recall_curve(y_test, y_proba_dict, save_path):
    """
    Plot precision-recall curve untuk kedua model.
    INI YANG MENJAWAB TRADE-OFF precision vs recall -> jadi bukti visual
    di laporan TA untuk justifikasi pemilihan threshold.
    """
    plt.figure(figsize=(8, 6))
    for name, y_proba in y_proba_dict.items():
        precision, recall, thresholds = precision_recall_curve(y_test, y_proba)
        plt.plot(recall, precision, label=name, linewidth=2)

    plt.xlabel("Recall (Kemampuan Menangkap Ancaman Asli)")
    plt.ylabel("Precision (Ketepatan Saat Menandai Berbahaya)")
    plt.title("Precision-Recall Curve — Trade-off Deteksi Phishing")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.savefig(save_path, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"\nGrafik precision-recall curve disimpan ke: {save_path}")


def find_threshold_for_recall(y_test, y_proba, target_recall=0.98):
    """
    Cari threshold yang menghasilkan recall tertentu (default 98%),
    sebagai rekomendasi konkret untuk kasus keamanan siber yang
    memprioritaskan menangkap ancaman asli.
    """
    precision, recall, thresholds = precision_recall_curve(y_test, y_proba)
    # thresholds punya panjang 1 lebih pendek dari precision/recall
    idx = np.argmin(np.abs(recall[:-1] - target_recall))
    return thresholds[idx], precision[idx], recall[idx]


def plot_feature_importance(model, feature_cols, name, save_path):
    importance = model.feature_importances_
    idx = np.argsort(importance)[-15:]  # top 15

    plt.figure(figsize=(8, 6))
    plt.barh(range(len(idx)), importance[idx])
    plt.yticks(range(len(idx)), [feature_cols[i] for i in idx])
    plt.xlabel("Feature Importance")
    plt.title(f"Top 15 Fitur Paling Berpengaruh — {name}")
    plt.tight_layout()
    plt.savefig(save_path, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"Grafik feature importance disimpan ke: {save_path}")


def compute_shap_summary(model, X_test, feature_cols, save_path):
    """
    Hitung SHAP values untuk sample data test, simpan summary plot.
    Fungsi terpisah (get_shap_for_single_url) akan dipakai di Fase 5
    untuk menghitung SHAP per-request secara real-time.
    """
    print("\nMenghitung SHAP values (mungkin perlu beberapa detik)...")
    explainer = shap.TreeExplainer(model)
    # Ambil sample biar cepat (SHAP bisa lambat untuk data besar)
    sample = X_test.sample(min(500, len(X_test)), random_state=RANDOM_SEED)
    shap_values = explainer.shap_values(sample)

    plt.figure()
    shap.summary_plot(shap_values, sample, feature_names=feature_cols, show=False)
    plt.tight_layout()
    plt.savefig(save_path, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"SHAP summary plot disimpan ke: {save_path}")

    return explainer


def main():
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(EVAL_DIR, exist_ok=True)

    X, y, feature_cols = load_data()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_SEED, stratify=y
    )
    print(f"Train: {len(X_train)} baris, Test: {len(X_test)} baris")

    results = {}
    y_proba_dict = {}

    # ============================================================
    # MODEL 1: XGBoost (model utama)
    # ============================================================
    print("\n" + "="*60)
    print("Melatih XGBoost...")
    print("="*60)
    start = time.time()
    xgb_model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        random_state=RANDOM_SEED,
        eval_metric="logloss",
    )
    xgb_model.fit(X_train, y_train)
    print(f"Selesai dalam {time.time()-start:.2f} detik")

    xgb_metrics, xgb_proba, xgb_cm = evaluate_model("XGBoost", xgb_model, X_test, y_test)
    results["xgboost"] = xgb_metrics
    y_proba_dict["XGBoost"] = xgb_proba

    # ============================================================
    # MODEL 2: LightGBM (pembanding)
    # ============================================================
    print("\n" + "="*60)
    print("Melatih LightGBM...")
    print("="*60)
    start = time.time()
    lgb_model = lgb.LGBMClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        random_state=RANDOM_SEED,
        verbose=-1,
    )
    lgb_model.fit(X_train, y_train)
    print(f"Selesai dalam {time.time()-start:.2f} detik")

    lgb_metrics, lgb_proba, lgb_cm = evaluate_model("LightGBM", lgb_model, X_test, y_test)
    results["lightgbm"] = lgb_metrics
    y_proba_dict["LightGBM"] = lgb_proba

    # ============================================================
    # PERBANDINGAN & PILIH MODEL TERBAIK
    # ============================================================
    print("\n" + "="*60)
    print("PERBANDINGAN MODEL")
    print("="*60)
    comparison_df = pd.DataFrame(results).T
    print(comparison_df.round(4))

    best_model_name = comparison_df["f1_score"].idxmax()
    best_model = xgb_model if best_model_name == "xgboost" else lgb_model
    print(f"\nModel terbaik (berdasarkan F1-score): {best_model_name.upper()}")

    # ============================================================
    # PRECISION-RECALL CURVE (untuk justifikasi threshold di laporan TA)
    # ============================================================
    plot_precision_recall_curve(
        y_test, y_proba_dict,
        os.path.join(EVAL_DIR, "precision_recall_curve.png")
    )

    best_proba = y_proba_dict["XGBoost"] if best_model_name == "xgboost" else y_proba_dict["LightGBM"]
    threshold_98, prec_98, rec_98 = find_threshold_for_recall(y_test, best_proba, target_recall=0.98)
    print(f"\nRekomendasi threshold untuk recall 98%: {threshold_98:.3f}")
    print(f"  (pada threshold ini: precision={prec_98*100:.1f}%, recall={rec_98*100:.1f}%)")
    print(f"Threshold default (0.5) hasil: precision={xgb_metrics['precision']*100:.1f}%, "
          f"recall={xgb_metrics['recall']*100:.1f}%")

    # ============================================================
    # FEATURE IMPORTANCE
    # ============================================================
    plot_feature_importance(
        best_model, feature_cols, best_model_name.upper(),
        os.path.join(EVAL_DIR, "feature_importance.png")
    )

    # ============================================================
    # SHAP EXPLAINABILITY
    # ============================================================
    explainer = compute_shap_summary(
        best_model, X_test, feature_cols,
        os.path.join(EVAL_DIR, "shap_summary.png")
    )

    # ============================================================
    # SIMPAN MODEL & METADATA
    # ============================================================
    model_path = os.path.join(MODELS_DIR, f"{best_model_name}_model.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(best_model, f)
    print(f"\nModel disimpan ke: {model_path}")

    explainer_path = os.path.join(MODELS_DIR, "shap_explainer.pkl")
    with open(explainer_path, "wb") as f:
        pickle.dump(explainer, f)
    print(f"SHAP explainer disimpan ke: {explainer_path}")

    metadata = {
        "best_model": best_model_name,
        "feature_columns": feature_cols,
        "metrics": results,
        "recommended_threshold_for_98pct_recall": float(threshold_98),
        "default_threshold": 0.5,
        "trained_at": pd.Timestamp.now().isoformat(),
        "train_size": len(X_train),
        "test_size": len(X_test),
    }
    metadata_path = os.path.join(MODELS_DIR, "model_metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata disimpan ke: {metadata_path}")

    print("\n" + "="*60)
    print("TRAINING SELESAI")
    print("="*60)


if __name__ == "__main__":
    main()