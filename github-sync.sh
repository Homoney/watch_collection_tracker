#!/bin/bash

echo "========================================="
echo "GitHub Sync - Watch Collection Tracker"
echo "========================================="
echo ""

# Check if git is initialized
if [ ! -d .git ]; then
    echo "Initializing git repository..."
    git init
    echo "✓ Git initialized"
fi

# Check if there are staged or committed files
if [ -z "$(git status --porcelain)" ]; then
    echo "Repository is clean, nothing to commit"
else
    echo "Staging all files..."
    git add .

    echo ""
    echo "Creating initial commit..."
    git commit -m "feat: initial implementation - Phase 1 Foundation

- Complete authentication system with JWT tokens
- FastAPI backend with SQLAlchemy and Alembic
- React + TypeScript frontend with TailwindCSS
- Docker Compose multi-container setup
- PostgreSQL database with full schema
- Nginx reverse proxy with security headers
- Comprehensive documentation

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

    echo "✓ Initial commit created"
fi

# Check if remote exists
if git remote | grep -q "^origin$"; then
    echo ""
    echo "Remote 'origin' already exists:"
    git remote get-url origin
else
    echo ""
    echo "Creating GitHub repository in Homoney organization..."

    # Create the repo using gh CLI
    gh repo create Homoney/watch-collection-tracker \
        --public \
        --source=. \
        --remote=origin \
        --description="Modern web app for watch collectors - track collections with multi-user support, authentication, and more"

    if [ $? -eq 0 ]; then
        echo "✓ GitHub repository created"
    else
        echo "⚠ Failed to create repository. Please check your gh CLI authentication."
        exit 1
    fi
fi

# Push to GitHub
echo ""
echo "Pushing to GitHub..."
git branch -M main
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================="
    echo "✓ Successfully synced to GitHub!"
    echo "========================================="
    echo ""
    echo "Repository URL:"
    gh repo view Homoney/watch-collection-tracker --web --json url -q .url
    echo ""
    echo "You can view it at:"
    echo "https://github.com/Homoney/watch-collection-tracker"
else
    echo ""
    echo "⚠ Push failed. This might be because:"
    echo "  1. The repository already exists - try: git push origin main"
    echo "  2. You need to authenticate with gh CLI: gh auth login"
    echo "  3. You don't have permission to create repos in Homoney org"
fi
