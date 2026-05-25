"""
Pillar 2: HTML/DOM Structure Analysis
Analyzes HTML structure, DOM depth, tag distribution, CSS classes
Extracts 15 features related to structural similarity
"""

import requests
import logging
import numpy as np
from typing import Dict, Set
from html.parser import HTMLParser as BaseHTMLParser

from config import HTTP_TIMEOUT
from utils import HTMLParser, SimilarityMetrics, DataValidator


class HTMLDOMAnalyzer:
    """Analyzes HTML structure and DOM characteristics."""
    
    def __init__(self, timeout: int = HTTP_TIMEOUT):
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        self.html_parser = HTMLParser()
        self.similarity_metrics = SimilarityMetrics()
    
    def fetch_html(self, url: str) -> str:
        """Fetch HTML content from URL."""
        if not DataValidator.is_valid_url(url):
            self.logger.error(f"Invalid URL: {url}")
            return ""
        
        try:
            response = requests.get(url, timeout=self.timeout, verify=False)
            response.encoding = 'utf-8'
            return response.text
        except Exception as e:
            self.logger.warning(f"Error fetching HTML from {url}: {e}")
            return ""
    
    def extract_features(self, old_url: str, new_url: str) -> np.ndarray:
        """Extract 15 HTML/DOM analysis features."""
        features = np.zeros(15)
        
        try:
            # Fetch HTML
            old_html = self.fetch_html(old_url)
            new_html = self.fetch_html(new_url)
            
            if not old_html or not new_html:
                self.logger.warning("Could not fetch both HTML documents")
                return features
            
            # Feature 0-2: DOM depth analysis
            old_depth = self._count_nesting_depth(old_html)
            new_depth = self._count_nesting_depth(new_html)
            features[0] = old_depth / 100  # Normalize
            features[1] = new_depth / 100
            features[2] = 1.0 if old_depth == new_depth else abs(old_depth - new_depth) / 100
            
            # Feature 3-5: Tag count analysis
            old_tags = self.html_parser.count_tags(old_html)
            new_tags = self.html_parser.count_tags(new_html)
            total_old = sum(old_tags.values()) if old_tags else 1
            total_new = sum(new_tags.values()) if new_tags else 1
            
            features[3] = min(total_old / 1000, 1.0)
            features[4] = min(total_new / 1000, 1.0)
            features[5] = 1.0 if total_old == total_new else abs(total_old - total_new) / max(total_old, total_new)
            
            # Feature 6: Tag frequency Jaccard similarity
            old_tag_set = set(old_tags.keys()) if old_tags else set()
            new_tag_set = set(new_tags.keys()) if new_tags else set()
            features[6] = self.similarity_metrics.jaccard_similarity(old_tag_set, new_tag_set)
            
            # Feature 7: CSS classes Jaccard similarity
            old_classes = self.html_parser.extract_css_classes(old_html)
            new_classes = self.html_parser.extract_css_classes(new_html)
            features[7] = self.similarity_metrics.jaccard_similarity(old_classes, new_classes)
            
            # Feature 8-9: Form structure analysis
            old_form_info = self.html_parser.extract_form_info(old_html)
            new_form_info = self.html_parser.extract_form_info(new_html)
            
            # Form similarity
            form_score = 0
            if old_form_info and new_form_info:
                max_forms = max(old_form_info.get('form_count', 0), new_form_info.get('form_count', 0))
                if max_forms > 0:
                    form_score = 1 - (abs(old_form_info.get('form_count', 0) - new_form_info.get('form_count', 0)) / max_forms)
            features[8] = max(0, form_score)
            
            # Input similarity
            input_score = 0
            if old_form_info and new_form_info:
                max_inputs = max(old_form_info.get('input_count', 0), new_form_info.get('input_count', 0))
                if max_inputs > 0:
                    input_score = 1 - (abs(old_form_info.get('input_count', 0) - new_form_info.get('input_count', 0)) / max_inputs)
            features[9] = max(0, input_score)
            
            # Feature 10: Header consistency (h1, h2, etc.)
            old_headers = self._extract_headers(old_html)
            new_headers = self._extract_headers(new_html)
            features[10] = self.similarity_metrics.jaccard_similarity(set(old_headers), set(new_headers))
            
            # Feature 11: Link density
            old_links = len(self.html_parser.extract_css_classes(old_html))
            old_link_density = old_links / max(total_old, 1)
            features[11] = min(old_link_density, 1.0)
            
            # Feature 12: Image density
            old_images = old_html.count('<img')
            old_image_density = old_images / max(total_old, 1)
            features[12] = min(old_image_density, 1.0)
            
            # Feature 13: Script similarity
            old_scripts = self._extract_script_content(old_html)
            new_scripts = self._extract_script_content(new_html)
            features[13] = self.similarity_metrics.jaccard_similarity(set(old_scripts), set(new_scripts))
            
            # Feature 14: Meta tag consistency
            old_meta = self._extract_meta_tags(old_html)
            new_meta = self._extract_meta_tags(new_html)
            features[14] = self.similarity_metrics.jaccard_similarity(set(old_meta.keys()), set(new_meta.keys()))
            
            # Normalize all features to 0-1 range
            features = np.clip(features, 0, 1)
            
        except Exception as e:
            self.logger.error(f"Error extracting HTML features: {e}")
        
        return features
    
    @staticmethod
    def _count_nesting_depth(html: str) -> int:
        """Count maximum nesting depth in HTML."""
        try:
            depth = 0
            max_depth = 0
            for char in html:
                if char == '<':
                    depth += 1
                    max_depth = max(max_depth, depth)
                elif char == '>':
                    depth = max(0, depth - 1)
            return max_depth
        except Exception:
            return 0
    
    @staticmethod
    def _extract_headers(html: str) -> list:
        """Extract header text content."""
        try:
            import re
            headers = []
            for match in re.finditer(r'<h[1-6]>([^<]+)</h[1-6]>', html, re.IGNORECASE):
                headers.append(match.group(1).strip())
            return headers
        except Exception:
            return []
    
    @staticmethod
    def _extract_script_content(html: str) -> list:
        """Extract inline script content."""
        try:
            import re
            scripts = []
            for match in re.finditer(r'<script[^>]*>([^<]*)</script>', html, re.IGNORECASE | re.DOTALL):
                content = match.group(1).strip()
                if content:
                    scripts.append(content[:100])  # First 100 chars
            return scripts
        except Exception:
            return []
    
    @staticmethod
    def _extract_meta_tags(html: str) -> Dict[str, str]:
        """Extract meta tag information."""
        try:
            import re
            meta_tags = {}
            for match in re.finditer(r'<meta\s+name=["\']([^"\']+)["\'][^>]*content=["\']([^"\']+)["\']', html, re.IGNORECASE):
                name, content = match.groups()
                meta_tags[name.lower()] = content[:50]
            return meta_tags
        except Exception:
            return {}


def extract_html_features(old_url: str, new_url: str, timeout: int = HTTP_TIMEOUT) -> np.ndarray:
    """Convenience function to extract HTML features."""
    analyzer = HTMLDOMAnalyzer(timeout=timeout)
    return analyzer.extract_features(old_url, new_url)
