# 🚀 Deploy to GitHub - Instructions

## Your repository is ready to push!

**Location:** `/home/sinexo/tools/osint-international/`

---

## Step 1: Configure Git (First Time Only)

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

---

## Step 2: Create Repository on GitHub

1. Go to: https://github.com/new
2. Repository name: `osint-international`
3. Description: "International OSINT Tool - Phone Numbers & Username Search"
4. **Keep it Public or Private** (your choice)
5. **Do NOT initialize with README** (we already have one)
6. Click "Create repository"

---

## Step 3: Push to GitHub

After creating the repository, GitHub will show you commands. Use these:

### Option A: If repository is empty (recommended)
```bash
cd /home/sinexo/tools/osint-international

# Add remote
git remote add origin https://github.com/YOUR_USERNAME/osint-international.git

# Push
git push -u origin main
```

### Option B: Using SSH (if you have SSH keys set up)
```bash
cd /home/sinexo/tools/osint-international

# Add remote
git remote add origin git@github.com:YOUR_USERNAME/osint-international.git

# Push
git push -u origin main
```

**Replace `YOUR_USERNAME` with your actual GitHub username!**

---

## Step 4: Verify

Visit your repository:
```
https://github.com/YOUR_USERNAME/osint-international
```

You should see:
- ✅ README.md displayed on the homepage
- ✅ osint_international.py (the main tool)
- ✅ LICENSE file
- ✅ .gitignore

---

## Authentication

GitHub may ask for authentication:

### HTTPS (recommended for beginners):
- Username: Your GitHub username
- Password: **Use a Personal Access Token** (not your password!)

To create a token:
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `repo` (full control)
4. Generate and save the token
5. Use the token as your password

### SSH (advanced):
Set up SSH keys: https://docs.github.com/en/authentication/connecting-to-github-with-ssh

---

## What's Included

```
osint-international/
├── osint_international.py    # Main tool (secure & clean)
├── README.md                  # Professional documentation
├── LICENSE                    # MIT License with disclaimer
└── .gitignore                 # Excludes sensitive files
```

---

## Security Notes

✅ **Safe to publish:**
- Tool code (secure, no vulnerabilities)
- README documentation
- LICENSE file
- .gitignore

❌ **Not included (protected by .gitignore):**
- Database files (*.db)
- Search results (osint_results/)
- Personal data
- User credentials

---

## After Pushing

### Update Repository Description
1. Go to your repo page
2. Click the gear icon next to "About"
3. Add topics/tags:
   - `osint`
   - `phone-lookup`
   - `username-search`
   - `international`
   - `security`
   - `intelligence`
   - `reconnaissance`

### Add Repository Details
- Website: (leave blank or add your site)
- Topics: Add relevant tags
- Include in GitHub Search: Yes

---

## Quick Commands Summary

```bash
# Navigate to repo
cd /home/sinexo/tools/osint-international

# Check status
git status

# Add remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/osint-international.git

# Push to GitHub
git push -u origin main
```

---

## Troubleshooting

### "fatal: remote origin already exists"
```bash
git remote rm origin
git remote add origin https://github.com/YOUR_USERNAME/osint-international.git
```

### Authentication Failed
Use a Personal Access Token instead of password:
https://github.com/settings/tokens

### Permission Denied (SSH)
Set up SSH keys or use HTTPS instead.

---

## Future Updates

When you make changes:
```bash
cd /home/sinexo/tools/osint-international

# Stage changes
git add .

# Commit
git commit -m "Description of changes"

# Push
git push
```

---

## Repository Ready! 🎉

Your OSINT tool is:
✅ Security reviewed
✅ Code cleaned
✅ Properly documented
✅ Git initialized
✅ Committed
✅ Ready to push

**Just create the repo on GitHub and push!**
