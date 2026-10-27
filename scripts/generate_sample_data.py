from pathlib import Path

import numpy as np
import pandas as pd


def main():
    rng=np.random.default_rng(20261025); dates=pd.date_range("2026-01-01",periods=120,freq="D",tz="UTC"); rows=[]
    for metric,base,noise,events in [("daily_orders",220,12,{31:110,78:-95}),("conversion_rate_pct",3.8,.18,{45:1.2,93:-1.1}),("revenue_usd",12500,650,{24:5200,84:-4700})]:
        vals=base+rng.normal(0,noise,len(dates))
        for i,d in events.items(): vals[i]+=d
        rows += [{"timestamp":t.isoformat(),"metric":metric,"value":round(float(v),4),"source":"seeded_synthetic_demo"} for t,v in zip(dates,vals)]
    p=Path(__file__).resolve().parents[1]/"sample_data"/"business_metrics.csv"; p.parent.mkdir(exist_ok=True,parents=True); pd.DataFrame(rows).to_csv(p,index=False); print(f"Wrote {len(rows)} rows to {p}")
if __name__=="__main__": main()
