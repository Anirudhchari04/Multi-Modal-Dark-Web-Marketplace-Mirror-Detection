# DEPLOYMENT GUIDE

**Production Deployment for Law Enforcement Agencies**

## Pre-Deployment Checklist

- ✅ System requirements verified
- ✅ Dependencies installed
- ✅ Model trained with real-world data
- ✅ Logging configured
- ✅ Security hardened
- ✅ Testing completed

## 1. System Requirements

### Minimum Specs
- **CPU**: 4 cores (recommended 8)
- **RAM**: 8 GB (recommended 16 GB)
- **Disk**: 50 GB free space
- **Network**: Tor connectivity (for .onion sites)
- **OS**: Linux (recommended), macOS, Windows

### Software Requirements
- Python 3.7+
- pip
- All packages in requirements.txt

## 2. Installation for Production

```bash
# Create dedicated user
sudo useradd -m -s /bin/bash mirror-detection

# Clone repository
git clone <repo> /opt/mirror-detection
cd /opt/mirror-detection

# Install dependencies in virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set permissions
sudo chown -R mirror-detection:mirror-detection /opt/mirror-detection
sudo chmod 750 /opt/mirror-detection
```

## 3. Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["python", "infer.py", "--help"]
```

Build and run:

```bash
docker build -t mirror-detector .
docker run -it mirror-detector python infer.py URL1 URL2
```

## 4. API Server Deployment (Flask)

```python
# api_server.py
from flask import Flask, request, jsonify
from main import MarketplaceMirrorDetector
import logging

app = Flask(__name__)
logger = logging.getLogger(__name__)

detector = MarketplaceMirrorDetector("models/mirror_detector.pkl")

@app.route('/detect', methods=['POST'])
def detect():
    """Detect if new_url mirrors old_url"""
    data = request.json
    
    result = detector.detect_mirror(
        old_url=data.get('old_url'),
        new_url=data.get('new_url'),
        pgp_old=data.get('pgp_old', ''),
        pgp_new=data.get('pgp_new', '')
    )
    
    return jsonify(result)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)
```

Usage:

```bash
pip install flask
python api_server.py

# In another terminal
curl -X POST http://localhost:8000/detect \
  -H "Content-Type: application/json" \
  -d '{
    "old_url": "http://market1.onion",
    "new_url": "http://market2.onion",
    "pgp_old": "ABC123...",
    "pgp_new": "ABC123..."
  }'
```

## 5. Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mirror-detector
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mirror-detector
  template:
    metadata:
      labels:
        app: mirror-detector
    spec:
      containers:
      - name: mirror-detector
        image: mirror-detector:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "2Gi"
            cpu: "2"
          limits:
            memory: "4Gi"
            cpu: "4"
        env:
        - name: LOG_LEVEL
          value: "INFO"
```

Deploy:

```bash
kubectl apply -f deployment.yaml
```

## 6. Monitoring & Logging

### Log Rotation

```bash
# /etc/logrotate.d/mirror-detection
/opt/mirror-detection/mirror_detection.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 mirror-detection mirror-detection
    sharedscripts
    postrotate
        systemctl restart mirror-detector
    endscript
}
```

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, start_http_server

detections = Counter('detections_total', 'Total detections', ['classification'])
detection_duration = Histogram('detection_duration_seconds', 'Detection time')

# Add to main.py
@detection_duration.time()
def detect_mirror(...):
    # ... detection code ...
    detections.labels(classification=result['classification']).inc()
```

## 7. Security Hardening

### Firewall Configuration

```bash
# Allow only authorized IPs
sudo ufw allow from 192.168.1.0/24 to any port 8000

# Enable firewall
sudo ufw enable
```

### SSL/TLS for API

```bash
# Generate self-signed cert
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

# Use in Flask
app.run(ssl_context=('cert.pem', 'key.pem'))
```

### Environment Variables

```bash
# .env file (in /opt/mirror-detection/)
MODEL_PATH=/opt/mirror-detection/models/mirror_detector.pkl
LOG_LEVEL=INFO
MAX_TIMEOUT=15
WORKERS=4

