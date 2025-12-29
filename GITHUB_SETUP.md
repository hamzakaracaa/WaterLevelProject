# GitHub Upload Guide

This guide will help you upload your Water Level Project to GitHub.

## Prerequisites

1. **Install Git** (if not already installed):
   - Download from: https://git-scm.com/download/win
   - During installation, select "Add Git to PATH"
   - Verify installation: Open PowerShell and run `git --version`

2. **Create a GitHub Account** (if you don't have one):
   - Go to: https://github.com
   - Sign up for a free account

## Step-by-Step Instructions

### Step 1: Initialize Git Repository (if not already done)

Open PowerShell or Command Prompt in your project directory:

```powershell
cd "D:\UserData\Belgeler\PlatformIO\Projects\WaterLevelProject"
git init
```

### Step 2: Add All Files

```powershell
git add .
```

**Note**: The `.gitignore` file will automatically exclude:
- CSV log files
- Build artifacts (`.pio` folder)
- Python cache files
- IDE settings

### Step 3: Create Initial Commit

```powershell
git commit -m "Initial commit: Water Level Monitoring System v2.0"
```

If this is your first time using Git, you may need to configure your identity:

```powershell
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

Then try the commit again.

### Step 4: Create Repository on GitHub

1. Go to https://github.com and sign in
2. Click the **"+"** icon in the top right corner
3. Select **"New repository"**
4. Fill in the details:
   - **Repository name**: `WaterLevelProject` (or your preferred name)
   - **Description**: "ESP32 Water Level Monitoring System with Python GUI"
   - **Visibility**: Choose Public or Private
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)
5. Click **"Create repository"**

### Step 5: Connect Local Repository to GitHub

After creating the repository, GitHub will show you commands. Use these:

```powershell
# Add the remote repository (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/WaterLevelProject.git

# Rename the default branch to main (if needed)
git branch -M main

# Push your code to GitHub
git push -u origin main
```

**If you get authentication errors**, you may need to:

1. **Use Personal Access Token** (recommended):
   - Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Click "Generate new token (classic)"
   - Give it a name and select scopes: `repo` (full control)
   - Copy the token
   - When prompted for password, paste the token instead

2. **Or use GitHub Desktop** (easier for beginners):
   - Download: https://desktop.github.com/
   - Sign in with your GitHub account
   - File → Add Local Repository
   - Select your project folder
   - Click "Publish repository"

### Step 6: Verify Upload

1. Go to your repository on GitHub: `https://github.com/YOUR_USERNAME/WaterLevelProject`
2. You should see all your files including:
   - `README.md`
   - `src/main.cpp`
   - `src/main.py`
   - `platformio.ini`
   - `requirements.txt`
   - `.gitignore`
   - `LICENSE`

## Future Updates

When you make changes to your project:

```powershell
# Navigate to project directory
cd "D:\UserData\Belgeler\PlatformIO\Projects\WaterLevelProject"

# Check what changed
git status

# Add changed files
git add .

# Commit changes
git commit -m "Description of your changes"

# Push to GitHub
git push
```

## Troubleshooting

### "Repository not found" error
- Check that the repository name matches exactly
- Verify you have access to the repository
- Make sure you're using the correct GitHub username

### "Authentication failed"
- Use Personal Access Token instead of password
- Or use GitHub Desktop for easier authentication

### "Permission denied"
- Make sure you're the owner of the repository
- Check your GitHub account permissions

## Optional: Add Topics/Tags to Your Repository

On your GitHub repository page:
1. Click the gear icon (⚙️) next to "About"
2. Add topics like: `esp32`, `arduino`, `python`, `water-level-sensor`, `iot`, `platformio`
3. Add a website URL if you have one
4. Click "Save changes"

## Optional: Create Releases

For version tracking:
1. Go to your repository → "Releases" → "Create a new release"
2. Tag version: `v2.0`
3. Release title: `Water Level Monitoring System v2.0`
4. Description: List of features and changes
5. Click "Publish release"

---

**Need Help?** Check out GitHub's documentation: https://docs.github.com/en/get-started

