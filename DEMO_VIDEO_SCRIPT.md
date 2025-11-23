# E2B Hackathon Demo Video Script
**Duration:** 2 minutes maximum
**Style:** Terminal demo with voiceover
**Format:** Screen recording + narration

---

## 🎬 SCENE 1: THE PROBLEM (0:00-0:20)

### Visual:
- Screen showing a typical AI agent error message
- OR: Simple slide with file icons (DOC, XLS, PSD) with red X marks
- Text overlay: "Error: Unsupported file format"

### What You Say:
> "AI agents fail when users upload legacy file formats. DOC files, old Excel spreadsheets, Photoshop documents—they all break the workflow. Manual conversion is slow, and it defeats the purpose of automation."

### Timing: **20 seconds**

---

## 🎬 SCENE 2: THE SOLUTION (0:20-0:40)

### Visual:
- Simple architecture diagram showing flow:
  ```
  User File → E2B Sandbox → TweekIT MCP → Groq Analysis → Results
  ```
- OR: Show three logos side by side (E2B, TweekIT, Groq)

### What You Say:
> "The solution? Combine three powerful tools. E2B provides secure sandbox execution. TweekIT MCP handles 400 file formats on demand. And Groq delivers instant AI analysis. Together, they eliminate workflow blockers completely."

### Timing: **20 seconds**

---

## 🎬 SCENE 3: LIVE DEMO (0:40-1:20)

### Visual:
**Terminal screen recording showing actual execution**

Start with terminal showing:
```bash
$ python scripts/e2b_demo_agent.py
```

### What You Say:
> "Let's see it in action. I'm running a simple Python script that processes a legacy Word document."

**[Pause as terminal shows output]**

> "First, it creates an E2B sandbox—a secure, isolated environment."

**[Terminal shows: "Creating E2B sandbox..."]**
**Overlay: ✅ E2B Sandbox Created**

> "Next, it calls the TweekIT MCP from Docker Hub to convert the DOC file to PDF."

**[Terminal shows: "Converting DOC → PDF..."]**
**Overlay: ⚡ Converting... (with small spinner)**

> "Conversion complete in under two seconds."

**[Terminal shows: "SUCCESS: Converted"]**
**Overlay: ✅ Converted in 1.8s**

> "Finally, Groq analyzes the content and extracts key insights."

**[Terminal shows: "Analyzing with Groq..." followed by analysis output]**
**Overlay: 🤖 Groq Analysis Complete**

> "Total processing time? Less than three seconds. No manual steps. Completely automated."

**[Final overlay: ⏱️ Total: 2.9 seconds]**

### Timing: **40 seconds**

---

## 🎬 SCENE 4: THE STACK (1:20-1:45)

### Visual:
Split screen or quick cuts showing:
1. Docker MCP Hub page (TweekIT listing)
2. E2B dashboard (optional)
3. Text slide with key stats

### What You Say:
> "This runs on production-grade infrastructure. TweekIT's conversion engine has twenty years in production, trusted by Fortune 500 companies. It supports over 400 file formats—from legacy Office docs to CAD files and Adobe formats. Available now on Docker's MCP Hub."

### Timing: **25 seconds**

### Text Overlays (show one at a time):
- "400+ formats supported"
- "20 years enterprise-proven"
- "Docker MCP Hub ready"

---

## 🎬 SCENE 5: CALL TO ACTION (1:45-2:00)

### Visual:
Simple end card with text:

```
🚀 TweekIT MCP + E2B + Groq

Try it: tweekit.io
Install: docker mcp install tweekit

First MCP to eliminate format workflow blockers
```

### What You Say:
> "Try it yourself at tweekit dot io. Install it from Docker MCP Hub with one command. The first MCP solution to truly eliminate format workflow blockers."

### Timing: **15 seconds**

---

## 📋 PRODUCTION CHECKLIST

### Before Recording:
- [ ] Test `scripts/e2b_demo_agent.py` runs successfully
- [ ] Have architecture diagram ready (PNG/PDF)
- [ ] Prepare error screenshot for Scene 1
- [ ] Have Docker Hub page open (for Scene 4)
- [ ] Test microphone in quiet room
- [ ] Close unnecessary apps (clean desktop)

