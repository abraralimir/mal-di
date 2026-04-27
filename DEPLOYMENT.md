# Deployment & Production Guide

## Local Deployment Checklist

### Pre-Deployment
- [ ] Python 3.10+ installed
- [ ] NVIDIA GPU drivers installed (latest)
- [ ] CUDA toolkit matching your GPU
- [ ] 20GB+ free disk space
- [ ] 16GB+ system RAM

### Installation Verification
```bash
# Run system tests
python test_system.py

# Expected output:
# ✓ PyTorch & CUDA
# ✓ OCR Pipeline
# ✓ Transformers
# (API test will show running after backend starts)
```

### Environment Setup
```bash
# Windows
setup.bat

# Linux/Mac
bash setup.sh

# Manual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

---

## Running in Production

### Option 1: Development Mode (Testing)
```bash
# Terminal 1 - Backend with hot reload
cd backend
python app.py

# Terminal 2 - Frontend with Vite dev server
cd frontend
npm run dev
```

### Option 2: Production Build

#### Backend
```bash
# No changes needed - FastAPI can run as-is
# For production, use a production ASGI server:

pip install gunicorn uvicorn

# Run with Gunicorn
cd backend
gunicorn -w 1 -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 300 \
  app:app
```

#### Frontend
```bash
# Build for production
cd frontend
npm run build

# Serve built files
npx serve -s dist -l 3000

# Or use your preferred web server (nginx, Apache, etc.)
```

---

## Performance Tuning for Production

### Backend Optimization

**For faster inference**:
```python
# backend/config.py
BATCH_SIZE = 2            # Increase if you have >6GB VRAM
USE_INT8_QUANTIZATION = True  # Keep enabled for T500
```

**For better throughput**:
```python
# Run multiple workers (if system allows)
gunicorn -w 2 \
  -k uvicorn.workers.UvicornWorker \
  --timeout 300 \
  app:app
```

**For lower latency**:
```python
# Reduce context size
CHUNK_SIZE = 256          # Smaller chunks = faster retrieval
TOP_K_RETRIEVAL = 3       # Fewer sources = faster processing
```

### Frontend Optimization

**Production build already optimized**:
- Tree-shaking removes unused code
- Minification reduces file size
- Code splitting for better loading

**Serve behind reverse proxy** (nginx example):
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
}
```

---

## Monitoring & Logging

### Backend Monitoring

```python
# Add to app.py for production monitoring
import logging
from logging.handlers import RotatingFileHandler

# Setup file logging
file_handler = RotatingFileHandler('logs/app.log', 
                                  maxBytes=10485760,  # 10MB
                                  backupCount=10)
logging.root.addHandler(file_handler)
```

### System Monitoring

```bash
# Monitor GPU usage
watch -n 1 nvidia-smi

# Monitor processes
top -p $(pgrep -f "python app.py")

# Check ports
netstat -an | grep LISTEN
```

### API Monitoring

```bash
# Health check endpoint
curl -X GET http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "models_loaded": {
    "ocr": true,
    "vision": true,
    "rag": true,
    "chat": true
  }
}
```

---

## Database Backup & Restore

### Backup Vector Database

```bash
# Backup vectors
cp -r backend/vectors backend/vectors.backup

# Backup uploaded documents
cp -r backend/uploads backend/uploads.backup

# Create timestamped backup
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
Copy-Item backend/vectors "backend/vectors_backup_$timestamp" -Recurse
```

### Restore from Backup

```bash
# Stop backend
# Restore
rm -rf backend/vectors
cp -r backend/vectors.backup backend/vectors

# Start backend
python app.py
```

---

## Scaling Considerations

### Single Machine Optimization
```
Current setup: Single GPU, single process
Recommended for: Up to 10 concurrent users

Bottlenecks:
- Single GPU instance
- Sequential processing
- Model loading time
```

### Multi-Machine Setup (Advanced)

Would require:
- Load balancer (nginx)
- Shared vector database (Distributed Chroma/Redis)
- Message queue for jobs (Celery/RabbitMQ)
- Model caching layer

Not recommended for T500 - stick with single machine.

---

## Docker Deployment (Optional)

### Dockerfile

