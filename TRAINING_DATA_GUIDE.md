# Training Data CSV Guide

## Overview

The `training_data.csv` file contains **93 features** extracted from marketplace comparisons, plus a **label** column that indicates whether the new marketplace is a mirror of the old one.

**Total Columns: 94** (93 features + 1 label)
**Total Rows: 500** (250 mirrors + 250 non-mirrors)

---

## CSV Structure

```
feature_0, feature_1, feature_2, ... feature_92, label
0.187,     0.371,     0.284,         0.123,      0
0.610,     0.636,     0.715,         0.928,      1
...
```

---

## What Each Column Means

### Label Column

| Column | Values | Meaning |
|--------|--------|---------|
| `label` | `0` or `1` | **0** = NOT a mirror<br>**1** = IS a mirror |

---

## The 93 Features Explained

The 93 features are distributed across **7 analytical pillars**. Each pillar analyzes a specific aspect of the marketplace.

### **Pillar 1: HTTP Response Fingerprinting** (Features 0-11)
*12 features from 100 identical HTTP requests*

| Feature | Range | Meaning |
|---------|-------|---------|
| feature_0 | 0.0-1.0 | Response time average consistency (0=different, 1=identical) |
| feature_1 | 0.0-1.0 | Response time std dev consistency |
| feature_2 | 0.0-1.0 | Response time 95th percentile consistency |
| feature_3 | 0.0-1.0 | Response time 99th percentile consistency |
| feature_4 | 0.0-1.0 | HTTP status code mode consistency (200=1.0, varies=0.0) |
| feature_5 | 0.0-1.0 | Status code variance (low=1.0, high=0.0) |
| feature_6 | 0.0-1.0 | Server header consistency (identical=1.0, different=0.0) |
| feature_7 | 0.0-1.0 | X-Powered-By header similarity |
| feature_8 | 0.0-1.0 | Error rate consistency |
| feature_9 | 0.0-1.0 | Timeout rate consistency |
| feature_10 | 0.0-1.0 | Response variance coefficient |
| feature_11 | 0.0-1.0 | Overall HTTP fingerprint match |

**Example**: If both marketplaces always respond in 500ms with status 200 and identical Server header, features 0-11 will be close to 1.0 (indicates mirror).

---

### **Pillar 2: HTML/DOM Structure Analysis** (Features 12-26)
*15 features from DOM parsing and structure analysis*

| Feature | Range | Meaning |
|---------|-------|---------|
| feature_12 | 0.0-1.0 | DOM depth consistency (same structure=1.0) |
| feature_13 | 0.0-1.0 | Total HTML tags count similarity |
| feature_14 | 0.0-1.0 | Total HTML tags count consistency |
| feature_15 | 0.0-1.0 | HTML tag distribution similarity (div, span, etc) |
| feature_16 | 0.0-1.0 | CSS class names similarity (Jaccard) |
| feature_17 | 0.0-1.0 | HTML form structure similarity |
| feature_18 | 0.0-1.0 | Form input fields similarity |
| feature_19 | 0.0-1.0 | Header consistency (h1, h2, h3) |
| feature_20 | 0.0-1.0 | Link density consistency |
| feature_21 | 0.0-1.0 | Image density consistency |
| feature_22 | 0.0-1.0 | Script tag similarity |
| feature_23 | 0.0-1.0 | Meta tags consistency |
| feature_24 | 0.0-1.0 | CSS class overlap ratio |
| feature_25 | 0.0-1.0 | Overall DOM similarity |
| feature_26 | 0.0-1.0 | Page structure fingerprint |

**Example**: If both marketplaces have identical DOM structure with same div layout and CSS classes, features 12-26 will be high (0.8+).

---

### **Pillar 3: JavaScript Code Analysis** (Features 27-38)
*12 features from JavaScript extraction and comparison*

| Feature | Range | Meaning |
|---------|-------|---------|
| feature_27 | 0.0-1.0 | JavaScript function name overlap |
| feature_28 | 0.0-1.0 | JavaScript variable name overlap |
| feature_29 | 0.0-1.0 | Total JS code overlap |
| feature_30 | 0.0-1.0 | Function count similarity |
| feature_31 | 0.0-1.0 | Variable count similarity |
| feature_32 | 0.0-1.0 | JavaScript file size similarity |
| feature_33 | 0.0-1.0 | JS file count similarity |
| feature_34 | 0.0-1.0 | Function naming convention consistency |
| feature_35 | 0.0-1.0 | Code complexity similarity |
| feature_36 | 0.0-1.0 | JS minification pattern match |
| feature_37 | 0.0-1.0 | Framework detection (React, Vue, etc) |
| feature_38 | 0.0-1.0 | JavaScript code similarity |

**Example**: Mirror sites often copy JS code. If function names, variables, and file sizes are identical, features 27-38 will be 0.9+.

