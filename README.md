# Next Move

Turn a messy project into the next useful actions.

Next Move is a small CLI that scans a repository and generates a practical
roadmap: quick wins, risks, monetization ideas, and ready-to-copy GitHub issues.

The goal is simple: when you do not know what to improve next, the tool gives
you a ranked starting point instead of a blank page.

## Why this exists

Many builders get stuck after the first working version. The project works, but
the next step is unclear:

- Should I improve the UI?
- Should I add tests?
- Should I turn it into a product?
- What could users pay for?
- What risks am I ignoring?

Next Move gives structure to that decision.

## MVP features

- Detects project shape: Python, JavaScript, frontend, backend, docs, deploy.
- Finds weak spots: missing README, tests, examples, env templates, CI, license.
- Suggests quick wins by impact and effort.
- Suggests monetization angles without pretending they are guaranteed.
- Generates GitHub issue drafts.
- Writes a `ROADMAP.md` report.
- No API keys and no paid model required.

## Usage

Try it immediately:

```bash
python next_move.py --demo
```

```bash
python next_move.py --repo path/to/project
```

Install locally while developing:

```bash
pip install -e .
next-move --repo path/to/project
```

Write to a custom file:

```bash
python next_move.py --repo path/to/project --output NEXT_MOVES.md
```

Print JSON:

```bash
python next_move.py --repo path/to/project --json
```

Generate GitHub issue drafts:

```bash
python next_move.py --repo path/to/project --issues-dir issues-drafts
```

Generate a guided self-improvement plan:

```bash
python next_move.py --repo . --self-improve
```

This writes `NEXT_ACTION.md` with the highest-priority move, a suggested branch,
implementation checklist, smoke-test commands, and stop conditions. It does not
modify code automatically.

## Example

```bash
python next_move.py --repo ../files-mentioned-by-the-user-www --output ROADMAP.md
```

## Monetization paths for this repo

This project can stay open source while making money through:

- GitHub Sponsors for people who find it useful.
- A hosted dashboard that runs scheduled project reviews.
- Team plans for multi-repo tracking.
- Premium templates for product, trading bots, SaaS, mobile apps, and AI tools.
- Setup services for founders who want this connected to Telegram, Discord, or GitHub Issues.

## Current scope

This first version is heuristic, not magic. It does not read private secrets,
does not call AI APIs, and does not create GitHub issues automatically yet.

Planned next steps:

- Add optional LLM review.
- Add GitHub issue creation.
- Add web dashboard.
- Add project-type playbooks.
- Add score history over time.
