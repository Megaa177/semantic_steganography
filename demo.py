import re
from math import log2, floor
from nltk.corpus import wordnet as wn
from nltk import pos_tag
import json

# TOKENIZER
def simple_tokenize(text):
    return re.findall(r'\w+|[^\w\s]', text)


# SECRET to BITSTREAM
def secret_to_bits(secret):
    return ''.join(format(ord(c), '08b') for c in secret)

def bits_to_secret(bits):
    out = ''
    for i in range(0, len(bits), 8):
        chunk = bits[i:i+8]
        if len(chunk) < 8:
            break
        out += chr(int(chunk, 2))
    return out

# POS MAP
def wn_pos(treebank_tag):
    if treebank_tag.startswith('N'):
        return wn.NOUN
    if treebank_tag.startswith('J'):
        return wn.ADJ
    return None   # Only nouns & adjectives

# SYNONYM CLUSTER
def get_synonym_cluster(word, pos):
    synsets = wn.synsets(word, pos=pos)
    if not synsets:
        return None

    base = synsets[0]
    lemmas = []

    for l in base.lemmas():
        name = l.name().replace('_', ' ')
        if name.isalpha():
            lemmas.append(name.lower())

    cluster = sorted(set(lemmas)) #using set to remove duplicates 

    # Only keeping clusters where original word exists
    if word.lower() not in cluster:
        return None

    return cluster if len(cluster) >= 2 else None


# BITS PER WORD
def bits_per_word(n):
    return floor(log2(n)) if n >= 2 else 0


# CARRIER SELECTION
def select_carriers(tokens):
    tagged = pos_tag(tokens)
    carriers = []

    for i, (tok, tag) in enumerate(tagged):
        if not tok.isalpha():
            continue

        pos = wn_pos(tag)
        if not pos:
            continue

        cluster = get_synonym_cluster(tok.lower(), pos)
        if not cluster:
            continue

        bpw = bits_per_word(len(cluster))
        if bpw == 0:
            continue

        carriers.append((i, tok, cluster, bpw))

    return carriers

# ENCODE
def encode_text(cover_text, secret):
    bits = secret_to_bits(secret)
    tokens = simple_tokenize(cover_text)

    carriers = select_carriers(tokens)
    capacity = sum(bpw for _, _, _, bpw in carriers)

    print(f"Carrier words: {len(carriers)}")
    print(f"Capacity (bits): {capacity}")
    print(f"Secret size (bits): {len(bits)}")

    if capacity < len(bits):
        raise ValueError("Not enough capacity.")

    bit_ptr = 0
    out = tokens[:]
    used_positions = []

    print("\n--- ENCODING TRACE ---")
    for idx, word, cluster, bpw in carriers:
        if bit_ptr >= len(bits):
            break

        chunk = bits[bit_ptr:bit_ptr+bpw].ljust(bpw, '0')
        sel = int(chunk, 2)
        sel = min(sel, len(cluster) - 1)

        chosen = cluster[sel]
        if word[0].isupper():
            chosen = chosen.capitalize()

        out[idx] = chosen
        used_positions.append((idx, cluster, bpw))

        print(f"{word} -> {chosen} | bits: {chunk} | pos: {idx}")
        bit_ptr += bpw

    metrics = compute_capacity_metrics(cover_text, carriers, len(bits))
    print("\n--- CAPACITY METRICS ---")
    for k, v in metrics.items():
        print(f"{k}: {v}")

    return ' '.join(out), used_positions, len(bits)

# DECODE
def decode_text(encoded_text, used_positions, secret_bit_len):
    tokens = simple_tokenize(encoded_text)
    recovered = ''

    print("\n--- DECODING TRACE ---")

    for idx, cluster, bpw in used_positions:
        if len(recovered) >= secret_bit_len:
            break

        word = tokens[idx].lower()
        if word not in cluster:
            print("DESYNC ERROR at position", idx)
            continue

        sel = cluster.index(word)
        chunk = format(sel, f'0{bpw}b')
        recovered += chunk

        print(f"{tokens[idx]} | index: {sel} | bits: {chunk}")

    return bits_to_secret(recovered[:secret_bit_len])


def compute_capacity_metrics(cover_text, carriers, secret_bits):
    total_words = len([t for t in simple_tokenize(cover_text) if t.isalpha()])
    total_carriers = len(carriers)
    total_capacity = sum(bpw for _, _, _, bpw in carriers)

    embedding_rate = secret_bits / total_words
    avg_bits_per_carrier = total_capacity / total_carriers if total_carriers else 0
    carrier_ratio = total_carriers / total_words if total_words else 0

    return {
        "total_words": total_words,
        "total_carriers": total_carriers,
        "total_capacity_bits": total_capacity,
        "embedding_rate_bits_per_word": embedding_rate,
        "avg_bits_per_carrier": avg_bits_per_carrier,
        "carrier_ratio": carrier_ratio
    }

from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction

def compute_bleu(original_text, encoded_text):
    smoothie = SmoothingFunction().method4
    reference = [original_text.split()]
    candidate = encoded_text.split()
    return sentence_bleu(reference, candidate, smoothing_function=smoothie)

from collections import Counter
import math

def shannon_entropy(bitstring):
    counts = Counter(bitstring)
    total = len(bitstring)
    entropy = 0
    for c in counts:
        p = counts[c] / total
        entropy -= p * math.log2(p)
    return entropy

# MAIN
if __name__ == "__main__":
    with open("c_article.txt", "r", encoding="utf-8") as f:
        cover = f.read()

    secret = "MFC"

    print("\n--- ENCODING ---")
    encoded, used_positions, bit_len = encode_text(cover, secret)

    # Save encoded article
    with open("encoded.txt", "w", encoding="utf-8") as f:
        f.write(encoded)

    # Save key file
    with open("key_positions.json", "w", encoding="utf-8") as f:
        json.dump(used_positions, f)

    print("\nEncoded text saved to encoded.txt")
    print("Key saved to key_positions.json")
    
    
    print("\n--- DECODING ---")
    with open("key_positions.json", "r", encoding="utf-8") as f:
        used_positions = json.load(f)

    decoded = decode_text(encoded, used_positions, bit_len)

    print("\nDECODED SECRET:", decoded)

    if decoded == secret:
        print("\n Secret successfully recovered!")
    else:
        print("\n Secret recovery failed!")

    bleu = compute_bleu(cover, encoded)
    print("BLEU Score:", bleu)

    base_bits = secret_to_bits(secret)
    print("Base entropy:", shannon_entropy(base_bits))
