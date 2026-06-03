from __future__ import annotations
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from classification.training_data import TONNAGE_SAMPLES, CARGO_VC_SAMPLES, CARGO_TC_SAMPLES

# ── Confidence threshold below which we fall back to keyword rules ──────────
CONFIDENCE_THRESHOLD = 0.55

# ── Keyword rule sets (based on real shipping email patterns) ────────────────
TONNAGE_KEYWORDS = [
    r'\bopen\s+[a-z]', r'\bdwt\b', r'\bbuilt\s*\d{4}', r'\bblt\s*\d{4}',
    r'\bloa\b', r'\beeta\b', r'\bscrubber\b', r'\bspeed.{0,20}cons',
    r'\bballast\b', r'\bbeam\b', r'\bgrain\s*cap', r'\bflag\b.*\bclass\b',
    r'\bopen\s+vessel', r'\bvessel\s+position', r'\bour\s+direct\s+ow',
    r'\bopen\s+as\s+follows', r'\bdirect\s+ow', r'o/a\s+\d',
]
CARGO_VC_KEYWORDS = [
    r'\bload\s*port\b', r'\bdischarge\s*port\b', r'\blaycan\b',
    r'\bpol\b', r'\bpod\b', r'\bfios\b', r'\bpwwd\b', r'\bsshex\b',
    r'\blp\s*:', r'\bdp\s*:', r'\bload\s*rate\b', r'\bvoyage\s*charter\b',
    r'\bmts\b.*\b(?:bulk|coal|grain|ore|cargo)\b',
    r'\bcargo.*(?:port|laycan)', r'(?:discharge|load).*laycan',
]
CARGO_TC_KEYWORDS = [
    r'\btime\s*charter\b', r'\btct\b', r'\bdely\b', r'\bdelivery\b.*\bredelivery\b',
    r'\bduration\s+abt\b', r'\bredel\b', r'\bredelivery\b', r'\bhire\b',
    r'1\s*tct\s*with', r'\bdelivery\b.*\blaycan\b', r'\bperiod\b.*\bdelivery\b',
    r'\b1[-–]\d+\s*years?\b', r'\bflat\s*or\s*index\b',
]

# ── Global pipeline instance ─────────────────────────────────────────────────
_pipeline: Pipeline | None = None


def _build_and_train():
    global _pipeline
    X = TONNAGE_SAMPLES + CARGO_VC_SAMPLES + CARGO_TC_SAMPLES
    y = (
        ["tonnage"] * len(TONNAGE_SAMPLES)
        + ["cargo_vc"] * len(CARGO_VC_SAMPLES)
        + ["cargo_tc"] * len(CARGO_TC_SAMPLES)
    )
    _pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 3),
            max_features=8000,
            sublinear_tf=True,
            min_df=1,
        )),
        ("clf", LogisticRegression(
            max_iter=1000,
            C=2.0,
            solver="lbfgs",
        )),
    ])
    _pipeline.fit(X, y)


def _keyword_classify(text: str) -> str | None:
    t = text.lower()
    scores = {
        "tonnage": sum(1 for p in TONNAGE_KEYWORDS if re.search(p, t)),
        "cargo_vc": sum(1 for p in CARGO_VC_KEYWORDS if re.search(p, t)),
        "cargo_tc": sum(1 for p in CARGO_TC_KEYWORDS if re.search(p, t)),
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "unknown"


def classify(text: str) -> tuple[str, float]:
    """Return (category, confidence).  Category is one of:
    'tonnage' | 'cargo_vc' | 'cargo_tc' | 'unknown'
    """
    global _pipeline
    if _pipeline is None:
        _build_and_train()

    clean = text.upper()
    proba = _pipeline.predict_proba([clean])[0]
    classes = _pipeline.classes_
    best_idx = proba.argmax()
    confidence = float(proba[best_idx])
    label = classes[best_idx]

    if confidence < CONFIDENCE_THRESHOLD:
        kw_label = _keyword_classify(text)
        return kw_label, confidence

    return label, confidence


# Initialise on import so first request is fast
_build_and_train()