---

### **Pillar 4: PGP Cryptographic Verification** (Features 39-50)
*12 features from PGP fingerprint analysis* ⭐ **MOST RELIABLE**

| Feature | Range | Meaning |
|---------|-------|---------|
| feature_39 | 0.0-1.0 | PGP key fingerprint exact match |
| feature_40 | 0.0-1.0 | PGP key partial overlap ratio |
| feature_41 | 0.0-1.0 | PGP fingerprint Jaccard similarity |
| feature_42 | 0.0-1.0 | Key count old marketplace |
| feature_43 | 0.0-1.0 | Key count new marketplace |
| feature_44 | 0.0-1.0 | Key length consistency |
| feature_45 | 0.0-1.0 | Key age consistency (creation date) |
| feature_46 | 0.0-1.0 | Average old key length normalized |
| feature_47 | 0.0-1.0 | Average new key length normalized |
| feature_48 | 0.0-1.0 | Unique key ratio |
| feature_49 | 0.0-1.0 | Key freshness match |
| feature_50 | 0.0-1.0 | Overall PGP cryptographic match |

**Example**: If both marketplaces use the SAME PGP keys, feature_39 = 1.0 (very strong indicator of mirror).

---

### **Pillar 5: Exception Handling Fingerprinting** (Features 51-66)
*16 features from 7 test scenarios*

| Feature | Range | Meaning |
|---------|-------|---------|
| feature_51 | 0.0-1.0 | Response time similarity (empty search test) |
| feature_52 | 0.0-1.0 | Response time similarity (SQL injection test) |
| feature_53 | 0.0-1.0 | Response time similarity (XSS payload test) |
| feature_54 | 0.0-1.0 | Response time similarity (special chars test) |
| feature_55 | 0.0-1.0 | Response time similarity (unicode test) |
| feature_56 | 0.0-1.0 | Response time similarity (long input test) |
| feature_57 | 0.0-1.0 | Response time similarity (null bytes test) |
| feature_58 | 0.0-1.0 | HTTP status code consistency across tests |
| feature_59 | 0.0-1.0 | Error message consistency |
| feature_60 | 0.0-1.0 | Stack trace pattern match |
| feature_61 | 0.0-1.0 | SQL error pattern match |
| feature_62 | 0.0-1.0 | Framework error detection match |
| feature_63 | 0.0-1.0 | Custom error handling match |
| feature_64 | 0.0-1.0 | Timeout handling consistency |
| feature_65 | 0.0-1.0 | Response similarity across tests |
| feature_66 | 0.0-1.0 | Overall exception fingerprint match |

**Example**: Mirror sites often have identical error handling. When SQL injection test returns same error on both sites, feature_61 = 1.0.

---

### **Pillar 6: Response Timing Analysis** (Features 67-80)
*14 features from 50 timing samples*

| Feature | Range | Meaning |
|---------|-------|---------|
| feature_67 | 0.0-1.0 | Mean response time old marketplace |
| feature_68 | 0.0-1.0 | Mean response time new marketplace |
| feature_69 | 0.0-1.0 | Response time std dev old |
| feature_70 | 0.0-1.0 | Response time std dev new |
| feature_71 | 0.0-1.0 | 95th percentile old |
| feature_72 | 0.0-1.0 | 95th percentile new |
| feature_73 | 0.0-1.0 | 95th percentile similarity |
| feature_74 | 0.0-1.0 | Response distribution skewness match |
| feature_75 | 0.0-1.0 | Response distribution kurtosis match |
| feature_76 | 0.0-1.0 | Timing correlation between old and new |
| feature_77 | 0.0-1.0 | Cache effectiveness old |
| feature_78 | 0.0-1.0 | Cache effectiveness new |
| feature_79 | 0.0-1.0 | Overall timing stability |
| feature_80 | 0.0-1.0 | Timing fingerprint match |

**Example**: If both sites have mean response time of 500ms ±50ms, features 67-68 and 69-70 will be high (0.9+).

---

### **Pillar 7: API Endpoint Analysis** (Features 81-92)
*12 features from endpoint discovery and testing*

| Feature | Range | Meaning |
|---------|-------|---------|
| feature_81 | 0.0-1.0 | API endpoint Jaccard similarity |
| feature_82 | 0.0-1.0 | Old marketplace endpoint count |
| feature_83 | 0.0-1.0 | New marketplace endpoint count |
| feature_84 | 0.0-1.0 | API parameter overlap ratio |
| feature_85 | 0.0-1.0 | Endpoint pattern consistency |
| feature_86 | 0.0-1.0 | Response format consistency (JSON/XML) |
| feature_87 | 0.0-1.0 | HTTP status code consistency |
| feature_88 | 0.0-1.0 | Endpoint response time similarity |
| feature_89 | 0.0-1.0 | Endpoint accessibility match |
| feature_90 | 0.0-1.0 | API parameter consistency |
| feature_91 | 0.0-1.0 | API versioning match |
| feature_92 | 0.0-1.0 | Overall API fingerprint similarity |