### During Recording:
- [ ] Record terminal at 1080p or higher
- [ ] Use large font in terminal (18-24pt for readability)
- [ ] Slow down slightly when speaking (easier to follow)
- [ ] Pause between sections (easier to edit)

### After Recording:
- [ ] Add text overlays at key moments (see script above)
- [ ] Speed up any slow parts to 1.5x (keep under 2 min)
- [ ] Add simple fade transitions between scenes
- [ ] Check audio levels (consistent volume)
- [ ] Export as MP4, 1080p, 30fps

---

## 🎯 KEY MESSAGES TO EMPHASIZE

1. **Speed**: "Under 3 seconds total" / "Less than 2 seconds conversion"
2. **Scale**: "400+ formats" / "20 years in production"
3. **Innovation**: "First MCP to eliminate format blockers"
4. **Enterprise**: "Fortune 500 trusted" / "Production-ready"
5. **Integration**: "E2B + TweekIT + Groq working together"

---

## 🎨 VISUAL STYLE GUIDE

### Colors:
- ✅ Green for success/checkmarks
- ⚡ Yellow/Orange for action/processing
- 🤖 Blue for AI/analysis
- ⏱️ White for timing

### Fonts:
- Sans-serif (Arial, Helvetica)
- Bold for emphasis
- Large enough to read on mobile

### Keep It Clean:
- Minimal overlays (don't clutter)
- One message at a time
- High contrast text (white on dark bg)

---

## 💡 ALTERNATIVE QUICK VERSION

**If pressed for time, use this 90-second version:**

Cut Scene 4 (The Stack) down to 10 seconds:
> "Built on Docker MCP Hub. 400 formats. 20 years proven. Production ready."

Extend Scene 3 (Demo) to show more detail.

---

## 📝 VOICEOVER RECORDING TIPS

1. **Read through 2-3 times** before recording (get comfortable)
2. **Smile while speaking** (it comes through in your voice)
3. **Use a conversational tone** (not robotic/scripted)
4. **Emphasize numbers**: "FOUR HUNDRED formats", "UNDER THREE seconds"
5. **Pause after key points** (let them sink in)
6. **Record 2-3 full takes** (pick the best, or mix/match)

---

## 🎬 EDITING SHORTCUTS

### Quick Overlay in iMovie:
1. Import video
2. Click Titles → choose "Lower Third" or "Centered"
3. Type text, adjust duration
4. Position at key moments

### Quick Overlay in DaVinci Resolve:
1. Timeline → right-click → Add Text
2. Type, adjust font/size
3. Set in/out points for timing

### Speed Up Sections:
- Select clip → Speed → 1.5x (keeps audio clear)
- Don't go above 2x (sounds rushed)

---

## 📤 UPLOAD DETAILS

**YouTube Settings:**
- **Title**: "E2B Hackathon: TweekIT MCP - Eliminating Agentic Workflow Blockers"
- **Description**:
  ```
  Demo of TweekIT MCP integration with E2B sandbox and Groq analysis.

  🚀 First MCP to support 400+ file formats
  ⚡ Process legacy formats in under 3 seconds
  🔒 Secure E2B sandbox execution
  🤖 Instant Groq AI analysis

  Links:
  - Website: https://www.tweekit.io
  - GitHub: https://github.com/equilibrium-eq/tweekit-mcp-docker-groq-e2b
  - Docker MCP Hub: Coming soon

  #E2BHackathon #MCP #AIAgents #FileConversion
  ```
- **Visibility**: Unlisted (shareable link for judges)
- **Category**: Science & Technology
- **Tags**: e2b, mcp, docker, ai agents, file conversion, groq

---

## ✅ FINAL CHECK BEFORE SUBMITTING

- [ ] Video is under 2 minutes
- [ ] Audio is clear (no background noise)
- [ ] Shows actual working demo (not mockup)
- [ ] All URLs are correct
- [ ] Key differentiators mentioned (400+ formats, < 3 sec)
- [ ] Video is uploaded and link works
- [ ] Ready to add to submission document

---

**Ready to record? Let's capture those demo assets during WS4 testing! 🎥**
