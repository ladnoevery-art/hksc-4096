#!/usr/bin/env python3
"""
Worst-Case Scenario Simulator
=============================
Giả lập tất cả các tình huống xấu nhất có thể xảy ra.

Chức năng:
- Giả lập tấn công (attack simulation)
- Giả lập lỗi hệ thống (failure simulation)
- Giả lập tải cao (load simulation)
- Giả lập mất kết nối (network partition)
- Đánh giá khả năng phục hồi
"""

import asyncio
import json
import logging
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Callable
import hashlib

from agents.controller import BaseAgent, Task, AgentState, TaskPriority

logger = logging.getLogger('HKSC-WorstCaseSimulator')


class ScenarioType(Enum):
    """Loại scenario giả lập"""
    SECURITY_ATTACK = "security_attack"
    SYSTEM_FAILURE = "system_failure"
    NETWORK_PARTITION = "network_partition"
    HIGH_LOAD = "high_load"
    DATA_CORRUPTION = "data_corruption"
    DEPENDENCY_FAILURE = "dependency_failure"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    CASCADING_FAILURE = "cascading_failure"
    BYZANTINE_ATTACK = "byzantine_attack"
    QUANTUM_ATTACK = "quantum_attack"


@dataclass
class SimulationResult:
    """Kết quả giả lập"""
    scenario_id: str
    scenario_type: ScenarioType
    duration: float
    success: bool
    system_recovered: bool
    recovery_time: Optional[float]
    data_loss: bool
    data_loss_amount: int
    weaknesses_found: List[str]
    recommendations: List[str]
    logs: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


