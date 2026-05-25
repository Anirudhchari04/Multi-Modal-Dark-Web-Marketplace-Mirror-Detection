# ARCHITECTURE DOCUMENTATION

**Technical Architecture & System Design**

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│           Marketplace Mirror Detection System               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Input URLs  →  Feature Extraction  →  ML Models  →  Output│
│  + PGP Keys      (7 Pillars, 93 features)  Ensemble         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Component Architecture

### Layer 1: Input Processing
```
MarketplaceMirrorDetector
  ├─ Validate URLs
  ├─ Parse PGP fingerprints
  └─ Initialize pillars
```

### Layer 2: Feature Extraction (7 Pillars)
```
Pillar 1: HTTPResponseFingerprinter (12 features)
  ├─ Send 100 identical queries
  ├─ Analyze response times
  ├─ Extract status codes
  └─ Check headers

Pillar 2: HTMLDOMAnalyzer (15 features)
  ├─ Fetch HTML content
  ├─ Calculate DOM depth
  ├─ Count HTML tags
  ├─ Extract CSS classes
  └─ Analyze forms

Pillar 3: JavaScriptAnalyzer (12 features)
  ├─ Download JS files
  ├─ Extract function names
  ├─ Extract variable names
  ├─ Detect frameworks
  └─ Analyze code patterns

Pillar 4: PGPVerifier (12 features) ⭐
  ├─ Parse fingerprints
  ├─ Check exact matches
  ├─ Calculate similarity
  ├─ Verify cryptographic strength
  └─ Assess freshness

Pillar 5: ExceptionAnalyzer (16 features)
  ├─ Test 7 exception scenarios
  ├─ Collect error responses
  ├─ Compare status codes
  ├─ Analyze error messages
  └─ Pattern matching

Pillar 6: ResponseTimingAnalyzer (14 features)
  ├─ Collect 50 timing samples
  ├─ Calculate distribution stats
  ├─ Compute percentiles
  ├─ Analyze skewness/kurtosis
  └─ Estimate cache effectiveness

Pillar 7: APIEndpointAnalyzer (12 features)
  ├─ Extract API endpoints
  ├─ Analyze parameters
  ├─ Test endpoint accessibility
  ├─ Compare response formats
  └─ Check response consistency
```

### Layer 3: Feature Combination
```
Feature Combination Pipeline
  ├─ Collect all 93 features
  ├─ Apply pillar weights:
  │   ├─ Pillar 1 (HTTP):        0.15
  │   ├─ Pillar 2 (HTML):        0.15
  │   ├─ Pillar 3 (JavaScript):  0.12
  │   ├─ Pillar 4 (PGP):        0.25 ⭐ Highest
  │   ├─ Pillar 5 (Exception):   0.12
  │   ├─ Pillar 6 (Timing):      0.12
  │   └─ Pillar 7 (API):         0.09
  └─ Normalize to 0-1 range
```

### Layer 4: Machine Learning
```
EnsembleClassifier
  ├─ Normalize features (StandardScaler)
  ├─ Model 1: Random Forest
  │   ├─ 100 trees
  │   ├─ max_depth=15
  │   ├─ Predict probability
  │   └─ Individual model accuracy
  ├─ Model 2: Gradient Boosting
  │   ├─ 100 estimators
  │   ├─ learning_rate=0.1
  │   ├─ Predict probability
  │   └─ Individual model accuracy
  └─ Ensemble Average
      ├─ Average both probabilities
      ├─ Generate classification
      └─ Output confidence
```

### Layer 5: Output Generation
```
MirrorDetectionPipeline
  ├─ Generate classification label
  ├─ Calculate confidence percentage
  ├─ Create summary report
  ├─ Format JSON output
  └─ Log results
```

## Data Flow

