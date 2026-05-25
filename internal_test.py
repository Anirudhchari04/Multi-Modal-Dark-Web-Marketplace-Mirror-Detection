import numpy as np
import pgpy
from pgpy.constants import PubKeyAlgorithm, HashAlgorithm, CompressionAlgorithm, SymmetricKeyAlgorithm
from pillar_4_pgp import PGPVerifier, extract_pgp_features
from pillar_1_http import HTTPResponseFingerprinter
import logging
import time

def generate_test_key(name="Tester"):
    """Generate a real PGP key for testing."""
    key = pgpy.PGPKey.new(PubKeyAlgorithm.RSAEncryptOrSign, 2048)
    uid = pgpy.PGPUID.new(name, email=f"{name.lower()}@example.com")
    key.add_uid(uid, 
                usage={pgpy.constants.KeyFlags.Sign, pgpy.constants.KeyFlags.EncryptCommunications},
                hashes=[HashAlgorithm.SHA256],
                ciphers=[SymmetricKeyAlgorithm.AES256],
                compression=[CompressionAlgorithm.ZLIB])
    return key

def test_pgp_cryptographic_verification():
    print("--- Testing PGP Cryptographic Verification ---")
    verifier = PGPVerifier()
    
    # generate two identical-ish keys (same identity, different keys)
    key_a = generate_test_key("MarketAdmin")
    print(f"Key Attributes: {dir(key_a)}")
    key_b = generate_test_key("MarketAdmin") 
    
    # 1. Test Exact Match
    text_a = str(key_a)
    features_exact = verifier.extract_features([text_a], [text_a])
    print(f"Exact Match Feature[0]: {features_exact[0]} (Expected 1.0)")
    
    # 2. Test Different Keys (same UID)
    features_diff = verifier.extract_features([str(key_a)], [str(key_b)])
    print(f"Different Keys (Same UID) Feature[6]: {features_diff[6]:.2f} (Expected > 0)")
    print(f"Different Keys Feature[0]: {features_diff[0]} (Expected 0.0)")
    
    # 3. Test Combined Trust Score
    print(f"Combined Trust Score (Exact): {features_exact[11]:.2f}")
    print(f"Combined Trust Score (Diff): {features_diff[11]:.2f}")

def test_http_fingerprinter_logic():
    print("\n--- Testing HTTP Fingerprinter Logic (Local) ---")
    # We test the session preparation logic
    fingerprinter = HTTPResponseFingerprinter()
    
    # Test Tor detection
    from config import USE_TOR, TOR_SOCKS_URL
    print(f"USE_TOR setting: {USE_TOR}")
    
    # Mock prepare_session call
    fingerprinter._prepare_session("http://vww6ybal4bd7szmgncyruucpgfkqahzddi37ktce3ahv66lyksre.onion")
    if fingerprinter.session.proxies.get('http') == TOR_SOCKS_URL:
        print("✅ Tor proxy correctly assigned for .onion URL")
    else:
        print("❌ Tor proxy NOT assigned for .onion URL")

    fingerprinter._prepare_session("http://google.com")
    if not fingerprinter.session.proxies:
        print("✅ No proxy assigned for non-onion URL")
    else:
        print("❌ Proxy INCORRECTLY assigned for non-onion URL")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        test_pgp_cryptographic_verification()
        test_http_fingerprinter_logic()
        print("\n✅ Internal Logic Verification Complete!")
    except Exception as e:
        print(f"\n❌ Test Suite Failed: {e}")
        import traceback
        traceback.print_exc()
