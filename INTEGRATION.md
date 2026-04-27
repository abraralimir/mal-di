# ✨ SIMPLIFIED SETUP - Everything from localhost:3000

Perfect! I've simplified everything. Now you can run **everything from a single command**!

---

## 🎯 How It Works Now

### **First Time Setup** (Just Once)
```powershell
cd c:\adev\arabic-vision-poc
.\setup.bat
```

### **Every Time You Use It** ⚡
```powershell
.\run.bat
```

That's it! 

✅ Backend starts automatically  
✅ Frontend starts automatically  
✅ Browser opens to http://localhost:3000  
✅ Everything works together!

---

## 🌐 Everything Accessible from localhost:3000

```
Frontend (Upload, Chat, Documents)
    http://localhost:3000

Backend (Auto-proxied, transparent)
    - All API calls go through localhost:3000
    - Direct access: http://localhost:8000 (if needed)

Completely integrated experience!
```

---

## ⏱️ How Long?

| Scenario | Time |
|----------|------|
| First ever setup | 5-10 minutes |
| First run (models load) | 3-5 minutes |
| **Every time after** | ~10 seconds ⚡ |

---

## 📁 New Files Created

```
✅ run.bat           → One-command startup (Windows)
✅ run.sh            → One-command startup (Linux/Mac)
✅ start.js          → Alternative startup (Node.js)
✅ RUN_NOW.md        → Fastest start guide
✅ START_HERE.md     → All startup options
✅ QUICK_REF.md      → Quick reference card
✅ INTEGRATION.md    → Technical integration details
```

---

## 🚀 What Changed

### Updated for Localhost:3000 Integration
✅ Vite proxy properly configured  
✅ Frontend auto-connects to backend  
✅ API calls route through port 3000  
✅ No manual port switching  
✅ Single dev server experience  

### Still Includes All Features
✅ PaddleOCR (Arabic+English)  
✅ Qwen Vision model  
✅ RAG semantic search  
✅ Local Q&A chat  
✅ NVIDIA T500 optimization  
✅ Beautiful React UI  
✅ Complete documentation  

---

## 💡 Usage Flow

```
1. Open PowerShell
   cd c:\adev\arabic-vision-poc

2. First time only:
   .\setup.bat

3. Whenever you want to use it:
   .\run.bat
   
4. Browser opens to http://localhost:3000

5. Upload documents

6. Ask questions

7. Done! Close terminal with Ctrl+C
```

---

## 🎨 Frontend-Only View

Everything you need is visible in ONE interface:

```
┌─────────────────────────────────────┐
│  Document Intelligence System       │
│  http://localhost:3000              │
├─────────────────────────────────────┤
│  [Upload] [Documents] [Chat & QA]  │
├─────────────────────────────────────┤
│  Upload Area / Chat Interface       │
│  (Automatically connects backend)   │
└─────────────────────────────────────┘
```

---

## ⚙️ Behind the Scenes

When you click on frontend:
1. React frontend responds immediately (localhost:3000)
2. When you upload/ask → Request goes to backend (transparent proxy)
3. Backend processes on GPU
4. Response comes back through port 3000
5. UI updates automatically

**Result:** Seamless experience, one port! 🎉

---

## 🆘 If Something Goes Wrong

```powershell
# Restart everything
Ctrl+C (in terminal)
.\run.bat (again)

# Check what's running
netstat -ano | findstr :3000
netstat -ano | findstr :8000

# GPU monitor
nvidia-smi -l 1

# Backend logs visible in terminal
# Frontend logs in browser console (F12)
```

---

## 📊 Technical Setup

### Vite Proxy Configuration
The frontend (port 3000) automatically proxies these calls to backend (port 8000):
- `/health` → Backend health check
- `/upload` → Upload documents
- `/ask` → Ask questions
- `/documents` → List files
- `/docs` → API documentation

### Result
Everything accessible from **localhost:3000** seamlessly!

---

## ✅ Verification

After running `run.bat`, check:

```powershell
# In browser
http://localhost:3000        # Should show app

# Backend running (check console output)
# Should see: "Application startup complete"

# GPU working
nvidia-smi                   # Should show VRAM usage
```

---

## 🎯 Next Steps

1. **Read** [RUN_NOW.md](RUN_NOW.md) - Quickest start
2. **Run** `setup.bat` - One time only
3. **Use** `run.bat` - Every time
4. **Visit** http://localhost:3000
5. **Upload** documents and ask questions!

---

## 📚 Documentation

| File | Purpose |
|------|---------|
| [RUN_NOW.md](RUN_NOW.md) | ⭐ Fastest path to running |
| [QUICK_REF.md](QUICK_REF.md) | Command reference |
| [README.md](README.md) | Full documentation |
| [QUICKSTART.md](QUICKSTART.md) | Detailed setup |

---

## 💾 File Locations

Everything you need:
```
c:\adev\arabic-vision-poc\
├── run.bat           ← USE THIS
├── setup.bat         ← FIRST TIME
├── RUN_NOW.md        ← READ THIS
└── ... (all other files)
```

---

## 🎉 Ready!

You now have the simplest possible setup:

1. `setup.bat` (once)
2. `run.bat` (every time)
3. `http://localhost:3000` (use it)

**That's all you need to know!** 🚀

Everything else runs automatically in the background. Document intelligence on your localhost!
