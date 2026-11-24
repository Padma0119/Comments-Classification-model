import re
from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parent.parent
RAW, OUT = ROOT / "data" / "raw", ROOT / "data" / "processed"
LABELS = ["toxic","severe_toxic","obscene","threat","insult","identity_hate"]
SEED = 42

def clean(t: str) -> str:
    t = re.sub(r"https?://\S+|www\.\S+", " ", str(t))   # URLs
    return re.sub(r"\s+", " ", t).strip()                # whitespace

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(next(RAW.glob("train.csv*")))

    df["text"] = df.comment_text.map(clean)
    df["key"] = df.text.str.lower()

    before = len(df)
    df = (df.groupby("key", as_index=False)
            .agg({"id": "first", "text": "first", **{l: "max" for l in LABELS}}))
    print(f"Removed {before - len(df)} duplicate rows")

    df = df[df.text.str.len() > 0].reset_index(drop=True)
    df["any_toxic"] = df[LABELS].max(axis=1)

    train, temp = train_test_split(df, test_size=0.20, random_state=SEED,
                                   stratify=df.any_toxic)
    val, test = train_test_split(temp, test_size=0.50, random_state=SEED,
                                 stratify=temp.any_toxic)

    cols = ["id", "text"] + LABELS
    for name, d in [("train", train), ("val", val), ("test", test)]:
        d[cols].to_parquet(OUT / f"{name}.parquet", index=False)
        print(name, len(d), d[LABELS].sum().to_dict())

if __name__ == "__main__":
    main()