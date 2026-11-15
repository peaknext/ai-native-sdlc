<!--
Template for turning a written policy into a skill.
Save the finished file as .claude/skills/<policy-name>/SKILL.md in the repo (or ship it
in an organisation plugin). Delete this comment.

Before writing: the policy needs a named owner and a written source of truth.
After writing: ask for the task in several different ways and confirm the skill is
picked up each time. If the policy must hold without exception, add a hook or a
PR-time check as well: a skill makes compliance likely, not certain.
-->
---
name: policy-name-in-kebab-case
description: What this policy covers and exactly when to apply it. Name the tasks, file types and phrases that should bring it in, for example "Use when creating or changing any external API endpoint, reviewing API code, or generating an OpenAPI specification."
---

# Policy title

**Owner:** name or team who approves changes to this policy
**Source of truth:** link or document ID
**Last reviewed with owner:** YYYY-MM-DD

## Why this exists
One or two sentences on the harm this policy prevents. People and models follow rules
better when they know what the rule protects.

## Rules
1. A rule, stated as an action, followed by the reason.
2. ...

## How to check your work
The command or inspection that shows the rules were followed. Include its output in
your summary.

## When the rules conflict or cannot be met
Do not choose silently. Flag it (in the "Flagged concerns" section of `spec.md`, or to
the person you are working with), give the options, and name the policy owner as the
decider.
