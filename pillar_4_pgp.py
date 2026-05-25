import re
import logging
import numpy as np
import pgpy
from typing import List, Set, Dict, Optional
from io import BytesIO

from utils import SimilarityMetrics, DataValidator


class PGPVerifier:
    """Verifies PGP key consistency using real cryptographic parsing."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.similarity_metrics = SimilarityMetrics()
    
    def parse_public_key(self, key_text: str) -> Optional[pgpy.PGPKey]:
        """Parse a PGP public key from text."""
        try:
            # Extract key block if surrounded by other text
            match = re.search(r'-----BEGIN PGP PUBLIC KEY BLOCK-----.*?-----END PGP PUBLIC KEY BLOCK-----', 
                             key_text, re.DOTALL)
            if match:
                key_text = match.group(0)
            
            key, _ = pgpy.PGPKey.from_blob(key_text)
            return key
        except Exception as e:
            self.logger.debug(f"Failed to parse PGP key: {e}")
            return None

    def get_key_features(self, key: pgpy.PGPKey) -> Dict:
        """Extract deep features from a PGP key."""
        features = {
            "fingerprint": str(key.fingerprint).replace(" ", ""),
            "creation": key.created,
            "algorithm": str(key.key_algorithm),
            "key_length": key.key_size,
            "is_expired": key.is_expired,
            "subkeys": [str(sk.fingerprint).replace(" ", "") for sk in key.subkeys],
            "uids": [str(uid) for uid in key.userids]
        }
        return features

    def extract_signature(self, keys_text: List[str]) -> 'PGPSignature':
        """Extract PGP signature from a list of key texts."""
        from signatures import PGPSignature
        sig = PGPSignature()
        
        sig.raw_keys = keys_text
        parsed_keys = []
        for t in keys_text:
            k = self.parse_public_key(t)
            if k:
                parsed_keys.append(k)
        
        if not parsed_keys:
            return sig
            
        sig.fingerprints = []
        for k in parsed_keys:
            if hasattr(k, 'fingerprint'):
                sig.fingerprints.append(str(k.fingerprint).replace(" ", ""))
            
        sig.creation_dates = [k.created.timestamp() for k in parsed_keys if hasattr(k, 'created')]
        sig.algorithms = [str(k.key_algorithm) for k in parsed_keys if hasattr(k, 'key_algorithm')]
        sig.key_sizes = [k.key_size for k in parsed_keys if hasattr(k, 'key_size')]
        
        for k in parsed_keys:
            if hasattr(k, 'subkeys') and k.subkeys:
                sig.subkeys.extend([str(sk.fingerprint).replace(" ", "") for sk in k.subkeys if hasattr(sk, 'fingerprint')])
            
            if hasattr(k, 'userids') and k.userids:
                sig.uids.extend([str(uid) for uid in k.userids])
            
        return sig

    def compute_features(self, sig1: 'PGPSignature', sig2: 'PGPSignature') -> np.ndarray:
        """Compute PGP features from two PGP signatures."""
        features = np.zeros(12)
        
        old_fps = set(sig1.fingerprints)
        new_fps = set(sig2.fingerprints)
        
        if not old_fps and not new_fps:
            return features

        # Feature 0: Primary Key Fingerprint Match (Exact)
        features[0] = 1.0 if old_fps & new_fps else 0.0

        # Feature 1: Subkey Overlap
        old_subkeys = set(sig1.subkeys)
        new_subkeys = set(sig2.subkeys)
        if old_subkeys and new_subkeys:
            features[1] = len(old_subkeys & new_subkeys) / max(len(old_subkeys), len(new_subkeys))

        # Feature 2: Jaccard Similarity of Primary Fingerprints
        features[2] = self.similarity_metrics.jaccard_similarity(old_fps, new_fps)

        # Feature 3: Algorithm Consistency
        old_algos = set(sig1.algorithms)
        new_algos = set(sig2.algorithms)
        features[3] = 1.0 if old_algos == new_algos else 0.5 if old_algos & new_algos else 0.0

        # Feature 4: Key Size Consistency
        old_sizes = set(sig1.key_sizes)
        new_sizes = set(sig2.key_sizes)
        features[4] = 1.0 if old_sizes == new_sizes else 0.0

        # Feature 5: Creation Date Similarity (Normalized)
        old_created = set(sig1.creation_dates)
        new_created = set(sig2.creation_dates)
        features[5] = 1.0 if old_created & new_created else 0.0

        # Feature 6: User ID Similarity
        old_uids = set(sig1.uids)
        new_uids = set(sig2.uids)
        features[6] = self.similarity_metrics.jaccard_similarity(old_uids, new_uids)

        # Feature 7: Key Expiry Consistency (Simplified as date presence check for now)
        # In a deep scan, we'd check actual expiry flags stored in signature if critical
        features[7] = 0.0 # Placeholder or requires expanding signature data

        # Feature 8: Primary Key count similarity
        features[8] = 1.0 - min(abs(len(old_fps) - len(new_fps)) / 5, 1.0)

        # Feature 9: Subkey count similarity
        old_sk_count = len(old_subkeys)
        new_sk_count = len(new_subkeys)
        if max(old_sk_count, new_sk_count) > 0:
            features[9] = min(old_sk_count, new_sk_count) / max(old_sk_count, new_sk_count)

        # Feature 10: Common Bit Strength
        features[10] = 1.0 if (4096 in old_sizes and 4096 in new_sizes) else 0.5 if (2048 in old_sizes and 2048 in new_sizes) else 0.0

        # Feature 11: Combined Cryptographic Trust Score
        features[11] = (features[0] * 0.4 + features[1] * 0.3 + features[5] * 0.2 + features[3] * 0.1)

        return np.clip(features, 0, 1)

    def calculate_similarity(self, sig1: 'PGPSignature', sig2: 'PGPSignature') -> float:
        """Calculate similarity score (0.0 to 1.0) between two PGP signatures."""
        
        # Case 1: Both have NO keys
        if not sig1.fingerprints and not sig2.fingerprints:
            return 0.0 # Neutral/Unknown. Don't claim they match just because both are empty.
            
        # Case 2: One has keys, one doesn't
        if not sig1.fingerprints or not sig2.fingerprints:
            return 0.0
            
        # Case 3: Key Matching
        # Primary Fingerprint Match (Strongest Signal)
        old_fps = set(sig1.fingerprints)
        new_fps = set(sig2.fingerprints)
        
        if old_fps & new_fps:
            return 1.0 # 100% Match if primary keys match
            
        # Subkey Match (Very Strong Signal)
        old_subs = set(sig1.subkeys)
        new_subs = set(sig2.subkeys)
        
        if old_subs & new_subs:
            return 0.95
            
        # Weak Signals (UIDs, etc)
        # Not implementing yet, strict crypto match is preferred for "Score"
        
        return 0.0

    def extract_features(self, old_keys_text: List[str], new_keys_text: List[str]) -> np.ndarray:
        """Legacy compatibility wrapper."""
        sig1 = self.extract_signature(old_keys_text)
        sig2 = self.extract_signature(new_keys_text)
        return self.compute_features(sig1, sig2)


def extract_pgp_features(old_keys_text: List[str], new_keys_text: List[str]) -> np.ndarray:
    """Convenience function to extract PGP features."""
    verifier = PGPVerifier()
    return verifier.extract_features(old_keys_text, new_keys_text)
