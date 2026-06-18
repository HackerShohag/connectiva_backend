import os
import sys
import pickle
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import json

def train():
    print("Starting model training (Static Weight Compilation)...")
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    data_path = os.path.join(base_dir, "data")
    
    # Check if input file is passed (like from trainer)
    input_file = None
    args = sys.argv[1:]
    if "--input" in args:
        idx = args.index("--input")
        if idx + 1 < len(args):
            input_file = args[idx + 1]
    
    master_csv = input_file if input_file else os.path.join(data_path, "master_engine_data.csv")
    weights_csv = os.path.join(data_path, "mvt_weights.csv")
    
    try:
        df = pd.read_csv(master_csv)
        if "dataYear" in df.columns:
            df = df.set_index("dataYear")
        for c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        df = df.interpolate(method="linear", limit_direction="both").bfill().ffill()
        
        weights_df = pd.read_csv(weights_csv)
        weights = dict(zip(weights_df["token"], weights_df["weight"]))
        common = [c for c in df.columns if c in weights]
        w_vec = np.array([weights[c] for c in common])
        w_vec = w_vec / w_vec.sum()
        
        scores_raw = df[common].values.dot(w_vec)
        scaler = MinMaxScaler(feature_range=(0, 100))
        scaler.fit(scores_raw.reshape(-1, 1))
        
        model_state = {
            "scaler": scaler,
            "weights": weights,
            "common": common,
            "w_vec": w_vec
        }
        
        model_out = os.path.join(data_path, "connectiva_model.pkl")
        with open(model_out, "wb") as f:
            pickle.dump(model_state, f)
        
        print(f"progress: 100%")
        print(f"Model state successfully saved to {model_out}")
        
        # Save dummy metrics JSON for model_trainer parsing
        metrics = {
            "algorithm": "Static Linear + MinMaxScaler",
            "feature_count": len(common),
            "rows_processed": len(df),
            "status": "success"
        }
        with open(os.path.join(data_path, "model_metrics.json"), "w") as f:
            json.dump(metrics, f)
            
    except Exception as e:
        print(f"Error during training: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    train()
