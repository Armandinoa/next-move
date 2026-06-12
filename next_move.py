from __future__ import annotations

import argparse
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".turbo",
    ".pytest_cache",
    ".mypy_cache",
}

CODE_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".go",
    ".rs",
    ".java",
    ".cs",
    ".php",
    ".rb",
}

TEST_HINTS = ("test_", "_test.", ".spec.", ".test.", "tests")
DOC_NAMES = {"readme.md", "docs", "documentation"}
CI_DIRS = {".github", ".gitlab-ci.yml", "azure-pipelines.yml"}
GENERATED_REPORT_NAMES = {"roadmap.md", "next_moves.md", "sample_roadmap.md"}
SELF_IMPROVE_REPORT_NAMES = {"next_action.md", "self_improve.md"}
ENV_MARKERS = (
    "os." + "environ",
    "get" + "env(",
    "process." + "env",
    "dot" + "env",
    "pydantic_" + "settings",
)

DEMO_PROJECT_FILES = {
    "README.md": "# Demo App\n\nA tiny unfinished app used to demonstrate Next Move.\n",
    "app.py": (
        "import os\n\n"
        "API_KEY = os." + "environ.get('DEMO_API_KEY')\n\n"
        "def main():\n"
        "    # TODO: add input validation before shipping\n"
        "    print('demo app')\n"
    ),
    "cli.py": (
        "def run():\n"
        "    print('demo cli')\n"
    ),
    "dashboard.py": (
        "def render_dashboard():\n"
        "    return '<h1>Demo</h1>'\n"
    ),
    "worker.py": (
        "def process_jobs(jobs):\n"
        "    return [job for job in jobs]\n"
    ),
}


@dataclass
class Finding:
    title: str
    why: str
    action: str
    impact: int
    effort: int
    category: str

    @property
    def priority(self) -> int:
        return self.impact * 2 - self.effort


@dataclass
class RepoProfile:
    root: str
    scanned_at: str
    total_files: int
    code_files: int
    test_files: int
    doc_files: int
    stacks: list[str]
    has_readme: bool
    has_license: bool
    has_env_example: bool
    has_ci: bool
    has_docker: bool
    has_web_ui: bool
    has_cli: bool
    has_demo: bool
    uses_env: bool
    todo_count: int
    large_files: list[str]


def iter_files(root: Path) -> Iterable[Path]:
    for current, dirs, files in os.walk(root):
        dirs[:] = [item for item in dirs if item not in IGNORE_DIRS]
        current_path = Path(current)
        for file_name in files:
            path = current_path / file_name
            if any(part in IGNORE_DIRS for part in path.parts):
                continue
            if path.name.lower() in GENERATED_REPORT_NAMES | SELF_IMPROVE_REPORT_NAMES:
                continue
            yield path


def safe_read_text(path: Path, max_bytes: int = 200_000) -> str:
    try:
        if path.stat().st_size > max_bytes:
            return ""
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def count_todo_markers(path: Path, text: str) -> int:
    count = 0
    is_doc = path.suffix.lower() in {".md", ".rst", ".txt"}
    comment_prefixes = ("#", "//", "/*", "*", "<!--")
    for line in text.splitlines():
        lowered = line.lower()
        if "todo" not in lowered and "fixme" not in lowered:
            continue
        stripped = line.lstrip()
        if is_doc or stripped.startswith(comment_prefixes):
            count += 1
    return count


def detect_stacks(files: list[Path]) -> list[str]:
    names = {path.name.lower() for path in files}
    suffixes = {path.suffix.lower() for path in files}
    stacks: list[str] = []

    if "pyproject.toml" in names or "requirements.txt" in names or ".py" in suffixes:
        stacks.append("Python")
    if "package.json" in names or ".ts" in suffixes or ".tsx" in suffixes or ".js" in suffixes:
        stacks.append("JavaScript/TypeScript")
    if "vite.config.ts" in names or "vite.config.js" in names:
        stacks.append("Vite")
    if "next.config.js" in names or "next.config.ts" in names:
        stacks.append("Next.js")
    if "dockerfile" in names or "docker-compose.yml" in names:
        stacks.append("Docker")
    if ".pine" in suffixes:
        stacks.append("TradingView Pine")

    return stacks or ["Unknown"]


