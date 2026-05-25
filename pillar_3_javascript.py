"""
Pillar 3: JavaScript Code Analysis
Analyzes JavaScript code structure and patterns
Extracts 12 features related to JavaScript similarity
"""

import requests
import re
import logging
import numpy as np
from typing import List, Set

from config import HTTP_TIMEOUT
from utils import URLCrawler, SimilarityMetrics, DataValidator


class JavaScriptAnalyzer:
    """Analyzes JavaScript code across marketplace mirrors."""
    
    def __init__(self, timeout: int = HTTP_TIMEOUT):
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        self.url_crawler = URLCrawler(timeout=timeout)
        self.similarity_metrics = SimilarityMetrics()
    
    def download_js_files(self, url: str) -> List[str]:
        """Download JavaScript files referenced in HTML."""
        js_contents = []
        
        try:
            response = requests.get(url, timeout=self.timeout, verify=False)
            html_content = response.text
            
            # Extract JS file URLs
            js_files = self.url_crawler.extract_js_files(html_content, url)
            
            for js_url in js_files[:10]:  # Limit to first 10 files
                try:
                    js_response = requests.get(js_url, timeout=self.timeout, verify=False)
                    js_contents.append(js_response.text)
                except Exception as e:
                    self.logger.warning(f"Could not fetch JS from {js_url}: {e}")
        
        except Exception as e:
            self.logger.warning(f"Error downloading JS files: {e}")
        
        return js_contents
    
    def extract_function_names(self, js_code: str) -> Set[str]:
        """Extract function names from JavaScript code."""
        try:
            functions = set()
            # Match function declarations and expressions
            patterns = [
                r'function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)',
                r'([a-zA-Z_$][a-zA-Z0-9_$]*)\s*:\s*function',
                r'([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*function',
                r'([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*\(.*?\)\s*=>'
            ]
            
            for pattern in patterns:
                for match in re.finditer(pattern, js_code):
                    func_name = match.group(1).lower()
                    functions.add(func_name)
            
            return functions
        except Exception:
            return set()
    
    def extract_variable_names(self, js_code: str) -> Set[str]:
        """Extract variable names from JavaScript code."""
        try:
            variables = set()
            # Match variable declarations
            patterns = [
                r'var\s+([a-zA-Z_$][a-zA-Z0-9_$]*)',
                r'let\s+([a-zA-Z_$][a-zA-Z0-9_$]*)',
                r'const\s+([a-zA-Z_$][a-zA-Z0-9_$]*)',
                r'([a-zA-Z_$][a-zA-Z0-9_$]*)\s*='
            ]
            
            for pattern in patterns:
                for match in re.finditer(pattern, js_code):
                    var_name = match.group(1).lower()
                    if len(var_name) < 50:  # Reasonable length limit
                        variables.add(var_name)
            
            return variables
        except Exception:
            return set()
    
    def extract_features(self, old_url: str, new_url: str) -> np.ndarray:
        """Extract 12 JavaScript analysis features."""
        features = np.zeros(12)
        
        try:
            # Download JS files
            old_js_files = self.download_js_files(old_url)
            new_js_files = self.download_js_files(new_url)
            
            if not old_js_files or not new_js_files:
                self.logger.warning("Could not fetch JavaScript files from one or both sites")
                return features
            
            # Combine all JS code
            old_js_all = " ".join(old_js_files)
            new_js_all = " ".join(new_js_files)
            
            # Extract functions
            old_functions = self.extract_function_names(old_js_all)
            new_functions = self.extract_function_names(new_js_all)
            
            # Feature 0: Function overlap percentage
            if old_functions or new_functions:
                overlap = len(old_functions & new_functions)
                max_set = max(len(old_functions), len(new_functions))
                features[0] = overlap / max_set if max_set > 0 else 0
            
            # Extract variables
            old_variables = self.extract_variable_names(old_js_all)
            new_variables = self.extract_variable_names(new_js_all)
            
            # Feature 1: Variable overlap percentage
            if old_variables or new_variables:
                overlap = len(old_variables & new_variables)
                max_set = max(len(old_variables), len(new_variables))
                features[1] = overlap / max_set if max_set > 0 else 0
            
            # Feature 2: Total code overlap
            total_overlap = len((old_functions | old_variables) & (new_functions | new_variables))
            total_set = len((old_functions | old_variables) | (new_functions | new_variables))
            features[2] = total_overlap / total_set if total_set > 0 else 0
            
            # Feature 3-4: Function/Variable counts
            features[3] = min(len(old_functions) / 100, 1.0)
            features[4] = min(len(old_variables) / 500, 1.0)
            
            # Feature 5: Size similarity
            old_size = len(old_js_all)
            new_size = len(new_js_all)
            if old_size > 0 and new_size > 0:
                size_ratio = min(old_size, new_size) / max(old_size, new_size)
                features[5] = size_ratio
            
            # Feature 6: File count similarity
            file_ratio = min(len(old_js_files), len(new_js_files)) / max(len(old_js_files), len(new_js_files))
            features[6] = file_ratio if max(len(old_js_files), len(new_js_files)) > 0 else 0
            
            # Feature 7: Naming convention consistency
            old_naming_score = self._analyze_naming_patterns(old_functions | old_variables)
            new_naming_score = self._analyze_naming_patterns(new_functions | new_variables)
            features[7] = 1.0 - abs(old_naming_score - new_naming_score)
            
            # Feature 8: Code complexity (ratio of functions to variables)
            old_complexity = len(old_functions) / max(len(old_variables), 1)
            new_complexity = len(new_functions) / max(len(new_variables), 1)
            complexity_sim = 1 - min(abs(old_complexity - new_complexity), 1.0)
            features[8] = complexity_sim
            
            # Feature 9: Minification pattern similarity
            old_minified_score = self._detect_minification(old_js_all)
            new_minified_score = self._detect_minification(new_js_all)
            features[9] = 1.0 - abs(old_minified_score - new_minified_score)
            
            # Feature 10: Library detection (common frameworks)
            old_libs = self._detect_frameworks(old_js_all)
            new_libs = self._detect_frameworks(new_js_all)
            features[10] = self.similarity_metrics.jaccard_similarity(old_libs, new_libs)
            
            # Feature 11: Comment density
            old_comments = len(re.findall(r'//.*|/\*.*?\*/', old_js_all))
            new_comments = len(re.findall(r'//.*|/\*.*?\*/', new_js_all))
            comment_sim = 1 - abs(old_comments - new_comments) / max(old_comments, new_comments, 1)
            features[11] = max(0, comment_sim)
            
            # Normalize all features to 0-1 range
            features = np.clip(features, 0, 1)
            
        except Exception as e:
            self.logger.error(f"Error extracting JavaScript features: {e}")
        
        return features
    
    @staticmethod
    def _analyze_naming_patterns(identifiers: Set[str]) -> float:
        """Analyze naming conventions (camelCase vs snake_case vs etc.)."""
        try:
            if not identifiers:
                return 0.5
            
            camel_case = sum(1 for i in identifiers if re.match(r'^[a-z]+([A-Z][a-z]*)*$', i))
            snake_case = sum(1 for i in identifiers if '_' in i)
            
            total = len(identifiers)
            camel_ratio = camel_case / total
            snake_ratio = snake_case / total
            
            return max(camel_ratio, snake_ratio)
        except Exception:
            return 0.5
    
    @staticmethod
    def _detect_minification(js_code: str) -> float:
        """Detect if JavaScript is minified."""
        try:
            # Heuristics: high density of symbols, few newlines
            lines = js_code.split('\n')
            if len(lines) < 10 and len(js_code) > 5000:
                return 0.9
            elif len(lines) > 1000:
                return 0.1
            else:
                return 0.5
        except Exception:
            return 0.5
    
    @staticmethod
    def _detect_frameworks(js_code: str) -> Set[str]:
        """Detect common JavaScript frameworks."""
        frameworks = set()
        framework_patterns = {
            'jquery': r'jquery|jQuery|\$\(',
            'react': r'React|react|ReactDOM',
            'angular': r'angular|Angular',
            'vue': r'Vue|vue',
            'lodash': r'lodash|_\.',
            'axios': r'axios',
            'bootstrap': r'bootstrap|Bootstrap'
        }
        
        for name, pattern in framework_patterns.items():
            if re.search(pattern, js_code):
                frameworks.add(name)
        
        return frameworks


def extract_javascript_features(old_url: str, new_url: str, timeout: int = HTTP_TIMEOUT) -> np.ndarray:
    """Convenience function to extract JavaScript features."""
    analyzer = JavaScriptAnalyzer(timeout=timeout)
    return analyzer.extract_features(old_url, new_url)
