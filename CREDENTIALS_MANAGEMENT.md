# Credentials Management - E2B Hackathon

## 🔐 **SECURITY PRINCIPLES**

1. **Never commit secrets to git**
2. **Rotate all keys after hackathon**
3. **Use environment-specific credentials**
4. **Audit access before sharing**

---

## 📋 **REQUIRED CREDENTIALS**

### **E2B**
- **What:** API Key
- **Where:** https://e2b.dev/dashboard
- **Quota:** Check free tier limits
- **Format:** `e2b_xxxxx...`

### **Groq**
- **What:** API Key
- **Where:** https://console.groq.com/keys
- **Rate Limits:**
  - Free: 30 requests/min, 14,400/day
  - Check: https://console.groq.com/settings/limits
- **Support:** support@groq.com (if rate limit issues)
- **Format:** `gsk_xxxxx...`

### **TweekIT**
- **What:** API Key + API Secret
- **Where:** https://www.tweekit.io → Manage Account
- **Quota:** 10,000 conversions/month (free tier)
- **Format:**
  - Key: alphanumeric string
  - Secret: alphanumeric string

### **GitHub (for PR submission)**
- **What:** Personal Access Token (classic)
- **Where:** https://github.com/settings/tokens
- **Scopes:** `repo`, `workflow`
- **Format:** `ghp_xxxxx...`

### **Streamlit Cloud (if deploying demo)**
- **What:** GitHub OAuth
- **Where:** https://share.streamlit.io
- **Secrets:** Add via app settings (not .env)

---

## 🛠️ **RECOMMENDED APPROACH: direnv + .envrc**

### **Why direnv?**
- Auto-loads/unloads env vars per directory
- Prevents accidental secret leaks
- Works with git-ignored files
- Cross-platform (macOS/Linux)

### **Setup:**

#### **1. Install direnv**
```bash
# macOS
brew install direnv

# Linux
sudo apt install direnv  # or yum, pacman

# Add to shell (~/.zshrc or ~/.bashrc)
eval "$(direnv hook zsh)"   # or bash
```

#### **2. Create .envrc (git-ignored)**
```bash
# File: .envrc
export E2B_API_KEY="e2b_xxxxxxxxxxxxxxxx"
export GROQ_API_KEY="gsk_xxxxxxxxxxxxxxxx"
export TWEEKIT_API_KEY="your-key-here"
export TWEEKIT_API_SECRET="your-secret-here"

# Optional: Docker/deployment
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxx"
export STREAMLIT_SHARING_MODE="prod"
```

#### **3. Whitelist the directory**
```bash
direnv allow .
# Now env vars auto-load when you cd into project
```

#### **4. Add to .gitignore**
```bash
echo ".envrc" >> .gitignore
echo ".env" >> .gitignore
echo ".env.local" >> .gitignore
```

---

## 📝 **ALTERNATIVE: .env with python-dotenv**

If direnv isn't available:

#### **1. Create .env file**
```bash
# File: .env
E2B_API_KEY=e2b_xxxxxxxxxxxxxxxx
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxx
TWEEKIT_API_KEY=your-key-here
TWEEKIT_API_SECRET=your-secret-here
```

#### **2. Load in Python scripts**
```python
# At top of scripts
from dotenv import load_dotenv
import os

load_dotenv()  # Loads .env file

# Access vars
e2b_key = os.getenv("E2B_API_KEY")
groq_key = os.getenv("GROQ_API_KEY")
```

#### **3. Install dotenv**
```bash
pip install python-dotenv
# Add to requirements.txt
```

#### **4. Git ignore**
```bash
echo ".env" >> .gitignore
```

---

## 🔒 **FOR DEMO DEPLOYMENT (Streamlit Cloud)**

### **Never put secrets in code!**

#### **Option A: Streamlit Secrets (Recommended)**
```bash
# In Streamlit Cloud dashboard:
# Settings → Secrets → Add secrets

[secrets]
E2B_API_KEY = "e2b_xxx"
GROQ_API_KEY = "gsk_xxx"
TWEEKIT_API_KEY = "xxx"
TWEEKIT_API_SECRET = "xxx"
```

```python
# In your Streamlit app:
import streamlit as st

e2b_key = st.secrets["E2B_API_KEY"]
groq_key = st.secrets["GROQ_API_KEY"]
```

#### **Option B: Environment Variables (Cloud Run, etc.)**
```bash
# Set via deployment config
gcloud run deploy --set-env-vars="E2B_API_KEY=xxx,GROQ_API_KEY=xxx"
```

---

## 📋 **CREDENTIALS CHECKLIST**

### **Before Starting Work:**
- [ ] All team members have API keys
- [ ] Keys tested and working
- [ ] Rate limits checked
- [ ] .envrc or .env created
- [ ] Git ignoring credential files
- [ ] Backup credentials stored securely (password manager)

### **During Development:**
- [ ] Never hardcode secrets in code
- [ ] Use os.getenv() or st.secrets
- [ ] Check git status before commits
- [ ] Rotate keys if accidentally exposed

### **Before Deployment:**
- [ ] Streamlit secrets configured (if using)
- [ ] Cloud Run env vars set (if using)
- [ ] Test with production credentials
- [ ] Document credential sources for team

