import pandas as pd
import numpy as np
import random
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
FEATURES_DIR = BASE_DIR / "features"
INPUT_CSV = FEATURES_DIR / "featured_master_dataset.csv"
OUTPUT_CSV = FEATURES_DIR / "training_dataset.csv"

def prepare_training_data():
    print(f"Loading dataset from {INPUT_CSV}...")
    df = pd.read_csv(INPUT_CSV)
    
    # Ensure percentile_cutoff exists
    if "percentile_cutoff" not in df.columns:
        raise ValueError("percentile_cutoff column missing from dataset!")
    
    print(f"Loaded {len(df)} base rows. Generating synthetic samples using vectorization...")
    
    # 1. Positive Samples
    pos_df = df.copy()
    pos_margins = np.random.uniform(0.05, 2.5, size=len(pos_df))
    pos_df["user_percentile"] = np.clip(pos_df["percentile_cutoff"] + pos_margins, 0.0, 100.0)
    pos_df["admitted"] = 1
    
    # 2. Negative Samples
    neg_df = df.copy()
    neg_margins = np.random.uniform(0.05, 1.5, size=len(neg_df))
    neg_df["user_percentile"] = neg_df["percentile_cutoff"] - neg_margins
    neg_df["admitted"] = 0
    
    # Filter negative samples to only valid percentiles > 0
    neg_df = neg_df[neg_df["user_percentile"] > 0]
    
    print("Concatenating dataset...")
    final_df = pd.concat([pos_df, neg_df], ignore_index=True)
    
    # Shuffle the dataset
    final_df = final_df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    print(f"Saving to {OUTPUT_CSV}...")
    final_df.to_csv(OUTPUT_CSV, index=False)
    
    print("=" * 50)
    print("DATA PREPARATION COMPLETE")
    print("=" * 50)
    print(f"Total Rows: {len(final_df):,}")
    print(f"Positive Samples: {len(pos_df):,}")
    print(f"Negative Samples: {len(neg_df):,}")
    print("=" * 50)

if __name__ == "__main__":
    prepare_training_data()
