# Railway Deployment Guide - FMCSA Scraper

## Files Created for Deployment:
- `deploy_requirements.txt` - Lists all Python packages needed
- `Procfile` - Tells Railway how to run your app
- `railway.json` - Railway configuration
- `runtime.txt` - Specifies Python version

## Step-by-Step Railway Deployment:

### Step 1: Download Your Code
1. In Replit, go to Files panel (left side)
2. Click the 3 dots menu → "Download as zip"
3. Extract the zip file on your computer
4. **IMPORTANT**: Before uploading, rename `deploy_requirements.txt` to `requirements.txt`

### Step 2: Create GitHub Repository
1. Go to https://github.com
2. Click "Sign up" if you don't have account (it's free)
3. Click green "New" button to create repository
4. Name it: `fmcsa-scraper`
5. Make it "Public" 
6. Click "Create repository"

### Step 3: Upload Your Code to GitHub
1. In your new repository, click "uploading an existing file"
2. Drag all your extracted files into the upload box
3. **Make sure these files are included:**
   - `app.py`
   - `license_service.py` 
   - `scraper.py`
   - `requirements.txt` (renamed from deploy_requirements.txt)
   - `Procfile`
   - `railway.json`
   - `runtime.txt`
   - `templates/` folder with all HTML files
   - `static/` folder with CSS and JS files
4. Write commit message: "Initial deployment files"
5. Click "Commit changes"

### Step 4: Deploy on Railway
1. Go to https://railway.app
2. Click "Start a New Project"
3. Sign in with your GitHub account
4. Click "Deploy from GitHub repo"
5. Select your `fmcsa-scraper` repository
6. Click "Deploy Now"

### Step 5: Configure Environment Variables
1. In Railway dashboard, click your project
2. Go to "Variables" tab
3. Add this variable:
   - Name: `SECRET_KEY`
   - Value: `your-secret-key-here-make-it-random`

### Step 6: Get Your Live URL
1. Go to "Settings" tab in Railway
2. Click "Generate Domain"
3. Your app will be live at: `https://your-app-name.up.railway.app`

## Important Notes:

### For Google Sheets Access:
- Your Google Sheets URL should work automatically
- Make sure your Google Sheet is set to "Anyone with the link can view"

### If You Get Errors:
- Check "Deploy" tab in Railway for error messages
- Most common issue: Make sure all files uploaded correctly
- Contact support if needed: hasnainabbas.contact@gmail.com

### Your App Features That Will Work:
✅ License key validation from Google Sheets
✅ Real-time web scraping from FMCSA
✅ Background license expiry monitoring
✅ Professional login system
✅ Data export (CSV, Excel, TXT)
✅ Real-time progress updates

## Cost: 
- Railway free tier gives you 500 hours/month + $5 credit
- Your app should run completely free
- No hidden costs or surprises

## Support:
If you need help with deployment:
- Email: hasnainabbas.contact@gmail.com
- WhatsApp: +923070467687