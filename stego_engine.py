import re
import math
import hashlib
import json
from math import log2, floor
from collections import Counter

import nltk
from nltk.corpus import wordnet as wn
from nltk import pos_tag
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from Crypto.Cipher import AES

# Ensure required NLTK resources are available
for resource in ['wordnet', 'averaged_perceptron_tagger_eng', 'omw-1.4']:
    try:
        nltk.data.find(f'corpora/{resource}' if 'net' in resource or 'omw' in resource else f'taggers/{resource}')
    except LookupError:
        nltk.download(resource, quiet=True)

# -----------------------------
# AES ENCRYPTION / DECRYPTION
# -----------------------------
def aes_encrypt(plaintext: str, password: str) -> bytes:
    key = hashlib.sha256(password.encode('utf-8')).digest()[:16]
    nonce = hashlib.md5(password.encode('utf-8')).digest()[:8]
    cipher = AES.new(key, AES.MODE_CTR, nonce=nonce)
    return cipher.encrypt(plaintext.encode('utf-8'))

def aes_decrypt(ciphertext: bytes, password: str) -> str:
    key = hashlib.sha256(password.encode('utf-8')).digest()[:16]
    nonce = hashlib.md5(password.encode('utf-8')).digest()[:8]
    cipher = AES.new(key, AES.MODE_CTR, nonce=nonce)
    return cipher.decrypt(ciphertext).decode('utf-8')

# -----------------------------
# BIT CONVERSIONS
# -----------------------------
def text_to_bits(text: str) -> str:
    return ''.join(format(ord(c), '08b') for c in text)

def bits_to_text(bits: str) -> str:
    out = ''
    for i in range(0, len(bits), 8):
        chunk = bits[i:i+8]
        if len(chunk) < 8:
            break
        out += chr(int(chunk, 2))
    return out

def bytes_to_bits(byte_data: bytes) -> str:
    return ''.join(format(b, '08b') for b in byte_data)

def bits_to_bytes(bits: str) -> bytes:
    return bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))

# -----------------------------
# TOKENIZER & POS MAPPING
# -----------------------------
def simple_tokenize(text: str):
    return re.findall(r'\w+|[^\w\s]', text)

def wn_pos(treebank_tag: str):
    if treebank_tag.startswith('N'):
        return wn.NOUN
    if treebank_tag.startswith('V'):
        return wn.VERB
    if treebank_tag.startswith('J'):
        return wn.ADJ
    if treebank_tag.startswith('R'):
        return wn.ADV
    return None

def bits_per_word(cluster_size: int) -> int:
    return floor(log2(cluster_size)) if cluster_size >= 2 else 0

def get_synonym_cluster(word: str, pos):
    if not word.isalpha():
        return None
    synsets = wn.synsets(word, pos=pos)
    if not synsets:
        return None

    lemmas = []
    for s in synsets[:3]:
        for l in s.lemmas():
            name = l.name().replace('_', ' ')
            if name.isalpha():
                lemmas.append(name.lower())

    cluster = sorted(set(lemmas))
    if word.lower() not in cluster:
        return None

    return cluster if len(cluster) >= 2 else None

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

# -----------------------------
# AUTOMATIC COVER GENERATOR
# -----------------------------
SUBJECTS = ["The market", "Economic analysts", "Research teams", "Industry leaders", "Global investors", "Technology developers"]
VERBS = ["indicated", "reported", "stated", "observed", "confirmed", "suggested"]
OBJECTS = ["strong growth trends", "significant progress", "new strategic plans", "positive market feedback", "future expansion opportunities"]
EXTENSIONS = ["across all major sectors.", "in the recent quarter.", "according to published reports.", "with optimistic forecasts.", "despite minor fluctuations."]

def generate_cover_sentence():
    import random
    return f"{random.choice(SUBJECTS)} {random.choice(VERBS)} {random.choice(OBJECTS)} {random.choice(EXTENSIONS)}"

def generate_cover_paragraph(sentences_count=4):
    return " ".join(generate_cover_sentence() for _ in range(sentences_count))

def auto_expand_cover(cover_text: str, required_bits: int) -> str:
    tokens = simple_tokenize(cover_text)
    carriers = select_carriers(tokens)
    current_capacity = sum(bpw for _, _, _, bpw in carriers)

    expanded_text = cover_text
    while current_capacity < required_bits:
        new_para = "\n\n" + generate_cover_paragraph(5)
        expanded_text += new_para
        tokens = simple_tokenize(expanded_text)
        carriers = select_carriers(tokens)
        current_capacity = sum(bpw for _, _, _, bpw in carriers)

    return expanded_text

# -----------------------------
# METRICS & EVALUATION
# -----------------------------
def compute_bleu(original_text: str, encoded_text: str) -> float:
    try:
        smoothie = SmoothingFunction().method4
        reference = [original_text.split()]
        candidate = encoded_text.split()
        return round(sentence_bleu(reference, candidate, smoothing_function=smoothie), 4)
    except Exception:
        return 1.0

def shannon_entropy(bitstring: str) -> float:
    if not bitstring:
        return 0.0
    counts = Counter(bitstring)
    total = len(bitstring)
    entropy = 0.0
    for c in counts:
        p = counts[c] / total
        entropy -= p * math.log2(p)
    return round(entropy, 4)

