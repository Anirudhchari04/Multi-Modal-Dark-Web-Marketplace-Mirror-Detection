import requests
import logging
import json
import os
from typing import Dict, List, Optional
from urllib.parse import urlparse
import time

from config import PROXIES, USE_TOR, HTTP_TIMEOUT, LOG_LEVEL
from utils import LoggingSetup

class DarknetIntelligenceCollector:
    """Collects raw intelligence from darknet marketplaces."""
    
    def __init__(self, output_dir: str = "intelligence"):
        self.logger = LoggingSetup.setup_logging("intel_collector", LOG_LEVEL)
        self.output_dir = output_dir
        self.session = requests.Session()
        if USE_TOR:
            self.session.proxies.update(PROXIES)
        
        os.makedirs(output_dir, exist_ok=True)

    def ingest_url(self, url: str, label: Optional[str] = None) -> Optional[str]:
        """Scan a URL, generate a signature, and save it to the DB."""
        from signatures import SiteSignature, HTMLSignature, PGPSignature
        from pillar_1_http import HTTPResponseFingerprinter
        from pillar_4_pgp import PGPVerifier
        from storage import FeatureStore
        from utils import URLCrawler
        
        try:
            self.logger.info(f"Ingesting signature for {url}...")
            
            # 1. HTTP Fingerprint
            http_fp = HTTPResponseFingerprinter()
            http_sig = http_fp.extract_signature(url)
            
            # 2. Get Page Content for HTML & PGP
            # We reuse the session from http_fp or make a new request
            # For simplicity, let's grab the content again or use what we can
            # Ideally, pillar 1 should give us the content, but it does multiple requests.
            # Let's do a single request for content analysis.
            response = self.session.get(url, timeout=HTTP_TIMEOUT, verify=False)
            html_content = response.text
            
            # 3. PGP Fingerprint
            try:
                # Extract PGP blocks from HTML
                import re
                pgp_pattern = r'-----BEGIN PGP PUBLIC KEY BLOCK-----.*?-----END PGP PUBLIC KEY BLOCK-----'
                key_blocks = re.findall(pgp_pattern, html_content, re.DOTALL)
                
                # SMART PGP HUNT: If no keys found, try common paths
                if not key_blocks:
                    self.logger.info("No PGP keys on index. Hunting common paths...")
                    common_paths = ["/pgp.txt", "/key.txt", "/security.txt", "/pgp", "/public_key"]
                    from urllib.parse import urljoin
                    
                    for path in common_paths:
                        try:
                            hunt_url = urljoin(url, path)
                            self.logger.debug(f"Checking {hunt_url}...")
                            hunt_resp = self.session.get(hunt_url, timeout=5, verify=False)
                            if hunt_resp.status_code == 200:
                                found_blocks = re.findall(pgp_pattern, hunt_resp.text, re.DOTALL)
                                if found_blocks:
                                    self.logger.info(f"✅ Found PGP key at {path}")
                                    key_blocks.extend(found_blocks)
                                    break
                        except:
                            pass
                
                pgp_verifier = PGPVerifier()
                pgp_sig = pgp_verifier.extract_signature(key_blocks)
            except Exception as e:
                self.logger.warning(f"PGP Extraction Failed (Non-Fatal): {e}")
                pgp_sig = PGPSignature() # Continue with empty PGP sig
            
            # 4. HTML Fingerprint (Placeholder for full implementation)
            html_sig = HTMLSignature()
            html_sig.dom_depth = 0 # Implement real DOM analysis later
            
            # 5. Construct Site Signature
            site_sig = SiteSignature(
                url=url,
                label=label,
                http=http_sig,
                pgp=pgp_sig,
                html=html_sig
            )
            
            # 6. Save to Store
            store = FeatureStore()
            store.add_signature(site_sig)
            
            self.logger.info(f"Successfully ingested {url}" + (f" as '{label}'" if label else ""))
            return url
            
        except Exception as e:
            self.logger.error(f"Failed to ingest {url}: {e}")
            return None

if __name__ == "__main__":
    collector = DarknetIntelligenceCollector()
    # collector.ingest_url("http://target-onion-url.onion", label="MyMarket")