### **After Hackathon:**
- [ ] Rotate all API keys
- [ ] Revoke GitHub tokens
- [ ] Delete test credentials
- [ ] Archive .env files (don't delete - might need for support)

---

## 🚨 **EMERGENCY: I COMMITTED A SECRET!**

### **If you accidentally commit credentials:**

#### **1. Immediately revoke the key**
- E2B: Dashboard → Delete key
- Groq: Console → Revoke key
- TweekIT: Account → Regenerate credentials
- GitHub: Settings → Delete token

#### **2. Generate new credentials**
- Get new keys from each service
- Update .envrc / .env
- Share new keys with team (securely)

#### **3. Remove from git history**
```bash
# Quick fix (if not pushed yet)
git reset --soft HEAD~1
# Edit files to remove secrets
git add .
git commit -m "Fix: remove credentials"

# If already pushed (nuclear option)
# Use BFG Repo Cleaner or filter-branch
# WARNING: This rewrites history!
```

#### **4. Notify team**
- Tell everyone keys were rotated
- Update shared password manager
- Check if any services were compromised

---

## 🔐 **SECURE SHARING WITH TEAM**

### **Do NOT use:**
- ❌ Slack/Discord DMs (plaintext)
- ❌ Email (unencrypted)
- ❌ Shared Google Docs
- ❌ Git commits

### **DO use:**
- ✅ 1Password shared vaults
- ✅ LastPass shared folders
- ✅ Bitwarden organizations
- ✅ Encrypted notes (Signal, Wire)
- ✅ In-person transfer (if co-located)

### **Quick Share Pattern:**
```bash
# Sender: Encrypt with gpg
echo "E2B_API_KEY=xxx" | gpg -c > creds.gpg

# Receiver: Decrypt
gpg -d creds.gpg
# Password shared separately (Signal, phone call)
```

---

## 📊 **RATE LIMIT MONITORING**

### **Groq Rate Limits (Free Tier)**
```python
# Check usage
# Visit: https://console.groq.com/usage

# In code: Track requests
from collections import deque
from time import time

class RateLimiter:
    def __init__(self, max_per_minute=30):
        self.max_per_minute = max_per_minute
        self.requests = deque()

    def wait_if_needed(self):
        now = time()
        # Remove requests older than 1 minute
        while self.requests and now - self.requests[0] > 60:
            self.requests.popleft()

        if len(self.requests) >= self.max_per_minute:
            sleep_time = 60 - (now - self.requests[0])
            print(f"Rate limit: sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)

        self.requests.append(now)

# Usage
limiter = RateLimiter(max_per_minute=30)
limiter.wait_if_needed()
# Make Groq API call
```

### **E2B Quota Tracking**
```python
# Check usage in E2B dashboard
# Or track manually:
import os

e2b_usage = {
    "sandboxes_created": 0,
    "total_runtime_seconds": 0
}

def track_e2b_usage(sandbox_id, runtime):
    e2b_usage["sandboxes_created"] += 1
    e2b_usage["total_runtime_seconds"] += runtime
    print(f"E2B Usage: {e2b_usage}")
```

---

## 🆘 **ESCALATION CONTACTS**

### **Groq Support**
- **Email:** support@groq.com
- **Issue:** Rate limit increase request
- **Template:**
  ```
  Subject: Rate Limit Increase Request - E2B Hackathon

  Hello Groq Team,

  We're participating in the E2B hackathon (Nov 21-22) and need a temporary
  rate limit increase.

  Current: 30 req/min
  Needed: 60 req/min (for demo testing)
  Duration: Nov 21-22 only

  Project: TweekIT + Groq agentic workflow demo
  Use case: File conversion + LLM analysis

  Thank you!
  ```

### **E2B Support**
- **Discord:** https://discord.gg/e2b
- **Email:** (check their site)
- **Issue:** Sandbox networking, quota

### **TweekIT Support**
- **Email:** support@tweekit.io
- **Issue:** API quota, conversion errors

---

## ✅ **QUICK START CHECKLIST**

### **Initial Setup (5 minutes)**
```bash
# 1. Install direnv (recommended)
brew install direnv
echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc
source ~/.zshrc

# 2. Create .envrc
cat > .envrc << 'EOF'
export E2B_API_KEY="get-from-e2b.dev"
export GROQ_API_KEY="get-from-console.groq.com"
export TWEEKIT_API_KEY="get-from-tweekit.io"
export TWEEKIT_API_SECRET="get-from-tweekit.io"
EOF

# 3. Whitelist directory
direnv allow .

# 4. Git ignore
echo ".envrc" >> .gitignore
echo ".env" >> .gitignore

# 5. Test
echo $E2B_API_KEY  # Should print your key
```

### **Verify Credentials (2 minutes)**
```bash
# Test E2B
python -c "import os; from e2b_code_interpreter import Sandbox; Sandbox(api_key=os.getenv('E2B_API_KEY')); print('E2B ✓')"

# Test Groq
python -c "import os; from groq import Groq; Groq(api_key=os.getenv('GROQ_API_KEY')).models.list(); print('Groq ✓')"

# Test TweekIT
curl -X POST https://mcp.tweekit.io/mcp \
  -H "ApiKey: $TWEEKIT_API_KEY" \
  -H "ApiSecret: $TWEEKIT_API_SECRET" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}' | grep -q "convert" && echo "TweekIT ✓"
```

---

## 📖 **ADDITIONAL RESOURCES**

- **direnv docs:** https://direnv.net/
- **python-dotenv:** https://pypi.org/project/python-dotenv/
- **Streamlit secrets:** https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management
- **Git secret management:** https://git-secret.io/
- **Security best practices:** https://owasp.org/www-community/vulnerabilities/

---

**REMEMBER:** Treat API keys like passwords. Never commit them. Rotate after hackathon. 🔐
