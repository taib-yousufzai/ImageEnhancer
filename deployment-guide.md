# Deployment Guide for PhotoEnhancer

Based on the configuration files in your project, the architecture is split into two parts. You should deploy using the following platforms:

### 1. The Python Backend (Deploy to **Render**)
Your project contains a `render.yaml` file configured specifically for the FastAPI/Uvicorn backend. 
* **How to deploy:** Go to Render.com, connect your GitHub repository, and choose "Blueprint" deployment. It will automatically read the `render.yaml` file.
* **Important Warning:** I just updated your `render.yaml` file to enforce our new security measures. Please make sure to update the environment variables `ALLOWED_ORIGINS` and `ALLOWED_API_KEY_HASHES` inside your Render dashboard with your actual Production Vercel URL and generated Key Hash!

### 2. The Next.js Frontend (Deploy to **Vercel**)
Your project contains a `vercel.json` file and a `next.config.mjs` optimized for Next.js.
* **How to deploy:** Go to Vercel.com, log in, import this same GitHub repository, and it will auto-detect Next.js.
* **Important Warning:** In your Vercel environment variables, make sure you configure your frontend to point safely to your Render backend URL, and include the **Plaintext** API key (the one starting with `pe_live...` that you generate) in the Vercel settings so Vercel can pass it securely to Render.
