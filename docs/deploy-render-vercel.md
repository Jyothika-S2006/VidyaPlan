# Deploy on Render (backend) + Vercel (frontend)

This is the fastest free deployment path for the hackathon demo.

---

## Part 1: Deploy Backend on Render

### Step 1 — Push to GitHub
```bash
cd d:\HackathonAJ
git init
git add .
git commit -m "feat: VidyaPlan initial build"
git remote add origin https://github.com/YOUR_USERNAME/vidyaplan.git
git push -u origin main
```

### Step 2 — Create Render service
1. Go to [https://dashboard.render.com](https://dashboard.render.com)
2. Click **New → Web Service**
3. Connect your GitHub repo
4. Configure:
   - **Name:** `vidyaplan-backend`
   - **Root Directory:** `backend`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free (or Starter for persistent disk)

### Step 3 — Set environment variables in Render dashboard
Under **Environment → Environment Variables**, add:

| Key | Value |
|---|---|
| `WATSONX_API_KEY` | `QwcCSksPTaCGupVe9_78mJSS6TG7lpu3-v-GxlOHYOqn` |
| `WATSONX_URL` | `https://us-south.ml.cloud.ibm.com` |
| `WATSONX_PROJECT_ID` | `031ca91d-54f8-4f02-9d6b-cd0f3e2e6888` |
| `WATSONX_MODEL_ID` | `ibm/granite-4-h-small` |
| `DATABASE_URL` | `sqlite+aiosqlite:///./vidyaplan.db` |
| `LLM_TIMEOUT_SECONDS` | `20` |
| `STRESS_SCENARIOS` | `100` |
| `CORS_ORIGINS` | `["https://vidyaplan.vercel.app"]` ← update after Vercel deploy |

### Step 4 — Add startup data loading
In Render → **Environment → Pre-Deploy Command** (or as part of start command):
```
python -m app.pipeline.load; uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

> ⚠️ **Important:** Render Free tier has ephemeral disk — the SQLite DB resets on each deploy.
> Use the pre-deploy command to reload data automatically.
> For persistent storage, upgrade to Render Starter ($7/mo) and add a disk at `/opt/render/project/src`.

### Step 5 — Note your backend URL
After deploy, your URL will be: `https://vidyaplan-backend.onrender.com`

Verify: `curl https://vidyaplan-backend.onrender.com/health`

---

## Part 2: Deploy Frontend on Vercel

### Step 1 — Update the API URL
Edit `frontend/.env.production` and set:
```
VITE_API_URL=https://vidyaplan-backend.onrender.com
```
(Replace with your actual Render URL)

Commit and push this change.

### Step 2 — Deploy to Vercel
1. Go to [https://vercel.com](https://vercel.com)
2. Click **New Project → Import from GitHub**
3. Select your `vidyaplan` repo
4. Configure:
   - **Root Directory:** `frontend`
   - **Framework Preset:** Vite
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`

5. Under **Environment Variables**, add:
   - `VITE_API_URL` = `https://vidyaplan-backend.onrender.com`

6. Click **Deploy**

Your frontend will be live at: `https://vidyaplan.vercel.app`

### Step 3 — Update CORS on Render
Go back to Render → Environment Variables → update `CORS_ORIGINS`:
```
["https://vidyaplan.vercel.app","http://localhost:5173"]
```

---

## ⚡ Quick reference: free tier limits

| Service | Free tier limits |
|---|---|
| Render Free | 750 hours/month, spins down after 15 min inactivity (cold start ~30s) |
| Render Starter | $7/mo — always on, persistent disk |
| Vercel Free | Unlimited for static/Vite frontends |

> **For the hackathon demo:** Use Render Starter ($7) to avoid cold starts, or keep the browser tab open to prevent spin-down.
> Alternatively, use the `--min-scale 1` IBM Code Engine option for no cold starts.

---

## 📋 Checklist

- [ ] GitHub repo is public
- [ ] `backend/requirements.txt` is committed
- [ ] `frontend/.env.production` has the correct Render URL
- [ ] Render `CORS_ORIGINS` includes your Vercel URL
- [ ] `/health` returns `{"status":"ok"}` from Render URL
- [ ] Frontend loads and shows the Data page from Vercel URL
- [ ] Update README.md with both URLs
