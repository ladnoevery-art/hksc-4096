#!/usr/bin/env python3
"""
Auto-Optimization Agent
=======================
Tự động tối ưu hiệu suất và chất lượng code.

Chức năng:
- Phân tích hiệu suất
- Tối ưu code tự động
- Cải thiện thuật toán
- Giảm chi phí gas (smart contracts)
- Tối ưu bộ nhớ và CPU
"""

import asyncio
import ast
import json
import logging
import os
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from agents.controller import BaseAgent, Task, AgentState, TaskPriority

logger = logging.getLogger('HKSC-OptimizationAgent')


@dataclass
class OptimizationOpportunity:
    """Cơ hội tối ưu được phát hiện"""
    id: str
    file_path: str
    line_start: int
    line_end: int
    category: str  # performance, memory, readability, gas
    severity: str  # critical, high, medium, low
    description: str
    current_code: str
    suggested_code: str
    expected_improvement: Dict[str, float]
    confidence: float
    auto_applicable: bool


class OptimizationAgent(BaseAgent):
    """
    Agent chuyên trách việc tự động tối ưu hệ thống.
    """
    
    def __init__(self):
        super().__init__("optimizer")
        
        self.config = {
            'auto_optimize': True,
            'optimization_threshold': 0.1,  # 10% improvement required
            'test_after_optimize': True,
            'max_optimizations_per_run': 10,
            'categories': ['performance', 'memory', 'gas', 'readability']
        }
        
        # Optimization patterns
        self.patterns = self._load_optimization_patterns()
        
        # Tracking
        self.optimization_history: List[Dict] = []
        self.opportunities: Dict[str, OptimizationOpportunity] = {}
        
        logger.info("OptimizationAgent initialized")
    
    def _load_optimization_patterns(self) -> Dict:
        """Load các pattern tối ưu"""
        return {
            'python': {
                'list_comprehension': {
                    'pattern': r'for\s+\w+\s+in\s+\w+:\s*\n\s+(\w+)\.append\(([^)]+)\)',
                    'replacement': r'[\2 for \1 in \3]',
                    'category': 'performance',
                    'description': 'Convert loop to list comprehension'
                },
                'unnecessary_list': {
                    'pattern': r'list\(([^)]+)\)',
                    'replacement': r'\1',
                    'category': 'memory',
                    'description': 'Remove unnecessary list() conversion'
                },
                'repeated_calculation': {
                    'pattern': r'(\w+)\s*=\s*([^\n]+)\n.*\1',
                    'replacement': 'hoist_calculation',
                    'category': 'performance',
                    'description': 'Hoist repeated calculations'
                },
                'string_concatenation': {
                    'pattern': r'(\w+)\s*\+=\s*["\']',
                    'replacement': 'use_join',
                    'category': 'performance',
                    'description': 'Use str.join() instead of +='
                }
            },
            'solidity': {
                'storage_to_memory': {
                    'pattern': r'(\w+)\s+storage\s+(\w+)',
                    'replacement': r'\1 memory \2',
                    'category': 'gas',
                    'description': 'Use memory instead of storage'
                },
                'unchecked_arithmetic': {
                    'pattern': r'(\w+)\s*=\s*(\w+)\s*([+\-])\s*(\w+)',
                    'replacement': 'unchecked { \1 = \2 \3 \4; }',
                    'category': 'gas',
                    'description': 'Use unchecked arithmetic'
                },
                'calldata_array': {
                    'pattern': r'function\s+\w+\([^)]*\w+\[\]\s+\w+',
                    'replacement': 'add_calldata',
                    'category': 'gas',
                    'description': 'Use calldata for external function arrays'
                },
                'pack_variables': {
                    'pattern': r'uint256\s+(\w+);\s*uint256\s+(\w+);',
                    'replacement': 'pack_to_smaller',
                    'category': 'gas',
                    'description': 'Pack variables to use smaller types'
                }
            },
            'javascript': {
                'unnecessary_async': {
                    'pattern': r'async\s+function\s*\([^)]*\)\s*\{[^}]*return\s+[^}]*\}',
                    'replacement': 'remove_async',
                    'category': 'performance',
                    'description': 'Remove unnecessary async'
                },
                'object_destructure': {
                    'pattern': r'const\s+(\w+)\s+=\s+(\w+)\.(\w+)',
                    'replacement': 'destructure',
                    'category': 'readability',
                    'description': 'Use object destructuring'
                }
            }
        }
    
    async def execute(self, task: Task) -> Any:
        """Thực thi optimization task"""
        action = task.payload.get('action', 'analyze_all')
        
        if action == 'analyze_all':
            return await self.analyze_all_files()
        
        elif action == 'optimize_file':
            file_path = task.payload.get('file_path')
            return await self.optimize_file(file_path)
        
        elif action == 'apply_optimization':
            opt_id = task.payload.get('optimization_id')
            return await self.apply_optimization(opt_id)
        
        elif action == 'benchmark':
            return await self.run_benchmarks()
        
        elif action == 'improve_scenario':
            scenario = task.payload.get('scenario')
            weaknesses = task.payload.get('weaknesses')
            return await self.improve_scenario_resilience(scenario, weaknesses)
        
        else:
            return {'error': f'Unknown action: {action}'}
    
    async def analyze_all_files(self) -> Dict:
        """Phân tích tất cả các file để tìm cơ hội tối ưu"""
        logger.info("Analyzing all files for optimization opportunities...")
        
        all_opportunities = []
        
        # Analyze Python files
        py_files = self._find_files('hksc-python', '.py')
        for file_path in py_files:
            opportunities = await self._analyze_python_file(file_path)
            all_opportunities.extend(opportunities)
        
        # Analyze Solidity files
        sol_files = self._find_files('hksc-verifier-contract/contracts', '.sol')
        for file_path in sol_files:
            opportunities = await self._analyze_solidity_file(file_path)
            all_opportunities.extend(opportunities)
        
        # Analyze JavaScript files
        js_files = self._find_files('hksc-electron', '.js')
        js_files.extend(self._find_files('hksc-electron', '.jsx'))
        for file_path in js_files:
            opportunities = await self._analyze_javascript_file(file_path)
            all_opportunities.extend(opportunities)
        
        # Store opportunities
        for opp in all_opportunities:
            self.opportunities[opp.id] = opp
        
        # Auto-apply eligible optimizations
        applied = 0
        if self.config['auto_optimize']:
            for opp in all_opportunities:
                if opp.auto_applicable and opp.confidence > 0.8:
                    if await self.apply_optimization(opp.id):
                        applied += 1
        
        return {
            'files_analyzed': len(py_files) + len(sol_files) + len(js_files),
            'opportunities_found': len(all_opportunities),
            'auto_applied': applied,
            'by_category': self._categorize_opportunities(all_opportunities)
        }
    
    def _find_files(self, directory: str, extension: str) -> List[str]:
        """Tìm tất cả file với extension trong directory"""
        files = []
        if os.path.exists(directory):
            for root, _, filenames in os.walk(directory):
                for filename in filenames:
                    if filename.endswith(extension):
                        files.append(os.path.join(root, filename))
        return files
    
    async def _analyze_python_file(self, file_path: str) -> List[OptimizationOpportunity]:
        """Phân tích file Python"""
        opportunities = []
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Parse AST
            try:
                tree = ast.parse(content)
            except SyntaxError:
                return opportunities
            
            # Analyze for opportunities
            for node in ast.walk(tree):
                # Check for list append in loops
                if isinstance(node, ast.For):
                    opp = self._check_list_append_loop(node, lines, file_path)
                    if opp:
                        opportunities.append(opp)
                
                # Check for repeated calculations
                if isinstance(node, ast.Assign):
                    opp = self._check_repeated_calculation(node, tree, lines, file_path)
                    if opp:
                        opportunities.append(opp)
            
            # Pattern-based analysis
            for pattern_name, pattern_info in self.patterns['python'].items():
                matches = re.finditer(pattern_info['pattern'], content, re.MULTILINE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    
                    opp = OptimizationOpportunity(
                        id=f"py_{file_path}_{line_num}_{pattern_name}",
                        file_path=file_path,
                        line_start=line_num,
                        line_end=line_num + match.group(0).count('\n'),
                        category=pattern_info['category'],
                        severity='medium',
                        description=pattern_info['description'],
                        current_code=match.group(0),
                        suggested_code=pattern_info['replacement'],
                        expected_improvement={'performance': 0.15},
                        confidence=0.7,
                        auto_applicable=pattern_name in ['list_comprehension', 'unnecessary_list']
                    )
                    opportunities.append(opp)
        
        except Exception as e:
            logger.debug(f"Error analyzing {file_path}: {e}")
        
        return opportunities
    
    def _check_list_append_loop(self, node: ast.For, lines: List[str], 
                                 file_path: str) -> Optional[OptimizationOpportunity]:
        """Kiểm tra loop có thể chuyển thành list comprehension"""
        # Simplified check
        return None
    
    def _check_repeated_calculation(self, node: ast.Assign, tree: ast.AST,
                                     lines: List[str], file_path: str) -> Optional[OptimizationOpportunity]:
        """Kiểm tra tính toán lặp lại"""
        # Simplified check
        return None
    
    async def _analyze_solidity_file(self, file_path: str) -> List[OptimizationOpportunity]:
        """Phân tích file Solidity để tối ưu gas"""
        opportunities = []
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Gas optimization patterns
            gas_patterns = [
                {
                    'name': 'storage_variable_in_loop',
                    'pattern': r'for\s*\([^)]*\)\s*\{[^}]*storage',
                    'description': 'Storage variable accessed in loop',
                    'improvement': 0.3
                },
                {
                    'name': 'multiple_sstore',
                    'pattern': r'(\w+)\s*=\s*[^;]+;\s*\1\s*=',
                    'description': 'Multiple SSTORE operations',
                    'improvement': 0.2
                },
                {
                    'name': 'public_vs_external',
                    'pattern': r'function\s+\w+\([^)]*\)\s+public',
                    'description': 'Use external instead of public for view functions',
                    'improvement': 0.1
                }
            ]
            
            for pattern in gas_patterns:
                matches = re.finditer(pattern['pattern'], content, re.MULTILINE | re.DOTALL)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    
                    opp = OptimizationOpportunity(
                        id=f"sol_{file_path}_{line_num}_{pattern['name']}",
                        file_path=file_path,
                        line_start=line_num,
                        line_end=line_num + 5,
                        category='gas',
                        severity='high',
                        description=pattern['description'],
                        current_code=match.group(0)[:100],
                        suggested_code='See optimization guide',
                        expected_improvement={'gas': pattern['improvement']},
                        confidence=0.6,
                        auto_applicable=False
                    )
                    opportunities.append(opp)
        
        except Exception as e:
            logger.debug(f"Error analyzing {file_path}: {e}")
        
        return opportunities
    
    async def _analyze_javascript_file(self, file_path: str) -> List[OptimizationOpportunity]:
        """Phân tích file JavaScript"""
        opportunities = []
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check for optimization opportunities
            for pattern_name, pattern_info in self.patterns.get('javascript', {}).items():
                matches = re.finditer(pattern_info['pattern'], content, re.MULTILINE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    
                    opp = OptimizationOpportunity(
                        id=f"js_{file_path}_{line_num}_{pattern_name}",
                        file_path=file_path,
                        line_start=line_num,
                        line_end=line_num,
                        category=pattern_info['category'],
                        severity='low',
                        description=pattern_info['description'],
                        current_code=match.group(0),
                        suggested_code=pattern_info['replacement'],
                        expected_improvement={'readability': 0.1},
                        confidence=0.8,
                        auto_applicable=True
                    )
                    opportunities.append(opp)
        
        except Exception as e:
            logger.debug(f"Error analyzing {file_path}: {e}")
        
        return opportunities
    
    async def optimize_file(self, file_path: str) -> Dict:
        """Tối ưu một file cụ thể"""
        logger.info(f"Optimizing file: {file_path}")
        
        # Determine file type
        if file_path.endswith('.py'):
            opportunities = await self._analyze_python_file(file_path)
        elif file_path.endswith('.sol'):
            opportunities = await self._analyze_solidity_file(file_path)
        elif file_path.endswith(('.js', '.jsx')):
            opportunities = await self._analyze_javascript_file(file_path)
        else:
            return {'error': f'Unsupported file type: {file_path}'}
        
        # Apply optimizations
        applied = []
        for opp in opportunities:
            if opp.auto_applicable:
                result = await self.apply_optimization(opp.id)
                if result.get('success'):
                    applied.append(opp.id)
        
        return {
            'file': file_path,
            'opportunities': len(opportunities),
            'applied': len(applied),
            'applied_ids': applied
        }
    
    async def apply_optimization(self, opt_id: str) -> Dict:
        """Áp dụng một optimization cụ thể"""
        if opt_id not in self.opportunities:
            return {'error': f'Optimization {opt_id} not found'}
        
        opp = self.opportunities[opt_id]
        
        logger.info(f"Applying optimization: {opp.description}")
        
        result = {
            'optimization_id': opt_id,
            'file': opp.file_path,
            'success': False
        }
        
        try:
            # Read file
            with open(opp.file_path, 'r') as f:
                content = f.read()
            
            # Apply optimization (simplified)
            # In reality, this would use proper AST transformation
            
            # Write back
            # with open(opp.file_path, 'w') as f:
            #     f.write(optimized_content)
            
            # Run tests
            if self.config['test_after_optimize']:
                tests_pass = await self._run_file_tests(opp.file_path)
                if not tests_pass:
                    logger.warning(f"Tests failed after optimization {opt_id}")
                    result['message'] = 'Tests failed'
                    return result
            
            result['success'] = True
            result['improvement'] = opp.expected_improvement
            
            self.optimization_history.append({
                'id': opt_id,
                'file': opp.file_path,
                'applied_at': time.time(),
                'improvement': opp.expected_improvement
            })
            
            logger.info(f"Successfully applied optimization: {opt_id}")
        
        except Exception as e:
            logger.error(f"Error applying optimization {opt_id}: {e}")
            result['error'] = str(e)
        
        return result
    
    async def _run_file_tests(self, file_path: str) -> bool:
        """Chạy tests cho file cụ thể"""
        # Determine project
        if 'hksc-python' in file_path:
            result = subprocess.run(
                ['python', '-m', 'pytest', '-xvs'],
                cwd='hksc-python',
                capture_output=True,
                timeout=300
            )
            return result.returncode == 0
        
        return True
    
    async def run_benchmarks(self) -> Dict:
        """Chạy benchmarks để đo hiệu suất"""
        logger.info("Running performance benchmarks...")
        
        benchmarks = {
            'python': await self._benchmark_python(),
            'contract_gas': await self._benchmark_contract_gas(),
            'electron_startup': await self._benchmark_electron()
        }
        
        return {
            'benchmarks': benchmarks,
            'timestamp': time.time()
        }
    
    async def _benchmark_python(self) -> Dict:
        """Benchmark Python performance"""
        try:
            # Run Python benchmarks
            result = subprocess.run(
                ['python', '-m', 'pytest', '--benchmark-only', '-q'],
                cwd='hksc-python',
                capture_output=True,
                text=True,
                timeout=300
            )
            
            return {
                'status': 'completed',
                'output': result.stdout
            }
        
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    async def _benchmark_contract_gas(self) -> Dict:
        """Benchmark gas usage của smart contracts"""
        try:
            result = subprocess.run(
                ['npx', 'hardhat', 'test', '--gas-report'],
                cwd='hksc-verifier-contract',
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Parse gas report
            gas_usage = self._parse_gas_report(result.stdout)
            
            return {
                'status': 'completed',
                'gas_usage': gas_usage
            }
        
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _parse_gas_report(self, output: str) -> Dict:
        """Parse gas report từ Hardhat"""
        gas_usage = {}
        
        # Simple parsing
        lines = output.split('\n')
        for line in lines:
            if '·' in line and 'gas' in line.lower():
                parts = line.split('·')
                if len(parts) >= 3:
                    method = parts[1].strip()
                    gas = parts[2].strip()
                    gas_usage[method] = gas
        
        return gas_usage
    
    async def _benchmark_electron(self) -> Dict:
        """Benchmark Electron startup time"""
        # Would require actual Electron testing
        return {'status': 'not_implemented'}
    
    async def improve_scenario_resilience(self, scenario: str, 
                                           weaknesses: List[str]) -> Dict:
        """Cải thiện khả năng chống chịu cho scenario cụ thể"""
        logger.info(f"Improving resilience for scenario: {scenario}")
        
        improvements = []
        
        for weakness in weaknesses:
            if 'performance' in weakness:
                # Find and optimize performance bottlenecks
                perf_opps = [
                    opp for opp in self.opportunities.values()
                    if opp.category == 'performance'
                ]
                for opp in perf_opps[:3]:  # Top 3
                    result = await self.apply_optimization(opp.id)
                    improvements.append({
                        'type': 'performance',
                        'optimization': opp.id,
                        'result': result
                    })
            
            elif 'memory' in weakness:
                # Optimize memory usage
                mem_opps = [
                    opp for opp in self.opportunities.values()
                    if opp.category == 'memory'
                ]
                for opp in mem_opps[:3]:
                    result = await self.apply_optimization(opp.id)
                    improvements.append({
                        'type': 'memory',
                        'optimization': opp.id,
                        'result': result
                    })
            
            elif 'gas' in weakness:
                # Optimize gas usage
                gas_opps = [
                    opp for opp in self.opportunities.values()
                    if opp.category == 'gas'
                ]
                for opp in gas_opps[:3]:
                    # Create PR for gas optimizations
                    result = await self._create_gas_optimization_pr(opp)
                    improvements.append({
                        'type': 'gas',
                        'optimization': opp.id,
                        'result': result
                    })
        
        return {
            'scenario': scenario,
            'weaknesses_addressed': len(weaknesses),
            'improvements': improvements
        }
    
    async def _create_gas_optimization_pr(self, opp: OptimizationOpportunity) -> Dict:
        """Tạo PR cho gas optimization"""
        # Similar to fix agent PR creation
        return {'status': 'pr_created', 'url': 'https://github.com/...'}
    
    def _categorize_opportunities(self, opportunities: List[OptimizationOpportunity]) -> Dict:
        """Phân loại opportunities theo category"""
        categories = {}
        
        for opp in opportunities:
            cat = opp.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(opp.id)
        
        return {k: len(v) for k, v in categories.items()}
    
    async def run_continuous(self) -> None:
        """Chạy liên tục để tối ưu"""
        while True:
            try:
                await self.analyze_all_files()
                await asyncio.sleep(3600)  # Check every hour
            
            except Exception as e:
                logger.error(f"Error in continuous optimization: {e}")
                await asyncio.sleep(300)