def build_profile(root: Path) -> RepoProfile:
    files = list(iter_files(root))
    names = {path.name.lower() for path in files}
    rels = [path.relative_to(root).as_posix().lower() for path in files]
    code_files = [path for path in files if path.suffix.lower() in CODE_EXTENSIONS]
    test_files = [path for path in files if any(hint in path.as_posix().lower() for hint in TEST_HINTS)]
    doc_files = [
        path for path in files
        if path.suffix.lower() in {".md", ".rst"} or path.name.lower() in DOC_NAMES
    ]
    todo_count = 0
    uses_env = False
    has_demo = False
    for path in code_files + doc_files:
        text = safe_read_text(path)
        todo_count += count_todo_markers(path, text)
        lowered = text.lower()
        if any(marker in lowered for marker in ENV_MARKERS):
            uses_env = True
        if "--demo" in lowered:
            has_demo = True

    large_files = []
    for path in files:
        try:
            if path.stat().st_size >= 1_000_000:
                large_files.append(path.relative_to(root).as_posix())
        except OSError:
            pass

    return RepoProfile(
        root=str(root),
        scanned_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        total_files=len(files),
        code_files=len(code_files),
        test_files=len(test_files),
        doc_files=len(doc_files),
        stacks=detect_stacks(files),
        has_readme="readme.md" in names,
        has_license=any(name.startswith("license") for name in names),
        has_env_example=any("env.example" in rel or ".env.example" in rel for rel in rels),
        has_ci=any(rel.startswith(".github/workflows/") for rel in rels)
        or any(name in names for name in CI_DIRS),
        has_docker="dockerfile" in names or "docker-compose.yml" in names,
        has_web_ui=any(part in rel for rel in rels for part in ("src/main", "app/", "pages/", "dashboard")),
        has_cli=any(path.name in {"cli.py", "__main__.py", "main.py", "next_move.py"} for path in files),
        has_demo=has_demo,
        uses_env=uses_env,
        todo_count=todo_count,
        large_files=large_files[:12],
    )


def create_demo_project(root: Path) -> None:
    for relative_path, content in DEMO_PROJECT_FILES.items():
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def add(finding_list: list[Finding], title: str, why: str, action: str, impact: int, effort: int, category: str) -> None:
    finding_list.append(Finding(title, why, action, impact, effort, category))


