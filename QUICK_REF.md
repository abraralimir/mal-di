# 🎯 Quick Reference Card

## In Your Pocket 📱

### Setup (Once)
```bash
setup.bat                    # Windows setup (5-10 min)
bash setup.sh                # Linux/Mac setup
```

### Run (Every Time) ⚡
```bash
run.bat                      # Windows startup
bash run.sh                  # Linux/Mac startup
```

### Access
```
Frontend:        http://localhost:3000  ✨
Backend API:     http://localhost:8000
API Docs:        http://localhost:8000/docs
Health Check:    http://localhost:8000/health
```

### Stop
```bash
Ctrl+C
```

---

## Task Guide

### Upload Document
1. Click **Upload** tab
2. Select file (PDF/JPG/PNG)
3. Wait for processing
4. Done! File indexed

### Ask Questions
1. Click **Chat** tab
2. Select document or **All Documents**
3. Type question (English or Arabic)
4. Get instant answer + sources

### Manage Files
1. Click **Documents** tab
2. See all indexed files
3. Click **Chat with this** to select
4. Click **Delete** to remove

---

## GPU Commands

```powershell
# Watch GPU usage
nvidia-smi -l 1

# Get info
nvidia-smi

# Check VRAM
nvidia-smi --query-gpu=memory.used,memory.free --format=csv
```

---

## Common Issues

| Problem | Fix |
|---------|-----|
| "Port 3000 in use" | Change port in `vite.config.ts` |
| Backend won't start | First run takes 3-5 min |
| Can't connect | Give backend 5+ seconds |
| Out of memory | Reduce in `backend/config.py` |
| Models won't download | Check internet/disk space |

---

## Folders

```
backend/
  ├── uploads/          # Your documents
  ├── vectors/          # Search database
  └── models/           # AI models cache

frontend/
  └── src/              # React code
```

---

## Environment

Edit `.env` for:
```
DEVICE=cuda              # GPU device
API_HOST=0.0.0.0        # API address
MAX_VRAM_GB=3.5         # GPU memory limit
```

---

## Files to Know

| File | Purpose |
|------|---------|
| `app.py` | FastAPI server |
| `App.tsx` | Main frontend |
| `run.bat` | Start everything |
| `config.py` | Settings |

---

**Everything is one command away! 🚀**