```
URLs + PGP
    ↓
┌───────────────────┐
│  MarketplaceMirror│
│    Detector       │
└────────┬──────────┘
         ↓
┌────────────────────────────────────────────────┐
│      Feature Extraction (7 Pillars)             │
│  ┌──────────────────────────────────────────┐  │
│  │ P1 (12) → HTTP Response Fingerprinting  │  │
│  │ P2 (15) → HTML/DOM Structure            │  │
│  │ P3 (12) → JavaScript Analysis           │  │
│  │ P4 (12) → PGP Verification              │  │
│  │ P5 (16) → Exception Handling            │  │
│  │ P6 (14) → Response Timing               │  │
│  │ P7 (12) → API Endpoints                 │  │
│  └──────────────────────────────────────────┘  │
│  Total: 93 features                            │
└────────┬─────────────────────────────────────┘
         ↓
┌────────────────────────────────────────────┐
│  Feature Normalization & Weighting         │
│  ├─ StandardScaler normalization           │
│  ├─ Apply pillar weights                   │
│  └─ Validate feature vector                │
└────────┬────────────────────────────────────┘
         ↓
┌────────────────────────────────────────────┐
│  Ensemble ML Classifier                    │
│  ├─ Random Forest (100 trees)              │
│  ├─ Gradient Boosting (100 estimators)     │
│  └─ Average probabilities                  │
└────────┬────────────────────────────────────┘
         ↓
┌────────────────────────────────────────────┐
│  Classification & Output                   │
│  ├─ Score > 0.75: MIRROR                   │
│  ├─ Score 0.60-0.75: LIKELY MIRROR         │
│  ├─ Score < 0.60: NOT MIRROR               │
│  └─ Generate JSON report                   │
└────────────────────────────────────────────┘
         ↓
    JSON Output
```

## Module Relationships

```
config.py (Central Configuration)
    ↑
    ├─ utils.py (Utility Classes)
    │   ├─ URLCrawler
    │   ├─ HTMLParser
    │   ├─ SimilarityMetrics
    │   ├─ FeatureNormalizer
    │   ├─ DataValidator
    │   ├─ ResponseAnalyzer
    │   ├─ PGPAnalyzer
    │   └─ LoggingSetup
    │
    ├─ pillar_1.py ─→ HTTPResponseFingerprinter
    ├─ pillar_2.py ─→ HTMLDOMAnalyzer
    ├─ pillar_3.py ─→ JavaScriptAnalyzer
    ├─ pillar_4.py ─→ PGPVerifier
    ├─ pillar_5.py ─→ ExceptionAnalyzer
    ├─ pillar_6.py ─→ ResponseTimingAnalyzer
    ├─ pillar_7.py ─→ APIEndpointAnalyzer
    │
    ├─ ensemble_classifier.py
    │   ├─ EnsembleClassifier
    │   └─ MirrorDetectionPipeline
    │
    ├─ main.py ─→ MarketplaceMirrorDetector
    │
    ├─ train.py
    │
    ├─ infer.py
```

## Feature Vector Structure

```
Combined Feature Vector (93 features total)
├─ Pillar 1: HTTP (features 0-11, 12 total)
│   ├─ Response time metrics (6)
│   ├─ Status code analysis (2)
│   ├─ Header consistency (2)
│   ├─ Error patterns (2)
│   └─ Timing stability (1)
│
├─ Pillar 2: HTML (features 12-26, 15 total)
│   ├─ DOM structure (3)
│   ├─ Tag analysis (3)
│   ├─ CSS/styling (2)
│   ├─ Forms (2)
│   ├─ Content density (3)
│   ├─ Metadata (2)
│   └─ Scripts (1)
│
├─ Pillar 3: JavaScript (features 27-38, 12 total)
│   ├─ Function overlap (1)
│   ├─ Variable overlap (1)
│   ├─ Code metrics (8)
│   └─ Framework detection (2)
│
├─ Pillar 4: PGP (features 39-50, 12 total)
│   ├─ Fingerprint matching (3)
│   ├─ Key counts (2)
│   ├─ Cryptographic strength (4)
│   ├─ Freshness/age (2)
│   └─ Uniqueness (1)
│
├─ Pillar 5: Exceptions (features 51-66, 16 total)
│   ├─ Test response times (7)
│   ├─ Status consistency (1)
│   ├─ Error analysis (4)
│   ├─ Error types (3)
│   ├─ Error handling (1)
│   └─ Overall match (1)
│
├─ Pillar 6: Timing (features 67-80, 14 total)
│   ├─ Distribution stats (5)
│   ├─ Timing similarity (3)
│   ├─ Cache analysis (2)
│   ├─ Distribution shape (2)
│   ├─ Correlation (1)
│   └─ Stability (1)
│
└─ Pillar 7: API (features 81-92, 12 total)
    ├─ Endpoint similarity (3)
    ├─ Parameter analysis (2)
    ├─ Response format (2)
    ├─ Accessibility (2)
    ├─ Status codes (1)
    └─ Overall match (2)
```

