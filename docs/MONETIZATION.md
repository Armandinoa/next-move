# Monetization Boundary

Next Move should stay useful as a free open source CLI. Monetization can exist
around the project, but the core promise should not be locked away.

## Free Core

The open source repo should always include:

- Local repository scanning.
- Markdown roadmap generation.
- JSON output.
- GitHub issue draft generation.
- Guided `--self-improve` mode.
- The one-command `--demo` flow.
- Basic project heuristics and playbooks.
- No required API key.
- No required hosted account.

This keeps the project trustworthy and easy to adopt.

## Paid Or Hosted Later

Potential paid layers can build on top of the free CLI:

- Scheduled scans across multiple repositories.
- Hosted dashboard with history and trends.
- Team workspaces and shared project scorecards.
- GitHub App that opens issues automatically.
- Telegram, Discord, Slack, or email notifications.
- Premium playbooks for specific project types.
- Private LLM review with user-provided keys or managed credits.
- Done-for-you setup for founders or teams.

Commercial support packages are described in
[COMMERCIAL.md](COMMERCIAL.md).

## What Not To Monetize

Avoid charging for the basics that make the project worth trying:

- Running a local scan.
- Exporting Markdown.
- Exporting JSON.
- Seeing the top recommendations.
- Reading the core heuristics.

If the free version feels useless, people will not trust the paid version.

## Early Pricing Hypothesis

This is only a starting hypothesis:

- Free: local CLI and open source development.
- Solo hosted: 5-10 EUR/month for scheduled scans and dashboard history.
- Team hosted: 19-49 EUR/month for multiple repos and shared reports.
- Setup service: fixed-price configuration for GitHub, Telegram, or Discord.

The product should validate demand before building billing.

## Practical Rule

Free should answer:

> What should I improve next?

Paid should answer:

> Keep watching all my projects and tell my team what changed.
