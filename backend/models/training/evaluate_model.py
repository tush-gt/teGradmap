import pandas as pd
import numpy as np
import random
from sklearn.metrics import classification_report, roc_auc_score, accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

def evaluate_classification(model, X_test, y_test, features_list):
    """
    Evaluates the trained RandomForest model and prints metrics.
    """
    print("=" * 50)
    print("EVALUATING MODEL")
    print("=" * 50)
    
    # Predict
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    
    # Core Metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_proba)
    
    print(f"Accuracy : {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall   : {recall:.4f}")
    print(f"F1-Score : {f1:.4f}")
    print(f"ROC AUC  : {roc_auc:.4f}")
    
    print("\n--- Classification Report ---")
    print(classification_report(y_test, y_pred, target_names=["Not Admitted (0)", "Admitted (1)"]))
    
    print("\n--- Confusion Matrix ---")
    cm = confusion_matrix(y_test, y_pred)
    print(f"TN: {cm[0][0]:<6} | FP: {cm[0][1]}")
    print(f"FN: {cm[1][0]:<6} | TP: {cm[1][1]}")
    
    print("\n--- Feature Importance ---")
    try:
        # If it's a pipeline, get the classifier step
        classifier = model.named_steps["classifier"]
        importances = classifier.feature_importances_
        feature_imp = pd.DataFrame({"Feature": features_list, "Importance": importances})
        feature_imp = feature_imp.sort_values(by="Importance", ascending=False)
        print(feature_imp.head(10).to_string(index=False))
    except Exception as e:
        print(f"Could not extract feature importances: {e}")
        
    print("\n--- Probability Examples ---")
    # Generate 5 random examples from the test set
    example_indices = random.sample(range(len(X_test)), 5)
    
    for idx in example_indices:
        # X_test could be a dataframe
        row = X_test.iloc[idx]
        actual = y_test.iloc[idx]
        prob = y_proba[idx]
        pred = y_pred[idx]
        
        print(f"User: {row['user_percentile']:.2f}%ile | College: {str(row['college_name'])[:25]}... | Branch: {str(row['branch_name'])[:15]}... | Category: {row['category']}")
        print(f"   -> Actual: {actual} | Predicted: {pred} | Probability: {prob:.2%}\n")
    
    print("=" * 50)
