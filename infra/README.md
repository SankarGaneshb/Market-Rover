# 📊 Market-Rover Observability

This directory contains infrastructure-as-code for monitoring the Market-Rover ecosystem in Google Cloud.

## ⚡ Quick Start (The "GCP Dashboard")

To create the **Global SRE Dashboard** in your GCP project, follow these steps:

### Option A: Using Terraform (Recommended)
If you have Terraform installed:
1. `cd infra`
2. `terraform init`
3. `terraform apply`

### Option B: Manual Import (No Setup Required)
1. Go to the [GCP Monitoring Dashboards](https://console.cloud.google.com/monitoring/dashboards) page.
2. Click **Create Dashboard**.
3. In the top right, click **JSON Editor**.
4. Copy and paste the contents of the `dashboard_json` block from [observability.tf](./observability.tf).
5. Click **Submit**.

---

## 💰 Is it Free? (Yes!)

Google Cloud has a very generous **Free Tier** for observability that covers almost everything Market-Rover needs:

| Service | Feature | Free Tier Limit | Market Rover Usage |
| :--- | :--- | :--- | :--- |
| **Cloud Monitoring** | Custom Dashboards | **Unlimited Free** | Dashboard views and creation. |
| **Cloud Monitoring** | Basic Metrics | **Unlimited Free** | Cloud Run CPU/Mem, Cloud SQL basic stats. |
| **Cloud Logging** | Log Ingestion | **50 GiB / project / month** | Service logs and build logs. |
| **Cloud Monitoring** | API Metrics | First 150 MiB / month | Gemini API latency/error tracking. |
| **Error Reporting** | Global Visibility | **Unlimited Free** | Centralized view of all crashes. |

**Verdict**: As long as your logs don't exceed 50GB per month (highly unlikely for this app), your dashboard and basic monitoring will cost **$0.00**.

---

## 🔍 What this Dashboard Tracks

1.  **Global Health**: Total request volume and 5xx error rates across all microservices.
2.  **Performance**: p50 Latency (how fast users feel the app is).
3.  **Compute Hygiene**: CPU and Memory utilization for Cloud Run (helps detect OOM crashes).
4.  **Database Integrity**: Active connections and disk utilization for Cloud SQL.
5.  **CI/CD Speed**: Build durations and success/failure rates for automated deployments.
