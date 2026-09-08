import re
import json
import math
from math import log2, floor
from collections import Counter as PyCounter
from nltk.corpus import wordnet as wn
from nltk import pos_tag
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from Crypto.Cipher import AES
from Crypto.Util import Counter



# AES SETTINGS

AES_KEY = b'0123456789abcdef'     # 16 bytes = AES-128
AES_NONCE = b'abcdef9876543210'   # 16 bytes fixed nonce


def aes_encrypt(plaintext):
    ctr = Counter.new(128, initial_value=int.from_bytes(AES_NONCE, byteorder='big'))
    cipher = AES.new(AES_KEY, AES.MODE_CTR, counter=ctr)
    return cipher.encrypt(plaintext.encode())


def aes_decrypt(cipher_bytes):
    ctr = Counter.new(128, initial_value=int.from_bytes(AES_NONCE, byteorder='big'))
    cipher = AES.new(AES_KEY, AES.MODE_CTR, counter=ctr)
    return cipher.decrypt(cipher_bytes).decode()



# TOKENIZER


def simple_tokenize(text):
    return re.findall(r'\w+|[^\w\s]', text)



# BIT CONVERSION

def bytes_to_bits(byte_data):
    return ''.join(format(b, '08b') for b in byte_data)


def bits_to_bytes(bits):
    return bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))


# ENTROPY CALCULATION

def calculate_entropy(byte_data):
    if not byte_data:
        return 0.0

    freq = PyCounter(byte_data)
    total = len(byte_data)

    entropy = 0
    for count in freq.values():
        p = count / total
        entropy -= p * math.log2(p)

    return entropy  # max = 8 for ideal AES



# POS MAP

def wn_pos(treebank_tag):
    if treebank_tag.startswith('N'):
        return wn.NOUN
    if treebank_tag.startswith('J'):
        return wn.ADJ
    return None


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

    cluster = sorted(set(lemmas))

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
    encrypted_bytes = aes_encrypt(secret)
    bits = bytes_to_bits(encrypted_bytes)

    tokens = simple_tokenize(cover_text)
    carriers = select_carriers(tokens)

    capacity = sum(bpw for _, _, _, bpw in carriers)

    print("\n--- CAPACITY METRICS ---")
    print("Total words:", len(tokens))
    print("Total carriers:", len(carriers))
    print("Total capacity (bits):", capacity)
    print("Secret size (bits):", len(bits))
    print("Embedding rate (bits/word):", capacity / len(tokens))

    if capacity < len(bits):
        raise ValueError("Not enough capacity.")

    bit_ptr = 0
    out = tokens[:]
    used_positions = []

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

        bit_ptr += bpw

    return ' '.join(out), used_positions, len(bits), encrypted_bytes


# DECODE

def decode_text(encoded_text, used_positions, secret_bit_len):
    tokens = simple_tokenize(encoded_text)
    recovered_bits = ''

    for idx, cluster, bpw in used_positions:
        if len(recovered_bits) >= secret_bit_len:
            break

        word = tokens[idx].lower()

        if word not in cluster:
            continue

        sel = cluster.index(word)
        chunk = format(sel, f'0{bpw}b')
        recovered_bits += chunk

    cipher_bytes = bits_to_bytes(recovered_bits[:secret_bit_len])
    return aes_decrypt(cipher_bytes)



# BLEU

def compute_bleu(original_text, encoded_text):
    smoothie = SmoothingFunction().method4
    reference = [original_text.split()]
    candidate = encoded_text.split()
    return sentence_bleu(reference, candidate, smoothing_function=smoothie)



# MAIN

if __name__ == "__main__":

    with open("c_article.txt", "r", encoding="utf-8") as f:
        cover = f.read()

    secret = "MFC"

    print("\n--- ENCODING ---")
    encoded, used_positions, bit_len, cipher_bytes = encode_text(cover, secret)
    print("\n--- AES ENCRYPTION OUTPUT ---")
    
    print("Ciphertext (raw bytes):")
    print(cipher_bytes)
    
    print("\nCiphertext (hex representation):")
    print(cipher_bytes.hex())
    
    print("\nCiphertext (bitstream):")
    print(bytes_to_bits(cipher_bytes))

    with open("encoded_aes.txt", "w", encoding="utf-8") as f:
        f.write(encoded)

    with open("key_positions_aes.json", "w", encoding="utf-8") as f:
        json.dump(used_positions, f)

    print("\n--- DECODING ---")
    with open("key_positions_aes.json", "r", encoding="utf-8") as f:
        used_positions = json.load(f)

    decoded = decode_text(encoded, used_positions, bit_len)

    print("\nDECODED SECRET:", decoded)

    if decoded == secret:
        print("Secret successfully recovered!")
    else:
        print("Secret recovery failed!")

    bleu = compute_bleu(cover, encoded)
    print("BLEU Score:", bleu)

    entropy = calculate_entropy(cipher_bytes)
    print("Ciphertext Entropy:", entropy, "(max ideal = 8)")