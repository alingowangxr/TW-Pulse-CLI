"""
SAPTA Feature Importance Analysis.

Analyzes and displays feature importance from trained SAPTA model.
"""

import json
from pathlib import Path
from typing import Any

from pulse.utils.logger import get_logger

log = get_logger(__name__)


# Module descriptions for better understanding
MODULE_DESCRIPTIONS = {
    "absorption": "Supply Absorption - Smart money accumulation detection",
    "compression": "Compression - Volatility contraction analysis",
    "bb_squeeze": "BB Squeeze - Bollinger Band squeeze detection",
    "elliott": "Elliott Wave - Wave position and Fibonacci analysis",
    "time_projection": "Time Projection - Fibonacci time windows",
    "anti_distribution": "Anti-Distribution - Distribution pattern filtering",
}

# Feature descriptions
FEATURE_DESCRIPTIONS = {
    # Absorption
    "absorption_score": "Raw absorption module score (0-20)",
    "absorption_score_pct": "Absorption score as percentage of max",
    "absorption_volume_spike_ratio": "Volume vs average volume ratio",
    "absorption_price_held": "Price held above key level percentage",
    "absorption_higher_lows_count": "Number of consecutive higher lows",
    "absorption_avg_close_strength": "Average close position (0-1, higher = stronger)",
    # Compression
    "compression_score": "Raw compression module score (0-15)",
    "compression_score_pct": "Compression score as percentage of max",
    "compression_atr_slope": "ATR change slope (negative = contracting)",
    "compression_range_contraction": "Price range contraction ratio",
    "compression_higher_lows": "Higher lows indicator (1=yes, 0=no)",
    "compression_lower_highs": "Lower highs indicator (1=yes, 0=no)",
    "compression_avg_body_ratio": "Average candlestick body ratio",
    # BB Squeeze
    "bb_squeeze_score": "Raw BB squeeze module score (0-15)",
    "bb_squeeze_score_pct": "BB squeeze score as percentage of max",
    "bb_squeeze_bb_width_current": "Current BB width value",
    "bb_squeeze_bb_width_percentile": "BB width percentile (lower = tighter)",
    "bb_squeeze_squeeze_duration": "Number of candles in squeeze",
    "bb_squeeze_price_position_in_bb": "Price position in BB (0-1)",
    # Elliott
    "elliott_score": "Raw Elliott module score (0-20)",
    "elliott_score_pct": "Elliott score as percentage of max",
    "elliott_fib_retracement": "Fibonacci retracement level",
    "elliott_trend_context": "Trend context (encoded)",
    "elliott_abc_pattern": "ABC pattern detected (0-1)",
    "elliott_rule_violations": "Number of Elliott rule violations",
    "elliott_rsi_divergence": "RSI divergence detected",
    # Time Projection
    "time_projection_score": "Raw time projection score (0-15)",
    "time_projection_score_pct": "Time score as percentage of max",
    "time_projection_days_since_low": "Days since recent low",
    "time_projection_in_fib_window": "In Fibonacci time window (0-1)",
    "time_projection_lunar_phase": "Lunar phase alignment",
    # Anti-Distribution
    "anti_distribution_score": "Raw anti-distribution score (0-15)",
    "anti_distribution_score_pct": "Anti-dist score as percentage of max",
    "anti_distribution_distribution_candles": "Distribution candle count",
    "anti_distribution_false_breakout": "False breakout ratio",
    "anti_distribution_obv_divergence": "OBV price divergence type",
    # Aggregate
    "total_score": "Sum of all module raw scores (0-100)",
    "weighted_score": "Weighted sum of module scores",
    "modules_active": "Number of modules with positive score",
    "penalty_score": "Penalty score from failed modules",
}