def generate_findings(profile: RepoProfile) -> list[Finding]:
    findings: list[Finding] = []

    if not profile.has_readme:
        add(
            findings,
            "Write a README that sells the first 60 seconds",
            "Without a clear README, users do not understand why the project exists or how to try it.",
            "Add problem, demo, install, quickstart, roadmap, and monetization-safe disclaimer.",
            5,
            2,
            "growth",
        )
    if profile.has_readme and profile.doc_files < 3:
        add(
            findings,
            "Add one practical example",
            "A README is useful, but a working example makes adoption much easier.",
            "Create an examples folder with one input project and one generated report.",
            4,
            2,
            "adoption",
        )
    if profile.test_files == 0 and profile.code_files > 3:
        add(
            findings,
            "Add smoke tests before adding features",
            "The project has code but no obvious tests, so future changes can silently break behavior.",
            "Add a tiny test suite for the main command or core functions.",
            5,
            3,
            "reliability",
        )
    if profile.uses_env and not profile.has_env_example:
        add(
            findings,
            "Add an env example",
            "Users need to know which configuration values exist without seeing private secrets.",
            "Create `.env.example` with placeholder values and short comments.",
            4,
            1,
            "setup",
        )
    if not profile.has_ci and profile.code_files > 3:
        add(
            findings,
            "Add a basic CI check",
            "A public repo feels more trustworthy when every change runs a small automated check.",
            "Add GitHub Actions for lint or syntax checks.",
            4,
            2,
            "trust",
        )
    if not profile.has_license:
        add(
            findings,
            "Choose a license before publishing",
            "Without a license, users do not clearly know what they can do with the code.",
            "Add MIT for permissive adoption or AGPL if you want hosted competitors to contribute back.",
            5,
            1,
            "legal",
        )
    if profile.todo_count > 0:
        add(
            findings,
            "Turn TODOs into explicit issues",
            f"The scan found {profile.todo_count} TODO/FIXME markers. Hidden TODOs do not create momentum.",
            "Convert the top TODOs into GitHub issues with labels and priority.",
            3,
            2,
            "execution",
        )
    if profile.has_web_ui:
        add(
            findings,
            "Create a screenshot-led demo",
            "A visual project is easier to understand when the first screen shows the actual product.",
            "Add screenshots or a short GIF to the README and link the live dashboard if public.",
            5,
            2,
            "marketing",
        )
    if profile.has_cli:
        add(
            findings,
            "Make the CLI output copy-paste friendly",
            "CLI tools spread faster when the output can become a report, issue, or checklist immediately.",
            "Add `--json`, `--markdown`, and `--output` options if missing.",
            4,
            2,
            "product",
        )
    if profile.large_files:
        add(
            findings,
            "Review large files",
            "Large files can make cloning slow and may accidentally include generated artifacts.",
            "Move generated outputs to releases, examples, or ignored folders where appropriate.",
            3,
            2,
            "maintenance",
        )

    add(
        findings,
        "Define the next paid boundary",
        "Open source projects monetize better when the free and paid value are intentionally separated.",
        "Keep the core scanner free. Make scheduling, hosted dashboards, team history, and integrations paid.",
        5,
        2,
        "monetization",
    )
    if not profile.has_demo:
        add(
            findings,
            "Add a one-command demo",
            "People decide quickly. A single command lowers the activation cost.",
            "Add a command that scans the current repo and writes `ROADMAP.md`.",
            5,
            1,
            "adoption",
        )

    return sorted(findings, key=lambda item: item.priority, reverse=True)


def monetization_ideas(profile: RepoProfile) -> list[str]:
    ideas = [
        "GitHub Sponsors: fund ongoing open source development.",
        "Hosted dashboard: scheduled scans, history, and team views for a monthly fee.",
        "Premium playbooks: repo-specific templates for SaaS, trading bots, AI apps, and mobile apps.",
        "Done-for-you setup: connect the scanner to GitHub Issues, Telegram, Discord, or Slack.",
    ]
    if profile.has_web_ui:
        ideas.append("Public demo hosting: let users scan sample projects before installing.")
    if "TradingView Pine" in profile.stacks:
        ideas.append("Trading project pack: risk checks, backtest TODOs, and disclaimer templates.")
    if "Python" in profile.stacks:
        ideas.append("Python package tier: publish a pip package and offer hosted reports.")
    return ideas


def github_issue_drafts(findings: list[Finding], limit: int = 8) -> list[dict[str, str]]:
    issues = []
    for finding in findings[:limit]:
        issues.append(
            {
                "title": finding.title,
                "labels": f"{finding.category}, impact-{finding.impact}, effort-{finding.effort}",
                "body": (
                    f"## Why\n{finding.why}\n\n"
                    f"## Action\n{finding.action}\n\n"
                    f"## Priority\nImpact: {finding.impact}/5\nEffort: {finding.effort}/5\n"
                ),
            }
        )
    return issues


def slugify(text: str) -> str:
    chars = []
    previous_dash = False
    for char in text.lower():
        if char.isalnum():
            chars.append(char)
            previous_dash = False
        elif not previous_dash:
            chars.append("-")
            previous_dash = True
    return "".join(chars).strip("-") or "issue"


