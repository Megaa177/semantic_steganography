from stego_engine import SemanticStegoEngine, aes_encrypt, aes_decrypt
from app import encode_message, decode_message, generate_cover, health_check, EncodeRequest, DecodeRequest, GenerateCoverRequest

def test_aes_encrypt_decrypt():
    print("Testing AES Encryption/Decryption...")
    msg = "Secret 123 Passphrase Test"
    pwd = "MySecretPassword"
    encrypted = aes_encrypt(msg, pwd)
    decrypted = aes_decrypt(encrypted, pwd)
    assert decrypted == msg, "AES Encryption/Decryption roundtrip failed."
    print("[OK] PASSED: AES Encryption/Decryption")

def test_stego_plain_roundtrip():
    print("Testing Plain Stego Roundtrip...")
    cover = "The government confirmed future expansion opportunities across all major sectors."
    secret = "HELLO WORLD"
    res = SemanticStegoEngine.encode(cover, secret, auto_expand=True)
    
    assert "stego_text" in res
    assert "key_data" in res
    assert res["metrics"]["bleu_score"] >= 0.0

    decoded = SemanticStegoEngine.decode(res["stego_text"], res["key_data"])
    assert decoded == secret, "Plain steganography decode failed."
    print("[OK] PASSED: Plain Stego Roundtrip")

def test_stego_aes_roundtrip():
    print("Testing AES Encrypted Stego Roundtrip...")
    cover = "The government confirmed future expansion opportunities across all major sectors."
    secret = "CONFIDENTIAL DATA 2026"
    pwd = "SecurePassphrase!"
    res = SemanticStegoEngine.encode(cover, secret, password=pwd, auto_expand=True)
    
    decoded = SemanticStegoEngine.decode(res["stego_text"], res["key_data"], password=pwd)
    assert decoded == secret, "AES encrypted steganography decode failed."
    print("[OK] PASSED: AES Encrypted Stego Roundtrip")

def test_auto_expansion():
    print("Testing Auto-Expansion for Large Inputs...")
    short_cover = "The market reported growth."
    long_secret = "This is a very long secret payload message that will definitely exceed the capacity of a short 4-word cover sentence. The auto-expansion feature must add additional paragraphs to handle this large input!"
    
    res = SemanticStegoEngine.encode(short_cover, long_secret, auto_expand=True)
    assert res["metrics"]["secret_bits_length"] <= res["metrics"]["total_capacity_bits"]
    
    decoded = SemanticStegoEngine.decode(res["stego_text"], res["key_data"])
    assert decoded == long_secret, "Auto-expanded steganography decode failed."
    print("[OK] PASSED: Auto-Expansion for Large Inputs")

def test_api_endpoints():
    print("Testing API Route Handlers...")
    # Health check
    res = health_check()
    assert res["status"] == "ok"

    # Generate cover
    res_cov = generate_cover(GenerateCoverRequest(paragraphs_count=2))
    assert res_cov["success"] is True
    assert "cover_text" in res_cov

    # Encode API
    enc_req = EncodeRequest(
        secret_text="API Test Message",
        cover_text=res_cov["cover_text"],
        password="TestPassword",
        auto_expand=True
    )
    res_enc = encode_message(enc_req)
    assert res_enc["success"] is True

    # Decode API
    dec_req = DecodeRequest(
        stego_text=res_enc["stego_text"],
        key_data=res_enc["key_data"],
        password="TestPassword"
    )
    res_dec = decode_message(dec_req)
    assert res_dec["success"] is True
    assert res_dec["secret_text"] == "API Test Message"
    print("[OK] PASSED: API Route Handlers")

if __name__ == "__main__":
    test_aes_encrypt_decrypt()
    test_stego_plain_roundtrip()
    test_stego_aes_roundtrip()
    test_auto_expansion()
    test_api_endpoints()
    print("\nALL 5 TEST SUITES PASSED CLEANLY!")
