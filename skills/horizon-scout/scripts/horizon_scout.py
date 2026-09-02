#!/usr/bin/env python3
"""Validate/score evidence and maintain a single-writer append-only forecast ledger."""
import argparse, datetime as dt, json, math, pathlib, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]; DEFAULT=ROOT/"assets"/"config.default.json"
POS=("reliability","independence","leadingness","magnitude","persistence","breadth","economics","bottleneck_relief")
PEN=("hype","fragility","missingness"); DIRECTIONS={"supports":1,"contradicts":-1,"ambiguous":0}
def obj(path):
    with open(path,encoding="utf-8") as f:return json.load(f)
def rows(path):
    p=pathlib.Path(path)
    if not p.exists():return []
    out=[]
    with p.open(encoding="utf-8") as f:
        for n,line in enumerate(f,1):
            if line.strip():
                try: out.append(json.loads(line))
                except json.JSONDecodeError as e: raise ValueError(f"{p}:{n}: {e}")
    return out
def date(v,name):
    try:return dt.date.fromisoformat(v)
    except (TypeError,ValueError):raise ValueError(f"{name} must be ISO date YYYY-MM-DD")
def prob(v,name):
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not 0<=v<=1:raise ValueError(f"{name} must be finite number [0,1]")
    return float(v)
def nonempty(o,keys):
    bad=[k for k in keys if not isinstance(o.get(k),str) or not o[k].strip()]
    if bad:raise ValueError("missing/non-string fields: "+", ".join(bad))
def validate_signal(x):
    nonempty(x,("id","as_of_date","observed_at","claim","lane","independence_group"))
    if x.get("record_type")!="signal":raise ValueError("record_type must be signal")
    if x.get("direction") not in DIRECTIONS:raise ValueError("bad direction")
    cutoff=date(x["as_of_date"],"as_of_date"); date(x["observed_at"],"observed_at")
    src=x.get("source");
    if not isinstance(src,dict):raise ValueError("source must be object")
    nonempty(src,("title","publisher","url","published_at","retrieved_at","source_type","reliability_note"))
    for k in ("published_at","retrieved_at"):
        if date(src[k],k)>cutoff:raise ValueError(f"future leakage: {k} after as_of_date")
    if src.get("event_at") and date(src["event_at"],"event_at")>cutoff:raise ValueError("future leakage: event_at")
    if not isinstance(src.get("primary"),bool):raise ValueError("source.primary must be boolean")
    s=x.get("scores",{})
    for k in POS+PEN:
        if isinstance(s.get(k),bool) or not isinstance(s.get(k),int) or not 0<=s[k]<=5:raise ValueError(f"scores.{k} must be integer 0..5")
def validate_forecast(x):
    nonempty(x,("id","created_at","as_of_date","question","resolution_date","resolution_rule","resolution_source"))
    if x.get("record_type")!="forecast" or x.get("status")!="open":raise ValueError("forecast must have record_type=forecast,status=open")
    created=date(x["created_at"],"created_at"); cutoff=date(x["as_of_date"],"as_of_date"); deadline=date(x["resolution_date"],"resolution_date")
    if cutoff>created or created>=deadline:raise ValueError("require as_of_date <= created_at < resolution_date")
    p=prob(x.get("probability"),"probability"); low=prob(x.get("probability_low",p),"probability_low"); high=prob(x.get("probability_high",p),"probability_high")
    if not low<=p<=high:raise ValueError("probability bounds must bracket probability")
    if x.get("base_rate") is not None:prob(x["base_rate"],"base_rate")
def validate_ledger(rs):
    fs={}; resolved=set()
    for x in rs:
        if x.get("record_type")=="forecast":
            validate_forecast(x)
            if x["id"] in fs:raise ValueError("duplicate forecast id")
            if x.get("supersedes") and x["supersedes"] not in fs:raise ValueError("supersedes must reference earlier forecast")
            fs[x["id"]]=x
        elif x.get("record_type")=="resolution":
            nonempty(x,("forecast_id","resolved_at","source"))
            if x["forecast_id"] not in fs:raise ValueError("orphan resolution")
            if x["forecast_id"] in resolved:raise ValueError("duplicate resolution")
            if isinstance(x.get("outcome"),bool) or x.get("outcome") not in (0,1):raise ValueError("outcome must be 0 or 1")
            if date(x["resolved_at"],"resolved_at")<date(fs[x["forecast_id"]]["resolution_date"],"resolution_date"):raise ValueError("resolution precedes deadline")
            resolved.add(x["forecast_id"])
        else:raise ValueError("unknown record_type in ledger")
    return fs,resolved
