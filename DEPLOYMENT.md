# Cloud Deployment Guide — AI Financial Decision Support System

This guide outlines the production cloud deployment procedure for the **AI-Powered Personal Financial Portfolio Management and Decision Support System**.

The application is structured into two cloud-native services:
- **Frontend Dashboard:** [Next.js 15](https://nextjs.org) deployed on [Vercel](https://vercel.com) (Global Edge CDN, HTTPS).
- **Backend API & Analytics Engine:** [FastAPI](https://fastapi.tiangolo.com) deployed on [Render](https://render.com) (Python 3.12 Web Service).
- **Database:** Managed [PostgreSQL 16](https://render.com/docs/databases) hosted on Render.
- **AI Engine:** Ultra-fast [Groq Cloud](https://groq.com) Llama/GPT-OSS inference.

---

## Pre-Deployment Verification Completed

The local codebase has been pre-configured and committed cleanly to Git:
1. **`render.yaml`:** Pre-configured Infrastructure-as-Code Blueprint defining the web service, environment variables, and PostgreSQL instance.
2. **`frontend/vercel.json`:** Optimized Next.js build detection.
3. **`backend/app/seed.py`:** Automated database seeder that detects an empty cloud database and automatically seeds `nikhilpillai538@gmail.com`, 90 days of transactions, 7 portfolio assets, 1,834 historical prices, and 3 investment goals on initial boot.
4. **CORS Hardening:** Configured in `backend/app/main.py` with `allow_origin_regex=r"https://.*\.vercel\.app"` so all Vercel deployments can communicate with the backend.

---

## Step 1: Push Code to GitHub

Open terminal in the project directory:
```powershell
cd C:\Users\NIKHIL.P\.gemini\antigravity\scratch\ai-financial-decision-support
```

1. Create a new empty repository on [GitHub](https://github.com/new) (e.g., named `ai-financial-decision-support`). Do **not** check "Add a README" or ".gitignore" as they already exist.
2. Link your local repo and push:
   ```bash
   git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/ai-financial-decision-support.git
   git branch -M main
   git push -u origin main
   ```

---

## Step 2: Deploy Backend & Database on Render (3 Minutes)

1. Sign up or log in at **[render.com](https://render.com)**.
2. Click **New +** at the top right and select **Blueprint**.
3. Connect your GitHub account and select your `ai-financial-decision-support` repository.
4. Render will detect the `render.yaml` file in the root directory and show:
   - **Service:** `ai-portfolio-backend` (Web Service, Python 3.12)
   - **Database:** `ai-portfolio-db` (PostgreSQL, Free Tier)
5. Click **Apply**.
6. Render will automatically:
   - Create the PostgreSQL database.
   - Build and start the FastAPI backend.
   - Execute database migrations and seed the sample data.
7. Once deployment finishes, copy your live backend URL (e.g., `https://ai-portfolio-backend.onrender.com`).
   - You can verify it by opening `https://ai-portfolio-backend.onrender.com/docs` in your browser.

---

## Step 3: Deploy Frontend on Vercel (2 Minutes)

1. Sign up or log in at **[vercel.com](https://vercel.com)**.
2. Click **Add New...** → **Project**.
3. Import your `ai-financial-decision-support` repository from GitHub.
4. In the configuration screen:
   - **Framework Preset:** Next.js (automatically detected)
   - **Root Directory:** Click **Edit** and select `frontend` folder.
   - **Environment Variables:** Add the following two variables:
     | Key | Value |
     | :--- | :--- |
     | `NEXT_PUBLIC_API_URL` | Your Render URL (e.g., `https://ai-portfolio-backend.onrender.com`) |
     | `NEXT_PUBLIC_API_BASE_URL` | Your Render URL (e.g., `https://ai-portfolio-backend.onrender.com`) |
5. Click **Deploy**.
6. Within 60 seconds, Vercel will complete the build and assign a live production URL (e.g., `https://ai-portfolio-frontend.vercel.app`).

---

## Step 4: Verification & Demonstration

1. Open your live Vercel URL in your browser or phone.
2. Log in with your demo credentials:
   - **Email:** `nikhilpillai538@gmail.com`
   - **Password:** Any standard password or existing credential.
3. Test all live features:
   - **Portfolio Valuation:** Verify the ₹9,20,200.00 multi-asset valuation across Reliance, TCS, HDFC Bank, Infosys, ICICI Bank, Gold BeES, and Liquid BeES.
   - **Cash Flow:** Review the 90 days of transactions and 30-day forecast.
   - **Optimization:** Run MPT Sharpe-ratio optimization on the real historical price series.
   - **Live News:** Review live market feeds and sentiment indicators.
   - **AI Assistant:** Ask conversational queries (e.g., "How is my 30-day cash flow looking?") powered by Groq Cloud.