# Load in production
export $(cat .env | xargs)
```

### Rate Limiting

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/detect', methods=['POST'])
@limiter.limit("10 per hour")
def detect():
    ...
```

## 8. Systemd Service

```ini
# /etc/systemd/system/mirror-detector.service
[Unit]
Description=Darknet Mirror Detection Service
After=network.target

[Service]
Type=simple
User=mirror-detection
Group=mirror-detection
WorkingDirectory=/opt/mirror-detection
Environment="PATH=/opt/mirror-detection/venv/bin"
ExecStart=/opt/mirror-detection/venv/bin/python api_server.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable:

```bash
sudo systemctl daemon-reload
sudo systemctl enable mirror-detector
sudo systemctl start mirror-detector
sudo systemctl status mirror-detector
```

## 9. Backup Strategy

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/backups/mirror-detection

# Backup model
cp /opt/mirror-detection/models/*.pkl $BACKUP_DIR/model_$DATE.pkl

# Backup logs
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz /opt/mirror-detection/mirror_detection.log

# Keep only 30 days
find $BACKUP_DIR -mtime +30 -delete
```

## 10. Disaster Recovery

### Database Backup (if using PostgreSQL)

```bash
# Backup
pg_dump mirror_detection > backup.sql

# Restore
psql mirror_detection < backup.sql
```

### Model Versioning

```bash
git tag -a v1.0.0 -m "Production model v1.0.0"
git push origin v1.0.0

# Rollback
git checkout v0.9.9
```

## 11. Performance Tuning

### Multi-threading

```python
# In config.py
RF_N_JOBS = -1          # Use all cores
GB_N_JOBS = -1          # Use all cores
```

### Caching

```python
# In config.py
ENABLE_FEATURE_CACHE = True
CACHE_DIR = "/tmp/mirror-detection-cache"
FEATURE_CACHE_TTL = 3600  # 1 hour
```

### Async Processing (with Celery)

```python
from celery import Celery

app = Celery('mirror_detection')

@app.task
def detect_mirror_async(old_url, new_url):
    detector = MarketplaceMirrorDetector()
    return detector.detect_mirror(old_url, new_url)

# Usage
result = detect_mirror_async.delay(url1, url2)
status = result.status
```

## 12. Monitoring Checklist

- ✅ Disk space monitoring
- ✅ Memory usage alerts
- ✅ CPU load monitoring
- ✅ API response times
- ✅ Error rate tracking
- ✅ Model accuracy metrics
- ✅ Log file rotation
- ✅ Backup verification

## 13. Upgrade Procedure

```bash
# 1. Backup current version
cp -r /opt/mirror-detection /opt/mirror-detection.backup

# 2. Pull updates
cd /opt/mirror-detection
git pull origin main

# 3. Update dependencies
source venv/bin/activate
pip install -r requirements.txt --upgrade

# 4. Retrain if needed
python train.py --data training_data.csv

# 5. Test
python examples.py

# 6. Restart service
sudo systemctl restart mirror-detector

# 7. Verify
sudo systemctl status mirror-detector
```

## 14. Common Issues

### Issue: Out of Memory
**Solution**: Increase swap, reduce TIMING_SAMPLES in config.py

### Issue: Slow Detection
**Solution**: Enable caching, use multi-processing, check network latency

### Issue: Model Accuracy Degraded
**Solution**: Retrain with fresh data, check feature extraction logs

### Issue: Connection Timeouts
**Solution**: Increase HTTP_TIMEOUT in config.py, check Tor connectivity

## 15. Support & Escalation

For issues:
1. Check `mirror_detection.log`
2. Review `ARCHITECTURE.md`
3. Run diagnostic: `python examples.py`
4. Check system resources: `free -h`, `df -h`

---

**Status**: Production-Ready  
**Version**: 1.0.0  
**Last Updated**: October 28, 2025
