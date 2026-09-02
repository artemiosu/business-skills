#!/usr/bin/env python3
"""Dependency-free repository checks used locally and in CI."""
import json, pathlib, re, subprocess, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]; errors=[]
def fail(msg):errors.append(msg)
manifest=json.loads((ROOT/".codex-plugin"/"plugin.json").read_text())
if manifest.get("name")!="business-skills" or manifest.get("skills")!="./skills/":fail("invalid plugin manifest")
names=set()
for d in sorted((ROOT/"skills").iterdir()):
    if not d.is_dir():continue
    f=d/"SKILL.md"
    if not f.is_file():fail(f"{d.name}: missing SKILL.md");continue
    text=f.read_text(encoding="utf-8");m=re.match(r"^---\n(.*?)\n---\n",text,re.S)
    if not m:fail(f"{d.name}: bad frontmatter");continue
    name=re.search(r"^name:\s*([^\n]+)$",m.group(1),re.M);desc=re.search(r"^description:\s*(.+)$",m.group(1),re.M)
    if not name or name.group(1).strip()!=d.name:fail(f"{d.name}: name mismatch")
    if not desc or len(desc.group(1).strip())<30:fail(f"{d.name}: weak description")
    if d.name in names:fail(f"duplicate skill {d.name}")
    names.add(d.name)
    harness=d/"scripts"/"eval_harness.py"
    if harness.exists() and subprocess.run([sys.executable,str(harness)]).returncode:fail(f"{d.name}: eval failed")
for rel in ("README.md","LICENSE","CONTRIBUTING.md","CODE_OF_CONDUCT.md","SECURITY.md","SUPPORT.md"):
    if not (ROOT/rel).exists():fail(f"missing {rel}")
compat=json.loads((ROOT/"compatibility.json").read_text())
if compat.get("standard")!="https://agentskills.io/specification":fail("compatibility standard missing")
if errors:
    print("\n".join("ERROR "+x for x in errors));raise SystemExit(1)
print(f"OK: {len(names)} skill(s), manifest and community files valid")
