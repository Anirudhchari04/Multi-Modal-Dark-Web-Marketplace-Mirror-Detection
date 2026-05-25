"""
Utility Functions Module for Darknet Mirror Detection System
Provides helper classes and functions for URL crawling, HTML parsing, similarity metrics, etc.
"""

import re
import logging
import hashlib
from typing import List, Dict, Tuple, Optional, Set
from urllib.parse import urljoin, urlparse
from collections import Counter
from difflib import SequenceMatcher
import numpy as np
from scipy.spatial.distance import cosine


class URLCrawler:
    """Crawls and extracts URLs and JavaScript file references from HTML."""
    
    def __init__(self, timeout: int = 10, max_retries: int = 2):
        self.timeout = timeout
        self.max_retries = max_retries
        self.logger = logging.getLogger(__name__)
    
    def extract_links(self, html_content: str, base_url: str) -> List[str]:
        """Extract all links from HTML content."""
        try:
            links = set()
            # Match href attributes
            href_pattern = r'href=["\']([^"\']+)["\']'
            for match in re.finditer(href_pattern, html_content):
                url = match.group(1)
                if url.startswith('/'):
                    url = urljoin(base_url, url)
                links.add(url)
            return list(links)
        except Exception as e:
            self.logger.warning(f"Error extracting links: {e}")
            return []
    
    def extract_js_files(self, html_content: str, base_url: str) -> List[str]:
        """Extract JavaScript file references from HTML."""
        try:
            js_files = set()
            # Match script src attributes
            script_pattern = r'<script[^>]+src=["\']([^"\']+)["\'][^>]*>'
            for match in re.finditer(script_pattern, html_content, re.IGNORECASE):
                url = match.group(1)
                if url.startswith('/'):
                    url = urljoin(base_url, url)
                js_files.add(url)
            return list(js_files)
        except Exception as e:
            self.logger.warning(f"Error extracting JS files: {e}")
            return []
    
    def extract_api_endpoints(self, html_content: str) -> List[str]:
        """Extract API endpoint patterns from HTML/JavaScript."""
        try:
            endpoints = set()
            # Match /api/ patterns
            api_pattern = r'/api/[a-zA-Z0-9/_\-\.]+'
            for match in re.finditer(api_pattern, html_content):
                endpoints.add(match.group(0))
            return list(endpoints)
        except Exception as e:
            self.logger.warning(f"Error extracting API endpoints: {e}")
            return []


