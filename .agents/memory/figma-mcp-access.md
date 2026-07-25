---
name: Figma MCP access
description: Figma design-to-code work may be blocked by Starter-plan MCP rate limits.
---

The connected Figma MCP can return a Starter-plan rate-limit error even when a shared design URL is valid. When that happens, ask for a screenshot or exported frame for pixel-accurate implementation; otherwise use the existing project design tokens and templates rather than guessing a new frontend stack.

**Why:** The dashboard reference could not be inspected after the MCP call limit was reached, while the repository already contained a matching indigo/white design system.

**How to apply:** Try the Figma context/screenshot tools once or twice, then switch to an exported frame or the repository's established visual system instead of repeatedly retrying.