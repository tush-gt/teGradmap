import logging
import joblib
import pandas as pd
import numpy as np
from pathlib import Path

# Setup logging for the utility module
logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")
logger = logging.getLogger(__name__)

# Constants
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
MODEL_PATH = BASE_DIR / "backend" / "models" / "trained" / "admission_rfc_model.pkl"

# Global memory cache
_MODEL_CACHE = None

# Mandatory features expected by the trained pipeline
REQUIRED_FEATURES = [
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

def load_model():
    """
    Loads the trained RandomForest pipeline from disk and caches it in memory.
    Raises FileNotFoundError if the model doesn't exist.
    """
    global _MODEL_CACHE
    
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE
        
    logger.info("Loading admission model...")
    
    if not MODEL_PATH.exists():
        error_msg = f"Model file missing at {MODEL_PATH}. Ensure the pipeline has been trained and saved."
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
        
    try:
        # Load the pipeline
        _MODEL_CACHE = joblib.load(MODEL_PATH)
        logger.info("Model loaded successfully into memory cache.")
        return _MODEL_CACHE
    except Exception as e:
        error_msg = f"Failed to load the model file. It may be corrupted. Error: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

def get_model():
    """
    Returns the loaded model from cache, or auto-loads it if not yet loaded.
    """
    if _MODEL_CACHE is None:
        return load_model()
    return _MODEL_CACHE

def validate_feature_columns(input_df: pd.DataFrame) -> bool:
    """
    Validates that the input DataFrame contains all required feature columns.
    Logs warnings for any missing columns.
    """
    if input_df.empty:
        logger.warning("Input DataFrame is empty.")
        return False
        
    missing_cols = [col for col in REQUIRED_FEATURES if col not in input_df.columns]
    if missing_cols:
        logger.warning(f"Missing feature columns: {missing_cols}")
        return False
        
    return True

def predict_probability(input_df: pd.DataFrame) -> np.ndarray:
    """
    Takes a DataFrame of features and returns a numpy array of admission probabilities.
    
    Raises ValueError if input lacks required features.
    """
    if not validate_feature_columns(input_df):
        raise ValueError("Input DataFrame is missing required features. Check logs for details.")
        
    try:
        model = get_model()
        # Ensure only the required columns in the correct order are passed
        X = input_df[REQUIRED_FEATURES]
        # predict_proba returns array of shape (n_samples, n_classes). Class 1 is 'Admitted'
        probabilities = model.predict_proba(X)[:, 1]
        return probabilities
    except (FileNotFoundError, RuntimeError) as e:
        logger.warning(f"ML Model unavailable, using neutral probabilities. Error: {e}")
        # Return neutral 0.5 probability for all rows if model is missing
        return np.full(len(input_df), 0.5)
    except Exception as e:
        logger.error(f"Error during probability prediction: {str(e)}")
        raise RuntimeError(f"Prediction failed: {str(e)}") from e
