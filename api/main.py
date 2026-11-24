import json, sqlite3, time
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import pipeline
from src.decide import decide, load_thresholds

ROOT = Path(__file__).resolve().parent.parent
THR = load_thresholds(ROOT / "thresholds.json")
DB = ROOT / "queue.db"

clf = pipeline("text-classification", model=str(ROOT / "models" / "distilbert"),
               top_k=None, truncation=True, max_length=128,
               function_to_apply="sigmoid")

def db():
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS queue(
        id TEXT PRIMARY KEY, text TEXT, scores_json TEXT, action TEXT,
        label TEXT, score REAL, status TEXT DEFAULT 'pending',
        reviewer_decision TEXT, reviewer_labels TEXT, appealed INTEGER DEFAULT 0,
        created_at REAL, reviewed_at REAL)""")
    return con

app = FastAPI(title="Toxic comment filter")

class Comment(BaseModel):
    id: str
    text: str

class Review(BaseModel):
    decision: str                 # "keep" or "remove"
    labels: list[str] = []        # labels the moderator confirms (for "remove")


@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/moderate")
def moderate(c: Comment):
    scores = {r["label"]: r["score"] for r in clf(c.text)[0]}
    res = decide(scores, THR, c.text)
    if res["action"] != "publish":
        with db() as con:
            con.execute("INSERT OR REPLACE INTO queue(id,text,scores_json,action,label,score,created_at) VALUES (?,?,?,?,?,?,?)",
                        (c.id, c.text, json.dumps(scores), res["action"],
                         res["label"], res["score"], time.time()))
    return {"id": c.id, "scores": {k: round(v, 4) for k, v in scores.items()}, **res}

@app.get("/queue")
def queue(limit: int = 20):
    with db() as con:
        rows = con.execute(
            "SELECT id,text,action,label,score,scores_json,appealed FROM queue "
            "WHERE status='pending' ORDER BY appealed DESC, score DESC LIMIT ?", (limit,)).fetchall()
        n = con.execute("SELECT COUNT(*) FROM queue WHERE status='pending'").fetchone()[0]
    keys = ["id","text","action","label","score","scores_json","appealed"]
    return {"pending": n, "items": [dict(zip(keys, r)) for r in rows]}

@app.post("/review/{cid}")
def review(cid: str, r: Review):
    if r.decision not in ("keep", "remove"):
        raise HTTPException(400, "decision must be keep or remove")
    with db() as con:
        cur = con.execute(
            "UPDATE queue SET status='reviewed', reviewer_decision=?, reviewer_labels=?, reviewed_at=? WHERE id=?",
            (r.decision, json.dumps(r.labels), time.time(), cid))
    if cur.rowcount == 0:
        raise HTTPException(404, "not found")
    return {"id": cid, "decision": r.decision}


@app.post("/appeal/{cid}")
def appeal(cid: str):
    """The author of a hidden comment asks for a second look."""
    with db() as con:
        cur = con.execute(
            "UPDATE queue SET status='pending', appealed=1, action='review' "
            "WHERE id=? AND (action='auto_hide' OR reviewer_decision='remove')", (cid,))
    if cur.rowcount == 0:
        raise HTTPException(404, "no hidden comment with that id")
    return {"id": cid, "status": "queued for re-review"}