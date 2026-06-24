#!/bin/bash
# ============================================================
# ONE-TIME SETUP SCRIPT
# Fill in the two lines below, save, then run this file.
# ============================================================

# 1. Your info (used to label commits - doesn't need to be perfect)
YOUR_EMAIL="deanshandymanservice1@gmail.com"
YOUR_NAME="Dean Elkins"

# 2. Paste the URL GitHub gave you after creating a new empty repo
#    (Go to https://github.com/new first, create a repo, don't add a README,
#    then copy the URL it shows you - looks like:
#    https://github.com/Deanthehandyman/dean-local-seo.git)
REPO_URL="https://github.com/Deanthehandyman/dean-local-seo.git"

# ============================================================
# Don't edit below this line
# ============================================================

set -e

if [ "$REPO_URL" = "PASTE_YOUR_GITHUB_REPO_URL_HERE" ]; then
  echo "STOP: You need to edit this file first and paste your real GitHub repo URL"
  echo "into the REPO_URL line near the top, then save and run again."
  exit 1
fi

echo "Setting your git identity..."
git config --global user.email "$YOUR_EMAIL"
git config --global user.name "$YOUR_NAME"

echo "Initializing repo..."
git init
git add -A
git commit -m "Initial local SEO site"
git branch -M main

echo "Connecting to GitHub..."
git remote remove origin 2>/dev/null || true
git remote add origin "$REPO_URL"

echo "Pushing to GitHub (this may ask you to log in)..."
git push -u origin main

echo ""
echo "============================================="
echo "DONE. Your code is now on GitHub."
echo "Next: go to https://app.netlify.com and connect this repo."
echo "============================================="
