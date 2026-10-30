import pandas as pd
import logging

logger = logging.getLogger(__name__)

def probability_bucket(prob: float) -> str:
    """
    Categorizes raw probability into a distinct counselling bucket.
    """
    if prob >= 0.70:
        return "SAFE"
    elif 0.45 <= prob < 0.70:
        return "TARGET"
    else:
        return "AMBITIOUS"

def get_confidence_label(prob: float) -> str:
    """
    Converts probability into a human-readable confidence label.
    """
    if prob >= 0.95:
        return "VERY_HIGH"
    elif prob >= 0.80:
        return "HIGH"
    elif prob >= 0.60:
        return "MODERATE"
    elif prob >= 0.40:
        return "LOW"
    else:
        return "VERY_LOW"

def attach_probability_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """
    Attaches derived ML probability metadata to the dataframe.
    Safely creates a copy to avoid side-effects on the original dataframe.
    Only computes percentage and confidence when real probability is present.
    """
    if df.empty:
        return df.copy()
        
    result_df = df.copy()
    has_valid_prob = "probability" in result_df.columns and result_df["probability"].notna().any()

    if not has_valid_prob:
        # Model is unavailable: fall back to percentile gap bucket, never invent 50%
        result_df["probability_bucket"] = result_df.get("recommendation_bucket", "TARGET")
        result_df["confidence_label"] = None
        result_df["probability_percent"] = None
        result_df["ml_probability"] = None
        return result_df

    # Vectorized / element-wise mapping for genuine probabilities
    def map_bucket(val, fallback):
        if pd.isna(val) or val is None:
            return fallback if pd.notna(fallback) else "TARGET"
        return probability_bucket(float(val))

    def map_confidence(val):
        if pd.isna(val) or val is None:
            return None
        return get_confidence_label(float(val))

    def map_percent(val):
        if pd.isna(val) or val is None:
            return None
        return f"{(float(val) * 100):.1f}%"

    fallback_bucket = result_df.get("recommendation_bucket", pd.Series(["TARGET"] * len(result_df)))
    result_df["probability_bucket"] = [
        map_bucket(p, f) for p, f in zip(result_df["probability"], fallback_bucket)
    ]
    result_df["confidence_label"] = result_df["probability"].apply(map_confidence)
    result_df["probability_percent"] = result_df["probability"].apply(map_percent)
    result_df["ml_probability"] = result_df["probability"].apply(
        lambda p: round(float(p), 4) if (pd.notna(p) and p is not None) else None
    )
    
    return result_df

def rank_recommendations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sorts recommendations intelligently using weighted sorting priorities.
    Primary: Probability (Descending, if available)
    Secondary: Recommendation Score (Descending)
    Tertiary: Year (Descending)
    """
    if df.empty:
        return df.copy()
        
    sort_cols = []
    ascending = []

    # Only sort by probability if valid probabilities exist
    if "probability" in df.columns and df["probability"].notna().any():
        sort_cols.append("probability")
        ascending.append(False)
        
    # Add secondary sorts if columns exist in the DataFrame
    if "recommendation_score" in df.columns:
        sort_cols.append("recommendation_score")
        ascending.append(False)
        
    if "year" in df.columns:
        sort_cols.append("year")
        ascending.append(False)
        
    if not sort_cols:
        return df.copy()

    return df.sort_values(by=sort_cols, ascending=ascending).reset_index(drop=True)

def diversify_recommendations(df: pd.DataFrame, max_per_college: int = 2) -> pd.DataFrame:
    """
    Prevents recommendation spam from a single institute.
    Limits the number of branches returned per college_name.
    """
    if df.empty or "college_name" not in df.columns:
        return df.copy()
        
    # Group by college and take top N rows (assumes df is already ranked appropriately)
    diversified_df = df.groupby("college_name", group_keys=False).head(max_per_college)
    
    return diversified_df

def split_into_buckets(df: pd.DataFrame) -> dict:
    """
    Splits the recommendation dataframe into distinct category buckets.
    Returns a dictionary of lists.
    """
    if df.empty:
        return {"SAFE": [], "TARGET": [], "AMBITIOUS": []}

    bucket_col = "probability_bucket" if "probability_bucket" in df.columns else "recommendation_bucket"
    if bucket_col not in df.columns:
        return {"SAFE": [], "TARGET": [], "AMBITIOUS": []}
        
    buckets = {
        "SAFE": df[df[bucket_col] == "SAFE"].to_dict(orient="records"),
        "TARGET": df[df[bucket_col] == "TARGET"].to_dict(orient="records"),
        "AMBITIOUS": df[df[bucket_col] == "AMBITIOUS"].to_dict(orient="records"),
    }
    
    return buckets
