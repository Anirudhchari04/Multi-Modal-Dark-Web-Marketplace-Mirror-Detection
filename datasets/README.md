# Datasets Folder

This folder contains all training, testing, and validation data for the mirror detection system.

## Folder Structure

```
datasets/
├── training/          # Training data (used to train models)
├── testing/           # Test data (used to evaluate model accuracy)
├── validation/        # Validation data (used for hyperparameter tuning)
├── raw/               # Raw data before processing
└── README.md          # This file
```

## Dataset Contents

### training/
- **Purpose**: Used to train the Random Forest and Gradient Boosting models
- **Format**: CSV with 93 features + 1 label column
- **Files**:
  - `training_data.csv` - Generated synthetic training data (500 samples)
  
**To train with this data**:
```bash
python train.py --data datasets/training/training_data.csv \
                --output models/mirror_detector.pkl
```

### testing/
- **Purpose**: Evaluate model performance on unseen data
- **Format**: CSV with same structure as training data
- **Use cases**: 
  - Test accuracy
  - Precision/Recall metrics
  - Confusion matrix

**To test**:
```bash
python examples.py  # Example 4 shows testing
```

### validation/
- **Purpose**: Hyperparameter tuning and model selection
- **Format**: CSV with same structure
- **Use cases**:
  - Cross-validation
  - Model selection
  - Parameter optimization

### raw/
- **Purpose**: Store raw data before feature extraction
- **Format**: URLs, HTML files, JavaScript files, etc.
- **Contents**:
  - Raw HTTP responses
  - HTML pages
  - JavaScript source files
  - PGP keys
  - Server headers

## Adding Your Own Data

### Option 1: Use Real Marketplace Data

```bash
# 1. Create CSV with same format as training_data.csv
# Columns: feature_0, feature_1, ..., feature_92, label

# 2. Place in appropriate folder
cp your_data.csv datasets/training/your_data.csv

# 3. Train model
python train.py --data datasets/training/your_data.csv \
                --output models/your_model.pkl

# 4. Test
python infer.py http://market1.onion http://market2.onion \
                 --model models/your_model.pkl
```

### Option 2: Generate Synthetic Data

```bash
python generate_test_data.py
# This will create datasets/training/training_data.csv automatically
```

### Option 3: Extract Features Manually

```python
from main import MarketplaceMirrorDetector
import csv

# Initialize
detector = MarketplaceMirrorDetector()

# Extract features for your marketplaces
features = detector.extract_all_features(
    "http://old.onion",
    "http://new.onion"
)

# Save to CSV
with open('datasets/training/custom_data.csv', 'w') as f:
    writer = csv.writer(f)
    writer.writerow(list(features.keys()) + ['label'])
    writer.writerow(list(features.values()) + [1])  # 1 if mirror, 0 if not
```

## File Format Specification

### CSV Structure

```
feature_0,feature_1,feature_2,...,feature_92,label
0.82,0.91,0.75,...,0.88,1
0.15,0.23,0.12,...,0.19,0
```

### Column Details

- **feature_0 to feature_92**: Float values between 0.0 and 1.0
  - Extracted from 7 analytical pillars
  - For details, see `TRAINING_DATA_GUIDE.md`
  
- **label**: Integer (0 or 1)
  - 0 = Not a mirror
  - 1 = Is a mirror

## Data Statistics

### Current training_data.csv

```
Total samples: 500
Mirrors (label=1): 250 (50%)
Non-mirrors (label=0): 250 (50%)
Features: 93
Feature range: 0.0 - 1.0
```

### Feature Distribution

Mirrors (label=1):
- All features: 0.6 - 1.0 (high similarity)
- Mean: ~0.8
- Indicates: Strong match across all pillars

Non-mirrors (label=0):
- All features: 0.0 - 0.4 (low similarity)
- Mean: ~0.2
- Indicates: Weak match across all pillars

## Working with Datasets

### Load Dataset

```python
import pandas as pd

df = pd.read_csv('datasets/training/training_data.csv')
print(df.shape)           # (500, 94)
print(df['label'].value_counts())  # Label distribution
print(df.describe())      # Statistics
```

### Split Dataset

```python
from sklearn.model_selection import train_test_split
import pandas as pd

df = pd.read_csv('datasets/training/training_data.csv')
X = df.drop('label', axis=1)
y = df['label']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Save splits
X_train.to_csv('datasets/training/X_train.csv', index=False)
y_train.to_csv('datasets/training/y_train.csv', index=False)
X_test.to_csv('datasets/testing/X_test.csv', index=False)
y_test.to_csv('datasets/testing/y_test.csv', index=False)
```

