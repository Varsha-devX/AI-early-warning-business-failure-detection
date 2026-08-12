<#
.SYNOPSIS
    Bidirectional Git Sync Script
.DESCRIPTION
    Syncs your local repo with origin and your friend's fork.
    - Pulls latest changes from both origin and friend's fork
    - Pushes your local changes to origin
    - Your friend can then pull from origin to get your changes
.USAGE
    .\sync.ps1                  # Full sync (pull from all remotes + push your changes)
    .\sync.ps1 -PullOnly        # Only pull changes from all remotes
    .\sync.ps1 -PushOnly        # Only push your changes to origin
    .\sync.ps1 -Message "msg"   # Commit all changes with a message and sync
#>

param(
    [switch]$PullOnly,
    [switch]$PushOnly,
    [string]$Message
)

$ErrorActionPreference = "Stop"
$repoPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoPath

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Git Bidirectional Sync Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# --- Helper function ---
function Write-Step($text) {
    Write-Host "[*] $text" -ForegroundColor Yellow
}
function Write-OK($text) {
    Write-Host "[+] $text" -ForegroundColor Green
}
function Write-Err($text) {
    Write-Host "[!] $text" -ForegroundColor Red
}

# --- Check if friend remote exists ---
$remotes = git remote
$hasFriend = $remotes -contains "friend"

# --- If user wants to commit local changes ---
if ($Message) {
    Write-Step "Staging all changes..."
    git add -A
    Write-Step "Committing with message: '$Message'"
    git commit -m $Message
    Write-OK "Changes committed."
    Write-Host ""
}

# --- PULL: Fetch and merge from all remotes ---
if (-not $PushOnly) {
    Write-Step "Fetching latest from origin..."
    git fetch origin
    Write-OK "Fetched origin."

    Write-Step "Merging origin/main into your local main..."
    try {
        git merge origin/main --no-edit
        Write-OK "Merged origin/main successfully."
    } catch {
        Write-Err "Merge conflict with origin/main! Resolve conflicts, then run sync again."
        exit 1
    }
    Write-Host ""

    if ($hasFriend) {
        Write-Step "Fetching latest from friend's fork..."
        git fetch friend
        Write-OK "Fetched friend."

        Write-Step "Merging friend/main into your local main..."
        try {
            git merge friend/main --no-edit
            Write-OK "Merged friend/main successfully."
        } catch {
            Write-Err "Merge conflict with friend/main! Resolve conflicts, then run sync again."
            exit 1
        }
        Write-Host ""
    } else {
        Write-Host "[i] No 'friend' remote found. Skipping friend sync." -ForegroundColor DarkGray
        Write-Host "    Run: git remote add friend https://github.com/<friend>/AI-early-warning-business-failure-detection.git" -ForegroundColor DarkGray
        Write-Host ""
    }
}

# --- PUSH: Push your merged changes to origin AND friend's fork ---
if (-not $PullOnly) {
    Write-Step "Pushing changes to origin/main..."
    try {
        git push origin main
        Write-OK "Pushed to origin/main successfully."
    } catch {
        Write-Err "Push to origin failed! You may need to pull first."
        exit 1
    }

    if ($hasFriend) {
        Write-Step "Pushing changes to friend/main..."
        try {
            git push friend main
            Write-OK "Pushed to friend/main successfully. Changes will reflect in friend's fork!"
        } catch {
            Write-Err "Push to friend's fork failed! Make sure your friend has added you as a collaborator."
            Write-Host "    Ask your friend to go to: Settings -> Collaborators -> Add your GitHub username" -ForegroundColor DarkGray
        }
    }
    Write-Host ""
}

# --- Summary ---
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Sync Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Status:" -ForegroundColor White
git log --oneline -3
Write-Host ""

if (-not $hasFriend) {
    Write-Host "TIP: Add your friend's fork with:" -ForegroundColor Magenta
    Write-Host "  git remote add friend https://github.com/<friend-username>/AI-early-warning-business-failure-detection.git" -ForegroundColor White
    Write-Host ""
}
