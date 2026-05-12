import pandas as pd
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OrdinalEncoder
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer

# Local import
from evaluate_model import evaluate_classification

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
FEATURES_DIR = BASE_DIR / "features"
DATASET_CSV = FEATURES_DIR / "training_dataset.csv"
MODEL_OUTPUT_PATH = BASE_DIR / "models" / "trained" / "admission_rfc_model.pkl"

FEATURES = [
    "college_name",
    "branch_name",
    "category",
    "round",
    "year",
    "quota_type",
    "branch_family",
    "institute_tier",
    "seat_competitiveness",
    "user_percentile",
]
TARGET = "admitted"

def train_model():
    print(f"Loading training data from {DATASET_CSV}...")
    df = pd.read_csv(DATASET_CSV)
    
    print(f"Dataset shape: {df.shape}")
    
    X = df[FEATURES]
    y = df[TARGET]
    
    # Identify categorical columns for ordinal encoding
    categorical_cols = X.select_dtypes(include=['object', 'string']).columns.tolist()
    
    print(f"Categorical features to encode: {categorical_cols}")
    
    # Preprocessor
    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), categorical_cols)
        ],
        remainder='passthrough'
    )
    
    # Pipeline
    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(
            n_estimators=200,
            max_depth=20,
            min_samples_leaf=3,
            random_state=42,
            n_jobs=-1
        ))
    ])
    
    print("Splitting dataset (80/20 stratify=y)...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, stratify=y, random_state=42)
    
    print("Training RandomForestClassifier... (This might take a minute)")
    pipeline.fit(X_train, y_train)
    print("Training complete.")
    
    # To get proper feature names for importance mapping
    numeric_cols = X.select_dtypes(exclude=['object', 'string']).columns.tolist()
    all_features = categorical_cols + numeric_cols
    
    # Evaluate
    evaluate_classification(pipeline, X_test, y_test, all_features)
    
    print(f"Saving model to {MODEL_OUTPUT_PATH}...")
    MODEL_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_OUTPUT_PATH)
    print("Model saved successfully!")
    # print("WARNING: Model saving is currently commented out. Review metrics first.")

if __name__ == "__main__":
    train_model()
