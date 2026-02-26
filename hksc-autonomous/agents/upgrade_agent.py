#!/usr/bin/env python3
"""
Auto-Upgrade Agent
==================
Tự động nâng cấp dependencies, security patches, và phiên bản mới.

Chức năng:
- Theo dõi các bản cập nhật bảo mật
- Tự động cập nhật dependencies
- Rollback nếu có vấn đề
- Kiểm tra tương thích
"""

import asyncio
import json
import logging
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import xml.etree.ElementTree as ET

import aiohttp
import semver

from agents.controller import BaseAgent, Task, AgentState, TaskPriority

logger = logging.getLogger('HKSC-UpgradeAgent')


class UpgradeAgent(BaseAgent):
    """
    Agent chuyên trách việc tự động nâng cấp hệ thống.
    """
    
    def __init__(self):
        super().__init__("upgrade")
        
        # Upgrade configuration
        self.config = {
            'check_interval': 3600,  # Check for updates every hour
            'auto_upgrade_security': True,
            'auto_upgrade_patch': True,
            'auto_upgrade_minor': False,
            'auto_upgrade_major': False,
            'test_before_deploy': True,
            'rollback_on_failure': True,
            'backup_before_upgrade': True,
            'notification_channels': ['log', 'slack', 'email']
        }
        
        # Track dependencies
        self.dependencies: Dict[str, Dict] = {}
        self.upgrade_history: List[Dict] = []
        self.pending_upgrades: List[Dict] = []
        
        # Vulnerability database
        self.vulnerability_db: Dict[str, List[Dict]] = {}
        
        logger.info("UpgradeAgent initialized")
    
    async def execute(self, task: Task) -> Any:
        """Thực thi upgrade task"""
        action = task.payload.get('action', 'check_updates')
        
        if action == 'check_updates':
            return await self.check_all_updates()
        
        elif action == 'upgrade_package':
            package = task.payload.get('package')
            version = task.payload.get('version')
            return await self.upgrade_package(package, version)
        
        elif action == 'security_patch':
            return await self.apply_security_patches()
        
        elif action == 'full_upgrade':
            return await self.perform_full_upgrade()
        
        elif action == 'rollback':
            upgrade_id = task.payload.get('upgrade_id')
            return await self.rollback_upgrade(upgrade_id)
        
        else:
            return {'error': f'Unknown action: {action}'}
    
    async def check_all_updates(self) -> Dict:
        """Kiểm tra tất cả các bản cập nhật có sẵn"""
        logger.info("Checking for updates...")
        
        results = {
            'python': await self._check_python_updates(),
            'nodejs': await self._check_nodejs_updates(),
            'contracts': await self._check_contract_updates(),
            'github_actions': await self._check_github_actions_updates(),
            'timestamp': time.time()
        }
        
        # Check for security vulnerabilities
        results['security_vulnerabilities'] = await self._check_security_vulnerabilities()
        
        # Store results
        self.pending_upgrades = self._consolidate_upgrades(results)
        
        logger.info(f"Found {len(self.pending_upgrades)} pending upgrades")
        
        # Auto-apply if configured
        if self.config['auto_upgrade_security']:
            security_updates = [
                u for u in self.pending_upgrades 
                if u.get('severity') in ['critical', 'high']
            ]
            for update in security_updates:
                await self.upgrade_package(update['package'], update['latest_version'])
        
        return results
    
    async def _check_python_updates(self) -> List[Dict]:
        """Kiểm tra cập nhật Python packages"""
        updates = []
        
        try:
            # Parse requirements.txt files
            req_files = [
                'hksc-python/requirements.txt',
                'hksc-verifier-contract/requirements.txt'
            ]
            
            for req_file in req_files:
                if not os.path.exists(req_file):
                    continue
                
                with open(req_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        
                        # Parse package name and version
                        if '==' in line:
                            pkg, version = line.split('==', 1)
                        elif '>=' in line:
                            pkg, version = line.split('>=', 1)
                        else:
                            pkg = line
                            version = '0.0.0'
                        
                        pkg = pkg.strip()
                        version = version.strip()
                        
                        # Check PyPI for updates
                        latest = await self._get_pypi_version(pkg)
                        
                        if latest and semver.compare(latest, version) > 0:
                            updates.append({
                                'package': pkg,
                                'current_version': version,
                                'latest_version': latest,
                                'file': req_file,
                                'type': 'python'
                            })
        
        except Exception as e:
            logger.error(f"Error checking Python updates: {e}")
        
        return updates
    
    async def _get_pypi_version(self, package: str) -> Optional[str]:
        """Lấy phiên bản mới nhất từ PyPI"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f'https://pypi.org/pypi/{package}/json',
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data['info']['version']
        except Exception as e:
            logger.debug(f"Could not fetch PyPI version for {package}: {e}")
        
        return None
    
    async def _check_nodejs_updates(self) -> List[Dict]:
        """Kiểm tra cập nhật Node.js packages"""
        updates = []
        
        package_json_files = [
            'hksc-electron/package.json',
            'hksc-verifier-contract/package.json'
        ]
        
        for pkg_file in package_json_files:
            if not os.path.exists(pkg_file):
                continue
            
            try:
                with open(pkg_file, 'r') as f:
                    pkg_data = json.load(f)
                
                # Check dependencies
                for dep_type in ['dependencies', 'devDependencies']:
                    if dep_type not in pkg_data:
                        continue
                    
                    for pkg, version in pkg_data[dep_type].items():
                        # Remove ^ or ~ prefix
                        clean_version = version.lstrip('^~')
                        
                        # Check npm for updates
                        latest = await self._get_npm_version(pkg)
                        
                        if latest and semver.compare(latest, clean_version) > 0:
                            updates.append({
                                'package': pkg,
                                'current_version': clean_version,
                                'latest_version': latest,
                                'file': pkg_file,
                                'type': 'nodejs',
                                'dep_type': dep_type
                            })
            
            except Exception as e:
                logger.error(f"Error checking Node.js updates for {pkg_file}: {e}")
        
        return updates
    
    async def _get_npm_version(self, package: str) -> Optional[str]:
        """Lấy phiên bản mới nhất từ npm"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f'https://registry.npmjs.org/{package}',
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data['dist-tags']['latest']
        except Exception as e:
            logger.debug(f"Could not fetch npm version for {package}: {e}")
        
        return None
    
    async def _check_contract_updates(self) -> List[Dict]:
        """Kiểm tra cập nhật cho smart contract dependencies"""
        updates = []
        
        # Check Hardhat and related tools
        try:
            result = subprocess.run(
                ['npm', 'outdated', '--json'],
                cwd='hksc-verifier-contract',
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                outdated = json.loads(result.stdout)
                for pkg, info in outdated.items():
                    updates.append({
                        'package': pkg,
                        'current_version': info.get('current', 'unknown'),
                        'latest_version': info.get('latest', 'unknown'),
                        'type': 'contract_tool'
                    })
        
        except Exception as e:
            logger.error(f"Error checking contract updates: {e}")
        
        return updates
    
    async def _check_github_actions_updates(self) -> List[Dict]:
        """Kiểm tra cập nhật cho GitHub Actions"""
        updates = []
        
        workflows_dir = '.github/workflows'
        if not os.path.exists(workflows_dir):
            return updates
        
        try:
            for filename in os.listdir(workflows_dir):
                if not filename.endswith('.yml'):
                    continue
                
                filepath = os.path.join(workflows_dir, filename)
                with open(filepath, 'r') as f:
                    content = f.read()
                
                # Parse actions used
                # This is a simplified check
                if 'uses:' in content:
                    lines = content.split('\n')
                    for line in lines:
                        if 'uses:' in line:
                            # Extract action and version
                            action = line.split('uses:')[1].strip()
                            if '@' in action:
                                name, version = action.rsplit('@', 1)
                                # Check for updates (simplified)
                                if version != 'main' and version != 'master':
                                    # Would check GitHub API for latest version
                                    pass
        
        except Exception as e:
            logger.error(f"Error checking GitHub Actions updates: {e}")
        
        return updates
    
    async def _check_security_vulnerabilities(self) -> List[Dict]:
        """Kiểm tra lỗ hổng bảo mật đã biết"""
        vulnerabilities = []
        
        # Check Python dependencies with Safety
        try:
            result = subprocess.run(
                ['safety', 'check', '--json'],
                capture_output=True,
                text=True,
                cwd='hksc-python'
            )
            
            if result.returncode == 0:
                safety_data = json.loads(result.stdout)
                for vuln in safety_data.get('vulnerabilities', []):
                    vulnerabilities.append({
                        'package': vuln.get('package_name'),
                        'affected_version': vuln.get('vulnerable_spec'),
                        'fixed_version': vuln.get('fixed_versions'),
                        'severity': vuln.get('severity'),
                        'cve': vuln.get('cve'),
                        'advisory': vuln.get('advisory')
                    })
        
        except Exception as e:
            logger.error(f"Error checking Python vulnerabilities: {e}")
        
        # Check Node.js dependencies with npm audit
        try:
            for project in ['hksc-electron', 'hksc-verifier-contract']:
                result = subprocess.run(
                    ['npm', 'audit', '--json'],
                    capture_output=True,
                    text=True,
                    cwd=project
                )
                
                if result.returncode == 0:
                    audit_data = json.loads(result.stdout)
                    for vuln in audit_data.get('vulnerabilities', {}).values():
                        vulnerabilities.append({
                            'package': vuln.get('name'),
                            'severity': vuln.get('severity'),
                            'via': vuln.get('via', []),
                            'fixAvailable': vuln.get('fixAvailable'),
                            'project': project
                        })
        
        except Exception as e:
            logger.error(f"Error checking Node.js vulnerabilities: {e}")
        
        return vulnerabilities
    
    def _consolidate_upgrades(self, results: Dict) -> List[Dict]:
        """Gộp tất cả các cập nhật thành một danh sách"""
        upgrades = []
        
        for category, items in results.items():
            if category == 'timestamp':
                continue
            
            if isinstance(items, list):
                for item in items:
                    item['category'] = category
                    upgrades.append(item)
        
        # Sort by severity/priority
        severity_order = {'critical': 0, 'high': 1, 'moderate': 2, 'low': 3}
        upgrades.sort(key=lambda x: severity_order.get(x.get('severity', 'low'), 4))
        
        return upgrades
    
    async def upgrade_package(self, package: str, version: str) -> Dict:
        """Nâng cấp một package cụ thể"""
        logger.info(f"Upgrading {package} to version {version}")
        
        upgrade_record = {
            'id': f"upgrade_{int(time.time())}_{package}",
            'package': package,
            'version': version,
            'started_at': time.time(),
            'status': 'in_progress'
        }
        
        try:
            # Backup before upgrade
            if self.config['backup_before_upgrade']:
                await self._create_backup(package)
            
            # Determine package type and upgrade
            pkg_info = next(
                (u for u in self.pending_upgrades if u['package'] == package),
                None
            )
            
            if not pkg_info:
                raise ValueError(f"Package {package} not found in pending upgrades")
            
            if pkg_info['type'] == 'python':
                success = await self._upgrade_python_package(package, version, pkg_info['file'])
            
            elif pkg_info['type'] == 'nodejs':
                success = await self._upgrade_nodejs_package(package, version, pkg_info['file'])
            
            else:
                raise ValueError(f"Unknown package type: {pkg_info['type']}")
            
            # Test after upgrade
            if success and self.config['test_before_deploy']:
                test_result = await self._run_tests(pkg_info['type'])
                if not test_result:
                    logger.warning(f"Tests failed after upgrading {package}, rolling back...")
                    if self.config['rollback_on_failure']:
                        await self.rollback_upgrade(upgrade_record['id'])
                    upgrade_record['status'] = 'failed'
                    upgrade_record['error'] = 'Tests failed'
                    return upgrade_record
            
            upgrade_record['status'] = 'completed' if success else 'failed'
            upgrade_record['completed_at'] = time.time()
            
            self.upgrade_history.append(upgrade_record)
            
            logger.info(f"Upgrade {package}@{version}: {upgrade_record['status']}")
            
            return upgrade_record
        
        except Exception as e:
            logger.error(f"Error upgrading {package}: {e}")
            upgrade_record['status'] = 'failed'
            upgrade_record['error'] = str(e)
            
            if self.config['rollback_on_failure']:
                await self.rollback_upgrade(upgrade_record['id'])
            
            return upgrade_record
    
    async def _upgrade_python_package(self, package: str, version: str, 
                                       req_file: str) -> bool:
        """Nâng cấp Python package"""
        try:
            # Update requirements.txt
            with open(req_file, 'r') as f:
                lines = f.readlines()
            
            updated = False
            for i, line in enumerate(lines):
                if line.startswith(f"{package}==") or line.startswith(f"{package}>="):
                    lines[i] = f"{package}>={version}\n"
                    updated = True
                    break
            
            if updated:
                with open(req_file, 'w') as f:
                    f.writelines(lines)
            
            # Install new version
            subprocess.run(
                ['pip', 'install', f'{package}=={version}'],
                check=True,
                capture_output=True
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Error upgrading Python package {package}: {e}")
            return False
    
    async def _upgrade_nodejs_package(self, package: str, version: str,
                                       pkg_file: str) -> bool:
        """Nâng cấp Node.js package"""
        try:
            project_dir = os.path.dirname(pkg_file)
            
            # Use npm to update
            subprocess.run(
                ['npm', 'install', f'{package}@{version}'],
                cwd=project_dir,
                check=True,
                capture_output=True
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Error upgrading Node.js package {package}: {e}")
            return False
    
    async def _create_backup(self, package: str) -> str:
        """Tạo backup trước khi nâng cấp"""
        backup_dir = f"backups/upgrade_{int(time.time())}"
        os.makedirs(backup_dir, exist_ok=True)
        
        # Backup relevant files
        files_to_backup = [
            'hksc-python/requirements.txt',
            'hksc-electron/package.json',
            'hksc-electron/package-lock.json',
            'hksc-verifier-contract/package.json',
            'hksc-verifier-contract/package-lock.json'
        ]
        
        for file_path in files_to_backup:
            if os.path.exists(file_path):
                backup_path = os.path.join(backup_dir, os.path.basename(file_path))
                subprocess.run(['cp', file_path, backup_path])
        
        logger.info(f"Backup created at {backup_dir}")
        return backup_dir
    
    async def _run_tests(self, project_type: str) -> bool:
        """Chạy tests sau khi nâng cấp"""
        try:
            if project_type == 'python':
                result = subprocess.run(
                    ['python', '-m', 'pytest', '-xvs'],
                    cwd='hksc-python',
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                return result.returncode == 0
            
            elif project_type == 'nodejs':
                result = subprocess.run(
                    ['npm', 'test'],
                    cwd='hksc-electron',
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                return result.returncode == 0
            
            return True
        
        except Exception as e:
            logger.error(f"Error running tests: {e}")
            return False
    
    async def rollback_upgrade(self, upgrade_id: str) -> Dict:
        """Rollback một bản nâng cấp"""
        logger.info(f"Rolling back upgrade: {upgrade_id}")
        
        # Find backup
        backup_dirs = sorted(
            [d for d in os.listdir('backups') if d.startswith('upgrade_')],
            reverse=True
        )
        
        if not backup_dirs:
            return {'error': 'No backup found for rollback'}
        
        latest_backup = os.path.join('backups', backup_dirs[0])
        
        # Restore files
        for filename in os.listdir(latest_backup):
            backup_file = os.path.join(latest_backup, filename)
            
            # Determine original location
            if 'requirements' in filename:
                original = 'hksc-python/requirements.txt'
            elif filename == 'package.json' or filename == 'package-lock.json':
                # Need to determine which project
                continue
            else:
                continue
            
            subprocess.run(['cp', backup_file, original])
        
        # Reinstall dependencies
        subprocess.run(['pip', 'install', '-r', 'hksc-python/requirements.txt'])
        
        return {
            'upgrade_id': upgrade_id,
            'rolled_back': True,
            'backup_used': latest_backup
        }
    
    async def apply_security_patches(self) -> Dict:
        """Áp dụng tất cả các bản vá bảo mật"""
        logger.info("Applying security patches...")
        
        vulnerabilities = await self._check_security_vulnerabilities()
        
        patches_applied = []
        for vuln in vulnerabilities:
            if vuln.get('severity') in ['critical', 'high']:
                result = await self.upgrade_package(
                    vuln['package'],
                    vuln.get('fixed_version', 'latest')
                )
                patches_applied.append(result)
        
        return {
            'vulnerabilities_found': len(vulnerabilities),
            'patches_applied': len(patches_applied),
            'details': patches_applied
        }
    
    async def perform_full_upgrade(self) -> Dict:
        """Thực hiện nâng cấp toàn bộ"""
        logger.info("Starting full system upgrade...")
        
        # Check all updates
        updates = await self.check_all_updates()
        
        # Apply all pending upgrades
        results = []
        for upgrade in self.pending_upgrades:
            if upgrade.get('auto_upgrade', False):
                result = await self.upgrade_package(
                    upgrade['package'],
                    upgrade['latest_version']
                )
                results.append(result)
        
        return {
            'total_upgrades': len(results),
            'successful': sum(1 for r in results if r['status'] == 'completed'),
            'failed': sum(1 for r in results if r['status'] == 'failed'),
            'details': results
        }
    
    async def run_continuous(self) -> None:
        """Chạy liên tục để kiểm tra và nâng cấp"""
        while True:
            try:
                await self.check_all_updates()
                await asyncio.sleep(self.config['check_interval'])
            
            except Exception as e:
                logger.error(f"Error in continuous upgrade check: {e}")
                await asyncio.sleep(60)
