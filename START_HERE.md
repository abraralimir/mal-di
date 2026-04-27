# ⚡ FASTEST START - Just Run This!

## 🚀 One Command Startup

### Windows (PowerShell)
```powershell
cd c:\adev\arabic-vision-poc

# First time only - setup
.\setup.bat

# Then - just run this every time:
.\run.bat
```

**That's it!** Everything starts automatically:
- ✅ Backend initializes
- ✅ Frontend starts
- ✅ Browser opens to http://localhost:3000

---

### Linux/Mac
```bash
cd c:\adev\arabic-vision-poc

# First time only - setup
bash setup.sh

# Then - just run this every time:
bash run.sh
```

---

## 📍 What's Running

Once started, everything is accessible from:

```
🌐 Frontend + API Gateway
   http://localhost:3000

📊 Backend API (if you need it directly)
   http://localhost:8000
   
📋 API Documentation
   http://localhost:8000/docs
```

---

## ⏱️ Wait Times

| Step | Time | What's Happening |
|------|------|------------------|
| Run command | ~2s | Backend initializes |
| Models load | ~3-5 min | First time only (automatic) |
| Frontend starts | ~3s | React dev server |
| **Total First Time** | **~8 min** | One-time only! |
| **Subsequent Times** | **~10s** | Models already cached |

---

## 🎯 Usage

1. **Upload document**
   - Click Upload tab
   - Select file
   - Wait for processing

2. **Ask questions**
   - Click Chat tab
   - Type question
   - Get instant answers

3. **Manage documents**
   - View all indexed docs
   - Delete if needed

---

## 🛑 Stop Everything

Just close both windows or press:
```
Ctrl+C
```

Everything stops cleanly!

---

## 🆘 Issues

**Can't find run.bat?**
```powershell
# Make sure you're in the right folder
cd c:\adev\arabic-vision-poc
ls  # Should show run.bat
```

**Port 3000 already in use?**
```python
# Edit frontend/vite.config.ts, change:
port: 3001,  # or 3002, etc.
```

**Backend won't start?**
- First run takes 3-5 minutes (models downloading)
- Check GPU memory: `nvidia-smi`
- If OOM: reduce `MAX_VRAM_GB` in `backend/config.py`

---

## 💡 Pro Tips

**Faster development**:
- Keep terminal open between runs
- Backend caches models after first run
- Frontend has hot reload (changes auto-update)

**Check if running**:
- Backend: http://localhost:8000/health
- Frontend: http://localhost:3000

**Monitor GPU**:
```powershell
# Open new terminal
nvidia-smi -l 1  # Update every 1 second
```

---

**Everything from localhost:3000! 🎉**
