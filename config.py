"""
Configuration Module for Darknet Marketplace Mirror Detection System
Centralized settings for all pillars, ML models, and system parameters
"""

import logging
import os
from pathlib import Path

# =============================================================================
# SYSTEM CONFIGURATION
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.absolute()
LOG_LEVEL = logging.INFO  # Set to DEBUG for verbose output
LOG_FILE = os.path.join(PROJECT_ROOT, "mirror_detection.log")

# =============================================================================
# NETWORK & TIMEOUT SETTINGS
# =============================================================================

HTTP_TIMEOUT = 10  # Seconds - prevents hanging on unreachable Tor sites
HTTP_QUERIES_COUNT = 10  # Reduced for real Tor network speed
TIMING_SAMPLES = 10  # Reduced for real Tor network speed
MAX_RETRIES = 3  # Increased for Tor network instability
CONNECTION_TIMEOUT = 10  # Increased for Tor

# =============================================================================
# TOR CONFIGURATION
# =============================================================================

USE_TOR = True  # Enable Tor proxying for .onion URLs
TOR_PROXY_HOST = "127.0.0.1"
TOR_PROXY_PORT = 9150
TOR_SOCKS_URL = f"socks5h://{TOR_PROXY_HOST}:{TOR_PROXY_PORT}"

PROXIES = {
    'http': TOR_SOCKS_URL,
    'https': TOR_SOCKS_URL
}

# =============================================================================
# FEATURE COUNTS BY PILLAR
# =============================================================================

PILLAR_1_FEATURES = 12  # HTTP Response Fingerprinting
PILLAR_2_FEATURES = 15  # HTML/DOM Structure Analysis
PILLAR_3_FEATURES = 12  # JavaScript Code Analysis
PILLAR_4_FEATURES = 12  # PGP Cryptographic Verification
PILLAR_5_FEATURES = 16  # Exception Handling Fingerprinting
PILLAR_6_FEATURES = 14  # Response Timing Analysis
PILLAR_7_FEATURES = 12  # API Endpoint Analysis

TOTAL_FEATURES = (
    PILLAR_1_FEATURES + PILLAR_2_FEATURES + PILLAR_3_FEATURES +
    PILLAR_4_FEATURES + PILLAR_5_FEATURES + PILLAR_6_FEATURES +
    PILLAR_7_FEATURES
)

# =============================================================================
# PILLAR WEIGHTS (Must sum to 1.0)
# =============================================================================

PILLAR_WEIGHTS = {
    "pillar_1_http": 0.15,          # HTTP Response Fingerprinting
    "pillar_2_html": 0.15,          # HTML/DOM Structure
    "pillar_3_javascript": 0.12,    # JavaScript Analysis
    "pillar_4_pgp": 0.25,           # PGP (Highest - Most Reliable)
    "pillar_5_exceptions": 0.12,    # Exception Handling
    "pillar_6_timing": 0.12,        # Response Timing
    "pillar_7_api": 0.09            # API Endpoints
}

# Verify weights sum to 1.0
assert abs(sum(PILLAR_WEIGHTS.values()) - 1.0) < 0.001, "Pillar weights must sum to 1.0"

# =============================================================================
# MACHINE LEARNING MODEL CONFIGURATION
# =============================================================================

# Random Forest Classifier
RF_N_ESTIMATORS = 100
RF_MAX_DEPTH = 15
RF_MIN_SAMPLES_SPLIT = 5
RF_RANDOM_STATE = 42
RF_N_JOBS = -1  # Use all cores

# Gradient Boosting Classifier
GB_N_ESTIMATORS = 100
GB_LEARNING_RATE = 0.1
GB_MAX_DEPTH = 5
GB_RANDOM_STATE = 42
GB_SUBSAMPLE = 0.8

# Training Configuration
TRAINING_TEST_SIZE = 0.2
TRAINING_RANDOM_STATE = 42
MIN_TRAINING_SAMPLES = 200

# =============================================================================
# CLASSIFICATION THRESHOLDS & OUTPUT
# =============================================================================

# Probability thresholds for classification
MIRROR_THRESHOLD_HIGH = 0.75      # > 0.75: "MIRROR (High Confidence)"
MIRROR_THRESHOLD_LOW = 0.60       # 0.60-0.75: "LIKELY MIRROR (Manual Review)"
# < 0.60: "NOT MIRROR"

# Classification labels
LABEL_MIRROR = "MIRROR (High Confidence)"
LABEL_LIKELY = "LIKELY MIRROR (Manual Review)"
LABEL_NOT_MIRROR = "NOT MIRROR"

# =============================================================================
# FEATURE VALIDATION THRESHOLDS
# =============================================================================

