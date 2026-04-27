# QUICKSTART GUIDE

## ⚡ 5-Minute Setup (Windows)

### Step 1: Open PowerShell in the project folder
```powershell
cd c:\adev\arabic-vision-poc
```

### Step 2: Run Setup
```powershell
.\setup.bat
```

During setup, when asked about CUDA version:
- If you have RTX 30xx/40xx series: Choose **2** (CUDA 12.1)
- If you have older cards: Choose **1** (CUDA 11.8)
- If unsure: Choose **2** (most common)

### Step 3: Start Backend (Terminal 1)
```powershell
cd backend
python app.py
```

**Wait for this output** (takes 2-3 minutes on first run):
```
All models initialized successfully!
```

### Step 4: Start Frontend (Terminal 2)
```powershell
cd frontend
npm run dev
```

Browser opens automatically at **http://localhost:3000** ✓

---

## 🚀 Usage

### Upload Documents
1. Click **Upload** tab
2. Select a PDF or image
3. Wait for processing (OCR → Vision → RAG)

### Ask Questions
1. Go to **Chat & QA** tab
2. Select document or query all
3. Type in English or Arabic
4. Get instant answers with sources

### Example Questions
- "What's the main content?"
- "استخرج المعلومات الرئيسية"
- "List all dates mentioned"
- "Summarize this document"

---

## 🆘 Troubleshooting

### Backend won't start - "CUDA out of memory"
```python
# Edit backend/config.py
MAX_VRAM_GB = 2.5  # Lower this value
```

### Models loading too slow
- First run: Normal (models download from HuggingFace)
- Requires 20GB free space
- Takes 2-3 minutes

### Frontend can't connect to API
- Check backend is running: http://localhost:8000
- Check firewall isn't blocking port 8000
- Restart both services

### OCR not working well
- Ensure image is clear
- Try rotating document 90°
- Use higher resolution (300+ DPI)

---

## 📊 System Info

### What's Running
- **Port 8000**: Backend API (FastAPI)
- **Port 3000**: Frontend (React)
- **http://localhost:8000/health** - Check if API is ready

### Check GPU Usage
```powershell
nvidia-smi
```

Look for:
- Process using ~3-3.5GB VRAM (that's your models)
- Temp should be < 85°C
- Memory usage will vary during inference

---

## 📁 Important Folders

- `backend/uploads/` - Your uploaded documents
- `backend/vectors/` - Vector database
- `backend/models/` - Downloaded AI models

---

## 💡 Tips for Better Results

1. **Upload clear documents** - Better text extraction
2. **Use specific questions** - "Extract invoice number" vs "What is this?"
3. **Check sources** - Click the sources dropdown to see where answers came from
4. **Try different documents** - Different content, different answers

---

## 🔧 Stop Everything

```powershell
# In Terminal 1 (Backend): Ctrl+C
# In Terminal 2 (Frontend): Ctrl+C
```

---

## 🎯 Next Steps

1. ✓ System is ready
2. Upload your first document
3. Ask questions
4. Explore the RAG system

**Performance**: First inference will be slower (model optimization). Subsequent requests are faster.

---

## 📞 Quick Commands Reference

```powershell
# Activate virtual environment
venv\Scripts\activate

# Stop backend
Ctrl+C

# Stop frontend
Ctrl+C

# Run tests
python test_system.py

# Check API health
curl http://localhost:8000/health

# View documents list
curl http://localhost:8000/documents
```

---

**You're all set! Start with the Backend first, then Frontend. Happy documenting! 🚀**
