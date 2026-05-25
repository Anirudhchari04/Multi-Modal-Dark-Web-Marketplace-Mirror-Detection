# Darknet Marketplace Mirror Detection System - QUICKSTART

**Get up and running in 5 minutes!**

## 1. Installation (2 minutes)

```bash
# Navigate to project directory
cd darknet_mirror_detection

# Install dependencies
pip install -r requirements.txt
```

## 2. Generate Test Data (1 minute)

```bash
python generate_test_data.py
```

This creates:
- `training_data.csv` - 500 synthetic samples
- `test_urls.json` - Sample marketplace pairs
- Sample PGP key files

## 3. Train Model (1 minute)

```bash
# Using synthetic data (default)
python train.py --output models/mirror_detector.pkl

# Or with custom data
python train.py --data training_data.csv --output models/mirror_detector.pkl
```

## 4. Run Detection (1 minute)

```bash
# Basic usage
python infer.py http://market1.onion http://mirror1.onion

# With PGP fingerprints
python infer.py http://market1.onion http://mirror1.onion \
  --pgp-old "1234567890ABCDEF1234567890ABCDEF12345678" \
  --pgp-new "1234567890ABCDEF1234567890ABCDEF12345678" \
  --output result.json

# Check custom model
python infer.py http://market1.onion http://mirror1.onion \
  --model models/my_model.pkl
```

## Output Format

```json
{
  "old_marketplace": "http://market1.onion",
  "new_marketplace": "http://mirror1.onion",
  "final_mirror_score": 0.85,
  "classification": "MIRROR (High Confidence)",
  "confidence_percentage": 85,
  "pillar_scores": {
    "pillar_1": 0.82,
    "pillar_2": 0.88,
    "pillar_3": 0.79,
    "pillar_4": 0.91,
    "pillar_5": 0.84,
    "pillar_6": 0.81,
    "pillar_7": 0.78
  },
  "recommendation": "INVESTIGATE",
  "extraction_info": {
    "total_features_extracted": 93,
    "model_type": "Ensemble (RF + GB)",
    "status": "success"
  }
}
```

## Classification Thresholds

- **Score > 0.75**: "MIRROR (High Confidence)" → Immediate action
- **Score 0.60-0.75**: "LIKELY MIRROR (Manual Review)" → Investigation  
- **Score < 0.60**: "NOT MIRROR" → No action

## Common Tasks

### View Help
```bash
python infer.py --help
python train.py --help
```

### Run Examples
```bash
python examples.py
```

### Verbose Logging
```bash
python infer.py http://m1.onion http://m2.onion --verbose
```

### Batch Processing
```python
from main import MarketplaceMirrorDetector

detector = MarketplaceMirrorDetector("models/mirror_detector.pkl")

urls = [
    ("http://market1.onion", "http://mirror1.onion"),
    ("http://market2.onion", "http://mirror2.onion"),
]

for old, new in urls:
    result = detector.detect_mirror(old, new)
    print(result["classification"])
```

## Troubleshooting

### "Model not found" Error
```bash
python train.py --output models/mirror_detector.pkl
```

### Connection Timeouts
Edit `config.py`:
```python
HTTP_TIMEOUT = 15  # Increase from 10
```

### Memory Issues
Reduce `HTTP_QUERIES_COUNT` in `config.py`:
```python
HTTP_QUERIES_COUNT = 50  # Reduce from 100
```

### Feature Extraction Fails
Check logs: `mirror_detection.log`

```bash
cat mirror_detection.log
```

## Next Steps

- Read **README.md** for complete documentation
- Study **DEPLOYMENT.md** for production setup
- Review **ARCHITECTURE.md** for technical details
- Run **examples.py** for 7 practical examples

## Quick Reference

| Command | Purpose |
|---------|---------|
| `python train.py` | Train model with synthetic data |
| `python infer.py URL1 URL2` | Detect if URL2 mirrors URL1 |
| `python examples.py` | Run 7 working examples |
| `python generate_test_data.py` | Create test datasets |

---

**System Status**: ✅ Production Ready

For more information: `README.md`
