"""
XGBoost Model Training Script
==============================
Trains an XGBoost classifier on a synthetic financial distress dataset.
Generates feature-engineered training data, trains the model, evaluates it,
and saves the model + scaler as .joblib files.

Usage:
    python -m app.ml_models.train_model
"""

import os
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from loguru import logger
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier


# Feature columns used for prediction
FEATURE_COLUMNS = [
    "current_ratio",
    "quick_ratio",
    "debt_to_equity",
    "operating_margin",
    "net_profit_margin",
    "working_capital_ratio",
    "cash_flow_ratio",
    "debt_ratio",
    "return_on_assets",
    "return_on_equity",
]

TARGET_COLUMN = "distress_label"


def generate_synthetic_dataset(n_samples: int = 2000, random_state: int = 42) -> pd.DataFrame:
    """
    Generate a realistic synthetic financial distress dataset.
    
    Creates samples with realistic distributions for healthy and distressed companies,
    modeled on patterns from real-world financial distress studies.
    """
    np.random.seed(random_state)
    logger.info(f"Generating synthetic dataset with {n_samples} samples")

    # 30% distressed, 70% healthy (realistic class imbalance)
    n_distressed = int(n_samples * 0.3)
    n_healthy = n_samples - n_distressed

    # --- Healthy Companies ---
    healthy = pd.DataFrame({
        "current_ratio": np.random.normal(2.0, 0.6, n_healthy).clip(0.8, 5.0),
        "quick_ratio": np.random.normal(1.5, 0.5, n_healthy).clip(0.5, 4.0),
        "debt_to_equity": np.random.normal(0.8, 0.4, n_healthy).clip(0.1, 2.5),
        "operating_margin": np.random.normal(15.0, 5.0, n_healthy).clip(-5, 40),
        "net_profit_margin": np.random.normal(10.0, 4.0, n_healthy).clip(-3, 30),
        "working_capital_ratio": np.random.normal(0.3, 0.15, n_healthy).clip(-0.1, 0.8),
        "cash_flow_ratio": np.random.normal(0.6, 0.25, n_healthy).clip(-0.1, 2.0),
        "debt_ratio": np.random.normal(0.35, 0.12, n_healthy).clip(0.05, 0.7),
        "return_on_assets": np.random.normal(8.0, 3.0, n_healthy).clip(-2, 25),
        "return_on_equity": np.random.normal(15.0, 6.0, n_healthy).clip(-5, 40),
        "distress_label": 0,
    })

    # --- Distressed Companies ---
    distressed = pd.DataFrame({
        "current_ratio": np.random.normal(0.7, 0.3, n_distressed).clip(0.1, 1.5),
        "quick_ratio": np.random.normal(0.4, 0.25, n_distressed).clip(0.05, 1.2),
        "debt_to_equity": np.random.normal(3.0, 1.2, n_distressed).clip(1.0, 8.0),
        "operating_margin": np.random.normal(-2.0, 6.0, n_distressed).clip(-20, 10),
        "net_profit_margin": np.random.normal(-5.0, 5.0, n_distressed).clip(-25, 5),
        "working_capital_ratio": np.random.normal(-0.15, 0.2, n_distressed).clip(-0.6, 0.2),
        "cash_flow_ratio": np.random.normal(-0.1, 0.3, n_distressed).clip(-0.8, 0.4),
        "debt_ratio": np.random.normal(0.75, 0.12, n_distressed).clip(0.4, 1.0),
        "return_on_assets": np.random.normal(-3.0, 4.0, n_distressed).clip(-20, 5),
        "return_on_equity": np.random.normal(-8.0, 8.0, n_distressed).clip(-40, 10),
        "distress_label": 1,
    })

    dataset = pd.concat([healthy, distressed], ignore_index=True)
    dataset = dataset.sample(frac=1, random_state=random_state).reset_index(drop=True)

    logger.info(f"Dataset generated: {len(dataset)} samples, "
                f"{n_distressed} distressed ({n_distressed/n_samples*100:.0f}%), "
                f"{n_healthy} healthy ({n_healthy/n_samples*100:.0f}%)")

    return dataset


def train_model(
    dataset: pd.DataFrame | None = None,
    output_dir: str = "./trained_models",
) -> dict:
    """
    Train the XGBoost financial distress classifier.

    Args:
        dataset: Optional pre-loaded DataFrame. If None, generates synthetic data.
        output_dir: Directory to save trained model and scaler.

    Returns:
        Dictionary with model metrics and file paths.
    """
    # Generate or load dataset
    if dataset is None:
        dataset = generate_synthetic_dataset()

    X = dataset[FEATURE_COLUMNS].copy()
    y = dataset[TARGET_COLUMN].copy()

    # Handle any missing values
    X = X.fillna(X.median())

    # Train/test split (stratified)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    logger.info("Training XGBoost classifier...")

    # XGBoost with tuned hyperparameters
    model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        gamma=0.1,
        reg_alpha=0.1,
        reg_lambda=1.0,
        scale_pos_weight=len(y_train[y_train == 0]) / max(len(y_train[y_train == 1]), 1),
        random_state=42,
        eval_metric="logloss",
        use_label_encoder=False,
    )

    model.fit(
        X_train_scaled,
        y_train,
        eval_set=[(X_test_scaled, y_test)],
        verbose=False,
    )

    # Evaluate
    y_pred = model.predict(X_test_scaled)
    y_proba = model.predict_proba(X_test_scaled)[:, 1]

    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    auc_roc = roc_auc_score(y_test, y_proba)

    logger.info(f"Model Performance — Accuracy: {accuracy:.4f}, F1: {f1:.4f}, AUC-ROC: {auc_roc:.4f}")
    logger.info(f"\n{classification_report(y_test, y_pred, target_names=['Healthy', 'Distressed'])}")

    # Save model and scaler
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    model_path = os.path.join(output_dir, "xgboost_distress_model.joblib")
    scaler_path = os.path.join(output_dir, "feature_scaler.joblib")

    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)

    # Save feature names
    feature_names_path = os.path.join(output_dir, "feature_names.joblib")
    joblib.dump(FEATURE_COLUMNS, feature_names_path)

    logger.info(f"Model saved to {model_path}")
    logger.info(f"Scaler saved to {scaler_path}")

    # Save dataset for reference
    dataset_path = os.path.join("datasets", "financial_distress.csv")
    Path("datasets").mkdir(parents=True, exist_ok=True)
    dataset.to_csv(dataset_path, index=False)
    logger.info(f"Dataset saved to {dataset_path}")

    return {
        "accuracy": accuracy,
        "f1_score": f1,
        "auc_roc": auc_roc,
        "model_path": model_path,
        "scaler_path": scaler_path,
        "feature_columns": FEATURE_COLUMNS,
        "train_samples": len(X_train),
        "test_samples": len(X_test),
    }


if __name__ == "__main__":
    # Allow running as: python -m app.ml_models.train_model
    logger.info("Starting model training...")
    metrics = train_model()
    logger.info(f"Training complete. Metrics: {metrics}")
