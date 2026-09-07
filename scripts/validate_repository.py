#!/usr/bin/env python3
"""Dependency-free repository checks used locally and in CI."""

import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
errors = []


def fail(message):
    errors.append(message)


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"invalid JSON {path.relative_to(ROOT)}: {exc}")
        return {}


manifest = load_json(ROOT / ".codex-plugin" / "plugin.json")
if manifest.get("name") != "business-skills" or manifest.get("skills") != "./skills/":
    fail("invalid plugin manifest")
if not re.fullmatch(r"\d+\.\d+\.\d+", str(manifest.get("version", ""))):
    fail("plugin version is not semantic")
default_prompts = manifest.get("interface", {}).get("defaultPrompt") if isinstance(manifest.get("interface"), dict) else None
if not isinstance(default_prompts, list) or not 1 <= len(default_prompts) <= 3 or any(not isinstance(item, str) or not item.strip() for item in default_prompts):
    fail("plugin interface.defaultPrompt must contain one to three non-empty strings")

catalog = load_json(ROOT / "catalog.json")
entries = catalog.get("skills", []) if isinstance(catalog, dict) else []
catalog_by_name = {}
for entry in entries:
    if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
        fail("catalog contains malformed entry")
        continue
    if entry["name"] in catalog_by_name:
        fail(f"duplicate catalog entry {entry['name']}")
    catalog_by_name[entry["name"]] = entry

skill_names = set()
for directory in sorted((ROOT / "skills").iterdir()):
    if not directory.is_dir():
        continue
    skill_file = directory / "SKILL.md"
    if not skill_file.is_file():
        fail(f"{directory.name}: missing SKILL.md")
        continue
    text = skill_file.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        fail(f"{directory.name}: bad frontmatter")
        continue
    frontmatter = match.group(1)
    top_level_keys = {
        key for key in re.findall(r"^([A-Za-z][A-Za-z0-9_-]*):", frontmatter, re.M)
    }
    unsupported_keys = top_level_keys - {"name", "description", "license", "metadata", "allowed-tools"}
    if unsupported_keys:
        fail(f"{directory.name}: unsupported frontmatter keys {sorted(unsupported_keys)}")
    name_match = re.search(r"^name:\s*([^\n]+)$", frontmatter, re.M)
    description_match = re.search(r"^description:\s*(.+)$", frontmatter, re.M)
    version_match = re.search(r'^\s*version:\s*"([^\"]+)"$', frontmatter, re.M)
    if not name_match or name_match.group(1).strip() != directory.name or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", directory.name):
        fail(f"{directory.name}: name mismatch")
    if not description_match or not 30 <= len(description_match.group(1).strip()) <= 1024:
        fail(f"{directory.name}: weak description")
    if len(text.splitlines()) > 500:
        fail(f"{directory.name}: SKILL.md exceeds 500 lines")
    if "[TODO" in text:
        fail(f"{directory.name}: unfinished placeholder")
    if directory.name in skill_names:
        fail(f"duplicate skill {directory.name}")
    skill_names.add(directory.name)

    entry = catalog_by_name.get(directory.name)
    if not entry:
        fail(f"{directory.name}: missing catalog entry")
    else:
        if entry.get("path") != f"skills/{directory.name}":
            fail(f"{directory.name}: bad catalog path")
        if not version_match or entry.get("version") != version_match.group(1):
            fail(f"{directory.name}: catalog/frontmatter version mismatch")

    if not (directory / "README.md").is_file():
        fail(f"{directory.name}: missing product README")
    for markdown_path in directory.rglob("*.md"):
        markdown_text = markdown_path.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", markdown_text):
            target = target.strip().strip("<>").split("#", 1)[0]
            if not target or re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I):
                continue
            resolved = (markdown_path.parent / target).resolve()
            try:
                resolved.relative_to(ROOT.resolve())
            except ValueError:
                fail(f"{markdown_path.relative_to(ROOT)}: link escapes repository: {target}")
                continue
            if not resolved.exists():
                fail(f"{markdown_path.relative_to(ROOT)}: broken local link: {target}")
    agent_yaml = directory / "agents" / "openai.yaml"
    if agent_yaml.is_file():
        agent_text = agent_yaml.read_text(encoding="utf-8")
        if f"${directory.name}" not in agent_text:
            fail(f"{directory.name}: default prompt must invoke the skill")
        for icon in re.findall(r'icon_(?:small|large):\s*"([^\"]+)"', agent_text):
            icon_path = directory / icon.removeprefix("./")
            if not icon_path.is_file():
                fail(f"{directory.name}: missing UI icon {icon}")

    harness = directory / "scripts" / "eval_harness.py"
    if harness.exists():
        completed = subprocess.run([sys.executable, str(harness)], cwd=ROOT, check=False)
        if completed.returncode:
            fail(f"{directory.name}: eval failed")

if set(catalog_by_name) != skill_names:
    fail(f"catalog/filesystem mismatch: catalog={sorted(catalog_by_name)} filesystem={sorted(skill_names)}")

root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
for name in sorted(skill_names):
    if f"skills/{name}/README.md" not in root_readme:
        fail(f"README does not link {name}")

for markdown_path in ROOT.rglob("*.md"):
    relative_path = markdown_path.relative_to(ROOT)
    if ".git" in markdown_path.parts or (relative_path.parts and relative_path.parts[0] == "skills"):
        continue
    markdown_text = markdown_path.read_text(encoding="utf-8")
    for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", markdown_text):
        target = target.strip().strip("<>").split("#", 1)[0]
        if not target or re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I):
            continue
        resolved = (markdown_path.parent / target).resolve()
        try:
            resolved.relative_to(ROOT.resolve())
        except ValueError:
            fail(f"{relative_path}: link escapes repository: {target}")
            continue
        if not resolved.exists():
            fail(f"{relative_path}: broken local link: {target}")

for path in ROOT.rglob("*.json"):
    if ".git" not in path.parts:
        load_json(path)
for path in ROOT.rglob("*.jsonl"):
    if ".git" in path.parts:
        continue
    lineno = 0
    try:
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip():
                json.loads(line)
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"invalid JSONL {path.relative_to(ROOT)} line {lineno}: {exc}")

for relative in ("README.md", "LICENSE", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md", "SECURITY.md", "SUPPORT.md"):
    if not (ROOT / relative).exists():
        fail(f"missing {relative}")

compatibility = load_json(ROOT / "compatibility.json")
if compatibility.get("standard") != "https://agentskills.io/specification":
    fail("compatibility standard missing")
if set(compatibility.get("skills", [])) != skill_names:
    fail("compatibility skill list mismatch")

if errors:
    print("\n".join("ERROR " + message for message in errors))
    raise SystemExit(1)
print(f"OK: {len(skill_names)} skill(s), catalog, manifests, structured assets, and community files valid")
