import random
from pathlib import Path

# ---------------- CONFIG ----------------
OUTPUT_PATH = Path("data/cover_article.txt")
NUM_PARAGRAPHS = 3
SENTENCES_PER_PARA = 4

# ---------------- LANGUAGE POOL ----------------
subjects = [
    "The government",
    "Economic analysts",
    "Researchers",
    "Industry experts",
    "Policy makers",
    "Officials",
]

verbs = [
    "stated",
    "reported",
    "explained",
    "confirmed",
    "suggested",
    "indicated",
]

objects = [
    "the new policy",
    "recent developments",
    "the economic situation",
    "the proposed changes",
    "current market trends",
    "the ongoing reforms",
]

extensions = [
    "could have long-term effects",
    "are being closely monitored",
    "may influence future decisions",
    "remain under discussion",
    "have raised public interest",
    "are expected to evolve",
]

# ---------------- ARTICLE GENERATION ----------------
def generate_sentence():
    s = random.choice(subjects)
    v = random.choice(verbs)
    o = random.choice(objects)
    e = random.choice(extensions)
    return f"{s} {v} that {o} {e}."


def generate_paragraph():
    return " ".join(generate_sentence() for _ in range(SENTENCES_PER_PARA))


def generate_article():
    return "\n\n".join(generate_paragraph() for _ in range(NUM_PARAGRAPHS))


# ---------------- SAVE TO FILE ----------------
def main():
    OUTPUT_PATH.parent.mkdir(exist_ok=True)

    article = generate_article()

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(article)

    print("Article generated successfully.")
    print(f"Saved to: {OUTPUT_PATH.resolve()}\n")
    print("Preview:\n")
    print(article)


if __name__ == "__main__":
    main()