### Analyze Features

```python
import pandas as pd
import numpy as np

df = pd.read_csv('datasets/training/training_data.csv')

# Feature statistics by label
print(df.groupby('label').describe())

# Correlation with label
correlations = df.corr()['label'].sort_values(ascending=False)
print(correlations.head(20))  # Top 20 correlated features

# Feature importance (using Random Forest)
from sklearn.ensemble import RandomForestClassifier
X = df.drop('label', axis=1)
y = df['label']
rf = RandomForestClassifier(n_estimators=100)
rf.fit(X, y)
importance = pd.DataFrame({
    'feature': X.columns,
    'importance': rf.feature_importances_
}).sort_values('importance', ascending=False)
print(importance.head(20))
```

## Dataset Best Practices

### ✅ DO:
- Keep training, testing, validation data separate
- Use consistent feature ranges (0.0 - 1.0)
- Balance classes (50% mirrors, 50% non-mirrors)
- Document data source and collection date
- Version your datasets
- Use CSV format for portability

### ❌ DON'T:
- Mix training and testing data
- Use features outside 0.0-1.0 range
- Forget to label your data
- Lose track of data provenance
- Use outdated/stale data
- Change feature order without updating code

## Common Tasks

### Combine Multiple Datasets
```python
import pandas as pd

df1 = pd.read_csv('datasets/training/data1.csv')
df2 = pd.read_csv('datasets/training/data2.csv')
df3 = pd.read_csv('datasets/training/data3.csv')

combined = pd.concat([df1, df2, df3], ignore_index=True)
combined.to_csv('datasets/training/combined.csv', index=False)
```

### Verify Dataset Integrity
```python
import pandas as pd
import numpy as np

df = pd.read_csv('datasets/training/training_data.csv')

# Check for missing values
print(df.isnull().sum())

# Check feature ranges
for col in df.columns[:-1]:  # Skip label
    print(f"{col}: [{df[col].min()}, {df[col].max()}]")
    assert 0.0 <= df[col].min()
    assert df[col].max() <= 1.0

# Check label values
assert set(df['label'].unique()) == {0, 1}

print("✓ Dataset integrity verified")
```

### Create Balanced Dataset
```python
import pandas as pd

df = pd.read_csv('datasets/training/training_data.csv')

# Ensure equal mirrors and non-mirrors
mirrors = df[df['label'] == 1]
non_mirrors = df[df['label'] == 0]

min_samples = min(len(mirrors), len(non_mirrors))

balanced = pd.concat([
    mirrors.sample(n=min_samples, random_state=42),
    non_mirrors.sample(n=min_samples, random_state=42)
])

balanced = balanced.sample(frac=1).reset_index(drop=True)
balanced.to_csv('datasets/training/balanced.csv', index=False)
print(f"Created balanced dataset: {len(balanced)} samples")
```

## Troubleshooting

### Issue: "File not found"
```
Solution: Check that file is in correct subdirectory
datasets/training/training_data.csv  ← Correct
training_data.csv                   ← Wrong
```

### Issue: "Features out of range"
```python
# Solutions
import pandas as pd
df = pd.read_csv('datasets/training/your_data.csv')

# Clamp features to 0-1
df.loc[:, 'feature_0':'feature_92'] = df.loc[:, 'feature_0':'feature_92'].clip(0, 1)

# Save corrected data
df.to_csv('datasets/training/your_data_fixed.csv', index=False)
```

### Issue: "Unbalanced classes"
```python
# Resample to balance
import pandas as pd
df = pd.read_csv('datasets/training/your_data.csv')

mirrors = df[df['label'] == 1]
non_mirrors = df[df['label'] == 0]

if len(mirrors) > len(non_mirrors):
    mirrors = mirrors.sample(n=len(non_mirrors), random_state=42)
else:
    non_mirrors = non_mirrors.sample(n=len(mirrors), random_state=42)

balanced = pd.concat([mirrors, non_mirrors]).sample(frac=1)
balanced.to_csv('datasets/training/balanced.csv', index=False)
```

## Next Steps

1. **Explore the data**: `python examples.py`
2. **Read the guide**: `TRAINING_DATA_GUIDE.md`
3. **Train a model**: `python train.py --data datasets/training/training_data.csv`
4. **Add your data**: Place your CSV in appropriate folder
5. **Get advanced**: See `ARCHITECTURE.md` for feature extraction details

---

For questions about features: See `TRAINING_DATA_GUIDE.md`
For questions about training: See `README.md`
For questions about deployment: See `DEPLOYMENT.md`
