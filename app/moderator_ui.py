import json
import requests
import streamlit as st

API = "http://127.0.0.1:8000"
LABELS = ["toxic","severe_toxic","obscene","threat","insult","identity_hate"]

st.set_page_config(page_title="Moderator queue", layout="centered")
st.title("Moderator queue")

try:
    data = requests.get(f"{API}/queue", params={"limit": 1}, timeout=10).json()
except Exception as e:
    st.error(f"API not reachable at {API}. Start it with: uvicorn api.main:app\n\n{e}")
    st.stop()

st.caption(f"{data['pending']} comments waiting")
if not data["items"]:
    st.success("Queue is empty.")
    st.stop()

it = data["items"][0]
if it["appealed"]:
    st.warning("Appeal: the author asked for a second look.")

st.subheader("Comment")
st.info(it["text"])
st.write(f"**Model action:** `{it['action']}` on **{it['label']}** (score {it['score']:.2f})")

scores = json.loads(it["scores_json"])
for l in LABELS:
    st.progress(min(max(scores.get(l, 0.0), 0.0), 1.0), text=f"{l}: {scores.get(l, 0.0):.2f}")

chosen = st.multiselect("Labels that apply (used if you remove it)", LABELS, default=[it["label"]])

c1, c2 = st.columns(2)
if c1.button("Keep (it's fine)", use_container_width=True):
    requests.post(f"{API}/review/{it['id']}", json={"decision": "keep", "labels": []})
    st.rerun()
if c2.button("Remove", type="primary", use_container_width=True):
    requests.post(f"{API}/review/{it['id']}", json={"decision": "remove", "labels": chosen})
    st.rerun()