def write_issue_files(findings: list[Finding], issues_dir: Path, limit: int = 8) -> list[Path]:
    issues_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for index, issue in enumerate(github_issue_drafts(findings, limit=limit), start=1):
        filename = f"{index:02d}-{slugify(issue['title'])}.md"
        path = issues_dir / filename
        content = (
            "---\n"
            f"title: {issue['title']}\n"
            f"labels: {issue['labels']}\n"
            "---\n\n"
            f"{issue['body']}"
        )
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written


def render_self_improve(profile: RepoProfile, findings: list[Finding]) -> str:
    if not findings:
        return "\n".join(
            [
                "# Next Action",
                "",
                f"Generated: {profile.scanned_at}",
                f"Repo: `{profile.root}`",
                "",
                "No obvious next move was detected. Review the project manually or add a project-specific playbook.",
                "",
            ]
        )

    top = findings[0]
    branch_name = f"next/{slugify(top.title)}"
    issue = github_issue_drafts([top], limit=1)[0]
    roadmap_command = "python next_move.py --repo . --output ROADMAP.md --issues-dir issues-drafts"

    lines = [
        "# Next Action",
        "",
        f"Generated: {profile.scanned_at}",
        f"Repo: `{profile.root}`",
        "",
        "## Recommended Move",
        "",
        f"### {top.title}",
        "",
        f"- Category: `{top.category}`",
        f"- Impact: {top.impact}/5",
        f"- Effort: {top.effort}/5",
        f"- Priority score: {top.priority}",
        f"- Why: {top.why}",
        f"- Action: {top.action}",
        "",
        "## Suggested Branch",
        "",
        f"`{branch_name}`",
        "",
        "## Implementation Checklist",
        "",
        "- Create or switch to the suggested branch.",
        "- Implement only this move; keep unrelated ideas for later.",
        "- Run the local smoke test.",
        "- Regenerate the roadmap and compare what changed.",
        "- Commit with a short message that names the move.",
        "",
        "## Commands",
        "",
        "```bash",
        f"git checkout -b {branch_name}",
        roadmap_command,
        "python -m py_compile next_move.py",
        "python next_move.py --repo . --json",
        "```",
        "",
        "## GitHub Issue Draft",
        "",
        f"Title: {issue['title']}",
        f"Labels: `{issue['labels']}`",
        "",
        issue["body"],
        "",
        "## Stop Conditions",
        "",
        "- Do not auto-edit files without human review.",
        "- Stop if the suggested move is vague, low-value, or already done.",
        "- Prefer one finished improvement over multiple half-started ideas.",
        "",
    ]
    return "\n".join(lines)


def render_markdown(profile: RepoProfile, findings: list[Finding]) -> str:
    issue_drafts = github_issue_drafts(findings)
    lines = [
        "# Next Move Report",
        "",
        f"Generated: {profile.scanned_at}",
        f"Repo: `{profile.root}`",
        "",
        "## Snapshot",
        "",
        f"- Files scanned: {profile.total_files}",
        f"- Code files: {profile.code_files}",
        f"- Test files: {profile.test_files}",
        f"- Docs files: {profile.doc_files}",
        f"- Stack hints: {', '.join(profile.stacks)}",
        f"- README: {'yes' if profile.has_readme else 'no'}",
        f"- License: {'yes' if profile.has_license else 'no'}",
        f"- CI: {'yes' if profile.has_ci else 'no'}",
        f"- Docker: {'yes' if profile.has_docker else 'no'}",
        f"- Demo: {'yes' if profile.has_demo else 'no'}",
        "",
        "## Recommended Next Moves",
        "",
    ]
    for index, finding in enumerate(findings[:10], start=1):
        lines.extend(
            [
                f"### {index}. {finding.title}",
                "",
                f"- Category: `{finding.category}`",
                f"- Impact: {finding.impact}/5",
                f"- Effort: {finding.effort}/5",
                f"- Priority score: {finding.priority}",
                f"- Why: {finding.why}",
                f"- Action: {finding.action}",
                "",
            ]
        )

    lines.extend(["## Monetization Angles", ""])
    for idea in monetization_ideas(profile):
        lines.append(f"- {idea}")

    lines.extend(["", "## GitHub Issue Drafts", ""])
    for issue in issue_drafts:
        lines.extend(
            [
                f"### {issue['title']}",
                "",
                f"Labels: `{issue['labels']}`",
                "",
                issue["body"],
            ]
        )

    if profile.large_files:
        lines.extend(["", "## Large Files To Review", ""])
        for path in profile.large_files:
            lines.append(f"- `{path}`")

    lines.extend(
        [
            "",
            "## Critical Check",
            "",
            "- This report is heuristic. Validate suggestions before acting.",
            "- Monetization ideas are options, not guaranteed revenue.",
            "- Do not publish secrets, private datasets, or API keys in the repo.",
        ]
    )
    return "\n".join(lines) + "\n"


