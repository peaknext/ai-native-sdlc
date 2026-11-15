---
tags: [skill-creator]
max_turns: 40
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

We are a 4-person team and want to start using Claude Code on this repo properly. Please set it up. Two things matter most to us: the AI must never edit the generated API client in src/generated (it gets overwritten by our codegen), and it must not deploy to production on its own.

Input files: package.json, README.md, src/index.js, src/pricing.js, src/generated/apiClient.js, test/pricing.test.js, scripts/build.js, scripts/deploy.js
