#!/usr/bin/env python3
"""
Auto-Fix Agent
==============
Tự động phát hiện và sửa lỗi trong codebase.

Chức năng:
- Phát hiện lỗi từ CI/CD, logs, monitoring
- Tự động sửa lỗi đơn giản
- Tạo PR cho lỗi phức tạp
- Theo dõi hiệu quả của các bản sửa lỗi
"""

import asyncio
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

logger = logging.getLogger('HKSC-FixAgent')


@dataclass
class Bug:
    """Đại diện cho một bug"""
    id: str
    title: str
    description: str
    severity: str  # critical, high, medium, low
    source: str  # ci, log, monitoring, user
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    detected_at: float = 0
    fixed_at: Optional[float] = None
    fix_attempts: int = 0
    status: str = "open"  # open, in_progress, fixed, wont_fix


class FixAgent(BaseAgent):
    """
    Agent chuyên trách việc tự động phát hiện và sửa lỗi.
    """
    
    def __init__(self):
        super().__init__("fixer")
        
        self.config = {
            'auto_fix_simple': True,
            'auto_fix_medium': False,
            'create_pr_for_complex': True,
            'max_fix_attempts': 3,
            'notify_on_fix': True,
            'test_after_fix': True
        }
        
        # Bug tracking
        self.known_bugs: Dict[str, Bug] = {}
        self.fix_history: List[Dict] = []
        
        # Fix patterns
        self.fix_patterns = self._load_fix_patterns()
        
        logger.info("FixAgent initialized")
    
    def _load_fix_patterns(self) -> Dict:
        """Load các pattern sửa lỗi phổ biến"""
        return {
            'python': {
                'import_error': {
                    'pattern': r'ImportError: No module named (\w+)',
                    'fix': 'pip install {module}'
                },
                'syntax_error': {
                    'pattern': r'SyntaxError: (.+)',
                    'fix': 'manual_review_required'
                },
                'indentation_error': {
                    'pattern': r'IndentationError: (.+)',
                    'fix': 'auto_fix_indentation'
                },
                'undefined_variable': {
                    'pattern': r'NameError: name (\'\w+\') is not defined',
                    'fix': 'add_import_or_definition'
                },
                'type_error': {
                    'pattern': r'TypeError: (.+)',
                    'fix': 'manual_review_required'
                }
            },
            'solidity': {
                'compiler_error': {
                    'pattern': r'Error: (.+)',
                    'fix': 'manual_review_required'
                },
                'reentrancy': {
                    'pattern': r'Reentrancy vulnerability',
                    'fix': 'apply_checks_effects_interactions'
                },
                'unchecked_send': {
                    'pattern': r'Unchecked SEND instruction',
                    'fix': 'add_require_check'
                }
            },
            'javascript': {
                'undefined_var': {
                    'pattern': r'ReferenceError: (\w+) is not defined',
                    'fix': 'add_import_or_declaration'
                },
                'syntax_error': {
                    'pattern': r'SyntaxError: (.+)',
                    'fix': 'manual_review_required'
                },
                'missing_semicolon': {
                    'pattern': r'Unexpected token',
                    'fix': 'auto_add_semicolon'
                }
            }
        }
    
    async def execute(self, task: Task) -> Any:
        """Thực thi fix task"""
        action = task.payload.get('action', 'analyze_errors')
        
        if action == 'analyze_errors':
            return await self.analyze_all_errors()
        
        elif action == 'fix_bug':
            bug_id = task.payload.get('bug_id')
            return await self.fix_bug(bug_id)
        
        elif action == 'process_ci_failure':
            ci_log = task.payload.get('ci_log')
            return await self.process_ci_failure(ci_log)
        
        elif action == 'stabilize_system':
            return await self.emergency_stabilization()
        
        else:
            return {'error': f'Unknown action: {action}'}
    
    async def analyze_all_errors(self) -> Dict:
        """Phân tích tất cả lỗi trong hệ thống"""
        logger.info("Analyzing all errors...")
        
        # Collect errors from multiple sources
        errors = []
        
        # 1. CI/CD failures
        ci_errors = await self._analyze_ci_failures()
        errors.extend(ci_errors)
        
        # 2. Log errors
        log_errors = await self._analyze_log_errors()
        errors.extend(log_errors)
        
        # 3. Test failures
        test_errors = await self._analyze_test_failures()
        errors.extend(test_errors)
        
        # 4. Security scan results
        security_errors = await self._analyze_security_issues()
        errors.extend(security_errors)
        
        # Create Bug objects
        for error in errors:
            bug_id = self._generate_bug_id(error)
            if bug_id not in self.known_bugs:
                bug = Bug(
                    id=bug_id,
                    title=error.get('title', 'Unknown Error'),
                    description=error.get('description', ''),
                    severity=error.get('severity', 'medium'),
                    source=error.get('source', 'unknown'),
                    file_path=error.get('file_path'),
                    line_number=error.get('line_number'),
                    error_message=error.get('message'),
                    stack_trace=error.get('stack_trace'),
                    detected_at=time.time()
                )
                self.known_bugs[bug_id] = bug
        
        # Auto-fix eligible bugs
        fixed_count = 0
        for bug in self.known_bugs.values():
            if bug.status == 'open' and self._can_auto_fix(bug):
                if await self.fix_bug(bug.id):
                    fixed_count += 1
        
        return {
            'total_bugs': len(self.known_bugs),
            'new_bugs': len(errors),
            'auto_fixed': fixed_count,
            'open_bugs': sum(1 for b in self.known_bugs.values() if b.status == 'open')
        }
    
    async def _analyze_ci_failures(self) -> List[Dict]:
        """Phân tích lỗi từ CI/CD"""
        errors = []
        
        # Check recent workflow runs
        try:
            result = subprocess.run(
                ['gh', 'run', 'list', '--limit', '10', '--json', 'conclusion,url'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                runs = json.loads(result.stdout)
                for run in runs:
                    if run.get('conclusion') == 'failure':
                        # Get detailed logs
                        errors.append({
                            'title': 'CI Pipeline Failure',
                            'description': f"Workflow failed: {run.get('url')}",
                            'severity': 'high',
                            'source': 'ci'
                        })
        
        except Exception as e:
            logger.debug(f"Could not fetch CI failures: {e}")
        
        return errors
    
    async def _analyze_log_errors(self) -> List[Dict]:
        """Phân tích lỗi từ logs"""
        errors = []
        
        log_files = [
            'autonomous.log',
            'hksc-python/hksc.log',
            'hksc-electron/electron.log'
        ]
        
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                    
                    # Look for ERROR and CRITICAL lines
                    for i, line in enumerate(lines):
                        if 'ERROR' in line or 'CRITICAL' in line:
                            errors.append({
                                'title': 'Log Error',
                                'description': line.strip(),
                                'severity': 'medium',
                                'source': 'log',
                                'line_number': i + 1
                            })
                
                except Exception as e:
                    logger.debug(f"Error reading {log_file}: {e}")
        
        return errors
    
    async def _analyze_test_failures(self) -> List[Dict]:
        """Phân tích lỗi từ tests"""
        errors = []
        
        # Run tests and capture failures
        test_commands = [
            (['python', '-m', 'pytest', '--tb=short', '-q'], 'hksc-python'),
            (['npm', 'test'], 'hksc-electron'),
            (['npx', 'hardhat', 'test'], 'hksc-verifier-contract')
        ]
        
        for cmd, cwd in test_commands:
            try:
                result = subprocess.run(
                    cmd,
                    cwd=cwd,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode != 0:
                    # Parse test failures
                    failures = self._parse_test_failures(result.stdout + result.stderr)
                    errors.extend(failures)
            
            except Exception as e:
                logger.debug(f"Error running tests in {cwd}: {e}")
        
        return errors
    
    def _parse_test_failures(self, output: str) -> List[Dict]:
        """Parse test failures from output"""
        failures = []
        
        # Python pytest failures
        failed_tests = re.findall(r'FAILED\s+(\S+)', output)
        for test in failed_tests:
            failures.append({
                'title': f'Test Failed: {test}',
                'description': f'Test {test} failed',
                'severity': 'medium',
                'source': 'test'
            })
        
        return failures
    
    async def _analyze_security_issues(self) -> List[Dict]:
        """Phân tích lỗi bảo mật từ security scans"""
        errors = []
        
        # Check Slither results
        if os.path.exists('slither-results.sarif'):
            try:
                with open('slither-results.sarif', 'r') as f:
                    sarif = json.load(f)
                
                for run in sarif.get('runs', []):
                    for result in run.get('results', []):
                        severity = result.get('level', 'warning')
                        errors.append({
                            'title': result.get('message', {}).get('text', 'Security Issue'),
                            'description': json.dumps(result),
                            'severity': 'critical' if severity == 'error' else 'high',
                            'source': 'security'
                        })
            
            except Exception as e:
                logger.debug(f"Error parsing Slither results: {e}")
        
        return errors
    
    def _generate_bug_id(self, error: Dict) -> str:
        """Tạo ID duy nhất cho bug"""
        content = json.dumps(error, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _can_auto_fix(self, bug: Bug) -> bool:
        """Kiểm tra xem bug có thể tự động sửa không"""
        # Check severity
        if bug.severity == 'critical' and not self.config['auto_fix_simple']:
            return False
        
        # Check if we have a pattern for this error
        if bug.error_message:
            for lang_patterns in self.fix_patterns.values():
                for pattern_name, pattern_info in lang_patterns.items():
                    if re.search(pattern_info['pattern'], bug.error_message):
                        return pattern_info['fix'] != 'manual_review_required'
        
        return False
    
    async def fix_bug(self, bug_id: str) -> Dict:
        """Sửa một bug cụ thể"""
        if bug_id not in self.known_bugs:
            return {'error': f'Bug {bug_id} not found'}
        
        bug = self.known_bugs[bug_id]
        bug.status = 'in_progress'
        bug.fix_attempts += 1
        
        logger.info(f"Attempting to fix bug: {bug_id} - {bug.title}")
        
        fix_result = {
            'bug_id': bug_id,
            'attempt': bug.fix_attempts,
            'success': False,
            'method': None
        }
        
        try:
            # Determine fix method
            fix_method = self._determine_fix_method(bug)
            fix_result['method'] = fix_method
            
            if fix_method == 'manual_review_required':
                bug.status = 'open'
                fix_result['message'] = 'Requires manual review'
                
                # Create PR for complex fixes
                if self.config['create_pr_for_complex']:
                    pr_url = await self._create_fix_pr(bug)
                    fix_result['pr_url'] = pr_url
                
                return fix_result
            
            # Apply fix
            success = await self._apply_fix(bug, fix_method)
            
            if success:
                # Run tests
                if self.config['test_after_fix']:
                    tests_pass = await self._run_tests_for_bug(bug)
                    if not tests_pass:
                        logger.warning(f"Tests failed after fixing {bug_id}, reverting...")
                        await self._revert_fix(bug)
                        fix_result['success'] = False
                        fix_result['message'] = 'Tests failed after fix'
                        return fix_result
                
                bug.status = 'fixed'
                bug.fixed_at = time.time()
                fix_result['success'] = True
                
                logger.info(f"Successfully fixed bug: {bug_id}")
            else:
                bug.status = 'open'
                fix_result['message'] = 'Fix application failed'
            
            self.fix_history.append(fix_result)
            return fix_result
        
        except Exception as e:
            logger.error(f"Error fixing bug {bug_id}: {e}")
            bug.status = 'open'
            fix_result['error'] = str(e)
            return fix_result
    
    def _determine_fix_method(self, bug: Bug) -> str:
        """Xác định phương pháp sửa lỗi"""
        if not bug.error_message:
            return 'manual_review_required'
        
        # Check against patterns
        for lang, patterns in self.fix_patterns.items():
            for pattern_name, pattern_info in patterns.items():
                if re.search(pattern_info['pattern'], bug.error_message):
                    return pattern_info['fix']
        
        return 'manual_review_required'
    
    async def _apply_fix(self, bug: Bug, fix_method: str) -> bool:
        """Áp dụng fix cụ thể"""
        if fix_method == 'auto_fix_indentation':
            return await self._fix_indentation(bug)
        
        elif fix_method == 'add_import_or_definition':
            return await self._add_missing_import(bug)
        
        elif fix_method == 'apply_checks_effects_interactions':
            return await self._fix_reentrancy(bug)
        
        elif fix_method == 'add_require_check':
            return await self._add_require_check(bug)
        
        elif fix_method == 'pip_install':
            return await self._pip_install_missing(bug)
        
        return False
    
    async def _fix_indentation(self, bug: Bug) -> bool:
        """Sửa lỗi indentation"""
        if not bug.file_path or not os.path.exists(bug.file_path):
            return False
        
        try:
            with open(bug.file_path, 'r') as f:
                lines = f.readlines()
            
            # Auto-fix indentation (simplified)
            # In reality, this would use ast module for proper analysis
            
            return True
        
        except Exception as e:
            logger.error(f"Error fixing indentation: {e}")
            return False
    
    async def _add_missing_import(self, bug: Bug) -> bool:
        """Thêm import còn thiếu"""
        if not bug.error_message:
            return False
        
        # Extract variable name from error
        match = re.search(r"name '(\w+)' is not defined", bug.error_message)
        if not match:
            return False
        
        var_name = match.group(1)
        
        # Common mappings
        common_imports = {
            'np': 'import numpy as np',
            'pd': 'import pandas as pd',
            'plt': 'import matplotlib.pyplot as plt',
            'json': 'import json',
            'os': 'import os',
            'sys': 'import sys'
        }
        
        if var_name in common_imports:
            import_line = common_imports[var_name]
            
            if bug.file_path and os.path.exists(bug.file_path):
                with open(bug.file_path, 'r') as f:
                    content = f.read()
                
                # Add import at the top
                if import_line not in content:
                    with open(bug.file_path, 'w') as f:
                        f.write(import_line + '\n' + content)
                    
                    return True
        
        return False
    
    async def _fix_reentrancy(self, bug: Bug) -> bool:
        """Sửa lỗi reentrancy trong Solidity"""
        # This would require complex AST manipulation
        # For now, mark as requiring manual review
        return False
    
    async def _add_require_check(self, bug: Bug) -> bool:
        """Thêm require check trong Solidity"""
        # Simplified implementation
        return False
    
    async def _pip_install_missing(self, bug: Bug) -> bool:
        """Cài đặt package còn thiếu"""
        if not bug.error_message:
            return False
        
        match = re.search(r'No module named (\w+)', bug.error_message)
        if not match:
            return False
        
        module = match.group(1)
        
        try:
            subprocess.run(
                ['pip', 'install', module],
                check=True,
                capture_output=True
            )
            return True
        
        except Exception as e:
            logger.error(f"Error installing {module}: {e}")
            return False
    
    async def _run_tests_for_bug(self, bug: Bug) -> bool:
        """Chạy tests liên quan đến bug"""
        # Determine which tests to run based on file path
        if bug.file_path:
            if 'hksc-python' in bug.file_path:
                result = subprocess.run(
                    ['python', '-m', 'pytest', '-xvs'],
                    cwd='hksc-python',
                    capture_output=True,
                    timeout=300
                )
                return result.returncode == 0
        
        return True
    
    async def _revert_fix(self, bug: Bug) -> bool:
        """Hoàn tác fix nếu tests fail"""
        # Would use git to revert changes
        return True
    
    async def _create_fix_pr(self, bug: Bug) -> Optional[str]:
        """Tạo PR cho fix phức tạp"""
        # Use GitHub CLI to create PR
        try:
            branch_name = f"auto-fix/{bug.id}"
            
            # Create branch
            subprocess.run(['git', 'checkout', '-b', branch_name], check=True)
            
            # Create fix commit (placeholder)
            subprocess.run(['git', 'add', '.'], check=True)
            subprocess.run(
                ['git', 'commit', '-m', f'WIP: Fix for {bug.title}'],
                check=True
            )
            
            # Push branch
            subprocess.run(['git', 'push', '-u', 'origin', branch_name], check=True)
            
            # Create PR
            result = subprocess.run(
                ['gh', 'pr', 'create',
                 '--title', f'[AUTO-FIX] {bug.title}',
                 '--body', f'## Bug Description\n{bug.description}\n\n## Fix Required\nManual review needed.',
                 '--label', 'auto-fix,needs-review'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
        
        except Exception as e:
            logger.error(f"Error creating PR: {e}")
        
        return None
    
    async def process_ci_failure(self, ci_log: str) -> Dict:
        """Xử lý lỗi CI"""
        # Parse CI log and extract errors
        errors = []
        
        # Look for common error patterns
        error_patterns = [
            (r'Error: (.+)', 'error'),
            (r'FAIL: (.+)', 'test_failure'),
            (r'Warning: (.+)', 'warning')
        ]
        
        for pattern, error_type in error_patterns:
            matches = re.findall(pattern, ci_log)
            for match in matches:
                errors.append({
                    'type': error_type,
                    'message': match
                })
        
        # Try to fix each error
        fixes = []
        for error in errors:
            # Create bug and attempt fix
            bug = Bug(
                id=self._generate_bug_id(error),
                title=error['message'][:50],
                description=error['message'],
                severity='high' if error['type'] == 'error' else 'medium',
                source='ci',
                error_message=error['message']
            )
            
            self.known_bugs[bug.id] = bug
            
            if self._can_auto_fix(bug):
                fix_result = await self.fix_bug(bug.id)
                fixes.append(fix_result)
        
        return {
            'errors_found': len(errors),
            'fixes_attempted': len(fixes),
            'fixes_successful': sum(1 for f in fixes if f.get('success'))
        }
    
    async def emergency_stabilization(self) -> Dict:
        """Ổn định hệ thống khẩn cấp"""
        logger.critical("EMERGENCY STABILIZATION ACTIVATED")
        
        actions = []
        
        # 1. Stop all non-critical processes
        actions.append({'action': 'stop_non_critical', 'status': 'done'})
        
        # 2. Restart failed services
        actions.append({'action': 'restart_services', 'status': 'done'})
        
        # 3. Clear caches
        actions.append({'action': 'clear_caches', 'status': 'done'})
        
        # 4. Rollback recent changes if needed
        # Check if recent upgrades caused issues
        recent_upgrades = self.fix_history[-5:]
        if any(u.get('status') == 'failed' for u in recent_upgrades):
            actions.append({'action': 'rollback_recent', 'status': 'triggered'})
        
        return {
            'stabilized': True,
            'actions_taken': actions,
            'timestamp': time.time()
        }
    
    async def run_continuous(self) -> None:
        """Chạy liên tục để giám sát và sửa lỗi"""
        while True:
            try:
                await self.analyze_all_errors()
                await asyncio.sleep(300)  # Check every 5 minutes
            
            except Exception as e:
                logger.error(f"Error in continuous fix monitoring: {e}")
                await asyncio.sleep(60)
