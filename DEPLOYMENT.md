# Deploying Market-Rover to Streamlit Community Cloud

## Overview
This guide walks you through deploying Market-Rover to Streamlit Community Cloud for free, public hosting with built-in authentication.

---

## Prerequisites

✅ **What you need**:
1. GitHub account
2. Streamlit Community Cloud account (free - sign up at [share.streamlit.io](https://share.streamlit.io))
3. Google Gemini API key ([get one here](https://makersuite.google.com/app/apikey))
4. Market-Rover code (this repository)

---

## Step 1: Prepare Your Repository

### 1.1 Push to GitHub

If not already on GitHub:

```bash
# Initialize git if needed
git init

# Add remote (replace with your GitHub repo URL)
git remote add origin https://github.com/YOUR_USERNAME/Market-Rover.git

# Add all files
git add .

# Commit
git commit -m "feat: Market-Rover - Ready for Streamlit Cloud deployment"

# Push to GitHub
git push -u origin main
```

### 1.2 Verify Files

Make sure these files are in your repository:
- ✅ `app.py` (main Streamlit app)
- ✅ `requirements.txt` (all dependencies)
- ✅ `.streamlit/config.toml` (configuration)
- ✅ `.gitignore` (includes `.streamlit/secrets.toml`)
- ✅ All other Python files (agents.py, crew.py, etc.)

⚠️ **DO NOT** commit:
- ❌ `.env` file
- ❌ `.streamlit/secrets.toml`
- ❌ Your API keys

---

## Step 2: Deploy to Streamlit Cloud

### 2.1 Sign in to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Authorize Streamlit to access your repositories

### 2.2 Create New App

1. Click "New app" button
2. Fill in the details:
   - **Repository**: `YOUR_USERNAME/Market-Rover`
   - **Branch**: `main`
   - **Main file path**: `app.py`
   - **App URL** (optional): Choose a custom name like `market-rover`

3. Click "Deploy!"

---

## Step 3: Configure Secrets

### 3.1 Add API Key

While the app is deploying (or after), add your API key:

1. Click on the app's settings (⚙️ icon) or go to "App settings"
2. Navigate to "Secrets" section
3. Add your secrets in TOML format:

```toml
GOOGLE_API_KEY = "your-actual-google-api-key-here"

# Optional: Override defaults
MAX_PARALLEL_STOCKS = 5
RATE_LIMIT_DELAY = 1.0
```

4. Click "Save"

### 3.2 Verify Secrets

The app will automatically restart when you save secrets. Check that it loads without errors.

---

## Step 4: Test Your Deployment

### 4.1 Access Your App

Your app will be live at: `https://YOUR_APP_NAME.streamlit.app`

### 4.2 Test Features

1. **Upload Portfolio**:
   - Use the test portfolio or create a new one
   - Upload CSV file

2. **Test Mode**:
   - Enable "Test Mode (No API Calls)" first
   - Click "Analyze Portfolio"
   - Verify visualizations appear

3. **Real API Mode**:
   - Disable test mode
   - Run analysis with 1-2 stocks
   - Verify Gemini API responds

4. **View Reports**:
   - Use the **Sidebar > Portfolio Analysis** to view past reports.
   - Check HTML reports with visualizations

---

## Step 5: Configure Access Control

### 5.1 Streamlit Cloud Authentication

Streamlit Community Cloud has built-in options:

1. **Public** (default): Anyone can access
2. **Restricted**: Only you can access
3. **Specific viewers**: Share with specific people

To configure:
1. Go to App settings → Sharing
2. Choose your preferred access level
3. Add email addresses if using "Specific viewers"

### 5.2 Free Tier Limits

**Streamlit Community Cloud Free Tier**:
- ✅ 1 GB RAM
- ✅ 1 CPU core  
- ✅ Unlimited apps (public repos)
- ✅ Built-in authentication
- ✅ HTTPS included
- ⚠️ Apps can sleep after inactivity

**Gemini API Free Tier**:
- ✅ 2 requests per minute
- ✅ 20 requests per day
- Suitable for personal use / demo

---

## Troubleshooting

### Issue: App Won't Start

**Check**:
1. Requirements.txt complete?
2. Secrets configured correctly?
3. Check app logs in Streamlit Cloud dashboard

**Common fixes**:
```bash
# Verify requirements locally
pip install -r requirements.txt

# Test app locally
streamlit run app.py
```

### Issue: API Key Not Working

**Check**:
1. Secrets format is valid TOML
2. Key name is `GOOGLE_API_KEY` (exact match)
3. No quotes issues (use double quotes in TOML)
4. API key is active in Google AI Studio

### Issue: App is Slow

**Solutions**:
1. Use Test Mode for demos
2. Limit portfolio to 5-10 stocks
3. Monitor Gemini API rate limits (20/day on free tier)
4. Consider upgrading Streamlit Cloud plan for more resources

### Issue: Security Vulnerabilities

**Run security audit**:
```bash
# Install safety
pip install safety

# Check for vulnerabilities
safety check

# Update vulnerable packages
pip install --upgrade PACKAGE_NAME
```

---

## Best Practices

### Production Use

1. **API Key Security**:
   - ✅ Use Streamlit secrets (never commit .env)
   - ✅ Rotate keys regularly
   - ✅ Monitor usage in Google AI Studio

2. **Access Control**:
   - 🔒 Use "Specific viewers" for team access
   - 🔒 Don't share public URL widely if using free API tier

3. **Resource Management**:
   - ⚡ Use Test Mode for demos/testing
   - ⚡ Monitor Gemini API quota (20 requests/day limit)
   - ⚡ Consider paid tier if exceeding limits

4. **Monitoring**:
   - 📊 Check Streamlit Cloud logs regularly
   - 📊 Monitor Gemini API usage
   - 📊 Track error rates

---

## Updating Your App

### Push Updates

```bash
# Make changes locally
git add .
git commit -m "feat: add new feature"
git push

# Streamlit Cloud auto-deploys on push!
```

### Manual Reboot

If needed:
1. Go to Streamlit Cloud dashboard
2. Click app settings
3. Click "Reboot app"

---

## Cost Estimate

**Free Tier (Recommended for Personal Use)**:
- Streamlit Cloud: **FREE**
- Gemini API: **FREE** (20 requests/day)
- Total: **$0/month** ✅

**Paid Tier (If Exceeding Limits)**:
- Streamlit Cloud: $20/month (Team plan)
- Gemini API: ~$1-5/month (light usage)
- Total: ~$21-25/month

---

## Next Steps

✅ **Your app is now live!**

**Share it**:
- Send URL to team members
- Configure access control
- Monitor usage and costs

**Enhance it**:
- Customize theme in `.streamlit/config.toml`
- Add more visualization types
- Implement advanced features

---

## Support

**Issues?**
- Check [Streamlit Community Forum](https://discuss.streamlit.io)
- Review [Streamlit Cloud Docs](https://docs.streamlit.io/streamlit-community-cloud)
- Check Gemini API [status page](https://status.cloud.google.com)

**Security Concerns?**
- Report via GitHub Issues
- Review security best practices
- Keep dependencies updated

---

**Congratulations! 🎉 Market-Rover 2.0 is now in production!**