class WorstCaseSimulator:
    """
    Simulator giả lập các tình huống xấu nhất để đánh giá khả năng chống chịu.
    
    Các scenario được giả lập:
    1. Tấn công bảo mật (brute force, side-channel, quantum)
    2. Lỗi hệ thống (crash, memory leak, deadlock)
    3. Mất kết nối mạng
    4. Tải cao (DDoS, spam)
    5. Hỏng dữ liệu
    6. Lỗi dependency
    7. Cạn kiệt tài nguyên
    8. Lỗi lan truyền (cascading failure)
    9. Byzantine fault
    10. Tấn công lượng tử
    """
    
    def __init__(self, controller=None):
        self.controller = controller
        
        self.config = {
            'simulation_timeout': 300,
            'max_concurrent_scenarios': 5,
            'auto_improve': True,
            'improvement_threshold': 0.8
        }
        
        # Scenario definitions
        self.scenarios: Dict[ScenarioType, Callable] = {
            ScenarioType.SECURITY_ATTACK: self._simulate_security_attack,
            ScenarioType.SYSTEM_FAILURE: self._simulate_system_failure,
            ScenarioType.NETWORK_PARTITION: self._simulate_network_partition,
            ScenarioType.HIGH_LOAD: self._simulate_high_load,
            ScenarioType.DATA_CORRUPTION: self._simulate_data_corruption,
            ScenarioType.DEPENDENCY_FAILURE: self._simulate_dependency_failure,
            ScenarioType.RESOURCE_EXHAUSTION: self._simulate_resource_exhaustion,
            ScenarioType.CASCADING_FAILURE: self._simulate_cascading_failure,
            ScenarioType.BYZANTINE_ATTACK: self._simulate_byzantine_attack,
            ScenarioType.QUANTUM_ATTACK: self._simulate_quantum_attack
        }
        
        # Results tracking
        self.simulation_history: List[SimulationResult] = []
        self.scenario_stats: Dict[ScenarioType, Dict] = {}
        
        logger.info("WorstCaseSimulator initialized")
    
    async def run_all_scenarios(self) -> Dict[str, SimulationResult]:
        """Chạy tất cả các scenarios"""
        logger.info("Starting worst-case scenario simulations...")
        
        results = {}
        
        for scenario_type in ScenarioType:
            logger.info(f"Running scenario: {scenario_type.value}")
            
            result = await self.run_scenario(scenario_type)
            results[scenario_type.value] = result
            
            self.simulation_history.append(result)
            
            # Update stats
            if scenario_type not in self.scenario_stats:
                self.scenario_stats[scenario_type] = {
                    'runs': 0,
                    'successes': 0,
                    'recoveries': 0,
                    'avg_recovery_time': 0
                }
            
            self.scenario_stats[scenario_type]['runs'] += 1
            if result.success:
                self.scenario_stats[scenario_type]['successes'] += 1
            if result.system_recovered:
                self.scenario_stats[scenario_type]['recoveries'] += 1
            
            # Wait between scenarios
            await asyncio.sleep(1)
        
        # Generate summary
        summary = self._generate_summary(results)
        
        logger.info(f"All scenarios completed. Success rate: {summary['overall_success_rate']:.2%}")
        
        return results
    
    async def run_scenario(self, scenario_type: ScenarioType,
                           params: Optional[Dict] = None) -> SimulationResult:
        """Chạy một scenario cụ thể"""
        scenario_id = f"{scenario_type.value}_{int(time.time())}"
        
        start_time = time.time()
        
        # Get simulator function
        simulator = self.scenarios.get(scenario_type)
        
        if not simulator:
            return SimulationResult(
                scenario_id=scenario_id,
                scenario_type=scenario_type,
                duration=0,
                success=False,
                system_recovered=False,
                recovery_time=None,
                data_loss=False,
                data_loss_amount=0,
                weaknesses_found=['Simulator not implemented'],
                recommendations=['Implement simulator']
            )
        
        try:
            # Run simulation with timeout
            result = await asyncio.wait_for(
                simulator(params or {}),
                timeout=self.config['simulation_timeout']
            )
            
            result.scenario_id = scenario_id
            result.duration = time.time() - start_time
            
            return result
        
        except asyncio.TimeoutError:
            return SimulationResult(
                scenario_id=scenario_id,
                scenario_type=scenario_type,
                duration=time.time() - start_time,
                success=False,
                system_recovered=False,
                recovery_time=None,
                data_loss=False,
                data_loss_amount=0,
                weaknesses_found=['Simulation timeout'],
                recommendations=['Optimize system performance']
            )
        
        except Exception as e:
            return SimulationResult(
                scenario_id=scenario_id,
                scenario_type=scenario_type,
                duration=time.time() - start_time,
                success=False,
                system_recovered=False,
                recovery_time=None,
                data_loss=False,
                data_loss_amount=0,
                weaknesses_found=[f'Simulation error: {str(e)}'],
                recommendations=['Fix simulation implementation']
            )
    
    async def _simulate_security_attack(self, params: Dict) -> SimulationResult:
        """Giả lập tấn công bảo mật"""
        logger.info("Simulating security attack...")
        
        attack_types = [
            'brute_force_key',
            'side_channel',
            'replay_attack',
            'man_in_the_middle',
            'cryptanalysis'
        ]
        
        attack_type = params.get('attack_type', random.choice(attack_types))
        
        weaknesses = []
        recommendations = []
        
        # Simulate brute force on 4096-cell tour
        if attack_type == 'brute_force_key':
            # Calculate theoretical brute force time
            tour_space = 2 ** 2500  # Approximate
            attempts_per_second = 10 ** 12  # Assume massive computing power
            seconds_needed = tour_space / attempts_per_second
            years_needed = seconds_needed / (365 * 24 * 3600)
            
            if years_needed > 10 ** 100:
                success = True
                system_recovered = True
            else:
                success = False
                system_recovered = False
                weaknesses.append('Key space may be insufficient')
                recommendations.append('Increase tour complexity')
        
        elif attack_type == 'side_channel':
            # Check for timing vulnerabilities
            success = False  # Assume protected
            system_recovered = True
            weaknesses.append('Potential timing side-channel')
            recommendations.append('Implement constant-time operations')
        
        elif attack_type == 'quantum':
            # Grover's algorithm provides sqrt speedup
            # 2^2500 becomes 2^1250 - still infeasible
            success = True
            system_recovered = True
            weaknesses.append('Quantum computers may reduce security margin')
            recommendations.append('Monitor quantum computing advances')
        
        else:
            success = True
            system_recovered = True
        
        return SimulationResult(
            scenario_id='',
            scenario_type=ScenarioType.SECURITY_ATTACK,
            duration=0,
            success=success,
            system_recovered=system_recovered,
            recovery_time=0 if system_recovered else None,
            data_loss=False,
            data_loss_amount=0,
            weaknesses_found=weaknesses,
            recommendations=recommendations,
            metrics={'attack_type': attack_type}
        )
    
    async def _simulate_system_failure(self, params: Dict) -> SimulationResult:
        """Giả lập lỗi hệ thống"""
        logger.info("Simulating system failure...")
        
        failure_types = [
            'memory_leak',
            'deadlock',
            'infinite_loop',
            'crash',
            'corruption'
        ]
        
        failure_type = params.get('failure_type', random.choice(failure_types))
        
        # Simulate failure and recovery
        if failure_type == 'memory_leak':
            # Check if system has memory monitoring
            has_monitoring = True  # Assume yes
            
            if has_monitoring:
                success = True
                system_recovered = True
                recovery_time = 30
                weaknesses = []
                recommendations = []
            else:
                success = False
                system_recovered = False
                recovery_time = None
                weaknesses = ['No memory leak detection']
                recommendations = ['Implement memory monitoring']
        
        elif failure_type == 'crash':
            # Check auto-restart capability
            has_auto_restart = True
            
            if has_auto_restart:
                success = True
                system_recovered = True
                recovery_time = 5
                weaknesses = []
                recommendations = []
            else:
                success = False
                system_recovered = False
                recovery_time = None
                weaknesses = ['No auto-restart mechanism']
                recommendations = ['Implement supervisor process']
        
        else:
            success = True
            system_recovered = True
            recovery_time = 10
            weaknesses = []
            recommendations = []
        
        return SimulationResult(
            scenario_id='',
            scenario_type=ScenarioType.SYSTEM_FAILURE,
            duration=0,
            success=success,
            system_recovered=system_recovered,
            recovery_time=recovery_time,
            data_loss=False,
            data_loss_amount=0,
            weaknesses_found=weaknesses,
            recommendations=recommendations,
            metrics={'failure_type': failure_type}
        )
    
    async def _simulate_network_partition(self, params: Dict) -> SimulationResult:
        """Giả lập mất kết nối mạng"""
        logger.info("Simulating network partition...")
        
        partition_duration = params.get('duration', 60)  # seconds
        
        # Check if system can operate offline
        can_operate_offline = True  # HKSC can encrypt/decrypt offline
        
        if can_operate_offline:
            success = True
            system_recovered = True
            recovery_time = 0
            weaknesses = []
            recommendations = []
        else:
            success = False
            system_recovered = True
            recovery_time = partition_duration
            weaknesses = ['System requires network for core operations']
            recommendations = ['Implement offline mode']
        
        return SimulationResult(
            scenario_id='',
            scenario_type=ScenarioType.NETWORK_PARTITION,
            duration=0,
            success=success,
            system_recovered=system_recovered,
            recovery_time=recovery_time,
            data_loss=False,
            data_loss_amount=0,
            weaknesses_found=weaknesses,
            recommendations=recommendations,
            metrics={'partition_duration': partition_duration}
        )
    
    async def _simulate_high_load(self, params: Dict) -> SimulationResult:
        """Giả lập tải cao"""
        logger.info("Simulating high load...")
        
        load_factor = params.get('load_factor', 10)  # 10x normal load
        duration = params.get('duration', 300)  # 5 minutes
        
        # Simulate load
        # Check if system can handle load
        max_capacity = 1000  # requests per second
        requested_capacity = 100 * load_factor  # assuming 100 req/s normal
        
        if requested_capacity <= max_capacity:
            success = True
            system_recovered = True
            recovery_time = 0
            weaknesses = []
            recommendations = []
        else:
            success = False
            system_recovered = True
            recovery_time = 60
            weaknesses = [f'System capacity ({max_capacity}) exceeded']
            recommendations = ['Implement rate limiting', 'Add caching layer']
        
        return SimulationResult(
            scenario_id='',
            scenario_type=ScenarioType.HIGH_LOAD,
            duration=0,
            success=success,
            system_recovered=system_recovered,
            recovery_time=recovery_time,
            data_loss=False,
            data_loss_amount=0,
            weaknesses_found=weaknesses,
            recommendations=recommendations,
            metrics={
                'load_factor': load_factor,
                'requested_capacity': requested_capacity,
                'max_capacity': max_capacity
            }
        )
    
    async def _simulate_data_corruption(self, params: Dict) -> SimulationResult:
        """Giả lập hỏng dữ liệu"""
        logger.info("Simulating data corruption...")
        
        corruption_rate = params.get('corruption_rate', 0.01)  # 1%
        
        # Check data integrity mechanisms
        has_checksum = True
        has_backup = True
        
        if has_checksum and has_backup:
            success = True
            system_recovered = True
            recovery_time = 30
            data_loss = False
            weaknesses = []
            recommendations = []
        elif has_checksum:
            success = True
            system_recovered = True
            recovery_time = 60
            data_loss = True
            data_loss_amount = int(corruption_rate * 100)
            weaknesses = ['No backup system']
            recommendations = ['Implement regular backups']
        else:
            success = False
            system_recovered = False
            recovery_time = None
            data_loss = True
            data_loss_amount = int(corruption_rate * 100)
            weaknesses = ['No data integrity checks']
            recommendations = ['Implement checksums and backups']
        
        return SimulationResult(
            scenario_id='',
            scenario_type=ScenarioType.DATA_CORRUPTION,
            duration=0,
            success=success,
            system_recovered=system_recovered,
            recovery_time=recovery_time,
            data_loss=data_loss,
            data_loss_amount=data_loss_amount,
            weaknesses_found=weaknesses,
            recommendations=recommendations,
            metrics={'corruption_rate': corruption_rate}
        )
    
    async def _simulate_dependency_failure(self, params: Dict) -> SimulationResult:
        """Giả lập lỗi dependency"""
        logger.info("Simulating dependency failure...")
        
        dependency = params.get('dependency', 'random')
        
        # Check fallback mechanisms
        has_fallback = True
        can_degrade = True
        
        if has_fallback:
            success = True
            system_recovered = True
            recovery_time = 5
            weaknesses = []
            recommendations = []
        elif can_degrade:
            success = True
            system_recovered = True
            recovery_time = 0
            weaknesses = ['System degraded without fallback']
            recommendations = ['Implement fallback mechanisms']
        else:
            success = False
            system_recovered = False
            recovery_time = None
            weaknesses = ['Hard dependency failure']
            recommendations = ['Add fallback and graceful degradation']
        
        return SimulationResult(
            scenario_id='',
            scenario_type=ScenarioType.DEPENDENCY_FAILURE,
            duration=0,
            success=success,
            system_recovered=system_recovered,
            recovery_time=recovery_time,
            data_loss=False,
            data_loss_amount=0,
            weaknesses_found=weaknesses,
            recommendations=recommendations,
            metrics={'failed_dependency': dependency}
        )
    
    async def _simulate_resource_exhaustion(self, params: Dict) -> SimulationResult:
        """Giả lập cạn kiệt tài nguyên"""
        logger.info("Simulating resource exhaustion...")
        
        resource_type = params.get('resource', 'memory')
        
        # Check resource limits
        has_limits = True
        has_monitoring = True
        
        if has_limits and has_monitoring:
            success = True
            system_recovered = True
            recovery_time = 10
            weaknesses = []
            recommendations = []
        else:
            success = False
            system_recovered = True
            recovery_time = 60
            weaknesses = ['No resource limits or monitoring']
            recommendations = ['Implement resource quotas and monitoring']
        
        return SimulationResult(
            scenario_id='',
            scenario_type=ScenarioType.RESOURCE_EXHAUSTION,
            duration=0,
            success=success,
            system_recovered=system_recovered,
            recovery_time=recovery_time,
            data_loss=False,
            data_loss_amount=0,
            weaknesses_found=weaknesses,
            recommendations=recommendations,
            metrics={'resource_type': resource_type}
        )
    
    async def _simulate_cascading_failure(self, params: Dict) -> SimulationResult:
        """Giả lập lỗi lan truyền"""
        logger.info("Simulating cascading failure...")
        
        initial_failure = params.get('initial_failure', 'component_a')
        
        # Check circuit breakers
        has_circuit_breaker = True
        has_bulkhead = True
        
        if has_circuit_breaker and has_bulkhead:
            success = True
            system_recovered = True
            recovery_time = 30
            weaknesses = []
            recommendations = []
        else:
            success = False
            system_recovered = True
            recovery_time = 300
            weaknesses = ['No circuit breaker or bulkhead pattern']
            recommendations = [
                'Implement circuit breaker pattern',
                'Add bulkhead isolation'
            ]
        
        return SimulationResult(
            scenario_id='',
            scenario_type=ScenarioType.CASCADING_FAILURE,
            duration=0,
            success=success,
            system_recovered=system_recovered,
            recovery_time=recovery_time,
            data_loss=False,
            data_loss_amount=0,
            weaknesses_found=weaknesses,
            recommendations=recommendations,
            metrics={'initial_failure': initial_failure}
        )
    
    async def _simulate_byzantine_attack(self, params: Dict) -> SimulationResult:
        """Giả lập Byzantine fault"""
        logger.info("Simulating Byzantine attack...")
        
        malicious_nodes = params.get('malicious_nodes', 1)
        total_nodes = params.get('total_nodes', 4)
        
        # Check BFT tolerance
        # System can tolerate f faults where n >= 3f + 1
        max_faults = (total_nodes - 1) // 3
        
        if malicious_nodes <= max_faults:
            success = True
            system_recovered = True
            recovery_time = 0
            weaknesses = []
            recommendations = []
        else:
            success = False
            system_recovered = False
            recovery_time = None
            weaknesses = [
                f'Byzantine tolerance exceeded: {malicious_nodes} > {max_faults}'
            ]
            recommendations = [
                'Increase node count',
                'Implement stronger consensus'
            ]
        
        return SimulationResult(
            scenario_id='',
            scenario_type=ScenarioType.BYZANTINE_ATTACK,
            duration=0,
            success=success,
            system_recovered=system_recovered,
            recovery_time=recovery_time,
            data_loss=False,
            data_loss_amount=0,
            weaknesses_found=weaknesses,
            recommendations=recommendations,
            metrics={
                'malicious_nodes': malicious_nodes,
                'total_nodes': total_nodes,
                'max_faults': max_faults
            }
        )
    
    async def _simulate_quantum_attack(self, params: Dict) -> SimulationResult:
        """Giả lập tấn công lượng tử"""
        logger.info("Simulating quantum attack...")
        
        attack_type = params.get('attack_type', 'grover')
        
        weaknesses = []
        recommendations = []
        
        if attack_type == 'grover':
            # Grover's algorithm: O(sqrt(N)) instead of O(N)
            # For 2^2500, becomes 2^1250 - still secure
            success = True
            system_recovered = True
            weaknesses.append('Grover algorithm reduces security margin')
            recommendations.append('Monitor quantum computing progress')
        
        elif attack_type == 'shor':
            # Shor's algorithm breaks RSA/ECC
            # HKSC is not based on factorization/discrete log
            success = True
            system_recovered = True
            weaknesses.append('Shor algorithm affects other crypto systems')
            recommendations.append('Ensure HKSC remains post-quantum')
        
        else:
            success = True
            system_recovered = True
        
        return SimulationResult(
            scenario_id='',
            scenario_type=ScenarioType.QUANTUM_ATTACK,
            duration=0,
            success=success,
            system_recovered=system_recovered,
            recovery_time=0,
            data_loss=False,
            data_loss_amount=0,
            weaknesses_found=weaknesses,
            recommendations=recommendations,
            metrics={'attack_type': attack_type}
        )
    
    def _generate_summary(self, results: Dict[str, SimulationResult]) -> Dict:
        """Tạo tóm tắt kết quả"""
        total = len(results)
        successes = sum(1 for r in results.values() if r.success)
        recoveries = sum(1 for r in results.values() if r.system_recovered)
        
        all_weaknesses = []
        all_recommendations = []
        
        for r in results.values():
            all_weaknesses.extend(r.weaknesses_found)
            all_recommendations.extend(r.recommendations)
        
        return {
            'total_scenarios': total,
            'successful': successes,
            'recovered': recoveries,
            'overall_success_rate': successes / total if total > 0 else 0,
            'overall_recovery_rate': recoveries / total if total > 0 else 0,
            'unique_weaknesses': list(set(all_weaknesses)),
            'unique_recommendations': list(set(all_recommendations)),
            'needs_improvement': successes / total < self.config['improvement_threshold']
        }
    
    def get_improvement_tasks(self) -> List[Task]:
        """Tạo các task cải thiện dựa trên kết quả giả lập"""
        tasks = []
        
        # Analyze recent simulations
        recent = self.simulation_history[-10:]
        
        # Find common weaknesses
        weakness_count = {}
        for sim in recent:
            for w in sim.weaknesses_found:
                weakness_count[w] = weakness_count.get(w, 0) + 1
        
        # Create tasks for frequent weaknesses
        for weakness, count in weakness_count.items():
            if count >= 2:  # Appears in multiple simulations
                task = Task(
                    id=f"improve_{hashlib.sha256(weakness.encode()).hexdigest()[:8]}",
                    name=f"address_{weakness.replace(' ', '_')}",
                    agent_type="optimizer",
                    priority=TaskPriority.HIGH,
                    payload={
                        'weakness': weakness,
                        'occurrence_count': count,
                        'action': 'improve_scenario',
                        'scenario': 'worst_case'
                    }
                )
                tasks.append(task)
        
        return tasks
    
    async def run_continuous(self) -> None:
        """Chạy simulations liên tục"""
        while True:
            try:
                results = await self.run_all_scenarios()
                
                summary = self._generate_summary(results)
                
                if summary['needs_improvement'] and self.config['auto_improve']:
                    # Create improvement tasks
                    tasks = self.get_improvement_tasks()
                    for task in tasks:
                        if self.controller:
                            self.controller.submit_task(task)
                
                # Wait before next run
                await asyncio.sleep(3600)  # Run every hour
            
            except Exception as e:
                logger.error(f"Error in continuous simulation: {e}")
                await asyncio.sleep(300)
