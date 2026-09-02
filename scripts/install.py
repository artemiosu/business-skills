#!/usr/bin/env python3
"""Install repository skills into Codex; preserve existing copies by default."""
import argparse, os, pathlib, shutil, tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument("--dest");p.add_argument("--agent",choices=("codex","claude-code","cursor","copilot","windsurf","gemini","agents"),default="codex");p.add_argument("--skill",action="append");p.add_argument("--force",action="store_true");p.add_argument("--dry-run",action="store_true");a=p.parse_args()
    homes={"codex":pathlib.Path(os.environ.get("CODEX_HOME",pathlib.Path.home()/".codex"))/"skills","claude-code":pathlib.Path.home()/".claude"/"skills","cursor":pathlib.Path.home()/".cursor"/"skills","copilot":pathlib.Path.home()/".copilot"/"skills","windsurf":pathlib.Path.home()/".codeium"/"windsurf"/"skills","gemini":pathlib.Path.home()/".gemini"/"skills","agents":pathlib.Path.home()/".agents"/"skills"}
    base=pathlib.Path(a.dest).expanduser() if a.dest else homes[a.agent]
    candidates=[d for d in sorted((ROOT/"skills").iterdir()) if d.is_dir() and (d/"SKILL.md").is_file()]
    if a.skill:
        wanted=set(a.skill);candidates=[d for d in candidates if d.name in wanted];missing=wanted-{d.name for d in candidates}
        if missing:print("ERROR unknown skill(s): "+", ".join(sorted(missing)));return 2
    if a.dry_run:
        for src in candidates:print(f"WOULD_INSTALL {src.name} -> {base/src.name}")
        return 0
    base.mkdir(parents=True,exist_ok=True);installed=[];skipped=[]
    for src in candidates:
        dst=base/src.name
        if dst.exists() and not a.force:skipped.append(src.name);print(f"SKIP {src.name}: {dst} exists (use --force)");continue
        stage=pathlib.Path(tempfile.mkdtemp(prefix=f".{src.name}-",dir=base))/src.name;backup=base/f".{src.name}.backup"
        try:
            shutil.copytree(src,stage,ignore=shutil.ignore_patterns("__pycache__","*.pyc"))
            if not (stage/"SKILL.md").is_file():raise RuntimeError("staged skill is invalid")
            if dst.exists():shutil.rmtree(backup,ignore_errors=True);dst.rename(backup)
            stage.rename(dst)
            if backup.exists():shutil.rmtree(backup)
            installed.append(src.name);print(f"INSTALLED {src.name} -> {dst}")
        except Exception:
            if backup.exists() and not dst.exists():backup.rename(dst)
            raise
        finally:shutil.rmtree(stage.parent,ignore_errors=True)
    print(f"SUMMARY installed={len(installed)} skipped={len(skipped)}");return 0
if __name__=="__main__":raise SystemExit(main())
