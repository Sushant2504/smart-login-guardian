# 🚀 Vercel Deployment Guide - Smart Login Guardian

## ✅ **Deployment Status: Ready for Vercel!**

---

## 📋 **Quick Deployment (2 Minutes)**

### **Option 1: Deploy via Vercel CLI (Recommended)**

```bash
# 1. Install Vercel CLI
npm install -g vercel

# 2. Navigate to project
cd /Users/snadavad/Documents/smart-login-guardian

# 3. Login to Vercel
vercel login

# 4. Deploy
vercel

# 5. Deploy to production
vercel --prod
```

### **Option 2: Deploy via Vercel Dashboard**

1. Go to [vercel.com](https://vercel.com)
2. Click "Add New Project"
3. Import Git Repository (or upload folder)
4. Select "smart-login-guardian" directory
5. Click "Deploy"

---

## 📁 **Files Created for Vercel**

### **1. `vercel.json`** - Vercel Configuration
```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "api/index.py"
    },
    {
      "src": "/(.*)",
      "dest": "api/index.py"
    }
  ]
}
```

### **2. `api/index.py`** - Serverless API
- FastAPI application
- Mangum adapter for Vercel
- Complete dashboard HTML
- ML model integration
- All API endpoints

### **3. `requirements-vercel.txt`** - Dependencies
- Minimal dependencies for serverless
- FastAPI, Scikit-learn, NumPy
- Mangum (ASGI adapter)

### **4. `.vercelignore`** - Ignore Files
- Excludes venv, tests, docs
- Reduces deployment size

---

## 🔧 **Important Changes for Vercel**

### **Serverless Adaptations:**

1. **No WebSockets** - Using polling instead (5-second refresh)
2. **In-Memory Storage** - State resets on cold starts
3. **Simplified Dashboard** - Optimized for serverless
4. **No Background Tasks** - Events generated on demand

### **What Still Works:**

✅ ML Model (Scikit-learn Isolation Forest)  
✅ Multi-signal Risk Detection  
✅ Real-time Charts (Chart.js)  
✅ Attack Simulation Buttons  
✅ Statistics Dashboard  
✅ Event Generation  
✅ Risk Scoring  

### **What's Different:**

⚠️ WebSockets → Polling (5s intervals)  
⚠️ Events reset on cold start  
⚠️ No 3D Globe (to reduce size)  
⚠️ Manual refresh needed  

---

## 📊 **Deployment Architecture**

```
┌─────────────────────────────────────────┐
│         Vercel Edge Network             │
│         (Global CDN)                    │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│      Serverless Function                │
│      (AWS Lambda)                       │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │   FastAPI Application            │  │
│  │   - ML Model                     │  │
│  │   - Risk Detection               │  │
│  │   - API Endpoints                │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │   In-Memory Storage              │  │
│  │   - Events (resets on cold)      │  │
│  │   - ML Model State               │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

---

## 🚀 **Step-by-Step Deployment**

### **Step 1: Prepare Project**

```bash
# Navigate to project
cd /Users/snadavad/Documents/smart-login-guardian

# Verify files exist
ls -la vercel.json
ls -la api/index.py
ls -la requirements-vercel.txt
```

### **Step 2: Install Vercel CLI**

```bash
# Install globally
npm install -g vercel

# Or use npx (no install needed)
npx vercel
```

### **Step 3: Login to Vercel**

```bash
vercel login

# Follow browser authentication
# Choose: Email, GitHub, GitLab, or Bitbucket
```

### **Step 4: Deploy to Preview**

```bash
# First deployment (preview)
vercel

# Vercel will ask:
# ? Set up and deploy "~/Documents/smart-login-guardian"? [Y/n] y
# ? Which scope do you want to deploy to? <your-username>
# ? Link to existing project? [y/N] n
# ? What's your project's name? smart-login-guardian
# ? In which directory is your code located? ./
```

### **Step 5: Deploy to Production**

```bash
# Deploy to production
vercel --prod

# You'll get a production URL like:
# https://smart-login-guardian.vercel.app
```

---

## 🌐 **Access Your Deployment**

After deployment, you'll get URLs like:

**Preview:** `https://smart-login-guardian-abc123.vercel.app`  
**Production:** `https://smart-login-guardian.vercel.app`

---

## 🎯 **Testing Your Deployment**

### **1. Open Dashboard**
```
https://your-deployment.vercel.app
```

### **2. Test API Endpoints**

```bash
# Get stats
curl https://your-deployment.vercel.app/api/stats

# Generate event
curl -X POST https://your-deployment.vercel.app/api/generate-event

# Trigger attack
curl -X POST https://your-deployment.vercel.app/api/attack/brute_force
```

### **3. Use Dashboard Buttons**

- Click "Generate Event" → Creates authentication event
- Click "🔨 Simulate Attack" → Triggers brute force
- Click "🔄 Refresh" → Updates statistics

---

## ⚙️ **Environment Variables (Optional)**

If you want to add custom configuration:

```bash
# Via CLI
vercel env add PYTHON_VERSION
# Enter value: 3.11

# Via Dashboard
# Settings → Environment Variables → Add
# Name: PYTHON_VERSION
# Value: 3.11
```

---

## 🔍 **Monitoring Your Deployment**

### **View Logs:**

```bash
# Real-time logs
vercel logs

# Or in Vercel Dashboard:
# Your Project → Deployments → Select Deployment → Logs
```

### **Check Build Status:**

```bash
vercel ls

# Or visit: vercel.com/dashboard
```

---

## 🎨 **Custom Domain (Optional)**

### **Add Custom Domain:**

```bash
vercel domains add yourdomain.com

# Or in Dashboard:
# Settings → Domains → Add Domain
```

### **Example Custom URLs:**
- `smart-login-guardian.yourdomain.com`
- `security.yourdomain.com`
- `threats.yourdomain.com`

---

## 📈 **Performance Optimization**

### **Current Configuration:**

```json
{
  "functions": {
    "api/index.py": {
      "memory": 1024,      // 1GB RAM
      "maxDuration": 10     // 10 seconds timeout
    }
  }
}
```

### **For Better Performance:**

```json
{
  "functions": {
    "api/index.py": {
      "memory": 3008,      // Max: 3GB
      "maxDuration": 60    // Max: 60s (Pro plan)
    }
  }
}
```

---

## 🐛 **Troubleshooting**

### **Issue 1: Build Failed**

```bash
# Check build logs
vercel logs

# Common fix: Update requirements
pip freeze > requirements-vercel.txt
```

### **Issue 2: Function Timeout**

```json
// Increase timeout in vercel.json
{
  "functions": {
    "api/index.py": {
      "maxDuration": 60
    }
  }
}
```

### **Issue 3: Module Not Found**

```bash
# Ensure all dependencies in requirements-vercel.txt
echo "package-name==version" >> requirements-vercel.txt
vercel --prod
```

### **Issue 4: Cold Starts**

```
- Expected: First request may be slow (1-3s)
- Solution: Keep-alive pings or upgrade to Vercel Pro
```

---

## 💰 **Vercel Plans**

### **Hobby (Free)**
- ✅ Perfect for this demo
- ✅ Unlimited deployments
- ✅ Automatic HTTPS
- ✅ 100GB bandwidth/month
- ⚠️ 10s function timeout
- ⚠️ Cold starts

### **Pro ($20/month)**
- ✅ 60s function timeout
- ✅ More bandwidth
- ✅ Better performance
- ✅ Analytics

---

## 📋 **Deployment Checklist**

- [x] Created `vercel.json`
- [x] Created `api/index.py`
- [x] Created `requirements-vercel.txt`
- [x] Created `.vercelignore`
- [ ] Install Vercel CLI
- [ ] Login to Vercel
- [ ] Run `vercel` command
- [ ] Test preview deployment
- [ ] Run `vercel --prod`
- [ ] Share production URL

---

## 🎯 **Next Steps After Deployment**

1. **Share URL** with team/clients
2. **Test all features** on live site
3. **Monitor logs** for errors
4. **Add custom domain** (optional)
5. **Set up analytics** (optional)

---

## 📞 **Support & Resources**

**Vercel Documentation:**
- Getting Started: https://vercel.com/docs
- Python Runtime: https://vercel.com/docs/runtimes#official-runtimes/python

**Project Repository:**
- Local: `/Users/snadavad/Documents/smart-login-guardian`
- Vercel Config: `vercel.json`
- API: `api/index.py`

---

## 🎉 **Quick Deploy Command**

```bash
# One-command deployment
cd /Users/snadavad/Documents/smart-login-guardian && vercel --prod
```

---

## ✅ **Deployment Complete!**

Once deployed, your Smart Login Guardian will be live at:

**Your URL:** `https://smart-login-guardian-[unique-id].vercel.app`

**Features Available:**
- ✅ Real-time threat detection
- ✅ ML anomaly detection
- ✅ Interactive dashboard
- ✅ Attack simulation
- ✅ Risk scoring
- ✅ Charts and statistics
- ✅ Global CDN delivery

---

**Ready to deploy!** Run `vercel` in the project directory! 🚀
