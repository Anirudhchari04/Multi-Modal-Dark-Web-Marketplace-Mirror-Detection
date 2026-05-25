"""
Pillar 5: Exception Handling Fingerprinting
Analyzes error responses to specific malformed requests
Extracts 16 features related to exception handling patterns
"""

import requests
import logging
import numpy as np
from typing import Dict, Tuple
import time

from config import HTTP_TIMEOUT
from utils import SimilarityMetrics, DataValidator


class ExceptionAnalyzer:
    """Analyzes exception handling and error fingerprints."""
    
    def __init__(self, timeout: int = HTTP_TIMEOUT):
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        self.similarity_metrics = SimilarityMetrics()
    
    def _test_exception(self, url: str, test_name: str, payload: str) -> Dict:
        """Test a specific exception condition."""
        result = {
            'status_code': 0,
            'response_time': 0,
            'response_text': '',
            'error_occurred': False
        }
        
        try:
            start_time = time.time()
            full_url = f"{url}?q={payload}" if '?' not in url else f"{url}&q={payload}"
            response = requests.get(full_url, timeout=self.timeout, verify=False)
            elapsed = time.time() - start_time
            
            result['status_code'] = response.status_code
            result['response_time'] = elapsed
            result['response_text'] = response.text[:500]
            result['error_occurred'] = response.status_code >= 400
            
        except requests.Timeout:
            result['status_code'] = 504  # Gateway Timeout
            result['response_time'] = self.timeout
            result['error_occurred'] = True
        except requests.ConnectionError:
            result['status_code'] = 503  # Service Unavailable
            result['response_time'] = self.timeout
            result['error_occurred'] = True
        except Exception as e:
            result['error_occurred'] = True
            self.logger.debug(f"Exception during test {test_name}: {e}")
        
        return result
    
    def test_empty_search(self, url: str) -> Dict:
        """Test with empty search query."""
        return self._test_exception(url, "empty_search", "")
    
    def test_sql_injection(self, url: str) -> Dict:
        """Test with SQL injection payload."""
        payload = "' OR '1'='1"
        return self._test_exception(url, "sql_injection", payload)
    
    def test_xss_payload(self, url: str) -> Dict:
        """Test with XSS payload."""
        payload = "<script>alert('xss')</script>"
        return self._test_exception(url, "xss", payload)
    
    def test_special_characters(self, url: str) -> Dict:
        """Test with special characters."""
        payload = "!@#$%^&*()"
        return self._test_exception(url, "special_chars", payload)
    
    def test_unicode_payload(self, url: str) -> Dict:
        """Test with Unicode characters."""
        payload = "测试中文字符"
        return self._test_exception(url, "unicode", payload)
    
    def test_extremely_long_input(self, url: str) -> Dict:
        """Test with extremely long input."""
        payload = "a" * 10000
        return self._test_exception(url, "long_input", payload)
    
    def test_null_bytes(self, url: str) -> Dict:
        """Test with null bytes."""
        payload = "test%00null"
        return self._test_exception(url, "null_bytes", payload)
    
    def extract_features(self, old_url: str, new_url: str) -> np.ndarray:
        """Extract 16 exception handling features."""
        features = np.zeros(16)
        
        try:
            # Run all exception tests on both URLs
            tests = [
                ("empty_search", lambda u: self.test_empty_search(u)),
                ("sql_injection", lambda u: self.test_sql_injection(u)),
                ("xss", lambda u: self.test_xss_payload(u)),
                ("special_chars", lambda u: self.test_special_characters(u)),
                ("unicode", lambda u: self.test_unicode_payload(u)),
                ("long_input", lambda u: self.test_extremely_long_input(u)),
                ("null_bytes", lambda u: self.test_null_bytes(u))
            ]
            
            old_results = {}
            new_results = {}
            
            for test_name, test_func in tests:
                try:
                    old_results[test_name] = test_func(old_url)
                    new_results[test_name] = test_func(new_url)
                except Exception as e:
                    self.logger.warning(f"Error in test {test_name}: {e}")
            
            # Feature 0-6: Response time similarity for each test
            for i, test_name in enumerate([t[0] for t in tests]):
                if test_name in old_results and test_name in new_results:
                    old_time = old_results[test_name].get('response_time', 0)
                    new_time = new_results[test_name].get('response_time', 0)
                    
                    max_time = max(old_time, new_time)
                    if max_time > 0:
                        features[i] = 1.0 - (abs(old_time - new_time) / max_time)
                    else:
                        features[i] = 1.0
            
            # Feature 7: Status code consistency
            old_status_codes = [r.get('status_code', 0) for r in old_results.values()]
            new_status_codes = [r.get('status_code', 0) for r in new_results.values()]
            
            if old_status_codes and new_status_codes:
                old_mode = max(set(old_status_codes), key=old_status_codes.count)
                new_mode = max(set(new_status_codes), key=new_status_codes.count)
                features[7] = 1.0 if old_mode == new_mode else abs(old_mode - new_mode) / 600
            
            # Feature 8: Error response consistency
            old_error_count = sum(1 for r in old_results.values() if r.get('error_occurred'))
            new_error_count = sum(1 for r in new_results.values() if r.get('error_occurred'))
            
            max_errors = max(len(old_results), len(new_results))
            if max_errors > 0:
                features[8] = 1.0 - (abs(old_error_count - new_error_count) / max_errors)
            
            # Feature 9: Response text similarity
            old_responses = " ".join([r.get('response_text', '') for r in old_results.values()])
            new_responses = " ".join([r.get('response_text', '') for r in new_results.values()])
            
            if old_responses and new_responses:
                similarity = self.similarity_metrics.normalized_similarity(old_responses[:1000], new_responses[:1000])
                features[9] = similarity
            
            # Feature 10: Stack trace presence
            old_stack_traces = sum(1 for r in old_results.values() if 'traceback' in r.get('response_text', '').lower())
            new_stack_traces = sum(1 for r in new_results.values() if 'traceback' in r.get('response_text', '').lower())
            features[10] = 1.0 - (abs(old_stack_traces - new_stack_traces) / len(old_results))
            
            # Feature 11: SQL error detection
            old_sql_errors = sum(1 for r in old_results.values() if any(e in r.get('response_text', '').lower() for e in ['sql', 'mysql', 'database']))
            new_sql_errors = sum(1 for r in new_results.values() if any(e in r.get('response_text', '').lower() for e in ['sql', 'mysql', 'database']))
            features[11] = 1.0 - (abs(old_sql_errors - new_sql_errors) / len(old_results))
            
            # Feature 12: Framework error detection
            old_framework_errors = sum(1 for r in old_results.values() if any(e in r.get('response_text', '').lower() for e in ['exception', 'error', 'fatal']))
            new_framework_errors = sum(1 for r in new_results.values() if any(e in r.get('response_text', '').lower() for e in ['exception', 'error', 'fatal']))
            features[12] = 1.0 - (abs(old_framework_errors - new_framework_errors) / len(old_results))
            
            # Feature 13: Custom error page detection
            old_custom = sum(1 for r in old_results.values() if r.get('status_code') != 200 and r.get('response_text'))
            new_custom = sum(1 for r in new_results.values() if r.get('status_code') != 200 and r.get('response_text'))
            features[13] = 1.0 - (abs(old_custom - new_custom) / len(old_results))
            
            # Feature 14: Timeout handling consistency
            old_timeouts = sum(1 for r in old_results.values() if r.get('response_time', 0) >= self.timeout * 0.95)
            new_timeouts = sum(1 for r in new_results.values() if r.get('response_time', 0) >= self.timeout * 0.95)
            features[14] = 1.0 - (abs(old_timeouts - new_timeouts) / len(old_results))
            
            # Feature 15: Overall fingerprint match
            features[15] = (features[7] + features[8] + features[9]) / 3
            
            # Normalize all features to 0-1 range
            features = np.clip(features, 0, 1)
            
        except Exception as e:
            self.logger.error(f"Error extracting exception features: {e}")
        
        return features


def extract_exception_features(old_url: str, new_url: str, timeout: int = HTTP_TIMEOUT) -> np.ndarray:
    """Convenience function to extract exception features."""
    analyzer = ExceptionAnalyzer(timeout=timeout)
    return analyzer.extract_features(old_url, new_url)
