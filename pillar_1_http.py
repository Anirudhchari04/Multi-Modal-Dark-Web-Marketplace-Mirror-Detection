"""
Pillar 1: HTTP Response Fingerprinting
Analyzes HTTP response patterns through multiple identical requests
Extracts 12 features related to response consistency and timing
"""

import requests
import numpy as np
import logging
from typing import Tuple
import time

from config import HTTP_TIMEOUT, HTTP_QUERIES_COUNT, USE_TOR, PROXIES
from utils import ResponseAnalyzer, DataValidator


class HTTPResponseFingerprinter:
    """Fingerprints marketplace HTTP responses."""
    
    def __init__(self, timeout: int = HTTP_TIMEOUT):
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
    
    def _prepare_session(self, url: str):
        """Configure session for Tor if needed."""
        if USE_TOR and (".onion" in url or "check.torproject.org" in url):
            self.session.proxies.update(PROXIES)
            self.logger.debug(f"Using Tor proxy for {url}")
        else:
            self.session.proxies = {}

    def send_identical_queries(self, url: str, count: int = HTTP_QUERIES_COUNT) -> Tuple[list, list]:
        """Send identical queries to URL and collect responses."""
        timings = []
        responses = []
        
        if not DataValidator.is_valid_url(url):
            self.logger.error(f"Invalid URL: {url}")
            return responses, timings
        
        self._prepare_session(url)
        
        for i in range(count):
            try:
                start_time = time.time()
                response = self.session.get(
                    url,
                    timeout=self.timeout,
                    allow_redirects=True,
                    verify=False
                )
                elapsed = time.time() - start_time
                timings.append(elapsed)
                responses.append(response)
            except requests.Timeout:
                self.logger.warning(f"Timeout on query {i+1} to {url}")
                timings.append(self.timeout)
            except requests.ConnectionError:
                self.logger.warning(f"Connection error on query {i+1} to {url}")
                timings.append(self.timeout)
            except Exception as e:
                self.logger.warning(f"Error on query {i+1}: {e}")
                timings.append(self.timeout)
        
        return responses, timings
    
    def extract_signature(self, url: str) -> 'HTTPSignature':
        """Extract HTTP signature from a URL."""
        from signatures import HTTPSignature
        
        responses, timings = self.send_identical_queries(url)
        sig = HTTPSignature()
        
        if not timings:
            return sig
            
        # Timing Stats
        sig.response_time_mean = float(np.mean(timings))
        sig.response_time_std = float(np.std(timings)) if len(timings) > 1 else 0.0
        sig.response_time_p95 = float(np.percentile(timings, 95))
        sig.response_time_p99 = float(np.percentile(timings, 99))
        
        # Status Codes
        status_codes = [r.status_code for r in responses if r]
        if status_codes:
            sig.status_code_mode = max(set(status_codes), key=status_codes.count)
            sig.status_code_variance = float(np.var(status_codes))
            sig.error_rate = sum(1 for s in status_codes if s >= 500) / len(status_codes)
        
        # Headers
        servers = [ResponseAnalyzer.extract_server_header(r) for r in responses if r]
        if servers:
            sig.server_header = servers[0] # Take the first one as representative
            sig.consistent_server_header = (sum(1 for s in servers if s == servers[0]) / len(servers)) > 0.9

        xpbs = [ResponseAnalyzer.extract_x_powered_by(r) for r in responses if r]
        if xpbs:
            sig.x_powered_by = xpbs[0]
            sig.consistent_x_powered_by = (sum(1 for x in xpbs if x == xpbs[0]) / len(xpbs)) > 0.9
            
        # Timeouts
        sig.timeout_rate = sum(1 for t in timings if t >= self.timeout * 0.95) / len(timings)
        
        return sig

    def compute_features(self, sig1: 'HTTPSignature', sig2: 'HTTPSignature') -> np.ndarray:
        """Compute features from two HTTP signatures."""
        features = np.zeros(12)
        
        # Feature 0-3: Timing Stats (using sig1 as reference "old" site)
        features[0] = sig1.response_time_mean
        features[1] = sig1.response_time_std
        features[2] = sig1.response_time_p95
        features[3] = sig1.response_time_p99
        
        # Feature 4: Status Code Mode Similarity
        if sig1.status_code_mode == sig2.status_code_mode:
            features[4] = 1.0
        else:
            features[4] = abs(sig1.status_code_mode - sig2.status_code_mode) / 600
            
        # Feature 5: Status Variance
        features[5] = sig1.status_code_variance / 10000
        
        # Feature 6: Server Header Consistency (sig1)
        features[6] = 1.0 if sig1.consistent_server_header else 0.0
        
        # Feature 7: XPB Presence
        features[7] = 1.0 if sig1.x_powered_by else 0.0
        
        # Feature 8: XPB Consistency
        features[8] = 1.0 if sig1.consistent_x_powered_by else 0.0
        
        # Feature 9: Error Rate
        features[9] = sig1.error_rate
        
        # Feature 10: Timeout Rate
        features[10] = sig1.timeout_rate
        
        # Feature 11: Timing Stability (CoV)
        if sig1.response_time_mean > 0:
            features[11] = sig1.response_time_std / sig1.response_time_mean
        
        return np.clip(features, 0, 1)

    def calculate_similarity(self, sig1: 'HTTPSignature', sig2: 'HTTPSignature') -> float:
        """Calculate a similarity score (0.0 to 1.0) between two HTTP signatures."""
        score = 0.0
        weights = {
            'status': 0.4,
            'headers': 0.3,
            'timing': 0.3
        }
        
        # 1. Status Code Logic (Critical)
        if sig1.status_code_mode == sig2.status_code_mode:
            status_sim = 1.0
        elif abs(sig1.status_code_mode - sig2.status_code_mode) < 100: # Same class (2xx)
            status_sim = 0.5
        else:
            status_sim = 0.0
        score += status_sim * weights['status']
        
        # 2. Header Logic
        header_sim = 0.0
        checks = 0
        if sig1.server_header or sig2.server_header:
            header_sim += 1.0 if sig1.server_header == sig2.server_header else 0.0
            checks += 1
        if sig1.x_powered_by or sig2.x_powered_by:
            header_sim += 1.0 if sig1.x_powered_by == sig2.x_powered_by else 0.0
            checks += 1
            
        if checks > 0:
            score += (header_sim / checks) * weights['headers']
        else:
            # If no headers to check, assume match (weak signal) or redistribute weight?
            # Let's assume neutral (0.5) to avoid penalizing empty headers too much
            score += 0.5 * weights['headers']

        # 3. Timing Logic (Soft Match)
        # We compare mean response times. darknet times fluctuate wildly.
        # If within 30% of each other, full points.
        t1 = sig1.response_time_mean
        t2 = sig2.response_time_mean
        if t1 > 0 and t2 > 0:
            diff_ratio = abs(t1 - t2) / ((t1 + t2) / 2)
            timing_sim = max(0.0, 1.0 - diff_ratio) # 1.0 diff = 0 score
            score += timing_sim * weights['timing']
        
        return score

    def extract_features(self, old_url: str, new_url: str) -> np.ndarray:
        """Legacy compatibility wrapper."""
        sig1 = self.extract_signature(old_url)
        sig2 = self.extract_signature(new_url)
        return self.compute_features(sig1, sig2)


def extract_http_features(old_url: str, new_url: str, timeout: int = HTTP_TIMEOUT) -> np.ndarray:
    """Convenience function to extract HTTP features."""
    fingerprinter = HTTPResponseFingerprinter(timeout=timeout)
    return fingerprinter.extract_features(old_url, new_url)
