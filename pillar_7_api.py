"""
Pillar 7: API Endpoint Analysis
Analyzes API endpoints and their patterns
Extracts 12 features related to API similarity
"""

import requests
import re
import logging
import numpy as np
from typing import List, Set, Dict
from urllib.parse import urljoin

from config import HTTP_TIMEOUT
from utils import URLCrawler, SimilarityMetrics, DataValidator


class APIEndpointAnalyzer:
    """Analyzes API endpoints across marketplaces."""
    
    def __init__(self, timeout: int = HTTP_TIMEOUT):
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        self.url_crawler = URLCrawler(timeout=timeout)
        self.similarity_metrics = SimilarityMetrics()
    
    def extract_endpoints_from_html(self, html_content: str, base_url: str) -> Set[str]:
        """Extract API endpoints from HTML and JavaScript."""
        endpoints = set()
        
        try:
            # Extract from fetch() calls
            fetch_pattern = r"fetch\(['\"]([^'\"]+)['\"]"
            for match in re.finditer(fetch_pattern, html_content):
                url = match.group(1)
                if url.startswith('/'):
                    url = urljoin(base_url, url)
                endpoints.add(url)
            
            # Extract from XMLHttpRequest
            xhr_pattern = r"XMLHttpRequest\(\).*?open\(['\"](?:GET|POST)['\"],\s*['\"]([^'\"]+)['\"]"
            for match in re.finditer(xhr_pattern, html_content, re.DOTALL):
                url = match.group(1)
                if url.startswith('/'):
                    url = urljoin(base_url, url)
                endpoints.add(url)
            
            # Extract /api/ paths
            api_pattern = r'/api/[a-zA-Z0-9/_\-\.]+'
            for match in re.finditer(api_pattern, html_content):
                endpoints.add(match.group(0))
            
        except Exception as e:
            self.logger.warning(f"Error extracting endpoints from HTML: {e}")
        
        return endpoints
    
    def extract_api_parameters(self, endpoint: str) -> Dict[str, str]:
        """Extract parameters from API endpoint."""
        try:
            params = {}
            # Match query parameters
            if '?' in endpoint:
                query_part = endpoint.split('?')[1]
                for param in query_part.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        params[key] = value
            return params
        except Exception:
            return {}
    
    def test_endpoint(self, endpoint: str) -> Dict:
        """Test an API endpoint and collect response information."""
        result = {
            'accessible': False,
            'status_code': 0,
            'response_time': 0,
            'response_format': 'unknown'
        }
        
        try:
            import time
            start_time = time.time()
            response = requests.get(endpoint, timeout=self.timeout, verify=False)
            elapsed = time.time() - start_time
            
            result['status_code'] = response.status_code
            result['response_time'] = elapsed
            result['accessible'] = response.status_code < 400
            
            # Detect response format
            content_type = response.headers.get('Content-Type', '').lower()
            if 'json' in content_type:
                result['response_format'] = 'json'
            elif 'xml' in content_type:
                result['response_format'] = 'xml'
            elif 'html' in content_type:
                result['response_format'] = 'html'
            
        except Exception as e:
            self.logger.debug(f"Error testing endpoint {endpoint}: {e}")
        
        return result
    
    def extract_features(self, old_url: str, new_url: str) -> np.ndarray:
        """Extract 12 API endpoint analysis features."""
        features = np.zeros(12)
        
        try:
            # Fetch HTML from both URLs
            try:
                old_response = requests.get(old_url, timeout=self.timeout, verify=False)
                old_html = old_response.text
            except Exception as e:
                self.logger.warning(f"Could not fetch old URL: {e}")
                old_html = ""
            
            try:
                new_response = requests.get(new_url, timeout=self.timeout, verify=False)
                new_html = new_response.text
            except Exception as e:
                self.logger.warning(f"Could not fetch new URL: {e}")
                new_html = ""
            
            if not old_html or not new_html:
                self.logger.warning("Could not fetch HTML from one or both URLs")
                return features
            
            # Extract endpoints
            old_endpoints = self.extract_endpoints_from_html(old_html, old_url)
            new_endpoints = self.extract_endpoints_from_html(new_html, new_url)
            
            if not old_endpoints or not new_endpoints:
                self.logger.warning("Could not extract endpoints from one or both URLs")
                return features
            
            # Feature 0: Endpoint Jaccard similarity
            features[0] = self.similarity_metrics.jaccard_similarity(old_endpoints, new_endpoints)
            
            # Feature 1-2: Endpoint count
            features[1] = min(len(old_endpoints) / 50, 1.0)
            features[2] = min(len(new_endpoints) / 50, 1.0)
            
            # Feature 3: Endpoint count similarity
            if max(len(old_endpoints), len(new_endpoints)) > 0:
                count_sim = min(len(old_endpoints), len(new_endpoints)) / max(len(old_endpoints), len(new_endpoints))
                features[3] = count_sim
            
            # Feature 4: Parameter overlap
            old_params = set()
            new_params = set()
            
            for ep in old_endpoints:
                params = self.extract_api_parameters(ep)
                old_params.update(params.keys())
            
            for ep in new_endpoints:
                params = self.extract_api_parameters(ep)
                new_params.update(params.keys())
            
            features[4] = self.similarity_metrics.jaccard_similarity(old_params, new_params)
            
            # Feature 5: API naming pattern consistency
            old_api_names = self._extract_api_names(old_endpoints)
            new_api_names = self._extract_api_names(new_endpoints)
            features[5] = self.similarity_metrics.jaccard_similarity(old_api_names, new_api_names)
            
            # Feature 6: Response format consistency
            old_formats = []
            new_formats = []
            
            for ep in list(old_endpoints)[:5]:  # Sample first 5
                result = self.test_endpoint(ep)
                old_formats.append(result['response_format'])
            
            for ep in list(new_endpoints)[:5]:
                result = self.test_endpoint(ep)
                new_formats.append(result['response_format'])
            
            format_consistency = 0
            if old_formats and new_formats:
                matching = sum(1 for i in range(min(len(old_formats), len(new_formats))) if old_formats[i] == new_formats[i])
                format_consistency = matching / min(len(old_formats), len(new_formats))
            features[6] = format_consistency
            
            # Feature 7: Status code consistency
            old_status_codes = []
            new_status_codes = []
            
            for ep in list(old_endpoints)[:5]:
                result = self.test_endpoint(ep)
                old_status_codes.append(result['status_code'])
            
            for ep in list(new_endpoints)[:5]:
                result = self.test_endpoint(ep)
                new_status_codes.append(result['status_code'])
            
            if old_status_codes and new_status_codes:
                old_mode = max(set(old_status_codes), key=old_status_codes.count) if old_status_codes else 0
                new_mode = max(set(new_status_codes), key=new_status_codes.count) if new_status_codes else 0
                features[7] = 1.0 if old_mode == new_mode else abs(old_mode - new_mode) / 600
            
            # Feature 8: Response time similarity
            old_times = [r.get('response_time', 0) for r in [self.test_endpoint(ep) for ep in list(old_endpoints)[:5]]]
            new_times = [r.get('response_time', 0) for r in [self.test_endpoint(ep) for ep in list(new_endpoints)[:5]]]
            
            if old_times and new_times:
                old_avg = np.mean(old_times)
                new_avg = np.mean(new_times)
                max_avg = max(old_avg, new_avg)
                if max_avg > 0:
                    features[8] = 1.0 - (abs(old_avg - new_avg) / max_avg)
            
            # Feature 9: Accessibility similarity
            old_accessible = sum(1 for result in [self.test_endpoint(ep) for ep in list(old_endpoints)[:5]] if result['accessible'])
            new_accessible = sum(1 for result in [self.test_endpoint(ep) for ep in list(new_endpoints)[:5]] if result['accessible'])
            
            if max(old_accessible, new_accessible) > 0:
                features[9] = min(old_accessible, new_accessible) / max(old_accessible, new_accessible)
            
            # Feature 10: Parameter consistency
            features[10] = features[4]  # Already calculated
            
            # Feature 11: Overall similarity
            features[11] = (features[0] + features[3] + features[5] + features[6]) / 4
            
            # Normalize all features to 0-1 range
            features = np.clip(features, 0, 1)
            
        except Exception as e:
            self.logger.error(f"Error extracting API features: {e}")
        
        return features
    
    @staticmethod
    def _extract_api_names(endpoints: Set[str]) -> Set[str]:
        """Extract API endpoint names/identifiers."""
        names = set()
        try:
            for ep in endpoints:
                # Extract meaningful parts from URL path
                path_parts = ep.split('/')
                for part in path_parts:
                    if part and part not in ['api', 'v1', 'v2', 'http', 'https', '']:
                        names.add(part.lower())
        except Exception:
            pass
        return names


def extract_api_features(old_url: str, new_url: str, timeout: int = HTTP_TIMEOUT) -> np.ndarray:
    """Convenience function to extract API features."""
    analyzer = APIEndpointAnalyzer(timeout=timeout)
    return analyzer.extract_features(old_url, new_url)
