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
    
    Expected Columns:
    - probability (float)
    """
    if df.empty or "probability" not in df.columns:
        logger.warning("Input DataFrame is empty or missing 'probability' column. Returning unmodified copy.")
        return df.copy()
        
    result_df = df.copy()
    
    # Apply vectorizable bucketing & labeling using apply (fast enough for post-inference slices)
    result_df["probability_bucket"] = result_df["probability"].apply(probability_bucket)
    result_df["confidence_label"] = result_df["probability"].apply(get_confidence_label)
    
    # Create formatted percent string (e.g. 84.5%)
    result_df["probability_percent"] = (result_df["probability"] * 100).round(1).astype(str) + "%"
    
    return result_df

def rank_recommendations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sorts recommendations intelligently using weighted sorting priorities.
    Primary: Probability (Descending)
    Secondary: Recommendation Score (Descending)
    Tertiary: Year (Descending)
    """
    if df.empty:
        return df.copy()
        
    sort_cols = ["probability"]
    ascending = [False]
    
    # Add secondary sorts if columns exist in the DataFrame
    if "recommendation_score" in df.columns:
        sort_cols.append("recommendation_score")
        ascending.append(False)
        
    if "year" in df.columns:
        sort_cols.append("year")
        ascending.append(False)
        
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
    if df.empty or "probability_bucket" not in df.columns:
        return {"SAFE": [], "TARGET": [], "AMBITIOUS": []}
        
    buckets = {
        "SAFE": df[df["probability_bucket"] == "SAFE"].to_dict(orient="records"),
        "TARGET": df[df["probability_bucket"] == "TARGET"].to_dict(orient="records"),
        "AMBITIOUS": df[df["probability_bucket"] == "AMBITIOUS"].to_dict(orient="records"),
    }
    
    return buckets