def compute_metrics(cover_text: str, stego_text: str, carriers, secret_bits: str):
    total_words = len([t for t in simple_tokenize(cover_text) if t.isalpha()])
    total_carriers = len(carriers)
    total_capacity = sum(bpw for _, _, _, bpw in carriers)

    embedding_rate = round(len(secret_bits) / total_words, 4) if total_words else 0
    avg_bits_per_carrier = round(total_capacity / total_carriers, 4) if total_carriers else 0
    carrier_ratio = round(total_carriers / total_words, 4) if total_words else 0
    bleu_score = compute_bleu(cover_text, stego_text)
    entropy = shannon_entropy(secret_bits)

    return {
        "total_words": total_words,
        "total_carriers": total_carriers,
        "total_capacity_bits": total_capacity,
        "secret_bits_length": len(secret_bits),
        "embedding_rate_bits_per_word": embedding_rate,
        "avg_bits_per_carrier": avg_bits_per_carrier,
        "carrier_ratio": carrier_ratio,
        "bleu_score": bleu_score,
        "shannon_entropy": entropy
    }

# -----------------------------
# CORE ENCODE / DECODE ENGINE
# -----------------------------
class SemanticStegoEngine:

    @staticmethod
    def encode(cover_text: str, secret_text: str, password: str = None, auto_expand: True = True):
        if not secret_text:
            raise ValueError("Secret message cannot be empty.")

        # 1. Convert secret to bits (AES encrypted if password provided)
        if password:
            encrypted_bytes = aes_encrypt(secret_text, password)
            bits = bytes_to_bits(encrypted_bytes)
        else:
            bits = text_to_bits(secret_text)

        # 2. Check capacity & auto-expand cover if needed
        if auto_expand:
            cover_text = auto_expand_cover(cover_text, len(bits))

        tokens = simple_tokenize(cover_text)
        carriers = select_carriers(tokens)
        capacity = sum(bpw for _, _, _, bpw in carriers)

        if capacity < len(bits):
            raise ValueError(f"Cover text capacity ({capacity} bits) insufficient for secret ({len(bits)} bits).")

        # 3. Encode bits into carrier words
        bit_ptr = 0
        stego_tokens = tokens[:]
        used_positions = []
        modifications = []

        for idx, word, cluster, bpw in carriers:
            if bit_ptr >= len(bits):
                break

            chunk = bits[bit_ptr:bit_ptr+bpw].ljust(bpw, '0')
            sel = int(chunk, 2)
            sel = min(sel, len(cluster) - 1)
            chosen = cluster[sel]

            if word[0].isupper():
                chosen = chosen.capitalize()

            stego_tokens[idx] = chosen
            used_positions.append((idx, cluster, bpw))

            if word != chosen:
                modifications.append({
                    "position": idx,
                    "original": word,
                    "substituted": chosen,
                    "bits": chunk
                })

            bit_ptr += bpw

        stego_text = " ".join(stego_tokens)
        metrics = compute_metrics(cover_text, stego_text, carriers, bits)

        key_data = {
            "used_positions": used_positions,
            "secret_bit_len": len(bits),
            "is_encrypted": bool(password)
        }

        return {
            "stego_text": stego_text,
            "expanded_cover": cover_text,
            "key_data": key_data,
            "metrics": metrics,
            "modifications": modifications
        }

    @staticmethod
    def decode(stego_text: str, key_data: dict, password: str = None) -> str:
        used_positions = key_data.get("used_positions", [])
        secret_bit_len = key_data.get("secret_bit_len", 0)
        is_encrypted = key_data.get("is_encrypted", False)

        if is_encrypted and not password:
            raise ValueError("Password is required to decrypt this stego message.")

        tokens = simple_tokenize(stego_text)
        recovered_bits = ''

        for idx, cluster, bpw in used_positions:
            if len(recovered_bits) >= secret_bit_len:
                break
            if idx >= len(tokens):
                break

            word = tokens[idx].lower()
            if word not in cluster:
                continue

            sel = cluster.index(word)
            chunk = format(sel, f'0{bpw}b')
            recovered_bits += chunk

        recovered_bits = recovered_bits[:secret_bit_len]

        if is_encrypted:
            cipher_bytes = bits_to_bytes(recovered_bits)
            return aes_decrypt(cipher_bytes, password)
        else:
            return bits_to_text(recovered_bits)

# -----------------------------
# QUICK STANDALONE TEST
# -----------------------------
if __name__ == "__main__":
    cover = "The economy is showing signs of improvement as markets stabilize after weeks of turbulence."
    secret = "Top Secret Information 2026!"

    print("--- TESTING PLAIN ENCODING ---")
    res = SemanticStegoEngine.encode(cover, secret, auto_expand=True)
    print("Stego Text:", res["stego_text"])
    print("Metrics:", res["metrics"])

    decoded = SemanticStegoEngine.decode(res["stego_text"], res["key_data"])
    print("Decoded Secret:", decoded)
    assert decoded == secret, "Plain decode failed!"

    print("\n--- TESTING AES ENCRYPTED ENCODING ---")
    pwd = "MySecretPassword123"
    res_aes = SemanticStegoEngine.encode(cover, secret, password=pwd, auto_expand=True)
    decoded_aes = SemanticStegoEngine.decode(res_aes["stego_text"], res_aes["key_data"], password=pwd)
    print("Decoded AES Secret:", decoded_aes)
    assert decoded_aes == secret, "AES decode failed!"

    print("\n All standalone tests passed cleanly!")
