# 🎨 InvestBrand

> **"Craft your wealth, one move at a time."**

Learn about Nifty 50 companies through engaging brand logo puzzles. InvestBrand transforms investment education into an interactive daily gaming experience.

---

## ✨ Features

- 🧩 **Brand Lore Puzzles** - Solve jigsaw puzzles of authentic Indian brand logos.
- 📜 **Nostalgic Insights** - Discover "Founder Moments" and historic milestones for major companies like TCS and Reliance.
- 🚀 **4-Tier Selection flow** - Navigate 151+ brands across Nifty 50, Next 50, and Midcap with zero horizontal scrolling.
- 📉 **Nifty Learning** - Deep-dive into the companies behind everyday household brands.
- 🔥 **Daily Streak** - Build habbits with daily challenges and global leaderboards.
- 📱 **Zero-Scroll Master UI** - High-density completion screens optimized for 100vh viewport.
- 🛡️ **Trademark Compliance** - Authentic sourcing via Wikipedia & gstatic domain validation.

---

## 🏗️ Architecture

```
Frontend (React + Tailwind CSS)
         ↓  REST API
Backend (Node.js + Express on Cloud Run)
         ↓  SQL
Cloud SQL PostgreSQL (market-rover project)
```

---

## 📦 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Tailwind CSS, Lucide Icons |
| Backend | Node.js 18, Express, Winston |
| Database | PostgreSQL 15 (Cloud SQL) |
| Hosting | Cloud Run + Cloud Storage |
| Auth | Google OAuth 2.0 |
| CI/CD | GitHub Actions |

---

## 🚀 Quick Start (Local Development)

### Prerequisites
- Node.js 18+
- Docker Desktop
- Google Cloud CLI

### Run Locally with Docker

```bash
# Clone the repo
git clone https://github.com/SankarGaneshb/Market-Rover.git
cd Market-Rover/investcraft

# Start all services
docker-compose up

# App runs at:
# Frontend: http://localhost:3000
# Backend:  http://localhost:8080/api/health
```

### Run Without Docker

```bash
# Backend
cd backend
npm install
cp .env.example .env
# Edit .env with your credentials
npm run dev

# Frontend (new terminal)
cd frontend
npm install
cp .env.example .env
npm start
```

---

## 🌐 Deployment (Google Cloud - market-rover)

### Automatic via GitHub Actions
Every push to `investcraft` branch auto-deploys:
- Backend → Cloud Run
- Frontend → Cloud Storage

### Manual Deployment

```bash
# Backend
cd backend
gcloud builds submit --tag gcr.io/market-rover/investcraft-api
gcloud run deploy investcraft-api --image gcr.io/market-rover/investcraft-api --region us-central1

# Frontend
cd frontend
npm run build
gsutil -m rsync -r build gs://market-rover-investcraft
```

---

## 💰 Estimated Monthly Cost

| Service | Tier | Cost |
|---------|------|------|
| Cloud SQL | db-f1-micro | ~$15-20 |
| Cloud Run | Serverless (0-10 instances) | ~$5-10 |
| Cloud Storage | Frontend hosting | ~$1-2 |
| **Total** | | **~$21-32/month** |

---

## 📊 Monitoring

- **Cloud Run**: https://console.cloud.google.com/run?project=market-rover
- **Cloud SQL**: https://console.cloud.google.com/sql?project=market-rover
- **Logs**: https://console.cloud.google.com/logs?project=market-rover

---

## 🎮 Taglines

- *"Your strategy, your craft, your success."*
- *"Craft your wealth, one move at a time."*
- *"Shape the market, shape your future."*
- *"Empowerment through play, mastery through craft."*
- *"Design wealth, discover wisdom."*
- *"Investing made a game of skill."*

---

## 👨‍💻 Author

**SankarGaneshb** - [@SankarGaneshb](https://github.com/SankarGaneshb)

Part of the **Market-Rover** investment platform.

---

*InvestBrand - Where every puzzle brings you closer to financial wisdom* 🚀
