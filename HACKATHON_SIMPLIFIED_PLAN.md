# E2B Hackathon – SIMPLIFIED Plan _(Archived)_
**Status (Nov 23, 2025):** Stage demo and MCP are deployed; submission deadline was missed. Use this plan for historical context only.

---

## 🎯 **CORE STRATEGY**

You already have a working web converter (`examples/web-converter/index.html`).

**The hackathon requirements:**
1. ✅ Use E2B sandbox
2. ✅ Use ≥1 MCP from Docker Hub
3. ✅ Working demo <2 minutes

**Our approach:**
1. Submit TweekIT to Docker MCP Hub (remote server)
2. Show E2B sandbox calling TweekIT MCP
3. Use your existing web converter as the demo UI
4. Make Groq/other use-cases optional

---

## 📋 **3 CORE WORKSTREAMS** (Down from 6!)

### **WS1: Docker MCP Hub Submission** ⚡ CRITICAL (2-3 hrs, Tonight)
**Owner:** 1 person
**Status:** Files ready in `docker-mcp-submission/`

#### **Tasks:**
- [ ] Fork `docker/mcp-registry`
- [ ] Copy files to `servers/tweekit/`
- [ ] Submit PR
- [ ] Provide test credentials

#### **Commands:**
```bash
gh repo fork docker/mcp-registry --clone
cd mcp-registry
mkdir -p servers/tweekit
cp ~/Documents/projects/tweekit-mcp-docker-groq-e2b/docker-mcp-submission/* servers/tweekit/
git checkout -b add-tweekit-mcp
git add servers/tweekit/
git commit -m "Add TweekIT MCP - Universal media converter for agentic workflows"
git push origin add-tweekit-mcp
gh pr create --repo docker/mcp-registry --title "Add TweekIT MCP" --body "..."
```

**Done when:** PR submitted, test credentials provided

---

### **WS2: E2B Integration Proof-of-Concept** ⚡ CRITICAL (4-6 hrs, Friday)
**Owner:** 1 person
**Goal:** Prove E2B sandbox can call TweekIT MCP

#### **Tasks:**
- [ ] E2B account + API key
- [ ] Simple Python script that:
  - Creates E2B sandbox
  - Calls TweekIT MCP convert tool
  - Returns result
- [ ] Test with 3-5 file formats
- [ ] Document how it works

#### **Core Script:**
`scripts/e2b_mcp_demo.py`
```python
#!/usr/bin/env python3
"""E2B calling TweekIT MCP - Proof of Concept"""
import os
import base64
from e2b_code_interpreter import Sandbox

def test_e2b_tweekit_integration():
    """Test E2B sandbox calling TweekIT MCP from Docker Hub"""

    # Create E2B sandbox
    print("Creating E2B sandbox...")
    sandbox = Sandbox(api_key=os.getenv("E2B_API_KEY"))

    # Install HTTP client in sandbox
    sandbox.run_code("!pip install httpx")

    # Test calling TweekIT MCP
    result = sandbox.run_code(f"""
import httpx
import base64

# Sample small file (1x1 PNG)
tiny_png = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

# Call TweekIT MCP convert tool
response = httpx.post(
    'https://mcp.tweekit.io/mcp',
    headers={{
        'Content-Type': 'application/json',
        'ApiKey': '{os.getenv("TWEEKIT_API_KEY")}',
        'ApiSecret': '{os.getenv("TWEEKIT_API_SECRET")}'
    }},
    json={{
        'jsonrpc': '2.0',
        'method': 'tools/call',
        'params': {{
            'name': 'convert',
            'arguments': {{
                'inext': 'png',
                'outfmt': 'webp',
                'blob': tiny_png,
                'width': 100,
                'height': 100
            }}
        }},
        'id': 1
    }},
    timeout=30.0
)

print(f"Status: {{response.status_code}}")
print(f"Result: {{response.text[:200]}}")
    """)

    print("E2B Result:", result)
    return result

if __name__ == "__main__":
    test_e2b_tweekit_integration()
```

**Test with:**
- DOC → PDF
- XLS → PNG
- PSD → JPG
- TIFF → WebP
- URL conversion

**Done when:** E2B successfully calls TweekIT MCP and gets results back

---

### **WS3: Demo Video + Submission** 🎬 CRITICAL (4-6 hrs, Saturday)
**Owner:** 1-2 people
**Goal:** Create submission package

#### **Tasks:**
- [ ] Record 2-minute demo video
- [ ] Write HACKATHON_SUBMISSION.md
- [ ] Update README with hackathon info
- [ ] Create architecture diagram
- [ ] Submit to hackathon

#### **Demo Video Script (2 min):**
```
[0:00-0:20] THE PROBLEM
- Show error: "AI tool rejects DOC/XLS/PSD file"
- Voiceover: "Agentic workflows break when users upload unsupported formats"

[0:20-0:40] THE SOLUTION
- Show architecture: E2B → Docker MCP Hub → TweekIT
- Voiceover: "TweekIT MCP removes blockers. E2B runs code safely."

[0:40-1:20] LIVE DEMO
Option A (Simple): Show Python script calling MCP from E2B
- Run e2b_mcp_demo.py
- Show sandbox logs
- Show successful conversion

Option B (Advanced): Show web converter + E2B integration
- Open examples/web-converter/index.html
- Upload legacy DOC file
- Show conversion to PDF
- Mention "Powered by E2B + TweekIT MCP"

[1:20-1:50] THE STACK
- Docker MCP Hub (TweekIT remote server)
- E2B sandbox (safe execution)
- 400+ formats supported
- Enterprise-grade (20 years)

[1:50-2:00] CALL TO ACTION
- "Try it: tweekit.io"
- "Install: docker mcp install tweekit"
```

