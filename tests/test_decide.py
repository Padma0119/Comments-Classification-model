from src.decide import decide

THR = {l: {"review": 0.4, "hide": 0.9} for l in
       ["toxic","severe_toxic","obscene","threat","insult","identity_hate"]}

def sc(**kw):
    base = {l: 0.01 for l in THR}
    base.update(kw); return base

def test_clean_published():
    assert decide(sc(), THR, "have a great day friends")["action"] == "publish"

def test_review_band():
    assert decide(sc(insult=0.6), THR, "some longer comment here")["action"] == "review"

def test_auto_hide():
    r = decide(sc(toxic=0.97), THR, "some longer comment here")
    assert r["action"] == "auto_hide" and r["label"] == "toxic"

def test_threat_never_auto_hidden():
    assert decide(sc(threat=0.99), THR, "a long threatening sentence")["action"] == "review"

def test_short_comment_not_auto_hidden():
    assert decide(sc(toxic=0.97), THR, "idiot")["action"] == "review"

def test_most_severe_label_wins():
    r = decide(sc(toxic=0.5, insult=0.95), THR, "some longer comment here")
    assert r["action"] == "auto_hide" and r["label"] == "insult"