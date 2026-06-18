import numpy as np
import pandas as pd
from .constants import COST_PER_ACTION, LOWER_IS_BETTER_TERMS, BTRC_DIVISION_DATA, DISTRICT_MODIFIERS
from .helpers import get_district_division, indicator_display_name
from .data_loader import df, weights, common, score_series, nttn_data

def estimate_budget(gap_pct, district_name, timeframe):
    division = get_district_division(district_name)
    nttn = nttn_data.get(division, {})
    btrc = BTRC_DIVISION_DATA.get(division, {})
    actions = []
    total_cost = 0
    if gap_pct > 20:
        towers_needed = max(5, int(gap_pct * 2.5))
        cost = towers_needed * COST_PER_ACTION["tower"]["cost"]
        total_cost += cost
        actions.append({"action": f"Install {towers_needed} new BTS/eNodeB towers", "cost_crore": round(cost, 2), "duration_months": COST_PER_ACTION["tower"]["time_months"], "parallel": True})
    fiber_km = max(20, int(gap_pct * 3))
    cost = fiber_km * COST_PER_ACTION["fiber"]["cost"]
    total_cost += cost
    actions.append({"action": f"Lay {fiber_km} km optical fiber backbone", "cost_crore": round(cost, 2), "duration_months": COST_PER_ACTION["fiber"]["time_months"], "parallel": True})
    if btrc.get("4g_pct", 0) < 40:
        sites = max(10, int(gap_pct * 1.8))
        cost = sites * COST_PER_ACTION["4g_upgrade"]["cost"]
        total_cost += cost
        actions.append({"action": f"Upgrade {sites} sites to 4G/LTE standard", "cost_crore": round(cost, 2), "duration_months": COST_PER_ACTION["4g_upgrade"]["time_months"], "parallel": False})
    pop_thousands = 500
    cost = (pop_thousands / 10) * COST_PER_ACTION["digital_literacy"]["cost"]
    total_cost += cost
    actions.append({"action": f"Digital literacy program for ~{pop_thousands}k residents", "cost_crore": round(cost, 2), "duration_months": COST_PER_ACTION["digital_literacy"]["time_months"], "parallel": True})
    return {
        "total_cost_crore": round(total_cost, 2), "total_cost_usd_million": round(total_cost * 0.0083, 2),
        "estimated_years": timeframe, "annual_budget_crore": round(total_cost / max(1, timeframe), 2),
        "actions": actions, "nttn_available_capacity_tbps": round(nttn.get("unused_tbps", 0), 2),
        "note": "Estimates based on BTRC/ITU infrastructure cost benchmarks"
    }

def get_national_trends():
    trends = {}
    for col in common[:15]:
        series = df[col].dropna()
        if len(series) >= 2:
            vals = list(series.values)
            years = list(series.index.astype(int))
            first, last = float(vals[0]), float(vals[-1])
            growth = ((last - first) / abs(first) * 100) if first != 0 else 0
            growth_per_year = (last - first) / max(1, len(vals) - 1)
            direction = "increased" if growth > 0 else "decreased"
            name = col.split('_')[0].replace('-', ' ').title()
            trends[col] = {
                "name": name, "2000": round(first, 2), "2025": round(last, 2),
                "growth_pct": round(growth, 1), "growth_per_year": round(growth_per_year, 3),
                "weight": round(float(weights.get(col, 0)), 5),
                "natural_language": f"{name} has {direction} by {abs(round(growth, 1))}% over 25 years, from {round(first,1)} to {round(last,1)}, averaging {abs(round(growth_per_year,2))} units/year.",
                "history": [{"year": y, "value": round(float(v), 2)} for y, v in zip(years[-10:], vals[-10:])]
            }
    return trends

def normalize_series(series):
    numeric = pd.to_numeric(series, errors="coerce").interpolate(limit_direction="both").bfill().ffill()
    min_v = float(numeric.min())
    max_v = float(numeric.max())
    if np.isclose(max_v, min_v):
        return pd.Series(np.full(len(numeric), 50.0), index=numeric.index)
    return ((numeric - min_v) / (max_v - min_v)) * 100

def year_value(series, active_year):
    years = list(series.index.astype(int))
    selected_year = active_year if active_year in years else min(years, key=lambda y: abs(y - active_year))
    return selected_year, float(series.loc[selected_year])

