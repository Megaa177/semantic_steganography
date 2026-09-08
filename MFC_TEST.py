import re
import math
import nltk
from nltk.corpus import wordnet as wn
import gensim.downloader as api

# --------------------------------------------------
# Only WordNet is needed
# --------------------------------------------------
nltk.download('wordnet')

# --------------------------------------------------
# Load GloVe embeddings (40MB)
# --------------------------------------------------
print("Loading GloVe model...")
model = api.load("glove-wiki-gigaword-100")
print("GloVe loaded.\n")

# --------------------------------------------------
# Regex tokenizer (stable)
# --------------------------------------------------
def simple_tokenize(text):
    return re.findall(r"\w+|[^\w\s]", text)

# --------------------------------------------------
# Convert secret message → binary
# --------------------------------------------------
def to_binary(msg):
    return ''.join(format(ord(c), '08b') for c in msg)

# --------------------------------------------------
# Infer POS using WordNet
# --------------------------------------------------
def infer_pos(word):
    synsets = wn.synsets(word)
    if not synsets:
        return None

    # Priority order
    for pos in [wn.NOUN, wn.VERB, wn.ADJ, wn.ADV]:
        if any(s.pos() == pos for s in synsets):
            return pos

    return None

# --------------------------------------------------
# Generate synonym cluster
# --------------------------------------------------
def get_synonym_cluster(word, pos, max_size=6):
    if word not in model or pos is None:
        return []

    cluster = []

    try:
        neighbors = model.most_similar(word, topn=25)
    except KeyError:
        return []

    for neigh, score in neighbors:
        synsets = wn.synsets(neigh)
        if any(s.pos() == pos for s in synsets):
            cluster.append(neigh)

        if len(cluster) >= max_size:
            break

    return list(dict.fromkeys(cluster))

# --------------------------------------------------
# Encode cover text
# --------------------------------------------------
def encode_text(cover_text, secret_msg):
    binary = to_binary(secret_msg)
    bit_ptr = 0

    tokens = simple_tokenize(cover_text)
    output = []

    for word in tokens:
        # Only alphabetic words
        if word.isalpha():
            pos = infer_pos(word.lower())
            cluster = get_synonym_cluster(word.lower(), pos)

            if len(cluster) >= 2 and bit_ptr < len(binary):
                bits_per_word = int(math.floor(math.log2(len(cluster))))

                if bits_per_word > 0:
                    bits = binary[bit_ptr: bit_ptr + bits_per_word]
                    if len(bits) < bits_per_word:
                        bits = bits.ljust(bits_per_word, '0')

                    idx = int(bits, 2)
                    idx = min(idx, len(cluster) - 1)

                    chosen = cluster[idx]

                    # Preserve capitalization
                    if word[0].isupper():
                        chosen = chosen.capitalize()

                    output.append(chosen)
                    bit_ptr += bits_per_word
                    continue

        output.append(word)

    return " ".join(output)

# --------------------------------------------------
# DEMO
# --------------------------------------------------
if __name__ == "__main__":
    cover = """
    The economy is showing signs of improvement as markets stabilize after weeks of turbulence.
    Experts believe consumer confidence will continue to grow.
    """

    secret = "HELLO"

    encoded = encode_text(cover, secret)

    print("ORIGINAL TEXT:\n")
    print(cover)

    print("\nENCODED TEXT:\n")
    print(encoded)

# --------------------------------------------------
# Convert binary → text
# --------------------------------------------------
def from_binary(binary):
    chars = []
    for i in range(0, len(binary), 8):
        byte = binary[i:i+8]
        if len(byte) < 8:
            break
        chars.append(chr(int(byte, 2)))
    return ''.join(chars)


# --------------------------------------------------
# Decode encoded text
# --------------------------------------------------
def decode_text(encoded_text):
    tokens = simple_tokenize(encoded_text)
    recovered_bits = ""

    for word in tokens:
        if word.isalpha():
            lower = word.lower()
            pos = infer_pos(lower)
            cluster = get_synonym_cluster(lower, pos)

            if len(cluster) >= 2:
                bits_per_word = int(math.floor(math.log2(len(cluster))))

                if bits_per_word > 0:
                    try:
                        idx = cluster.index(lower)
                        bits = format(idx, f'0{bits_per_word}b')
                        recovered_bits += bits
                    except ValueError:
                        # Word not in cluster → skip
                        pass

    return from_binary(recovered_bits)

decoded = decode_text(encoded)
print("\nDECODED SECRET:\n")
print(decoded)