def load_model_data() -> dict[str, Any] | None:
    """Load trained model data."""
    model_dir = Path(__file__).parent

    model_path = model_dir / "sapta_model.pkl"
    thresholds_path = model_dir / "thresholds.json"

    if not model_path.exists():
        log.warning("Model not found. Run /sapta-retrain first.")
        return None

    data = {}

    # Load thresholds
    if thresholds_path.exists():
        with open(thresholds_path) as f:
            data["thresholds"] = json.load(f)
    else:
        data["thresholds"] = None

    return data


def get_feature_importance() -> dict[str, float] | None:
    """Get feature importance from model."""
    try:
        import joblib

        model_dir = Path(__file__).parent
        model_path = model_dir / "sapta_model.pkl"

        if not model_path.exists():
            return None

        model = joblib.load(model_path)

        # Get feature names
        from pulse.core.sapta.ml.features import SaptaFeatureExtractor

        extractor = SaptaFeatureExtractor()
        feature_names = extractor.feature_names

        # Get importance
        if hasattr(model, "feature_importances_"):
            importance = dict(zip(feature_names, model.feature_importances_))
            return importance

        return None
    except Exception as e:
        log.error(f"Error loading feature importance: {e}")
        return None


def analyze_feature_importance(importance: dict[str, float]) -> dict[str, Any]:
    """Analyze feature importance and group by module."""
    # Sort by importance
    sorted_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)

    # Group by module
    module_features: dict[str, list[dict]] = {}

    for feature, score in sorted_features:
        # Extract module name from feature
        parts = feature.split("_")
        if parts[0] in MODULE_DESCRIPTIONS:
            module = parts[0]
        elif feature in ["total_score", "weighted_score", "modules_active", "penalty_score"]:
            module = "aggregate"
        else:
            module = "other"

        if module not in module_features:
            module_features[module] = []

        module_features[module].append(
            {
                "feature": feature,
                "importance": float(score),
                "description": FEATURE_DESCRIPTIONS.get(feature, "No description"),
            }
        )

    # Calculate module totals
    module_totals: dict[str, float] = {}
    for module, features in module_features.items():
        module_totals[module] = sum(f["importance"] for f in features)

    # Sort modules by total importance
    sorted_modules = sorted(module_totals.items(), key=lambda x: x[1], reverse=True)

    return {
        "top_features": sorted_features[:15],
        "module_features": module_features,
        "module_totals": dict(sorted_modules),
        "total_features": len(sorted_features),
    }


def format_feature_importance_report(analysis: dict[str, Any]) -> str:
    """Format feature importance analysis as a report."""
    lines = []
    lines.append("=" * 60)
    lines.append("SAPTA Feature Importance Analysis")
    lines.append("=" * 60)
    lines.append("")

    # Top features
    lines.append("📊 TOP 15 MOST IMPORTANT FEATURES")
    lines.append("-" * 60)
    for i, (feature, importance) in enumerate(analysis["top_features"], 1):
        desc = FEATURE_DESCRIPTIONS.get(feature, "")
        lines.append(f"{i:2}. {feature:<40} {importance:.4f}")
        if desc:
            lines.append(f"    └─ {desc[:50]}")
    lines.append("")

    # Module breakdown
    lines.append("📦 FEATURE IMPORTANCE BY MODULE")
    lines.append("-" * 60)
    for module, total in analysis["module_totals"].items():
        module_name = MODULE_DESCRIPTIONS.get(module, module.title())
        lines.append(f"{module_name:<25} {total:.4f} ({total * 100:.1f}%)")

        # Show top 3 features per module
        if module in analysis["module_features"]:
            features = analysis["module_features"][module][:3]
            for f in features:
                lines.append(f"  ├─ {f['feature']:<23} {f['importance']:.4f}")
    lines.append("")

    # Recommendations
    lines.append("💡 OPTIMIZATION RECOMMENDATIONS")
    lines.append("-" * 60)

    # Find low importance features
    low_importance = [f for f in analysis["top_features"] if f[1] < 0.01]

    if low_importance:
        lines.append("Low importance features (consider removing):")
        for feature, importance in low_importance[:5]:
            lines.append(f"  - {feature} ({importance:.4f})")

    # Find high importance features
    high_importance = [f for f in analysis["top_features"] if f[1] > 0.05]

    if high_importance:
        lines.append("\nHigh importance features (focus on these):")
        for feature, importance in high_importance[:5]:
            lines.append(f"  - {feature} ({importance:.4f})")

    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)