def build_indicator_trends(current_score, target, timeframe, multipliers, active_year, district_name, division_name):
    gap = max(0.0, float(target) - float(current_score))
    safe_margin = max(0.0, float(current_score) - float(target))
    national_current = float(score_series.iloc[-1]) or 1.0
    district_factor = max(0.55, min(1.25, float(current_score) / national_current))
    weighted = sorted(common, key=lambda col: abs(float(weights.get(col, 0))), reverse=True)
    candidates = []
    for col in weighted:
        norm = normalize_series(df[col])
        _, current_val = year_value(norm, active_year)
        lower_is_better = any(term in col for term in LOWER_IS_BETTER_TERMS)
        has_room = current_val > 35.0 if lower_is_better else current_val < 99.0
        if has_room:
            candidates.append(col)
        if len(candidates) >= 8:
            break
    top = candidates or weighted[:8]
    total_weight = sum(abs(float(weights.get(col, 0))) for col in top) or 1.0
    indicators = []

    pid_step = min(15.0, (0.6 * gap) + (0.1 * gap * max(1, timeframe) / 5.0) + (0.05 * gap))

    for col in top:
        norm = normalize_series(df[col])
        selected_year, national_val = year_value(norm, active_year)
        lower_is_better = any(term in col for term in LOWER_IS_BETTER_TERMS)
        if lower_is_better:
            current_val = max(0.0, min(100.0, national_val / district_factor))
        else:
            current_val = max(0.0, min(100.0, national_val * district_factor))
        hist = []
        for y, v in norm.tail(10).items():
            adjusted = (float(v) / district_factor) if lower_is_better else (float(v) * district_factor)
            hist.append({"year": int(y), "value": round(max(0.0, min(100.0, adjusted)), 2)})
        historical_growth = (float(hist[-1]["value"]) - float(hist[0]["value"])) / max(1, len(hist) - 1)
        multiplier = float(multipliers.get(col, 1.0) or 1.0)
        share = abs(float(weights.get(col, 0))) / total_weight

        correction = pid_step * share * multiplier
        if gap <= 0:
            target_val = max(0.0, current_val - (safe_margin * share)) if lower_is_better else min(100.0, current_val + (safe_margin * share))
        elif lower_is_better:
            target_val = max(0.0, current_val - correction)
        else:
            target_val = min(100.0, current_val + correction)

        change = target_val - current_val
        change_pct = (change / current_val * 100) if abs(current_val) > 0.001 else (100.0 if change > 0 else -100.0 if change < 0 else 0.0)
        direction = "decrease" if change < 0 else "increase"
        verb = "reduce" if direction == "decrease" else "raise"
        recent_delta = hist[-1]["value"] - hist[0]["value"] if len(hist) >= 2 else 0.0
        recent_direction = "upward" if recent_delta > 0 else "downward" if recent_delta < 0 else "flat"
        if lower_is_better:
            social_effect = "service friction is easing" if recent_delta < 0 else "service friction is rising" if recent_delta > 0 else "service friction is stable"
        else:
            social_effect = "access/readiness is improving" if recent_delta > 0 else "access/readiness is weakening" if recent_delta < 0 else "access/readiness is stable"
        plan_action = "hold and protect the margin" if gap <= 0 else (f"{verb} this lever by {abs(change):.2f} normalized points")
        indicators.append({
            "name": indicator_display_name(col),
            "token": col,
            "weight": round(float(weights.get(col, 0)), 5),
            "current_value": round(float(current_val), 2),
            "target_value": round(float(target_val), 2),
            "change": round(float(change), 2),
            "change_pct": round(float(change_pct), 1),
            "growth_per_year": round(float(historical_growth), 3),
            "direction": direction,
            "active_year": int(selected_year),
            "national_value": round(float(national_val), 2),
            "district_factor": round(float(district_factor), 3),
            "safe_margin": round(float(abs(change) if gap <= 0 else 0.0), 2),
            "is_safe_margin": gap <= 0,
            "recent_delta": round(float(recent_delta), 2),
            "recent_direction": recent_direction,
            "trend_summary": (
                f"Recent district-adjusted movement is {recent_direction} ({recent_delta:+.2f} points across the shown years); "
                f"human/social signal: {social_effect}. National reference in {selected_year}: {national_val:.1f}."
            ),
            "plan_summary": (
                f"Near-future target for {district_name}: {plan_action} over {timeframe} years. "
                f"MVT share {share * 100:.1f}%, PID multiplier {multiplier:.2f}x."
            ),
            "natural_language": (
                f"District micro view for {district_name}: {indicator_display_name(col)} is adjusted from the national {selected_year} value "
                f"using the district score factor ({district_factor:.2f}x)."
            ),
            "history": hist,
        })
    return indicators

def get_district_score(district_name, division_name, national_score):
    btrc = BTRC_DIVISION_DATA.get(division_name, {"4g_pct": 25.0})
    div_modifier = (btrc["4g_pct"] - 30) / 100
    dist_modifier = DISTRICT_MODIFIERS.get(district_name, 0)
    return round(min(100, max(0, national_score + (div_modifier * 20) + (dist_modifier * 30))), 2)
