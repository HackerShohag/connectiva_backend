from flask import Flask, jsonify, request
from flask_cors import CORS
import re
import io
import json
from datetime import datetime
from src.core.data_loader import df, common, weights, score_series, bts_data, nttn_data
from src.core.helpers import get_district_division, get_dominant_operator, normalize_district_name
from src.core.constants import BTRC_DIVISION_DATA, DIVISION_DISTRICTS, TELECOM_KEYWORDS
from src.core.indicators import get_national_trends, build_indicator_trends, estimate_budget, get_district_score
from src.core.scraper import scrape_news, news_cache
from scripts.model_trainer import trainer
from scripts.data_verifier import verifier
from src.utils.file_parser import parse_uploaded_file

app = Flask(__name__)
CORS(app)

# ── File upload analysis endpoint ──────────────────────────────
@app.route("/api/analyze-upload", methods=["POST"])
def analyze_upload():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["file"]
    result, status_code = parse_uploaded_file(file)
    return jsonify(result), status_code

@app.route("/api/verify-data", methods=["POST"])
def verify_data():
    """Endpoint for DataVerifier logic"""
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["file"]
    
    # Save temporarily for verifier
    temp_path = f"/tmp/{file.filename}"
    file.save(temp_path)
    
    try:
        result = verifier.verify_upload(temp_path, file.filename)
        return jsonify(result)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.route("/api/train/start", methods=["POST"])
def train_start():
    """Start model training job"""
    # Optional input file
    input_file = None
    if "file" in request.files:
        file = request.files["file"]
        input_file = f"/tmp/train_{file.filename}"
        file.save(input_file)
        
    job_id = trainer.create_job(input_file)
    result = trainer.start_training(job_id)
    return jsonify(result)

@app.route("/api/train/status/<job_id>", methods=["GET"])
def train_status(job_id):
    """Check training job status"""
    job = trainer.get_job(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job.to_dict())

@app.route("/api/train/cancel/<job_id>", methods=["POST"])
def train_cancel(job_id):
    """Cancel training job"""
    result = trainer.cancel_job(job_id)
    return jsonify(result)

