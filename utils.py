import nltk
from nltk import pos_tag
from nltk.corpus import wordnet as wn

# ---- DOWNLOAD REQUIRED MODELS (RUN ONCE) ----
nltk.download('averaged_perceptron_tagger_eng')
nltk.download('wordnet')
nltk.download('omw-1.4')

print("\n--- POS TAG TEST ---")
tokens = ["The", "economy", "is", "showing", "signs", "of", "growth"]
tags = pos_tag(tokens)
print(tags)

print("\n--- WORDNET SYNONYM TEST ---")
word = "economy"
synsets = wn.synsets(word, pos=wn.NOUN)

if synsets:
    print(f"Synonyms for '{word}':")
    for lemma in synsets[0].lemmas():
        print(" -", lemma.name())
else:
    print("No synsets found.")