def append(path,x):
    p=pathlib.Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("a",encoding="utf-8") as f:f.write(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n");f.flush()
def quality(x,cfg):
    validate_signal(x); s=x["scores"];w=cfg["positive_weights"]
    raw=100*sum(s[k]*w[k] for k in POS)/(5*sum(w[k] for k in POS));pen=sum(s[k]*cfg["penalty_points"][k] for k in PEN)
    return round(max(0,min(100,raw-pen)),2)
def cmd_score(a):
    cfg=obj(a.config); out=[]
    for x in rows(a.signals):out.append({"id":x["id"],"evidence_quality":quality(x,cfg),"direction":x["direction"],"signed_support":round(DIRECTIONS[x["direction"]]*quality(x,cfg),2),"not_a_probability":True})
    print(json.dumps(out,ensure_ascii=False,indent=2))
def cmd_assess(a):
    cfg=obj(a.config); xs=rows(a.signals)
    for x in xs:quality(x,cfg)
    lanes={x["lane"] for x in xs};groups={x["independence_group"] for x in xs};g=cfg["gates"]
    gate="PASS" if len(lanes)>=g["minimum_evidence_lanes"] and len(groups)>=g["minimum_independence_groups"] else "MONITOR"
    by_group={}
    for x in xs:by_group.setdefault(x["independence_group"],[]).append(DIRECTIONS[x["direction"]]*quality(x,cfg))
    group_support=[sum(v)/len(v) for v in by_group.values()];support=sum(group_support)/max(1,len(group_support))
    thesis="SUPPORT" if support>=20 else "OPPOSE" if support<=-20 else "UNCERTAIN"
    print(json.dumps({"evidence_gate":gate,"thesis_evidence":thesis,"lanes":len(lanes),"independence_groups":len(groups),"group_capped_signed_support":round(support,2),"not_a_probability":True},indent=2))
def cmd_add(a):
    x=obj(a.forecast);x.setdefault("record_type","forecast");x.setdefault("status","open");validate_forecast(x);rs=rows(a.ledger);fs,_=validate_ledger(rs)
    if x["id"] in fs:raise ValueError("forecast id exists")
    if x.get("supersedes") and x["supersedes"] not in fs:raise ValueError("supersedes must reference earlier forecast")
    append(a.ledger,x);print(x["id"])
def cmd_resolve(a):
    rs=rows(a.ledger);fs,resolved=validate_ledger(rs)
    if a.id not in fs or a.id in resolved:raise ValueError("unknown or already resolved forecast")
    when=a.resolved_at or dt.date.today().isoformat()
    if date(when,"resolved_at")<date(fs[a.id]["resolution_date"],"resolution_date"):raise ValueError("resolution precedes deadline")
    append(a.ledger,{"record_type":"resolution","forecast_id":a.id,"resolved_at":when,"outcome":a.outcome,"source":a.source,"notes":a.notes});print(a.id)
def cmd_validate(a):validate_ledger(rows(a.ledger));print("valid")
def cmd_backtest(a):
    rs=rows(a.ledger);fs,resolved=validate_ledger(rs);ys={x["forecast_id"]:x["outcome"] for x in rs if x.get("record_type")=="resolution"};pairs=[(float(fs[i]["probability"]),y,fs[i].get("base_rate")) for i,y in ys.items()]
    if not pairs:raise ValueError("no resolved forecasts")
    b=sum((p-y)**2 for p,y,_ in pairs)/len(pairs);base=[(q-y)**2 for _,y,q in pairs if q is not None]
    print(json.dumps({"n_resolved":len(pairs),"n_open":len(fs)-len(resolved),"brier":round(b,6),"baseline_0_5_brier":0.25,"reference_rate_brier":round(sum(base)/len(base),6) if base else None,"warning":"Resolution scoring only. A valid temporal backtest additionally requires a preregistered cohort and frozen evidence snapshot; do not claim improvement for small/selected samples."},indent=2))
def main():
    p=argparse.ArgumentParser(description=__doc__);sp=p.add_subparsers(required=True)
    for name,fun in (("score",cmd_score),("assess",cmd_assess)):
        q=sp.add_parser(name);q.add_argument("signals");q.add_argument("--config",default=str(DEFAULT));q.set_defaults(func=fun)
    q=sp.add_parser("add-forecast");q.add_argument("ledger");q.add_argument("forecast");q.set_defaults(func=cmd_add)
    q=sp.add_parser("resolve");q.add_argument("ledger");q.add_argument("id");q.add_argument("outcome",type=int,choices=(0,1));q.add_argument("source");q.add_argument("--resolved-at");q.add_argument("--notes");q.set_defaults(func=cmd_resolve)
    q=sp.add_parser("validate-ledger");q.add_argument("ledger");q.set_defaults(func=cmd_validate)
    q=sp.add_parser("backtest");q.add_argument("ledger");q.set_defaults(func=cmd_backtest)
    a=p.parse_args()
    try:a.func(a)
    except (ValueError,OSError,KeyError,TypeError) as e:print(f"error: {e}",file=sys.stderr);return 2
    return 0
if __name__=="__main__":raise SystemExit(main())