def analyze_thresholds(thresholds: dict[str, float]) -> str:
    """Analyze current thresholds and provide recommendations."""
    lines = []
    lines.append("=" * 60)
    lines.append("SAPTA Threshold Analysis")
    lines.append("=" * 60)
    lines.append("")

    # Current thresholds
    lines.append("📌 CURRENT THRESHOLDS")
    lines.append("-" * 60)
    lines.append(f"PRE-MARKUP (準備突破):   score >= {thresholds.get('pre_markup', 0):.1f}")
    lines.append(f"SIAP (接近突破):        score >= {thresholds.get('siap', 0):.1f}")
    lines.append(f"WATCHLIST (觀察中):     score >= {thresholds.get('watchlist', 0):.1f}")
    lines.append("")

    # Score ranges
    premarkup_min = thresholds.get("pre_markup", 80)
    siap_min = thresholds.get("siap", 60)
    watchlist_min = thresholds.get("watchlist", 40)

    lines.append("📏 SCORE RANGES")
    lines.append("-" * 60)
    lines.append(
        f"PRE-MARKUP zone:  {premarkup_min:.1f} - 100.0 ({(100 - premarkup_min):.1f} range)"
    )
    lines.append(
        f"SIAP zone:        {siap_min:.1f} - {premarkup_min:.1f} ({(premarkup_min - siap_min):.1f} range)"
    )
    lines.append(
        f"WATCHLIST zone:   {watchlist_min:.1f} - {siap_min:.1f} ({(siap_min - watchlist_min):.1f} range)"
    )
    lines.append(f"SKIP zone:        0 - {watchlist_min:.1f} ({watchlist_min:.1f} range)")
    lines.append("")

    # Balance check
    premarkup_range = 100 - premarkup_min
    siap_range = premarkup_min - siap_min
    watchlist_range = siap_min - watchlist_min

    lines.append("⚖️ BALANCE ANALYSIS")
    lines.append("-" * 60)

    if premarkup_range < 10:
        lines.append("⚠️  PRE-MARKUP zone is very tight (<10 range)")
        lines.append("    Consider lowering pre_markup threshold")
    elif premarkup_range > 30:
        lines.append("ℹ️  PRE-MARKUP zone is wide (>30 range)")
        lines.append("    Consider raising pre_markup threshold")

    if watchlist_range > 30:
        lines.append("ℹ️  WATCHLIST zone is very wide (>30 range)")
        lines.append("    Consider lowering watchlist threshold")

    lines.append("")

    # Recommendations
    lines.append("🎯 RECOMMENDATIONS")
    lines.append("-" * 60)

    if premarkup_range < 15:
        lines.append("1. Lower PRE-MARKUP threshold by 5-10 points")
        lines.append("   Example: --target-gain 12 for wider distribution")

    if watchlist_range > 40:
        lines.append("2. Raise WATCHLIST threshold by 10-15 points")
        lines.append("   This reduces noise in watchlist")

    if abs(siap_range - watchlist_range) > 20:
        lines.append("3. Balance SIAP and WATCHLIST zones")
        lines.append("   Ideal: similar ranges for both zones")

    lines.append("")
    lines.append("💡 Use /sapta-retrain --walk-forward to optimize thresholds")
    lines.append("=" * 60)

    return "\n".join(lines)


# Run analysis if executed directly
if __name__ == "__main__":
    importance = get_feature_importance()
    if importance:
        analysis = analyze_feature_importance(importance)
        print(format_feature_importance_report(analysis))

        data = load_model_data()
        if data and data["thresholds"]:
            print("\n")
            print(analyze_thresholds(data["thresholds"]))
    else:
        print("No trained model found. Run /sapta-retrain first.")
