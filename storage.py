import json
import os
from typing import List, Dict, Optional
from signatures import SiteSignature
import logging

class FeatureStore:
    """Persists site fingerprints to a local database."""
    
    def __init__(self, db_path: str = "fingerprints.json"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._load_db()
        
    def _load_db(self):
        """Load the database from disk."""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r") as f:
                    self.data = json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load DB: {e}")
                self.data = []
        else:
            self.data = []
            
    def save_db(self):
        """Save the database to disk."""
        try:
            with open(self.db_path, "w") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save DB: {e}")
            
    def add_signature(self, signature: SiteSignature):
        """Add or update a site signature."""
        # Check if URL already exists, update if so
        for i, entry in enumerate(self.data):
            if entry['url'] == signature.url:
                self.data[i] = signature.to_dict()
                self.save_db()
                self.logger.info(f"Updated signature for {signature.url}")
                return
        
        self.data.append(signature.to_dict())
        self.save_db()
        self.logger.info(f"Added signature for {signature.url}")
        
    def get_all_signatures(self) -> List[SiteSignature]:
        """Retrieve all stored signatures."""
        return [SiteSignature.from_dict(d) for d in self.data]
        
    def find_matches(self, probe_sig: SiteSignature, threshold: float = 0.8) -> List[Dict]:
        """Find matching sites in the database."""
        matches = []
        # Import comparisons here to avoid circular imports if pillars import storage
        from pillar_1_http import HTTPResponseFingerprinter
        from pillar_4_pgp import PGPVerifier
        
        http_verifier = HTTPResponseFingerprinter()
        pgp_verifier = PGPVerifier()
        
        for stored_sig in self.get_all_signatures():
            score = 0
            details = {}
            
            # HTTP Score
            http_score = http_verifier.calculate_similarity(stored_sig.http, probe_sig.http)
            details['http_score'] = http_score
            
            # PGP Score
            pgp_score = pgp_verifier.calculate_similarity(stored_sig.pgp, probe_sig.pgp)
            details['pgp_score'] = pgp_score
            
            # Weighted Total
            # If PGP match is strong (1.0), it overrides everything (Trust Score)
            if pgp_score > 0.9:
                total_score = 1.0
            else:
                # Otherwise, mix HTTP (0.6) and PGP (0.4)
                # If PGP is 0 (missing), we rely on HTTP/HTML
                weight_http = 0.6 if pgp_score == 0 else 0.4
                weight_pgp = 0.4 if pgp_score > 0 else 0.0
                
                # Normalize weights
                total_weight = weight_http + weight_pgp
                if total_weight > 0:
                    total_score = (http_score * weight_http + pgp_score * weight_pgp) / total_weight
                else:
                    total_score = 0.0
            
            if total_score >= threshold:
                matches.append({
                    "site": stored_sig.to_dict(),
                    "score": total_score,
                    "details": details
                })
                
        matches.sort(key=lambda x: x['score'], reverse=True)
        return matches
