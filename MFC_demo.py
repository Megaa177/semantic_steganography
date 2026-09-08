import re
from math import log2, floor

# -----------------------------
# TOKENIZER
# -----------------------------
def simple_tokenize(text):
    return re.findall(r'\w+|[^\w\s]', text)

# -----------------------------
# SECRET → BITSTREAM
# -----------------------------
def secret_to_bits(secret):
    bits = ''.join(format(ord(c), '08b') for c in secret)  # 8 bits per char
    return bits

def bits_to_secret(bits):
    secret = ''
    for i in range(0, len(bits), 8):
        chunk = bits[i:i+8]
        if len(chunk) < 8:
            break
        secret += chr(int(chunk, 2))
    return secret

# -----------------------------
# CUSTOM SYNONYM DICTIONARY
# -----------------------------
custom_syns = {
    'boy': ['boy', 'kid', 'child', 'lad'],
    'said': ['said', 'stated', 'remarked', 'noted'],
    'happy': ['happy', 'glad', 'joyful', 'pleased'],
    'economy': ['economy','market','trade','commerce'],
    'improvement': ['improvement','growth','progress','advance','development'],
    'markets': ['markets','exchanges','bazaars','trading'],
    'confidence': ['confidence','trust','faith','assurance'],
    'investors': ['investors','backers','financiers','supporters'],
    'optimistic': ['optimistic','hopeful','cheerful','upbeat'],
    'companies': ['companies','firms','businesses','enterprises'],
    'plan': ['plan','prepare','schedule','organize'],
    'future': ['future','coming','forthcoming','upcoming'],
    'expansions': ['expansions','growths','extensions','developments'],
}

# -----------------------------
# HELPER: bits per word
# -----------------------------
def bits_per_word(cluster_size):
    return floor(log2(cluster_size)) if cluster_size >= 2 else 0

# -----------------------------
# ENCODE TEXT
# -----------------------------
def encode_text(cover_text, secret):
    bits = secret_to_bits(secret)
    bit_ptr = 0
    tokens = simple_tokenize(cover_text)
    output = []
    changed_positions = []

    print("\n--- ENCODING TRACE ---")
    for i, word in enumerate(tokens):
        lw = word.lower()
        cluster = custom_syns.get(lw, [word])
        bpw = bits_per_word(len(cluster))
        if bpw > 0 and bit_ptr < len(bits):
            chunk = bits[bit_ptr:bit_ptr+bpw]
            if len(chunk) < bpw:
                chunk = chunk.ljust(bpw, '0')
            idx = int(chunk, 2)
            idx = min(idx, len(cluster)-1)
            chosen = cluster[idx]
            if word[0].isupper():
                chosen = chosen.capitalize()
            output.append(chosen)
            changed_positions.append(i)
            print(f"Word: '{word}' -> '{chosen}' | Bits stored: {chunk} | Position: {i}")
            bit_ptr += bpw
            continue
        output.append(word)

    if bit_ptr < len(bits):
        print("\nWARNING: Secret too long for cover text!")
    return ' '.join(output), changed_positions

# -----------------------------
# DECODE TEXT
# -----------------------------
def decode_text(encoded_text, changed_positions):
    tokens = simple_tokenize(encoded_text)
    recovered_bits = ''

    print("\n--- DECODING TRACE ---")
    for i in changed_positions:
        word = tokens[i]
        lw = word.lower()
        cluster = None
        for key, cl in custom_syns.items():
            if lw in [w.lower() for w in cl]:
                cluster = cl
                break
        if not cluster:
            print(f"Word: '{word}' | Not found in any cluster!")
            continue
        idx = [w.lower() for w in cluster].index(lw)
        bpw = bits_per_word(len(cluster))
        chunk = format(idx, f'0{bpw}b')
        recovered_bits += chunk
        print(f"Word: '{word}' | Index: {idx} | Bits recovered: {chunk} | Position: {i}")

    return bits_to_secret(recovered_bits)

# -----------------------------
# DEMO
# -----------------------------
if __name__ == "__main__":
    cover = ("The economy is showing signs of improvement as markets stabilize after weeks of turbulence. "
             "Investors remain optimistic while companies plan future expansions. "
             "The boy said he was happy.")

    secret = "DOG"

    print("\nCOVER TEXT:\n", cover)
    encoded, changed_positions = encode_text(cover, secret)
    print("\nENCODED TEXT:\n", encoded)
    decoded = decode_text(encoded, changed_positions)
    print("\nDECODED SECRET:\n", decoded)

    if decoded == secret:
        print("\n Secret successfully recovered!")
    else:
        print("\n Secret not recovered!")
