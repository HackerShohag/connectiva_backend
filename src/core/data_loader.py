import os
import pandas as pd
import numpy as np
import csv
import pickle
from sklearn.preprocessing import MinMaxScaler
from .helpers import parse_number, normalize_division_name

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROJECT_ROOT = os.path.abspath(os.path.join(BACKEND_DIR, "..", ".."))

def data_path(filename):
    candidates = [
        os.path.join(BACKEND_DIR, "data", filename),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    raise FileNotFoundError(f"Required data file not found: {filename}")

df = None
weights = None
common = []
w_vec = None
scaler = None
score_series = None

def load_model_state():
    global df, weights, common, w_vec, scaler, score_series
    
    df = pd.read_csv(data_path("master_engine_data.csv"))
    if "dataYear" in df.columns:
        df = df.set_index("dataYear")
    for c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.interpolate(method="linear", limit_direction="both").bfill().ffill()

    model_pkl = os.path.join(BACKEND_DIR, "data", "connectiva_model.pkl")
    try:
        with open(model_pkl, "rb") as f:
            state = pickle.load(f)
            weights = state["weights"]
            common = state["common"]
            w_vec = state["w_vec"]
            scaler = state["scaler"]
            print(f"Loaded ML model state from {model_pkl}")
    except (FileNotFoundError, KeyError, EOFError, pickle.UnpicklingError):
        print("No valid pickled model found, falling back to dynamic computation.")
        weights_df = pd.read_csv(data_path("mvt_weights.csv"))
        weights = dict(zip(weights_df["token"], weights_df["weight"]))
        common = [c for c in df.columns if c in weights]
        w_vec = np.array([weights[c] for c in common])
        w_vec = w_vec / w_vec.sum()
        
        scores_raw = df[common].values.dot(w_vec)
        scaler = MinMaxScaler(feature_range=(0, 100))
        scaler.fit(scores_raw.reshape(-1, 1))
    
    scores_raw = df[common].values.dot(w_vec)
    scores = scaler.transform(scores_raw.reshape(-1, 1)).flatten()
    score_series = pd.Series(scores, index=df.index, name="score")

load_model_state()

def load_bts_data():
    try:
        bts_raw = pd.read_csv(data_path("Report (2022 to 2025)_BTS.csv"), header=None)
        bts_raw.columns = ['Month', 'Operator', 'BTS_2G', 'NodeB_3G', 'eNodeB_4G'] + list(bts_raw.columns[5:])
        bts_raw = bts_raw.dropna(subset=['Operator'])
        bts_raw = bts_raw[bts_raw['Operator'].astype(str).str.strip().isin(['GP','Robi','BL','TBL','Teletalk'])]
        latest = {}
        for _, row in bts_raw.iterrows():
            op = str(row['Operator']).strip()
            latest[op] = {'BTS_2G': row['BTS_2G'], 'NodeB_3G': row['NodeB_3G'], 'eNodeB_4G': row['eNodeB_4G']}
        return latest
    except Exception as e:
        print(f"BTS load error: {e}")
        return {}

def load_nttn_data():
    try:
        result = {}
        current_op = None
        with open(data_path("Summary_NTTN Core&Capacity_Final.csv"), newline="") as f:
            reader = csv.reader(f)
            next(reader, None)
            next(reader, None)
            for row in reader:
                if len(row) < 11:
                    continue
                if row[1].strip():
                    current_op = row[1].strip()
                division = normalize_division_name(row[2])
                if not current_op or not division:
                    continue
                bucket = result.setdefault(division, {
                    "ofc_km": 0, "capacity_tbps": 0, "unused_tbps": 0,
                    "links": 0, "pops": 0, "operators": []
                })
                bucket["links"] += parse_number(row[3])
                bucket["pops"] += parse_number(row[4])
                bucket["ofc_km"] += parse_number(row[5])
                bucket["capacity_tbps"] += parse_number(row[9])
                bucket["unused_tbps"] += parse_number(row[10])
                if current_op not in bucket["operators"]:
                    bucket["operators"].append(current_op)
        return result
    except Exception as e:
        print(f"NTTN load error: {e}")
        return {}

bts_data = load_bts_data()
nttn_data = load_nttn_data()
