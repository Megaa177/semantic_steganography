from utils import tokenize_with_punct, is_safe_word

# ---------------- LOAD COVER TEXT ----------------
def load_cover(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ---------------- SECRET TO BITS ----------------
def text_to_bits(text):
    return "".join(f"{ord(c):08b}" for c in text)


# ---------------- ENCRYPT (PLAIN) ----------------
def encrypt_plain(cover_text, secret_text):
    tokens = tokenize_with_punct(cover_text)
    secret_bits = text_to_bits(secret_text)

    bit_idx = 0
    stego_tokens = []

    for tok in tokens:
        if bit_idx >= len(secret_bits):
            stego_tokens.append(tok)
            continue

        if is_safe_word(tok):
            bit = secret_bits[bit_idx]
            bit_idx += 1

            if bit == "1":
                stego_tokens.append(tok.capitalize())
            else:
                stego_tokens.append(tok.lower())
        else:
            stego_tokens.append(tok)

    if bit_idx < len(secret_bits):
        raise ValueError("Cover text too small to hide the secret.")

    return reconstruct_text(stego_tokens)


# ---------------- RECONSTRUCT TEXT ----------------
def reconstruct_text(tokens):
    text = ""
    for t in tokens:
        if re_match_punct(t):
            text += t
        else:
            if text and not text.endswith(" "):
                text += " "
            text += t
    return text


def re_match_punct(token):
    return len(token) == 1 and not token.isalnum()


# ---------------- MAIN ----------------
if __name__ == "__main__":
    cover = load_cover("data/cover_article.txt")

    secret = "HELLO"  # demo secret
    stego = encrypt_plain(cover, secret)

    with open("data/stego_plain.txt", "w", encoding="utf-8") as f:
        f.write(stego)

    print("[+] Plaintext steganography complete.")
