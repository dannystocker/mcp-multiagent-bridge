#!/bin/bash
# Update all references from old repo name to new name
# Run this after renaming the repository on GitHub

set -e

OLD_NAME="claude-code-bridge"
NEW_NAME="mcp-multiagent-bridge"
OLD_URL="github.com/dannystocker/claude-code-bridge"
NEW_URL="github.com/dannystocker/mcp-multiagent-bridge"

echo "Updating repository references..."
echo "  Old: $OLD_NAME -> New: $NEW_NAME"
echo ""

# Find all occurrences (dry run)
echo "Files to update:"
git grep -l "$OLD_NAME" | grep -v "scripts/update-repo-links.sh" || echo "  (none found)"
echo ""

# Confirm before proceeding
read -p "Proceed with replacement? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# Perform replacements
git grep -l "$OLD_NAME" | grep -v "scripts/update-repo-links.sh" | xargs sed -i "s|$OLD_NAME|$NEW_NAME|g"
git grep -l "$OLD_URL" | grep -v "scripts/update-repo-links.sh" | xargs sed -i "s|$OLD_URL|$NEW_URL|g"

echo ""
echo "✅ Updated all repository references"
echo ""
echo "Files changed:"
git status --short

echo ""
echo "Review changes, then commit:"
echo "  git add -A"
echo "  git commit -m 'chore: update repository references to mcp-multiagent-bridge'"