@app.route("/api/train/reload", methods=["POST"])
def train_reload():
    """Reload the ML model state from disk without restarting."""
    from src.core.data_loader import load_model_state
    try:
        load_model_state()
        return jsonify({"status": "success", "message": "Model state reloaded into memory"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── API Routes ─────────────────────────────────────────────────
@app.route("/api/summary", methods=["GET"])
def get_summary():
    latest = round(float(score_series.iloc[-1]), 2)
    prev = round(float(score_series.iloc[-2]), 2)
    return jsonify({
        "latest_year": int(score_series.index[-1]), "latest_score": latest,
        "change": round(latest - prev, 2), "total_years": len(score_series),
        "total_indicators": len(common)
    })

@app.route("/api/score", methods=["GET"])
def get_scores():
    return jsonify([{"year": int(y), "score": round(float(s), 2)} for y, s in score_series.items()])

@app.route("/api/indicators", methods=["GET"])
def get_indicators():
    result = []
    for col in common[:20]:
        s2 = MinMaxScaler(feature_range=(0, 100))
        vals = s2.fit_transform(df[col].values.reshape(-1, 1)).flatten()
        result.append({
            "name": col.split("_")[0].replace("-", " ").title(), "token": col,
            "weight": round(float(weights[col]), 6), "latest": round(float(vals[-1]), 2),
            "trend": [{"year": int(y), "value": round(float(v), 2)} for y, v in zip(df.index, vals)]
        })
    return jsonify(result)

@app.route("/api/analyze", methods=["GET"])
def analyze():
    national_score = float(score_series.iloc[-1])
    trends = get_national_trends()
    divisions = {}
    for div, btrc in BTRC_DIVISION_DATA.items():
        div_score = get_district_score(div, div, national_score)
        nttn = nttn_data.get(div, {})
        district_scores = {d: get_district_score(d, div, national_score) for d in DIVISION_DISTRICTS[div]}
        divisions[div] = {
            "score": div_score, "total_subscribers_m": btrc["total_subscribers_m"],
            "2g_pct": btrc["2g_pct"], "3g_pct": btrc["3g_pct"], "4g_pct": btrc["4g_pct"],
            "5g_available": btrc["5g_available"], "dominant_operator": btrc["dominant_operator"],
            "ofc_km": nttn.get("ofc_km", 0), "capacity_tbps": nttn.get("capacity_tbps", 0),
            "districts": district_scores
        }
    return jsonify({"national": {"score": round(national_score, 2), "year_range": f"{int(df.index.min())}–{int(df.index.max())}", "top_trends": trends}, "divisions": divisions})

@app.route("/api/district-roadmap", methods=["POST"])
def district_roadmap():
    data = request.json
    district = data.get("district", "Dhaka")
    target = data.get("target", 80)
    timeframe = data.get("timeframe", 5)
    multipliers = data.get("multipliers", {})
    active_year = data.get("active_year", 2025)
    client_current = data.get("current_connectivity")
    division = get_district_division(district)
    national_score = float(score_series.iloc[-1])

    # Apply active_year modifier while preserving the map's selected district baseline.
    mod = 0.78 if active_year == 2022 else 0.86 if active_year == 2023 else 0.94 if active_year == 2024 else 1.0

    try:
        base_score = float(client_current) if client_current is not None else get_district_score(district, division, national_score)
    except (TypeError, ValueError):
        base_score = get_district_score(district, division, national_score)
    current_score = base_score * mod
    
    delta = sum((multipliers.get(t, 1.0) - 1.0) * weights.get(t, 0) * 40 for t in common)
    current_score = min(100, max(0, current_score + delta))
    
    btrc = BTRC_DIVISION_DATA.get(division, {})
    nttn = nttn_data.get(division, {})
    if btrc.get("5g_available"): network_gen = "5G (available)"
    elif btrc.get("4g_pct", 0) > 40: network_gen = f"4G ({btrc.get('4g_pct', 0):.1f}%)"
    elif btrc.get("4g_pct", 0) > 10: network_gen = f"4G transitioning ({btrc.get('4g_pct', 0):.1f}%)"
    else: network_gen = f"2G/3G dominant ({btrc.get('2g_pct', 0):.1f}% on 2G)"

    indicator_trends = build_indicator_trends(current_score, target, timeframe, multipliers, active_year, district, division)

    gap = max(0, target - current_score)
    budget = estimate_budget(gap, district, timeframe)
    news = scrape_news(district, division)
    return jsonify({
        "district": district, "division": division, "current_score": round(current_score, 2),
        "target": target, "gap": round(gap, 2), "timeframe": timeframe,
        "network_generation": network_gen,
        "division_context": {
            "division": division,
            "data_year": int(score_series.index[-1]),
            "district_score": round(float(current_score), 2),
            "district_gap": round(float(gap), 2),
            "subscribers_m": btrc.get("total_subscribers_m", 0),
            "two_g_pct": btrc.get("2g_pct", 0),
            "three_g_pct": btrc.get("3g_pct", 0),
            "four_g_pct": btrc.get("4g_pct", 0),
            "dominant_operator": get_dominant_operator(district, division),
            "ofc_km": round(nttn.get("ofc_km", 0), 1),
            "capacity_tbps": round(nttn.get("capacity_tbps", 0), 2),
            "unused_tbps": round(nttn.get("unused_tbps", 0), 2),
            "nttn_count": len(nttn.get("operators", [])),
        },
        "btrc_data": {"total_subscribers_m": btrc.get("total_subscribers_m", 0), "2g_pct": btrc.get("2g_pct", 0), "3g_pct": btrc.get("3g_pct", 0), "4g_pct": btrc.get("4g_pct", 0), "5g_available": btrc.get("5g_available", False), "dominant_operator": get_dominant_operator(district, division), "operator_basis": "inferred from BTRC division mix and district market presence", "network_gen": network_gen},
        "nttn_data": {"ofc_km": round(nttn.get("ofc_km", 0), 1), "capacity_tbps": round(nttn.get("capacity_tbps", 0), 2), "unused_tbps": round(nttn.get("unused_tbps", 0), 2), "links": int(nttn.get("links", 0)), "pops": int(nttn.get("pops", 0)), "operators": nttn.get("operators", [])},
        "bts_data": bts_data,
        "budget": budget, "indicator_trends": indicator_trends, "news": news
    })

@app.route("/api/news-cache-status", methods=["GET"])
def news_cache_status():
    return jsonify({"cached_keys": len(news_cache), "last_updated": max(news_cache.keys()) if news_cache else "never"})

@app.route("/api/data-freshness", methods=["GET"])
def data_freshness():
    """Check data freshness and when last updated"""
    return jsonify({
        "last_data_year": int(df.index.max()),
        "indicators_count": len(common),
        "data_rows": len(df),
        "sources": ["ITU DataHub", "BTRC", "HIES 2022", "BTS Registry", "NTTN"],
        "last_checked": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })

@app.route("/api/world-comparison", methods=["GET"])
def world_comparison():
    return jsonify({
        "bangladesh": { "country": "Bangladesh", "internet_access_pct": 45.2, "4g_availability_pct": 45.2, "digital_literacy_pct": 38.5, "connectivity_score": 45.2 },
        "peer_countries_lowest_3": [
            { "country": "Nepal", "internet_access_pct": 38.0, "4g_availability_pct": 35.0, "digital_literacy_pct": 30.0, "connectivity_score": 34.0 }
        ],
        "peer_countries_highest_3": [
            { "country": "Vietnam", "internet_access_pct": 73.0, "4g_availability_pct": 75.0, "digital_literacy_pct": 60.0, "connectivity_score": 69.0 }
        ],
        "global_average": { "country": "Global Average", "internet_access_pct": 63.5, "connectivity_score": 59.0, "4g_availability_pct": 58.2, "digital_literacy_pct": 55.3 },
        "regional_average": { "country": "Asia-Pacific", "internet_access_pct": 72.1, "connectivity_score": 68.0, "4g_availability_pct": 68.5, "digital_literacy_pct": 62.7 }
    })

@app.route("/api/generate-report/<report_type>", methods=["POST"])
def generate_report(report_type):
    return jsonify({
        "status": "success",
        "format": report_type,
        "file": f"mock_report_{report_type}.pdf",
        "note": f"Mock generated {report_type} report successfully."
    })

@app.route("/api/download", methods=["GET"])
def download_file():
    file_path = request.args.get("file", "download.pdf")
    return f"Mock file content for: {file_path}", 200, {'Content-Disposition': f'attachment; filename="{file_path}"'}

if __name__ == "__main__":
    app.run(debug=True, port=5000)