```dockerfile
FROM nvidia/cuda:12.1.0-devel-ubuntu22.04

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend
COPY backend ./backend
COPY frontend ./frontend

EXPOSE 8000 3000

# Start backend
CMD ["python", "backend/app.py"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEVICE=cuda
      - MAX_VRAM_GB=3.5
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  frontend:
    image: node:18
    working_dir: /app/frontend
    volumes:
      - ./frontend:/app/frontend
    ports:
      - "3000:3000"
    command: npm run dev
```

### Run with Docker

```bash
docker-compose up --build
```

---

## Security Hardening

### For Production Deployment

1. **Add authentication**:
```python
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/ask")
async def ask_question(request: QuestionRequest, 
                      credentials: HTTPAuthCredentials = Depends(security)):
    # Verify token
    # Process request
    pass
```

2. **Add rate limiting**:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/ask")
@limiter.limit("5/minute")
async def ask_question(request: QuestionRequest):
    pass
```

3. **Add input validation**:
```python
from pydantic import BaseModel, validator, constr

class QuestionRequest(BaseModel):
    question: constr(min_length=3, max_length=1000)
    
    @validator('question')
    def question_cannot_be_empty(cls, v):
        if not v or v.isspace():
            raise ValueError('Question cannot be empty')
        return v
```

4. **Enable HTTPS**:
```bash
# Generate self-signed certificate (development only)
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

# Run with SSL
uvicorn app:app --ssl-keyfile=key.pem --ssl-certfile=cert.pem
```

---

## Troubleshooting Production Issues

### OOM Errors in Production

```python
# backend/config.py - Emergency mode
MAX_VRAM_GB = 2.0          # Reduce further
BATCH_SIZE = 1             # Already minimal
CHUNK_SIZE = 256           # Halve it
```

### Slow Responses

```
Check:
1. GPU memory usage: nvidia-smi
2. CPU usage: top
3. Network: check latency
4. Log files: tail -f logs/app.log

Optimize:
- Reduce TOP_K_RETRIEVAL
- Increase BATCH_SIZE (if VRAM available)
- Cache frequent queries
```

### Model Loading Takes Too Long

```
Check:
1. Is disk slow? SSD recommended
2. Is network slow? Models download once then cache

Solutions:
- Pre-load models on startup
- Use faster SSDs
- Increase startup timeout for gunicorn
```

---

## Performance Metrics

### Expected Performance (T500)

```
Upload + OCR: 2-5 seconds
Vision Analysis: 1-2 seconds
RAG Indexing: ~1 second per 500 tokens
Question Answering: 2-3 seconds
Total workflow: 6-11 seconds
```

### Monitoring Key Metrics

```
- Memory usage: Should stay < 3.5GB
- Temperature: Keep < 85°C
- Response time: Monitor average
- Error rate: Track failures
- Throughput: Questions/minute
```

---

## Regular Maintenance

### Daily
- Monitor GPU health
- Check error logs
- Clear cache if needed

### Weekly
- Backup vector database
- Review performance metrics
- Test backup restore

### Monthly
- Update dependencies (cautiously)
- Analyze usage patterns
- Plan improvements

---

## Emergency Procedures

### System Crash Recovery

```bash
# Force clean state
rm -rf backend/uploads/* backend/vectors/*

# Restart services
cd backend && python app.py  # Terminal 1
cd frontend && npm run dev   # Terminal 2
```

### GPU Memory Leak

```bash
# Restart backend
# Kill any lingering processes
pkill -f "python app.py"
pkill -f "python -m"

# Monitor
nvidia-smi watch -n 1

# Restart
python app.py
```

### Vector DB Corruption

```bash
# Restore from backup
rm -rf backend/vectors
cp -r backend/vectors.backup backend/vectors

# Or rebuild
rm -rf backend/vectors
# Re-upload documents
```

---

## Performance Targets

- **Concurrent Users**: 1-2 (T500 limitation)
- **Documents Indexed**: 100+ (depends on size)
- **Query Latency**: 2-3 seconds
- **Uptime**: 99%+ (stable)
- **VRAM Usage**: 3-3.5GB
- **GPU Temp**: 50-80°C

---

**For most use cases, the single-machine deployment is sufficient and simple. Scale only if needed.**
