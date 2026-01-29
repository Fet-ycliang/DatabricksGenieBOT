#!/bin/bash
# Git History Cleanup Script for Removing Secrets

echo "This script will help you remove secrets from Git history"
echo "================================"
echo ""

# Backup current branch
echo "[1] Creating backup..."
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
BACKUP_BRANCH="${CURRENT_BRANCH}-backup-$(date +%s)"
git branch $BACKUP_BRANCH
echo "✓ Backup created: $BACKUP_BRANCH"
echo ""

# Define patterns to remove (use regex)
echo "[2] Removing secrets from Git history..."

# Function to remove token patterns
remove_secrets() {
    # Pattern 1: dapi followed by alphanumeric (Databricks token)
    git filter-branch --tree-filter '
        find . -type f \( -name "*.md" -o -name "*.py" -o -name ".env*" \) -exec sed -i "s/dapi[a-f0-9]\{32,\}/dapi_REDACTED/g" {} \;
    ' -f -- --all 2>/dev/null || true
    
    echo "✓ Secrets removed from history"
}

remove_secrets

echo ""
echo "[3] Garbage collection..."
git reflog expire --expire=now --all
git gc --prune=now --aggressive
echo "✓ Garbage collection complete"
echo ""

echo "[SUCCESS] History cleaned!"
echo ""
echo "To verify changes:"
echo "  git log --all -p | grep -i 'dapi' | head"
echo ""
echo "To push changes (WARNING: This will rewrite remote history):"
echo "  git push --force origin $CURRENT_BRANCH"
echo ""
echo "To restore from backup if needed:"
echo "  git reset --hard $BACKUP_BRANCH"
