import os, pandas as pd, plotly.express as px, requests, streamlit as st
st.set_page_config(page_title="Business Metrics Anomaly Detection",layout="wide")
st.title("Business Metrics Anomaly Detection")
api=os.getenv("API_BASE_URL","http://localhost:8000").rstrip("/")
upload=st.file_uploader("Upload CSV",type=["csv"])
if upload:
    try:
        df=pd.read_csv(upload)
        if not {"timestamp","metric","value"}.issubset(df.columns): st.error("CSV requires timestamp, metric, value"); st.stop()
        r=requests.post(api+"/detect",json={"records":df.where(pd.notna(df),None).to_dict("records")},timeout=30)
        if r.status_code!=200: st.error(f"API error {r.status_code}: {r.text}"); st.stop()
        out=pd.DataFrame(r.json()["results"]); out["timestamp"]=pd.to_datetime(out.timestamp,utc=True); bad=out[out.is_anomaly==True] # noqa: E712
        a,b,c=st.columns(3); a.metric("Rows",len(out)); b.metric("Anomalies",len(bad)); c.metric("Rate",f"{len(bad)/max(1,len(out)):.1%}")
        metric=st.selectbox("Metric",sorted(out.metric.unique())); view=out[out.metric==metric]
        fig=px.line(view,x="timestamp",y="value",title=f"{metric}: observed values")
        marked=view[view.is_anomaly==True] # noqa: E712
        if not marked.empty: fig.add_scatter(x=marked.timestamp,y=marked.value,mode="markers",name="Anomaly")
        st.plotly_chart(fig,use_container_width=True); st.dataframe(bad,use_container_width=True)
        st.download_button("Download scored CSV",out.to_csv(index=False),"anomaly_results.csv","text/csv")
    except requests.RequestException as e: st.error(f"Cannot reach API {api}: {e}")
else: st.info("Upload a CSV with timestamp, metric, and value columns.")
