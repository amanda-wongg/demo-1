# Deployment Instructions for GitHub Pages

Follow these steps to deploy your Stock Market Prediction Game to GitHub Pages:

## 📋 Prerequisites

1. A GitHub account
2. Git installed on your computer

## 🚀 Deployment Steps

### Step 1: Create a New Repository

1. Go to [GitHub](https://github.com) and sign in to your account
2. Click the "+" icon in the top right corner and select "New repository"
3. Name your repository (e.g., `stock-prediction-game`)
4. Make sure it's set to "Public" (required for free GitHub Pages)
5. Click "Create repository"

### Step 2: Upload Your Files

You can either use Git commands or GitHub's web interface:

#### Option A: Using Git Commands

```bash
# Navigate to your project directory
cd /path/to/your/project

# Initialize git repository
git init

# Add all files
git add .

# Commit files
git commit -m "Initial commit: Stock Market Prediction Game"

# Add remote origin (replace 'yourusername' with your GitHub username)
git remote add origin https://github.com/yourusername/stock-prediction-game.git

# Push to GitHub
git branch -M main
git push -u origin main
```

#### Option B: Using GitHub Web Interface

1. In your new repository, click "uploading an existing file"
2. Drag and drop all your files (`index.html`, `script.js`, `README.md`, etc.)
3. Scroll down, add a commit message like "Initial commit"
4. Click "Commit changes"

### Step 3: Enable GitHub Pages

1. In your repository, click on the "Settings" tab
2. Scroll down to the "Pages" section in the left sidebar
3. Under "Source", select "Deploy from a branch"
4. Choose "main" branch and "/ (root)" folder
5. Click "Save"

### Step 4: Access Your Game

1. GitHub will provide you with a URL like: `https://yourusername.github.io/stock-prediction-game/`
2. It may take a few minutes for the site to become available
3. Visit the URL to play your game!

## 🔧 Automatic Deployment

The included GitHub Actions workflow (`.github/workflows/deploy.yml`) will automatically deploy your site whenever you push changes to the main branch.

## 🐛 Troubleshooting

### Common Issues:

1. **Site not loading**: Wait 5-10 minutes after enabling Pages
2. **404 Error**: Make sure your main file is named `index.html`
3. **API not working**: Check browser console for CORS errors (Alpha Vantage should work fine)

### CORS Issues:

If you encounter CORS issues with the Alpha Vantage API:
1. The API should work fine from GitHub Pages
2. If testing locally, you may need to run a local server:
   ```bash
   # Python 3
   python -m http.server 8000
   
   # Python 2
   python -m SimpleHTTPServer 8000
   
   # Node.js (if you have npx)
   npx serve .
   ```

## 🔑 API Key Security

The Alpha Vantage API key included is for demonstration purposes. For production use:
1. Get your own free API key at [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
2. Replace the API key in `script.js`
3. Consider using environment variables for sensitive keys in more complex applications

## 📈 Updates

To update your game:
1. Make changes to your files
2. Commit and push to the main branch
3. GitHub Pages will automatically update your live site

Your Stock Market Prediction Game is now live and ready to play! 🎉