class HTMLParser:
    """Analyzes HTML structure and DOM properties."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_dom_depth(self, element) -> int:
        """Calculate maximum depth of DOM tree from BeautifulSoup element."""
        try:
            if not hasattr(element, 'children'):
                return 0
            max_depth = 0
            for child in element.children:
                if hasattr(child, 'name') and child.name:
                    depth = 1 + self.calculate_dom_depth(child)
                    max_depth = max(max_depth, depth)
            return max_depth
        except Exception as e:
            self.logger.warning(f"Error calculating DOM depth: {e}")
            return 0
    
    def count_tags(self, html_content) -> Dict[str, int]:
        """Count occurrences of each HTML tag."""
        try:
            tag_counts = {}
            # Match opening tags only
            tag_pattern = r'<([a-zA-Z][a-zA-Z0-9]*)'
            for match in re.finditer(tag_pattern, str(html_content)):
                tag = match.group(1).lower()
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
            return tag_counts
        except Exception as e:
            self.logger.warning(f"Error counting tags: {e}")
            return {}
    
    def extract_css_classes(self, html_content: str) -> Set[str]:
        """Extract all unique CSS class names."""
        try:
            classes = set()
            # Match class attributes
            class_pattern = r'class=["\']([^"\']+)["\']'
            for match in re.finditer(class_pattern, html_content):
                class_list = match.group(1).split()
                classes.update(class_list)
            return classes
        except Exception as e:
            self.logger.warning(f"Error extracting CSS classes: {e}")
            return set()
    
    def extract_form_info(self, html_content: str) -> Dict[str, int]:
        """Extract information about forms."""
        try:
            form_info = {
                'form_count': len(re.findall(r'<form', html_content, re.IGNORECASE)),
                'input_count': len(re.findall(r'<input', html_content, re.IGNORECASE)),
                'textarea_count': len(re.findall(r'<textarea', html_content, re.IGNORECASE)),
                'button_count': len(re.findall(r'<button', html_content, re.IGNORECASE))
            }
            return form_info
        except Exception as e:
            self.logger.warning(f"Error extracting form info: {e}")
            return {}


class SimilarityMetrics:
    """Calculates various similarity metrics between two objects."""
    
    @staticmethod
    def jaccard_similarity(set1: Set, set2: Set) -> float:
        """Calculate Jaccard similarity between two sets."""
        try:
            if not set1 and not set2:
                return 1.0
            if not set1 or not set2:
                return 0.0
            intersection = len(set1 & set2)
            union = len(set1 | set2)
            if union == 0:
                return 0.0
            return intersection / union
        except Exception:
            return 0.0
    
    @staticmethod
    def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            if len(vec1) == 0 or len(vec2) == 0:
                return 0.0
            # Normalize vectors
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            if norm1 == 0 or norm2 == 0:
                return 0.0
            vec1_norm = vec1 / norm1
            vec2_norm = vec2 / norm2
            return np.clip(np.dot(vec1_norm, vec2_norm), 0, 1)
        except Exception:
            return 0.0
    
    @staticmethod
    def levenshtein_distance(s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings."""
        try:
            if len(s1) < len(s2):
                return SimilarityMetrics.levenshtein_distance(s2, s1)
            if len(s2) == 0:
                return len(s1)
            
            previous_row = range(len(s2) + 1)
            for i, c1 in enumerate(s1):
                current_row = [i + 1]
                for j, c2 in enumerate(s2):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row
            
            return previous_row[-1]
        except Exception:
            return max(len(s1), len(s2))
    
    @staticmethod
    def normalized_similarity(s1: str, s2: str) -> float:
        """Calculate normalized string similarity (0-1)."""
        try:
            if not s1 and not s2:
                return 1.0
            if not s1 or not s2:
                return 0.0
            distance = SimilarityMetrics.levenshtein_distance(s1, s2)
            max_length = max(len(s1), len(s2))
            if max_length == 0:
                return 1.0
            return 1 - (distance / max_length)
        except Exception:
            return 0.0


class FeatureNormalizer:
    """Handles feature normalization using StandardScaler approach."""
    
    def __init__(self):
        self.mean = None
        self.std = None
        self.logger = logging.getLogger(__name__)
    
    def fit(self, features: np.ndarray) -> None:
        """Calculate mean and std for normalization."""
        try:
            self.mean = np.nanmean(features, axis=0)
            self.std = np.nanstd(features, axis=0)
            # Avoid division by zero
            self.std[self.std == 0] = 1.0
        except Exception as e:
            self.logger.error(f"Error fitting normalizer: {e}")
    
    def normalize(self, features: np.ndarray) -> np.ndarray:
        """Normalize features using fitted mean and std."""
        try:
            if self.mean is None or self.std is None:
                self.logger.warning("Normalizer not fitted. Returning original features.")
                return features
            return (features - self.mean) / self.std
        except Exception as e:
            self.logger.error(f"Error normalizing features: {e}")
            return features
    
    def fit_and_normalize(self, features: np.ndarray) -> np.ndarray:
        """Fit and normalize in one step."""
        self.fit(features)
        return self.normalize(features)