FEATURE_NAN_TOLERANCE = 0.1  # Tolerance for NaN values in feature vectors
MIN_VALID_FEATURES_RATIO = 0.8  # Minimum percentage of valid features

# =============================================================================
# SIMILARITY METRICS CONFIGURATION
# =============================================================================

LEVENSHTEIN_THRESHOLD = 0.8  # Strings above this similarity are considered matches
JACCARD_THRESHOLD = 0.6  # Jaccard similarity threshold
COSINE_THRESHOLD = 0.75  # Cosine similarity threshold

# =============================================================================
# ERROR RESPONSE CODES FOR EXCEPTION PILLAR
# =============================================================================

EXCEPTION_TESTS = [
    "empty_search",
    "sql_injection",
    "xss_payload",
    "special_characters",
    "unicode_payload",
    "extremely_long_input",
    "null_bytes"
]

# =============================================================================
# CACHE & PERFORMANCE SETTINGS
# =============================================================================

ENABLE_FEATURE_CACHE = True
CACHE_DIR = os.path.join(PROJECT_ROOT, ".cache")
FEATURE_CACHE_TTL = 3600  # Cache features for 1 hour

# =============================================================================
# MODEL PERSISTENCE
# =============================================================================

MODEL_DIR = os.path.join(PROJECT_ROOT, "models")
DEFAULT_MODEL_PATH = os.path.join(MODEL_DIR, "mirror_detector.pkl")
SCALER_PATH = os.path.join(MODEL_DIR, "feature_scaler.pkl")

# =============================================================================
# API CONFIGURATION (for Flask API server)
# =============================================================================

API_HOST = "0.0.0.0"
API_PORT = 8000
API_DEBUG = False
API_WORKERS = 4

# =============================================================================
# DATA VALIDATION PATTERNS
# =============================================================================

# URL validation
VALID_URL_SCHEMES = ("http://", "https://", ".onion")
MIN_URL_LENGTH = 5
MAX_URL_LENGTH = 500

# PGP Fingerprint validation
PGP_FINGERPRINT_REGEX = r"[A-F0-9]{40}|[A-F0-9]{64}"

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': LOG_FORMAT,
            'datefmt': LOG_DATE_FORMAT
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': LOG_LEVEL,
            'formatter': 'standard'
        },
        'file': {
            'class': 'logging.FileHandler',
            'level': LOG_LEVEL,
            'formatter': 'standard',
            'filename': LOG_FILE
        }
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': LOG_LEVEL
        }
    }
}

# =============================================================================
# FEATURE RANGES (for validation and normalization)
# =============================================================================

FEATURE_RANGES = {
    # Pillar 1: HTTP (12 features)
    "response_time_mean": (0, 60),
    "response_time_std": (0, 30),
    "response_time_p95": (0, 120),
    "response_time_p99": (0, 150),
    "status_code_mode": (100, 600),
    "status_code_variance": (0, 100),
    "server_header_consistency": (0, 1),
    "x_powered_by_presence": (0, 1),
    "x_powered_by_consistency": (0, 1),
    "error_rate": (0, 1),
    "timeout_rate": (0, 1),
    "variance_coefficient": (0, 1),
    
    # Pillar 2: HTML (15 features)
    "dom_depth_old": (0, 50),
    "dom_depth_new": (0, 50),
    "dom_depth_similarity": (0, 1),
    "tag_count_old": (0, 1000),
    "tag_count_new": (0, 1000),
    "tag_count_similarity": (0, 1),
    "tag_frequency_jaccard": (0, 1),
    "css_classes_jaccard": (0, 1),
    "form_similarity": (0, 1),
    "input_similarity": (0, 1),
    "header_consistency": (0, 1),
    "link_density": (0, 1),
    "image_density": (0, 1),
    "script_similarity": (0, 1),
    "meta_consistency": (0, 1),
}

# =============================================================================
# SUMMARY TEMPLATE
# =============================================================================

SUMMARY_TEMPLATE = """
===== MIRROR DETECTION REPORT =====
Old Marketplace: {old_marketplace}
New Marketplace: {new_marketplace}
Detection Time: {detection_time}

Overall Score: {final_score:.2%}
Classification: {classification}
Confidence: {confidence}%

Pillar Scores:
  HTTP: {pillar_1:.2%}
  HTML: {pillar_2:.2%}
  JavaScript: {pillar_3:.2%}
  PGP: {pillar_4:.2%}
  Exception: {pillar_5:.2%}
  Timing: {pillar_6:.2%}
  API: {pillar_7:.2%}

Recommendation: {recommendation}
====================================
"""

# Ensure models directory exists
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)