#### **Submission Document:**
`HACKATHON_SUBMISSION.md`
```markdown
# E2B Hackathon: TweekIT MCP

## Problem
Agentic workflows fail when users upload unsupported file formats (DOC, XLS, PSD, DWG, etc.). This blocks automation and frustrates users.

## Solution
TweekIT MCP Server + E2B Sandbox = Complete format compatibility

- **TweekIT MCP:** Converts 400+ formats (Docker MCP Hub)
- **E2B Sandbox:** Safe code execution environment
- **Result:** Agents can process ANY file format

## Innovation
- **First MCP with 400+ format support**
- **On-demand optimization** (resize, crop, format)
- **Enterprise-grade** (20 years production)
- **Removes agentic workflow blockers** (core value prop)

## Technical Stack
- E2B Sandbox (Python SDK)
- Docker MCP Hub (TweekIT remote server)
- TweekIT REST API (Cloud Run backend)
- ISO 27001/SAS 70 compliant processing

## Demo
- **Video:** [YouTube link]
- **Code:** https://github.com/equilibrium-team/tweekit-mcp
- **Try it:** https://www.tweekit.io

## Use Case
User uploads DOC file → Agent fails ❌
User uploads DOC file → E2B calls TweekIT MCP → Converts to PDF → Agent succeeds ✅

## Team
Equilibrium - 20+ years enterprise media processing (MediaRich, DeBabelizer heritage)
```

**Done when:** Video uploaded, submission document complete, submitted by 6 PM Saturday

---

## 🎯 **OPTIONAL ENHANCEMENTS** (If time allows)

### **Optional: Groq Integration** (3-4 hrs)
**Only do this if WS1-WS3 are done early**

Add Groq analysis after TweekIT conversion:
```python
# After converting DOC → PDF with TweekIT
# Analyze with Groq
from groq import Groq
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
analysis = client.chat.completions.create(
    model="mixtral-8x7b-32768",
    messages=[{"role": "user", "content": f"Summarize: {converted_content}"}]
)
```

**Only add if:**
- WS2 is done by Friday 3 PM
- Team has bandwidth
- Groq API key ready

---

## ⏰ **SIMPLIFIED TIMELINE**

### **Thursday Night (Tonight, 2-3 hrs)**
- **WS1:** Submit Docker MCP PR ✅
- **Setup:** E2B account, Groq account (if using)

### **Friday (4-6 hrs)**
- **WS2:** Build E2B integration script ✅
- **Test:** Verify E2B → TweekIT MCP works
- **Optional:** Add Groq if time

### **Saturday (4-6 hrs)**
- **WS3:** Record demo video
- **WS3:** Write submission docs
- **WS3:** Submit by 6 PM ✅

---

## 📊 **TEAM SIZE OPTIONS**

| Team Size | Assignment |
|-----------|------------|
| **1 person** | Do WS1 tonight, WS2 Friday, WS3 Saturday |
| **2 people** | Person A: WS1+WS2, Person B: WS3 (can start docs Friday) |
| **3+ people** | Person A: WS1, Person B: WS2+optional Groq, Person C: WS3 |

---

## ✅ **HACKATHON REQUIREMENTS CHECK**

✅ **Use E2B sandbox:** WS2 proves E2B calling TweekIT MCP
✅ **Use ≥1 Docker MCP:** TweekIT from Docker MCP Hub (WS1)
✅ **Working demo <2 min:** Video shows real execution (WS3)
✅ **Innovation:** First MCP with 400+ formats, removes workflow blockers

---

## 🎯 **SUCCESS CRITERIA**

**MUST HAVE (to submit):**
- [ ] Docker MCP PR submitted
- [ ] E2B script calling TweekIT MCP works
- [ ] 2-minute demo video
- [ ] Submission document
- [ ] Submitted by 6 PM Saturday

**NICE TO HAVE (bonus points):**
- [ ] Groq integration
- [ ] Multiple use cases shown
- [ ] Web converter deployed publicly
- [ ] Professional slide deck

---

## 🚨 **RISK MITIGATION**

| Risk | Mitigation |
|------|------------|
| Docker approval delay | Submit as "remote server" (doesn't need Docker build approval) |
| E2B connectivity issues | Test early Friday; use mock if needed |
| Video quality issues | Simple screen recording + voiceover is fine |
| Time overrun | Cut Groq, focus on core demo |

---

## 💡 **KEY INSIGHTS**

**What changed:**
- Realized you have working web converter already ✅
- Don't need to build new Streamlit app ❌
- Focus on E2B + MCP integration only ✅
- Make Groq optional ⚡

**Why this is better:**
- Less work (3 workstreams vs 6)
- Uses proven components (your web converter)
- Focuses on hackathon requirements
- More time for polish

---

## 🚀 **NEXT IMMEDIATE STEPS**

1. **Tonight:** Do WS1 (submit Docker PR) - 2 hours
2. **Friday:** Do WS2 (E2B integration) - 4-6 hours
3. **Saturday:** Do WS3 (demo video + submit) - 4-6 hours

**Total work: 10-14 hours across 3 days = Very achievable** ✅
