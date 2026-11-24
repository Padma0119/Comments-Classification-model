import requests

API = "http://127.0.0.1:8000"
samples = [
    "Have a great day, everyone!",
    "You are a stupid idiot and everyone hates you",
    "I will find you and hurt you",
    "shut up you moron",
    "I am a gay man",
    "what a pathetic loser",
    "This article is garbage and so are you",
    "idiot",
    "Thanks for sharing, very helpful",
    "go away you worthless piece of trash",
]
for i, t in enumerate(samples):
    r = requests.post(f"{API}/moderate", json={"id": f"seed{i}", "text": t}).json()
    print(f"{r['action']:10s} {r['label']:13s} {r['score']:.2f}  {t}")