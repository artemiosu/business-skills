#!/usr/bin/env python3
"""Minimum deterministic checks for Horizon Scout package invariants."""
import json, pathlib, subprocess, sys, tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
def run(*args): return subprocess.run([sys.executable,str(ROOT/"scripts"/"horizon_scout.py"),*map(str,args)],text=True,capture_output=True)
def main():
    checks=[]
    def check(name,ok,detail=""): checks.append((name,bool(ok),detail))
    good=run("score",ROOT/"assets"/"example_signals.jsonl"); check("valid signal scores",good.returncode==0,good.stderr)
    if good.returncode==0:
        data=json.loads(good.stdout); check("score bounded and labeled",0<=data[0]["evidence_quality"]<=100 and data[0]["not_a_probability"])
        check("contradicting evidence is negative",data[0]["direction"]!="contradicts" or data[0]["signed_support"]<=0)
    with tempfile.TemporaryDirectory() as d:
        ledger=pathlib.Path(d)/"ledger.jsonl"; forecast=pathlib.Path(d)/"f.json"
        obj={"id":"t1","created_at":"2026-01-01","as_of_date":"2026-01-01","question":"Binary test?","resolution_date":"2026-12-31","resolution_rule":"1 iff authoritative source says yes","resolution_source":"https://example.org","probability":0.7,"probability_low":0.5,"probability_high":0.8}
        forecast.write_text(json.dumps(obj),encoding="utf-8")
        first=run("add-forecast",ledger,forecast); duplicate=run("add-forecast",ledger,forecast)
        check("forecast appends",first.returncode==0,first.stderr); check("duplicate rejected",duplicate.returncode!=0)
        res=run("resolve",ledger,"t1","1","https://example.org/result","--resolved-at","2027-01-01"); again=run("resolve",ledger,"t1","1","https://example.org/result","--resolved-at","2027-01-01")
        check("resolution appends",res.returncode==0,res.stderr); check("second resolution rejected",again.returncode!=0)
        bt=run("backtest",ledger); check("backtest works",bt.returncode==0 and json.loads(bt.stdout)["n_resolved"]==1,bt.stderr)
        obj["id"]="bad"; obj["probability"]=1.2; forecast.write_text(json.dumps(obj),encoding="utf-8")
        check("invalid probability rejected",run("add-forecast",ledger,forecast).returncode!=0)
        obj["id"]="bool"; obj["probability"]=True; forecast.write_text(json.dumps(obj),encoding="utf-8")
        check("boolean probability rejected",run("add-forecast",ledger,forecast).returncode!=0)
        obj.update(id="leak",probability=.5,as_of_date="2028-01-01",created_at="2027-01-01",resolution_date="2026-01-01"); forecast.write_text(json.dumps(obj),encoding="utf-8")
        check("invalid temporal order rejected",run("add-forecast",ledger,forecast).returncode!=0)
        signal=json.loads((ROOT/"assets"/"example_signals.jsonl").read_text())
        signal["direction"]="contradicts"; signal["id"]="c1"
        signal2=dict(signal,id="c2")
        sigfile=pathlib.Path(d)/"signals.jsonl";sigfile.write_text(json.dumps(signal)+"\n"+json.dumps(signal2)+"\n",encoding="utf-8")
        assessment=run("assess",sigfile); result=json.loads(assessment.stdout)
        check("all-counterevidence cannot support thesis",assessment.returncode==0 and result["thesis_evidence"]=="OPPOSE")
        check("duplicate group does not satisfy gate",result["evidence_gate"]=="MONITOR" and result["independence_groups"]==1)
    required=[ROOT/"SKILL.md",ROOT/"agents"/"openai.yaml",ROOT/"references"/"workflow.md",ROOT/"references"/"schemas.md",ROOT/"references"/"evaluation.md",ROOT/"assets"/"config.default.json"]
    check("required files present",all(p.exists() for p in required))
    for name,ok,detail in checks: print(("PASS" if ok else "FAIL"),name,detail.strip())
    failed=sum(not x[1] for x in checks); print(f"{len(checks)-failed}/{len(checks)} checks passed"); return 1 if failed else 0
if __name__=="__main__": raise SystemExit(main())
