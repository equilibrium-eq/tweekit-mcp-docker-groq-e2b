TweekIT Branding Assets
=======================

This directory hosts curated PNG assets that ship with the MCP server and bundles:

- `tweekit-icon-square-150.png` – 150×150 icon, best for tight UI placements.
- `tweekit-icon-square-300.png` – 300×300 primary icon; exposed as `/logo.png`.
- `tweekit-icon-345x192.png`, `tweekit-icon-600x320.png`, `tweekit-icon-600x384.png` – alternative aspect ratios for cards or tiles.
- `tweekit-logo-full-*.png` – horizontal lockups sized from 150px to 768px wide plus the original source.

The FastAPI plugin proxy serves these at `https://<host>/mcp/assets/<filename>` and aliases the 300×300 icon to `https://<host>/mcp/logo.png`.

Use these files when preparing connector submissions (ChatGPT, Claude Desktop, MCP Pulse) to keep branding consistent across clients. If you need additional sizes, regenerate them from the master artwork and add the PNGs here.
