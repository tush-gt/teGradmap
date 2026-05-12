import pandas as pd
import joblib
from pathlib import Path


# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODEL_PATH = BASE_DIR / "models" / "trained" / "admission_rfc_model.pkl"

def run_inference_demo():
    print("=" * 50)
    print("GRADMAP INFERENCE DEMO")
    print("=" * 50)
    
    if not MODEL_PATH.exists():
        print(f"ERROR: Trained model not found at {MODEL_PATH}")
        print("Please review evaluate_model metrics and uncomment the save block in train_rfc.py.")
        return
        
    print("Loading model...")
    pipeline = joblib.load(MODEL_PATH)
    print("Model loaded successfully.\n")
    
    # Mock some data that looks like the dataset features
    # Features required: "college_name", "branch_name", "category", "round", "year", "quota_type", 
    # "branch_family", "institute_tier", "seat_competitiveness", "user_percentile"
    
    demo_samples = pd.DataFrame([
        {
            "college_name": "COEP Technological University, Pune",
            "branch_name": "Computer Engineering",
            "category": "GOPEN",
            "round": 1,
            "year": 2025,
            "quota_type": "MH",
            "branch_family": "CS_FAMILY",
            "institute_tier": 1,
            "seat_competitiveness": 0.99,
            "user_percentile": 99.7
        },
        {
            "college_name": "Pune Institute of Computer Technology, Pune",
            "branch_name": "Computer Engineering",
            "category": "GOPEN",
            "round": 1,
            "year": 2025,
            "quota_type": "MH",
            "branch_family": "CS_FAMILY",
            "institute_tier": 1,
            "seat_competitiveness": 0.98,
            "user_percentile": 98.2
        },
        {
            "college_name": "VJTI Mumbai",
            "branch_name": "Information Technology",
            "category": "GOPEN",
            "round": 2,
            "year": 2025,
            "quota_type": "MH",
            "branch_family": "CS_FAMILY",
            "institute_tier": 1,
            "seat_competitiveness": 0.97,
            "user_percentile": 97.4
        },
        {
            "college_name": "Tier 3 Engineering College",
            "branch_name": "Civil Engineering",
            "category": "GOPEN",
            "round": 3,
            "year": 2025,
            "quota_type": "MH",
            "branch_family": "CIVIL_FAMILY",
            "institute_tier": 3,
            "seat_competitiveness": 0.45,
            "user_percentile": 83.0
        }
    ])
    
    print(f"Simulating for User: {demo_samples.iloc[0]['user_percentile']} percentile, Category: {demo_samples.iloc[0]['category']}\n")
    
    # Predict probabilities ([:, 1] for class 1 / Admitted)
    probabilities = pipeline.predict_proba(demo_samples)[:, 1]
    
    demo_samples["Probability"] = probabilities
    
    # Sort and format output
    demo_samples = demo_samples.sort_values(by="Probability", ascending=False)
    
    print(f"{'College':<40} | {'Branch':<25} | {'Probability':<12}")
    print("-" * 82)
    for _, row in demo_samples.iterrows():
        print(f"{row['college_name'][:38]:<40} | {row['branch_name'][:23]:<25} | {row['Probability']:.2f}")

if __name__ == "__main__":
    run_inference_demo()
