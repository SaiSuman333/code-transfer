import json
import numpy as np
import pandas as pd
import plotly.express as px
from fastapi import HTTPException
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score, f1_score, mean_absolute_error,
    mean_squared_error, precision_score, r2_score, recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder

from backend.schemas.predict import FeatureImportance, PredictResponse
from backend.services import llm_service


def run_prediction(
    df: pd.DataFrame,
    session_id: str,
    target_column: str,
    feature_columns: list[str] | None,
    task_type: str,
    test_size: float,
) -> PredictResponse:
    if target_column not in df.columns:
        raise HTTPException(400, f"Target column '{target_column}' not found.")

    # Drop rows where target is null
    df = df.dropna(subset=[target_column]).copy()
    if len(df) < 10:
        raise HTTPException(400, "Not enough data after removing missing target values (need at least 10 rows).")

    # Auto-select features
    if feature_columns is None:
        feature_columns = [c for c in df.select_dtypes(include="number").columns if c != target_column]
        cat_cols = [c for c in df.select_dtypes(include="object").columns if c != target_column]
        feature_columns = feature_columns + cat_cols[:5]  # include up to 5 categoricals

    if not feature_columns:
        raise HTTPException(400, "No feature columns available for prediction.")

    X = df[feature_columns].copy()
    y = df[target_column].copy()

    # Auto-detect task type
    if task_type == "auto":
        is_numeric_target = pd.api.types.is_numeric_dtype(y)
        unique_ratio = y.nunique() / len(y)
        task_type = "classification" if (not is_numeric_target or (is_numeric_target and y.nunique() <= 15 and unique_ratio < 0.05)) else "regression"

    # Encode classification target
    le = None
    if task_type == "classification":
        le = LabelEncoder()
        y = le.fit_transform(y.astype(str))

    # Build preprocessing pipeline
    num_features = [c for c in feature_columns if pd.api.types.is_numeric_dtype(X[c])]
    cat_features = [c for c in feature_columns if not pd.api.types.is_numeric_dtype(X[c])]

    transformers = []
    if num_features:
        transformers.append(("num", SimpleImputer(strategy="median"), num_features))
    if cat_features:
        transformers.append((
            "cat",
            Pipeline([
                ("impute", SimpleImputer(strategy="most_frequent")),
                ("encode", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
            ]),
            cat_features,
        ))

    preprocessor = ColumnTransformer(transformers=transformers, remainder="drop")

    if task_type == "regression":
        model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
        model_name = "RandomForestRegressor"
    else:
        model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        model_name = "RandomForestClassifier"

    pipeline = Pipeline([("preprocessor", preprocessor), ("model", model)])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    # Compute metrics
    if task_type == "regression":
        metrics = {
            "r2": float(r2_score(y_test, y_pred)),
            "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred))),
            "mae": float(mean_absolute_error(y_test, y_pred)),
        }
        fig = px.scatter(
            x=y_test, y=y_pred,
            labels={"x": "Actual", "y": "Predicted"},
            title="Actual vs Predicted",
            trendline="ols",
        )
        fig.update_layout(template="plotly_white")
        plotly_json = json.loads(fig.to_json())
    else:
        metrics = {
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "f1_weighted": float(f1_score(y_test, y_pred, average="weighted", zero_division=0)),
            "precision_weighted": float(precision_score(y_test, y_pred, average="weighted", zero_division=0)),
            "recall_weighted": float(recall_score(y_test, y_pred, average="weighted", zero_division=0)),
        }
        # Confusion matrix
        from sklearn.metrics import confusion_matrix
        classes = le.classes_ if le else sorted(set(y_test))
        cm = confusion_matrix(y_test, y_pred)
        fig = px.imshow(
            cm, x=[str(c) for c in classes], y=[str(c) for c in classes],
            text_auto=True, color_continuous_scale="Blues",
            title="Confusion Matrix",
            labels={"x": "Predicted", "y": "Actual"},
        )
        fig.update_layout(template="plotly_white")
        plotly_json = json.loads(fig.to_json())

    # Feature importances
    rf_model = pipeline.named_steps["model"]
    raw_importances = rf_model.feature_importances_

    # Get feature names after preprocessing
    try:
        feature_names = pipeline.named_steps["preprocessor"].get_feature_names_out()
    except Exception:
        feature_names = [f"feature_{i}" for i in range(len(raw_importances))]

    fi_list = sorted(
        [FeatureImportance(feature=str(n), importance=float(v)) for n, v in zip(feature_names, raw_importances)],
        key=lambda x: x.importance,
        reverse=True,
    )[:20]

    explanation = llm_service.explain_prediction(
        metrics=metrics,
        feature_importances=[f.model_dump() for f in fi_list],
        task_type=task_type,
        target_column=target_column,
        model_name=model_name,
    )

    return PredictResponse(
        session_id=session_id,
        task_type=task_type,
        model_name=model_name,
        metrics=metrics,
        feature_importances=fi_list,
        plotly_json=plotly_json,
        explanation=explanation,
        model_used="template-engine",
    )