def run_report(
    root: Path,
    output: Path | None,
    as_json: bool,
    issues_dir: Path | None,
    self_improve: bool,
    self_improve_output: Path | None,
    default_output: Path | None = None,
    print_markdown: bool = False,
) -> int:
    profile = build_profile(root)
    findings = generate_findings(profile)
    payload = {
        "profile": asdict(profile),
        "findings": [asdict(finding) | {"priority": finding.priority} for finding in findings],
        "monetization": monetization_ideas(profile),
        "issues": github_issue_drafts(findings),
    }

    if as_json:
        print(json.dumps(payload, indent=2))
        return 0

    if self_improve:
        target = self_improve_output or root / "NEXT_ACTION.md"
        target.write_text(render_self_improve(profile, findings), encoding="utf-8")
        print(f"Wrote {target}")
        return 0

    markdown = render_markdown(profile, findings)
    target = output or default_output
    if target:
        target.write_text(markdown, encoding="utf-8")
        print(f"Wrote {target}")
    if print_markdown or not target:
        print(markdown)
    if issues_dir:
        written = write_issue_files(findings, issues_dir.resolve())
        print(f"Wrote {len(written)} issue drafts to {issues_dir.resolve()}")
    return 0


def run(
    repo: Path,
    output: Path | None,
    as_json: bool,
    issues_dir: Path | None,
    self_improve: bool,
    self_improve_output: Path | None,
    demo: bool,
) -> int:
    if demo:
        with tempfile.TemporaryDirectory(prefix="next-move-demo-") as tmp:
            demo_root = Path(tmp)
            create_demo_project(demo_root)
            return run_report(
                demo_root,
                output,
                as_json,
                issues_dir,
                self_improve,
                self_improve_output,
                print_markdown=output is None and not as_json and not self_improve,
            )

    root = repo.resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Repo path does not exist or is not a directory: {root}")
    return run_report(root, output, as_json, issues_dir, self_improve, self_improve_output, default_output=root / "ROADMAP.md")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate practical next moves for a repository.")
    parser.add_argument("--demo", action="store_true", help="Run against a built-in demo project and print the report.")
    parser.add_argument("--repo", default=".", help="Repository or project directory to scan.")
    parser.add_argument("--output", help="Markdown output path. Defaults to ROADMAP.md inside the repo.")
    parser.add_argument("--issues-dir", help="Write GitHub issue draft Markdown files to this directory.")
    parser.add_argument("--self-improve", action="store_true", help="Write a guided next-action plan for this repo.")
    parser.add_argument(
        "--self-improve-output",
        help="Markdown output path for --self-improve. Defaults to NEXT_ACTION.md inside the repo.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON instead of writing Markdown.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = Path(args.output).resolve() if args.output else None
    issues_dir = Path(args.issues_dir).resolve() if args.issues_dir else None
    self_improve_output = Path(args.self_improve_output).resolve() if args.self_improve_output else None
    return run(Path(args.repo), output, args.json, issues_dir, args.self_improve, self_improve_output, args.demo)


if __name__ == "__main__":
    raise SystemExit(main())