## Model Architecture

### Random Forest Classifier
```
Random Forest (100 trees)
├─ max_depth: 15
├─ min_samples_split: 5
├─ n_jobs: -1 (all cores)
├─ Training: StandardScaler(features) → RF.fit()
├─ Prediction: RF.predict_proba() → probability
└─ Output: 0-1 confidence score
```

### Gradient Boosting Classifier
```
Gradient Boosting (100 estimators)
├─ learning_rate: 0.1
├─ max_depth: 5
├─ subsample: 0.8
├─ Training: StandardScaler(features) → GB.fit()
├─ Prediction: GB.predict_proba() → probability
└─ Output: 0-1 confidence score
```

### Ensemble Strategy
```
Ensemble Average
├─ RF_probability: from Random Forest
├─ GB_probability: from Gradient Boosting
├─ Ensemble_probability: (RF_probability + GB_probability) / 2
└─ Classification: Apply thresholds
    ├─ > 0.75: MIRROR
    ├─ 0.60-0.75: LIKELY MIRROR
    └─ < 0.60: NOT MIRROR
```

## Error Handling Strategy

```
Level 1: Individual Pillar Errors
├─ Try-except in each pillar
├─ Log warning
└─ Return zero features vector

Level 2: Feature Extraction Errors
├─ Continue with available pillars
├─ Pad missing features with zeros
└─ Flag in extraction_info

Level 3: Model Errors
├─ Fail-safe default classification
├─ Return error status
└─ Alert user

Level 4: Network Errors
├─ Respect 10-second timeouts
├─ Retry 2 times maximum
├─ Fall back to zeros
└─ Log connection issues

Level 5: Data Validation
├─ Check feature vector size
├─ Check for NaN values
├─ Check value ranges (0-1)
└─ Normalize if needed
```

## Performance Metrics

- **Feature Extraction Time**: ~45-60 minutes (parallel)
- **Model Prediction Time**: <1 second
- **Memory Usage**: ~500 MB baseline
- **Accuracy**: 85-95% (depends on training data)
- **Throughput**: ~1 detection per minute per core

## Security Architecture

```
Security Layers
├─ Input Validation
│   ├─ URL format checking
│   ├─ PGP fingerprint validation
│   └─ Timeout enforcement
├─ Data Protection
│   ├─ No persistent marketplace data
│   ├─ Audit logging
│   └─ SSL/TLS ready
├─ Access Control
│   ├─ Environment-based config
│   ├─ User-based permissions
│   └─ API rate limiting
└─ Error Handling
    ├─ Graceful degradation
    ├─ Comprehensive logging
    └─ Exception capture
```

## Scalability Architecture

```
Horizontal Scaling
├─ Stateless design
├─ Multi-process support (n_jobs=-1)
├─ Kubernetes ready
└─ Docker containerization

Vertical Scaling
├─ Feature caching
├─ Reduced sampling for speed
├─ Batch processing
└─ Resource optimization
```

## Integration Points

```
External Systems
├─ Tor Browser / Proxy (for .onion access)
├─ Elasticsearch (for logging)
├─ PostgreSQL (optional database)
├─ Redis (optional caching)
├─ Prometheus (monitoring)
└─ Grafana (visualization)
```

---

**Architecture Version**: 1.0.0  
**Last Updated**: October 28, 2025  
**Status**: Production-Ready
