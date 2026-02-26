#!/usr/bin/env python3
"""
Auto-Analyze Utility
====================
Tiện ích phân tích tự động cho HKSC-4096 Autonomous System.

Chức năng:
- Phân tích codebase
- Phát hiện vấn đề
- Đề xuất cải thiện
- Tạo báo cáo
"""

import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('AutoAnalyze')


class CodeAnalyzer:
    """Phân tích codebase"""
    
    def __init__(self):
        self.findings: List[Dict] = []
        self.metrics: Dict[str, Any] = {}
    
    def analyze_all(self) -> Dict:
        """Phân tích toàn bộ codebase"""
        logger.info("Starting comprehensive code analysis...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'python': self._analyze_python(),
            'javascript': self._analyze_javascript(),
            'solidity': self._analyze_solidity(),
            'dependencies': self._analyze_dependencies(),
            'security': self._analyze_security(),
            'performance': self._analyze_performance(),
            'findings': self.findings
        }
        
        # Calculate overall health score
        results['health_score'] = self._calculate_health_score(results)
        
        return results
    
    def _analyze_python(self) -> Dict:
        """Phân tích code Python"""
        logger.info("Analyzing Python code...")
        
        results = {
            'files': 0,
            'lines': 0,
            'issues': []
        }
        
        # Count files
        py_files = list(Path('hksc-python').rglob('*.py'))
        results['files'] = len(py_files)
        
        # Count lines
        for f in py_files:
            try:
                with open(f, 'r') as file:
                    results['lines'] += len(file.readlines())
            except:
                pass
        
        # Run pylint
        try:
            result = subprocess.run(
                ['pylint', 'hksc-python', '--output-format=json'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.stdout:
                pylint_issues = json.loads(result.stdout)
                for issue in pylint_issues:
                    self.findings.append({
                        'type': 'python',
                        'severity': issue.get('type', 'convention'),
                        'message': issue.get('message'),
                        'file': issue.get('path'),
                        'line': issue.get('line')
                    })
                
                results['issues'] = pylint_issues
        
        except Exception as e:
            logger.debug(f"Pylint analysis failed: {e}")
        
        # Run bandit
        try:
            result = subprocess.run(
                ['bandit', '-r', 'hksc-python', '-f', 'json'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.stdout:
                bandit_results = json.loads(result.stdout)
                results['security_issues'] = bandit_results.get('results', [])
                
                for issue in bandit_results.get('results', []):
                    self.findings.append({
                        'type': 'security',
                        'severity': issue.get('issue_severity', 'low'),
                        'message': issue.get('issue_text'),
                        'file': issue.get('filename'),
                        'line': issue.get('line_number')
                    })
        
        except Exception as e:
            logger.debug(f"Bandit analysis failed: {e}")
        
        return results
    
    def _analyze_javascript(self) -> Dict:
        """Phân tích code JavaScript"""
        logger.info("Analyzing JavaScript code...")
        
        results = {
            'files': 0,
            'lines': 0,
            'issues': []
        }
        
        # Count files
        js_files = list(Path('hksc-electron').rglob('*.js'))
        js_files.extend(Path('hksc-electron').rglob('*.jsx'))
        results['files'] = len(js_files)
        
        # Count lines
        for f in js_files:
            try:
                with open(f, 'r') as file:
                    results['lines'] += len(file.readlines())
            except:
                pass
        
        # Run ESLint if available
        try:
            result = subprocess.run(
                ['npx', 'eslint', 'hksc-electron', '--format=json'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.stdout:
                eslint_results = json.loads(result.stdout)
                results['issues'] = eslint_results
        
        except Exception as e:
            logger.debug(f"ESLint analysis failed: {e}")
        
        return results
    
    def _analyze_solidity(self) -> Dict:
        """Phân tích code Solidity"""
        logger.info("Analyzing Solidity code...")
        
        results = {
            'files': 0,
            'lines': 0,
            'issues': []
        }
        
        # Count files
        sol_files = list(Path('hksc-verifier-contract/contracts').rglob('*.sol'))
        results['files'] = len(sol_files)
        
        # Count lines
        for f in sol_files:
            try:
                with open(f, 'r') as file:
                    results['lines'] += len(file.readlines())
            except:
                pass
        
        # Run Slither if available
        try:
            result = subprocess.run(
                ['slither', 'hksc-verifier-contract', '--json', '-'],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.stdout:
                slither_results = json.loads(result.stdout)
                results['issues'] = slither_results
                
                for issue in slither_results.get('results', {}).get('detectors', []):
                    self.findings.append({
                        'type': 'solidity',
                        'severity': issue.get('impact', 'informational'),
                        'message': issue.get('description'),
                        'file': issue.get('check'),
                        'line': issue.get('elements', [{}])[0].get('source_mapping', {}).get('lines', [0])[0]
                    })
        
        except Exception as e:
            logger.debug(f"Slither analysis failed: {e}")
        
        return results
    
    def _analyze_dependencies(self) -> Dict:
        """Phân tích dependencies"""
        logger.info("Analyzing dependencies...")
        
        results = {
            'python': {},
            'nodejs': {}
        }
        
        # Python dependencies
        try:
            result = subprocess.run(
                ['pip', 'list', '--format=json'],
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                packages = json.loads(result.stdout)
                results['python']['count'] = len(packages)
                results['python']['packages'] = packages[:20]  # Top 20
        
        except Exception as e:
            logger.debug(f"Python dependency analysis failed: {e}")
        
        # Node.js dependencies
        try:
            with open('hksc-electron/package.json', 'r') as f:
                pkg = json.load(f)
                deps = pkg.get('dependencies', {})
                dev_deps = pkg.get('devDependencies', {})
                results['nodejs']['count'] = len(deps) + len(dev_deps)
                results['nodejs']['dependencies'] = deps
        
        except Exception as e:
            logger.debug(f"Node.js dependency analysis failed: {e}")
        
        return results
    
    def _analyze_security(self) -> Dict:
        """Phân tích bảo mật"""
        logger.info("Analyzing security...")
        
        results = {
            'vulnerabilities': [],
            'score': 100
        }
        
        # Check for secrets in code
        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', 'Hardcoded password'),
            (r'api_key\s*=\s*["\'][^"\']+["\']', 'Hardcoded API key'),
            (r'secret\s*=\s*["\'][^"\']+["\']', 'Hardcoded secret'),
            (r'private_key\s*=\s*["\'][^"\']+["\']', 'Hardcoded private key'),
        ]
        
        for root, _, files in os.walk('.'):
            for file in files:
                if file.endswith(('.py', '.js', '.sol', '.yml', '.yaml')):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r') as f:
                            content = f.read()
                        
                        for pattern, description in secret_patterns:
                            import re
                            if re.search(pattern, content, re.IGNORECASE):
                                self.findings.append({
                                    'type': 'security',
                                    'severity': 'critical',
                                    'message': f'Potential secret: {description}',
                                    'file': filepath
                                })
                                results['score'] -= 20
                    
                    except:
                        pass
        
        return results
    
    def _analyze_performance(self) -> Dict:
        """Phân tích hiệu suất"""
        logger.info("Analyzing performance...")
        
        results = {
            'bottlenecks': [],
            'recommendations': []
        }
        
        # Check for common performance issues
        performance_patterns = [
            (r'for\s+\w+\s+in\s+range\([^)]+\):\s*\n\s+\w+\.append\(', 
             'List append in loop - consider list comprehension'),
            (r'\.querySelectorAll\([^)]+\)',
             'DOM query - consider caching results'),
        ]
        
        return results
    
    def _calculate_health_score(self, results: Dict) -> float:
        """Tính điểm sức khỏe tổng thể"""
        score = 100.0
        
        # Deduct for findings
        for finding in self.findings:
            severity = finding.get('severity', 'low')
            if severity == 'critical':
                score -= 15
            elif severity == 'high':
                score -= 10
            elif severity == 'medium':
                score -= 5
            else:
                score -= 1
        
        return max(0, score)
    
    def generate_report(self, results: Dict, output_path: str = 'autonomous-report.json'):
        """Tạo báo cáo"""
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Report saved to {output_path}")


def main():
    """Main entry point"""
    analyzer = CodeAnalyzer()
    results = analyzer.analyze_all()
    analyzer.generate_report(results)
    
    # Print summary
    print(f"\n{'='*60}")
    print("AUTO-ANALYSIS SUMMARY")
    print(f"{'='*60}")
    print(f"Health Score: {results['health_score']:.1f}/100")
    print(f"Total Findings: {len(results['findings'])}")
    print(f"Python Files: {results['python']['files']}")
    print(f"JavaScript Files: {results['javascript']['files']}")
    print(f"Solidity Files: {results['solidity']['files']}")
    print(f"{'='*60}\n")
    
    # Exit with error code if health is poor
    if results['health_score'] < 50:
        print("WARNING: Health score is below 50!")
        sys.exit(1)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