class DataValidator:
    """Validates input data and URLs."""
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Validate URL format."""
        try:
            if not isinstance(url, str):
                return False
            if len(url) < 5 or len(url) > 500:
                return False
            # Check for valid schemes
            if not any(url.startswith(scheme) for scheme in ('http://', 'https://', '.onion')):
                return False
            return True
        except Exception:
            return False
    
    @staticmethod
    def is_valid_pgp_fingerprint(fingerprint: str) -> bool:
        """Validate PGP fingerprint format."""
        try:
            if not isinstance(fingerprint, str):
                return False
            # 40 hex chars (short) or 64 hex chars (long)
            return bool(re.match(r'^[A-F0-9]{40}$|^[A-F0-9]{64}$', fingerprint, re.IGNORECASE))
        except Exception:
            return False
    
    @staticmethod
    def sanitize_html(html: str) -> str:
        """Remove potentially problematic content from HTML."""
        try:
            # Remove script tags
            html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.IGNORECASE | re.DOTALL)
            # Remove event handlers
            html = re.sub(r'\s*on\w+\s*=\s*["\'][^"\']*["\']', '', html, flags=re.IGNORECASE)
            return html
        except Exception:
            return html


class ResponseAnalyzer:
    """Analyzes HTTP response characteristics."""
    
    @staticmethod
    def extract_server_header(response) -> str:
        """Extract Server header from HTTP response."""
        try:
            return response.headers.get('Server', '')
        except Exception:
            return ''
    
    @staticmethod
    def extract_x_powered_by(response) -> str:
        """Extract X-Powered-By header from HTTP response."""
        try:
            return response.headers.get('X-Powered-By', '')
        except Exception:
            return ''
    
    @staticmethod
    def calculate_timing_stats(timings: List[float]) -> Dict[str, float]:
        """Calculate statistics from response timings."""
        try:
            if not timings:
                return {
                    'mean': 0.0,
                    'std': 0.0,
                    'min': 0.0,
                    'max': 0.0,
                    'p50': 0.0,
                    'p95': 0.0,
                    'p99': 0.0
                }
            
            timings_arr = np.array(timings)
            return {
                'mean': float(np.mean(timings_arr)),
                'std': float(np.std(timings_arr)),
                'min': float(np.min(timings_arr)),
                'max': float(np.max(timings_arr)),
                'p50': float(np.percentile(timings_arr, 50)),
                'p95': float(np.percentile(timings_arr, 95)),
                'p99': float(np.percentile(timings_arr, 99))
            }
        except Exception:
            return {}


class PGPAnalyzer:
    """Analyzes PGP cryptographic keys and fingerprints."""
    
    @staticmethod
    def extract_fingerprints(text: str) -> List[str]:
        """Extract PGP fingerprints from text."""
        try:
            fingerprints = []
            # Match both 40-char and 64-char hex fingerprints
            pattern = r'[A-F0-9]{40}(?:[A-F0-9]{24})?'
            for match in re.finditer(pattern, text.upper()):
                fp = match.group(0)
                if len(fp) in [40, 64]:
                    fingerprints.append(fp)
            return list(set(fingerprints))
        except Exception:
            return []
    
    @staticmethod
    def fingerprint_match_score(fp1: str, fp2: str) -> float:
        """Calculate fingerprint match score."""
        try:
            if fp1 == fp2:
                return 1.0
            if not fp1 or not fp2:
                return 0.0
            # Use suffix matching (last 16 chars commonly match)
            suffix_len = min(16, len(fp1), len(fp2))
            if fp1[-suffix_len:] == fp2[-suffix_len:]:
                return 0.95
            # Use Levenshtein similarity
            return SimilarityMetrics.normalized_similarity(fp1, fp2)
        except Exception:
            return 0.0


class LoggingSetup:
    """Configures logging for the system."""
    
    @staticmethod
    def setup_logging(name: str, level: int = logging.INFO) -> logging.Logger:
        """Setup logger with console and file handlers."""
        try:
            logger = logging.getLogger(name)
            logger.setLevel(level)
            
            # Only add handlers if not already present
            if logger.handlers:
                return logger
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            
            return logger
        except Exception as e:
            print(f"Error setting up logging: {e}")
            return logging.getLogger(name)
