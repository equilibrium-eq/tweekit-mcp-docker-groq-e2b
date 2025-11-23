# A Letter to the E2B & MCP Community: Building Better Hackathons Together

**Date:** November 23, 2025  
**From:** Team Equilibrium (TweekIT)  
**Project:** TweekIT InstantOn™ Demo  
**Live Demo (stage):** https://stage-958133016924.us-west1.run.app  
**Repository:** https://github.com/equilibrium-eq/tweekit-mcp-docker-groq-e2b

---

## 1. Timeline & Evidence (Pacific Time)

| Time & Date | Workstream | Evidence |
|-------------|------------|----------|
| **Nov 20 – 23:30** | Drafted hackathon plan; Workstream 1 labelled “Docker MCP Hub submission — Critical Path” | `HACKATHON_PARALLEL_WORKSTREAMS.md` (lines 12‑49) |
| **Nov 21 – 09:00‑18:00** | Implemented E2B sandbox handshake (`GET /mcp` SSE → `initialize` → `notifications/initialized`) and parallel MCP/Groq calls | `scripts/e2b_demo_agent.py` (lines 61‑188) |
| **Nov 21 – evening** | Moved homepage styling into `/static/styles/main.css` and applied same layout to press release | `demo/static/index.html`, `demo/static/press-release.html`, `demo/static/styles/main.css` |
| **Nov 22 – 07:00‑10:00** | Added local Markdown fallback (handles `.txt`/text inputs without MCP 500s) and logs unsupported formats | `demo/api.py` (lines 238‑318), `demo/logs/unsupported_formats.log` |
| **Nov 22 – 13:00‑15:00** | Prepared demo deploy script (`demo/deploy.sh`) but *did not run it* before submission window | Script present; no deploy log prior to Nov 23 |
| **Nov 22 – 19:00 planned** | Internal buffer for submission (based on 9 PM deadline posted in one part of the invite) | `HACKATHON_PARALLEL_WORKSTREAMS.md` header |
| **Nov 23 – 09:15** | Enabled `direnv`, executed demo deploy: `direnv exec . bash demo/deploy.sh stage --version 1.6.01` → Cloud Run service `stage-00002-qlr` | Deploy log (Nov 23) |

---

## 2. What We Delivered

- **E2B sandbox integration** creating the full MCP session handshake and running both conversion and Groq analysis.
- **Remote TweekIT MCP** (https://mcp.tweekit.io/mcp) serving 400 + file formats on Google Cloud Run.
- **Local fallback** for text formats to avoid 500s and structured logging of unsupported cases.
- **Shared frontend theme** across homepage and press release, now live at the stage URL.
- **Discord error reporting hooks** (disabled until webhook provided) in `demo/api.py`.

All code is MIT‑licensed in the repo above.

---

## 3. Where We Went Wrong

1. **Missed Architectural Requirement**  
   - Workstream 1 correctly flagged “Docker MCP Hub submission”, but we only consumed our own MCP remotely.  
   - Nowhere in the repo do we say “no need to host inside E2B”; that guidance must have been verbal/AI hallucinated.  
   - The rule was “use an MCP from Docker Hub *inside* the E2B sandbox.” We interpreted that as “call an MCP you submitted.” That interpretation was wrong.

2. **Deadline Confusion**  
   - The Luma invite showed both **Nov 22 09:00** and **Nov 22 21:00** Pacific. We planned against the later time.  
   - When we arrived at 19:00, the portal was already closed. That is on us.

3. **Delayed Deployment**  
   - We finished the demo but postponed deployment until after the submission window. When we re-ran `demo/deploy.sh` on Nov 23 with `direnv`, Cloud Run went live immediately, proving the feature was ready but simply late.

We missed the deadline **and** we failed to run an MCP inside E2B. It would not be fair to the other teams to request special treatment.

---

## 4. Action Items (Already Underway)

1. **Document Requirements for AI** – Future hackathons will have a machine‑readable “manifest” (see below) so assistants cannot misinterpret architecture rules.
2. **Publish an In‑Sandbox MCP** – We’re packaging the TweekIT server (and a fallback Pandoc MCP) as Docker Hub MCPs that run entirely inside E2B.
3. **Automate Deadline Checks** – Add ISO‑8601 timestamps to plans, with reminders six hours prior to close.
4. **Enable Discord Alerts** – As soon as the webhook is in `.envrc`, error reporting will automatically notify organizers.
5. **Share Lessons Openly** – Everything, including this letter, remains open source for the community.

---

## 5. The “Hackathon Manifest” Proposal

To prevent future ambiguity—especially for AI‑assisted teams—we propose a machine‑readable requirements file. Below is an excerpt of what we’re drafting with `req-002` explicitly calling out the in‑sandbox MCP requirement.

```yaml
hackathon:
  name: "E2B MCP Hackathon"
  timezone: "America/Los_Angeles"
  dates:
    start: "2025-11-21T00:00:00-08:00"
    end:   "2025-11-22T19:00:00-08:00"    # single source of truth

requirements:
  must_have:
    - id: "req-001"
      description: "Run all agent code inside an E2B sandbox"
      validation: "Uses e2b_code_interpreter.Sandbox()"

    - id: "req-002"
      description: "Install ≥1 MCP from Docker Hub inside the sandbox"
      validation: "MCP is containerized/in-process within E2B, not a remote HTTPS call"
      anti_patterns:
        - "Calling https://<remote>/mcp"
      examples:
        - "sandbox.install_mcp('dockerhub/pandoc')"

submission:
  closes_at: "2025-11-22T19:00:00-08:00"
  format: ["github_repo", "demo_video", "live_url"]
  video_max_seconds: 120

support:
  clarification_webhook:
    enabled: true
    endpoint: "https://api.e2b.dev/hackathon/clarify"
    example_request:
      question: "Can I use a remote MCP HTTP server?"
    example_response:
      answer: "No. MCPs must run inside E2B."
      broadcast_to_all: true
```

This format lets AI assistants plan correctly, gives organizers a single source of truth, and provides teams with ready‑made validation checks.

---

## 6. No Appeal, Only Improvement

We accept that our submission is ineligible. Instead of asking for flexibility, we’re publishing everything we built, the mistakes we made, and a concrete path to do better—both for us and for future participants.

---

## 7. Call to Action

We invite the community—organizers, tool builders, and fellow teams—to collaborate on:

1. **Hackathon Manifest v1.0** – AI‑friendly requirement schema.  
2. **Clarification Webhook Protocol** – Real‑time Q&A that updates every team’s context.  
3. **Reference MCP Bundles** – Examples that run natively inside E2B.

Open an issue or PR in our repo if you’re interested in helping.

---

## 8. Contact

- **Team:** Equilibrium (TweekIT)  
- **GitHub:** https://github.com/equilibrium-eq  
- **Website:** https://www.tweekit.io  
- **Email:** via GitHub or marketing@equilibrium.com

---

## 9. Closing Thoughts

We spent ~45 hours building an end‑to‑end demo that converts 400 + formats, runs inside an E2B sandbox, and layers Groq analysis on top. The technology works—and is now live at the URL above—but we missed the architectural requirement and the submission window. That’s on us.

If sharing the lessons helps future hackathons set clearer rules, avoids AI hallucination traps, and keeps teams focused on building great software, the effort was still worth it.

**Let’s build better hackathons together.** 🚀

*Published under CC BY 4.0 so anyone can adapt these ideas with attribution.*