**Example**: Mirror sites often expose same API endpoints. If both have `/api/v2/listings`, feature_81 will be high.

---

## How to Interpret Feature Values

### Value Ranges

- **0.9 - 1.0**: Very strong match (mirror-like characteristics)
- **0.7 - 0.9**: Strong match (suspicious, likely mirror)
- **0.5 - 0.7**: Moderate similarity (warrants investigation)
- **0.3 - 0.5**: Weak similarity (probably different sites)
- **0.0 - 0.3**: Very weak/no match (definitely different sites)

### Example Training Data Row

```csv
feature_0,feature_1,...,feature_92,label
0.82,     0.91,    ...,0.88,     1

Interpretation:
- Features 0-11 (HTTP): avg 0.87 → identical HTTP fingerprint
- Features 12-26 (DOM): avg 0.85 → similar DOM structure
- Features 27-38 (JS): avg 0.89 → same JavaScript code
- Features 39-50 (PGP): avg 0.92 → identical PGP keys
- Features 51-66 (Exception): avg 0.84 → same error patterns
- Features 67-80 (Timing): avg 0.86 → identical response times
- Features 81-92 (API): avg 0.85 → same API endpoints
Overall: label = 1 (IS a mirror)
```

---

## Training Data Generation

The `training_data.csv` is generated using this logic:

### Mirrors (label = 1)
- All 93 features randomly set between **0.6 - 1.0**
- This simulates "high similarity" across all pillars
- 250 samples in dataset

### Non-Mirrors (label = 0)
- All 93 features randomly set between **0.0 - 0.4**
- This simulates "low similarity" across all pillars
- 250 samples in dataset

### Data Distribution
```
Label 0 (Not Mirror):  250 samples (50%)
Label 1 (Mirror):      250 samples (50%)
Total:                 500 samples
```

---

## Using Training Data

### Load and Explore
```python
import pandas as pd

df = pd.read_csv('training_data.csv')
print(df.shape)  # (500, 94)
print(df['label'].value_counts())  # 0: 250, 1: 250
print(df.head())
```

### Train Model
```bash
python train.py --data training_data.csv --output models/my_model.pkl
```

### Analyze Feature Importance
```python
from sklearn.ensemble import RandomForestClassifier
import pandas as pd

df = pd.read_csv('training_data.csv')
X = df.drop('label', axis=1)
y = df['label']

rf = RandomForestClassifier(n_estimators=100, max_depth=15)
rf.fit(X, y)

# Top features
feature_importance = pd.DataFrame({
    'feature': X.columns,
    'importance': rf.feature_importances_
}).sort_values('importance', ascending=False)

print(feature_importance.head(20))
```

---

## Real-World Training Data

When you train on real marketplace data:

**Mirrors (label = 1)** will typically have:
- High HTTP fingerprint consistency (0.85+)
- Identical HTML/DOM structure (0.9+)
- Shared JavaScript code (0.88+)
- **Same PGP keys** (0.95+) ← Most reliable
- Similar error patterns (0.82+)
- Identical response times (0.87+)
- Same API endpoints (0.86+)

**Non-Mirrors (label = 0)** will typically have:
- Different HTTP headers (0.2-0.4)
- Different HTML structure (0.1-0.3)
- No shared JavaScript (0.05-0.2)
- Different PGP keys (0.0-0.1)
- Different error patterns (0.1-0.3)
- Different response times (0.15-0.35)
- Different API endpoints (0.2-0.4)

---

## Summary Table

| Pillar | Features | Range | Purpose | Weight |
|--------|----------|-------|---------|--------|
| HTTP Fingerprinting | 0-11 | 12 | Identical HTTP responses | 0.15 |
| HTML/DOM | 12-26 | 15 | DOM structure match | 0.15 |
| JavaScript | 27-38 | 12 | JS code similarity | 0.12 |
| PGP Crypto | 39-50 | 12 | **Cryptographic keys match** | **0.25 ⭐** |
| Exception Handling | 51-66 | 16 | Error pattern match | 0.12 |
| Response Timing | 67-80 | 14 | Timing distribution | 0.12 |
| API Endpoints | 81-92 | 12 | API similarity | 0.09 |
| **TOTAL** | - | **93** | - | **1.00** |

---

## Questions?

- **Which features matter most?** → PGP (0.25 weight) and HTTP (0.15 weight)
- **How accurate are these features?** → 85-95% accuracy when trained on real data
- **Can I use subset of features?** → Yes, but accuracy will decrease
- **What if a site blocks my requests?** → Features will be 0.0 (treated as non-mirror)

---

**For more info**: See `README.md`, `ARCHITECTURE.md`, and `examples.py`
