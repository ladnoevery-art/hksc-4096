#!/usr/bin/env python3
"""
HKSC-4096 Autonomous AI Agent Controller
========================================
Trung tâm điều phối hệ thống AI tự trị cho HKSC-4096.

Các chức năng chính:
- Điều phối các AI Agent chuyên biệt
- Giám sát trạng thái hệ thống
- Ra quyết định tự động
- Xử lý xung đột và ưu tiên
- Tự động tiến hóa hệ thống

Author: HKSC Autonomous System
Version: 1.0.0
"""

import asyncio
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import hashlib
import threading
import queue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('autonomous.log')
    ]
)
logger = logging.getLogger('HKSC-AgentController')


class AgentState(Enum):
    """Trạng thái của một Agent"""
    IDLE = auto()
    RUNNING = auto()
    PAUSED = auto()
    ERROR = auto()
    EVOLVING = auto()
    SHUTDOWN = auto()


class TaskPriority(Enum):
    """Mức độ ưu tiên của task"""
    CRITICAL = 1    # Security breach, system failure
    HIGH = 2        # Performance degradation, bugs
    NORMAL = 3      # Regular maintenance, updates
    LOW = 4         # Optimization, enhancements
    BACKGROUND = 5  # Research, experimentation


@dataclass
class Task:
    """Đại diện cho một task trong hệ thống"""
    id: str
    name: str
    agent_type: str
    priority: TaskPriority
    payload: Dict[str, Any]
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    status: str = "pending"
    result: Any = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    dependencies: List[str] = field(default_factory=list)


@dataclass
class AgentMetrics:
    """Metrics cho một Agent"""
    agent_id: str
    state: AgentState
    tasks_completed: int = 0
    tasks_failed: int = 0
    avg_execution_time: float = 0.0
    last_active: float = field(default_factory=time.time)
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    evolution_generation: int = 0
    fitness_score: float = 0.0


class AgentController:
    """
    Trung tâm điều phối tất cả các AI Agent trong hệ thống HKSC-4096.
    
    Đây là "bộ não" của hệ thống tự trị, chịu trách nhiệm:
    - Khởi tạo và quản lý các Agent chuyên biệt
    - Phân phối task đến đúng Agent
    - Giám sát hiệu suất và sức khỏe hệ thống
    - Tự động điều chỉnh và tối ưu
    - Xử lý xung đột giữa các Agent
    - Quyết định khi nào cần tiến hóa
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.started_at = time.time()
        self.agent_id = self._generate_agent_id()
        self.state = AgentState.IDLE
        
        # Configuration
        self.config = self._load_config(config_path)
        
        # Task management
        self.task_queue: queue.PriorityQueue = queue.PriorityQueue()
        self.completed_tasks: Dict[str, Task] = {}
        self.running_tasks: Dict[str, Task] = {}
        self.task_history: List[Task] = []
        
        # Agent registry
        self.agents: Dict[str, 'BaseAgent'] = {}
        self.agent_metrics: Dict[str, AgentMetrics] = {}
        
        # Event system
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.event_history: List[Dict] = []
        
        # Decision engine
        self.decision_history: List[Dict] = []
        self.conflict_resolutions: List[Dict] = []
        
        # Evolution tracking
        self.evolution_history: List[Dict] = []
        self.current_generation = 0
        
        # Safety mechanisms
        self.emergency_stop = False
        self.safety_thresholds = {
            'max_cpu': 90.0,
            'max_memory': 85.0,
            'max_error_rate': 0.1,
            'min_fitness': 0.5
        }
        
        # Lock for thread safety
        self._lock = threading.RLock()
        
        logger.info(f"AgentController initialized: {self.agent_id}")
    
    def _generate_agent_id(self) -> str:
        """Tạo ID duy nhất cho controller"""
        timestamp = str(time.time())
        random_component = str(os.urandom(16))
        return hashlib.sha256(
            (timestamp + random_component).encode()
        ).hexdigest()[:16]
    
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load cấu hình từ file hoặc sử dụng mặc định"""
        default_config = {
            'max_concurrent_tasks': 10,
            'task_timeout': 300,
            'auto_evolution': True,
            'evolution_interval': 86400,  # 24 hours
            'conflict_resolution': 'priority_based',
            'backup_interval': 3600,  # 1 hour
            'metrics_retention_days': 30,
            'enable_worst_case_simulation': True,
            'simulation_frequency': 3600,
            'decision_threshold': 0.75,
            'silent_mode': False,
            'autonomy_level': 'full'  # 'none', 'assisted', 'semi', 'full'
        }
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def register_agent(self, agent: 'BaseAgent') -> None:
        """Đăng ký một Agent mới vào hệ thống"""
        with self._lock:
            agent_id = agent.agent_id
            self.agents[agent_id] = agent
            self.agent_metrics[agent_id] = AgentMetrics(
                agent_id=agent_id,
                state=AgentState.IDLE
            )
            agent.controller = self
            logger.info(f"Agent registered: {agent_id} ({agent.agent_type})")
    
    def unregister_agent(self, agent_id: str) -> None:
        """Xóa một Agent khỏi hệ thống"""
        with self._lock:
            if agent_id in self.agents:
                agent = self.agents[agent_id]
                agent.shutdown()
                del self.agents[agent_id]
                del self.agent_metrics[agent_id]
                logger.info(f"Agent unregistered: {agent_id}")
    
    def submit_task(self, task: Task) -> str:
        """Gửi một task vào hệ thống"""
        with self._lock:
            # Validate task
            if not self._validate_task(task):
                raise ValueError(f"Invalid task: {task.id}")
            
            # Check dependencies
            if task.dependencies:
                for dep_id in task.dependencies:
                    if dep_id not in self.completed_tasks:
                        logger.warning(f"Task {task.id} has unmet dependency: {dep_id}")
                        task.status = "waiting"
                        return task.id
            
            # Add to queue with priority
            priority_value = (task.priority.value, task.created_at)
            self.task_queue.put((priority_value, task))
            task.status = "queued"
            
            logger.info(f"Task submitted: {task.id} (priority: {task.priority.name})")
            return task.id
    
    def _validate_task(self, task: Task) -> bool:
        """Validate một task trước khi thêm vào queue"""
        if not task.id or not task.agent_type:
            return False
        
        # Check if agent type exists
        agent_exists = any(
            agent.agent_type == task.agent_type 
            for agent in self.agents.values()
        )
        
        return agent_exists
    
    async def process_tasks(self) -> None:
        """Xử lý các task trong queue"""
        while not self.emergency_stop:
            try:
                # Get task from queue (non-blocking)
                try:
                    _, task = self.task_queue.get(timeout=1)
                except queue.Empty:
                    await asyncio.sleep(0.1)
                    continue
                
                # Find appropriate agent
                agent = self._select_agent_for_task(task)
                
                if agent:
                    # Execute task
                    await self._execute_task(agent, task)
                else:
                    # Re-queue if no agent available
                    logger.warning(f"No agent available for task {task.id}, re-queueing")
                    task.retry_count += 1
                    if task.retry_count < task.max_retries:
                        self.task_queue.put(((task.priority.value, time.time()), task))
                    else:
                        task.status = "failed"
                        task.error = "Max retries exceeded"
                        self.completed_tasks[task.id] = task
                
            except Exception as e:
                logger.error(f"Error processing tasks: {e}")
                await asyncio.sleep(1)
    
    def _select_agent_for_task(self, task: Task) -> Optional['BaseAgent']:
        """Chọn agent phù hợp nhất cho một task"""
        candidates = [
            agent for agent in self.agents.values()
            if agent.agent_type == task.agent_type
            and agent.state in [AgentState.IDLE, AgentState.RUNNING]
        ]
        
        if not candidates:
            return None
        
        # Score each candidate based on metrics
        best_agent = None
        best_score = -1
        
        for agent in candidates:
            metrics = self.agent_metrics[agent.agent_id]
            
            # Calculate fitness score
            score = metrics.fitness_score
            score -= metrics.cpu_usage / 100  # Penalize high CPU
            score -= metrics.memory_usage / 100  # Penalize high memory
            score += metrics.tasks_completed / (metrics.tasks_completed + metrics.tasks_failed + 1)
            
            if score > best_score:
                best_score = score
                best_agent = agent
        
        return best_agent
    
    async def _execute_task(self, agent: 'BaseAgent', task: Task) -> None:
        """Thực thi một task với agent được chọn"""
        task.started_at = time.time()
        task.status = "running"
        self.running_tasks[task.id] = task
        
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                agent.execute(task),
                timeout=self.config['task_timeout']
            )
            
            task.result = result
            task.status = "completed"
            task.completed_at = time.time()
            
            # Update metrics
            self.agent_metrics[agent.agent_id].tasks_completed += 1
            
            logger.info(f"Task completed: {task.id}")
            
        except asyncio.TimeoutError:
            task.status = "timeout"
            task.error = "Task execution timeout"
            self.agent_metrics[agent.agent_id].tasks_failed += 1
            logger.error(f"Task timeout: {task.id}")
            
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            self.agent_metrics[agent.agent_id].tasks_failed += 1
            logger.error(f"Task failed: {task.id}, error: {e}")
        
        finally:
            del self.running_tasks[task.id]
            self.completed_tasks[task.id] = task
            self.task_history.append(task)
    
    def make_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ra quyết định tự động dựa trên context.
        
        Đây là hàm quan trọng nhất của hệ thống tự trị.
        """
        decision_id = hashlib.sha256(
            json.dumps(context, sort_keys=True).encode()
        ).hexdigest()[:16]
        
        # Analyze context
        analysis = self._analyze_context(context)
        
        # Generate options
        options = self._generate_decision_options(context, analysis)
        
        # Evaluate each option
        scored_options = []
        for option in options:
            score = self._evaluate_option(option, context)
            scored_options.append((option, score))
        
        # Sort by score
        scored_options.sort(key=lambda x: x[1], reverse=True)
        
        # Select best option (with confidence threshold)
        best_option, best_score = scored_options[0]
        
        if best_score < self.config['decision_threshold']:
            # Not confident enough - escalate or request human
            decision = {
                'id': decision_id,
                'type': 'escalate',
                'reason': 'Low confidence score',
                'confidence': best_score,
                'context': context,
                'recommended_option': best_option,
                'timestamp': time.time()
            }
        else:
            decision = {
                'id': decision_id,
                'type': 'auto',
                'action': best_option,
                'confidence': best_score,
                'alternatives': scored_options[1:3],
                'context': context,
                'timestamp': time.time()
            }
        
        # Record decision
        self.decision_history.append(decision)
        
        logger.info(f"Decision made: {decision_id} (confidence: {best_score:.2f})")
        
        return decision
    
    def _analyze_context(self, context: Dict) -> Dict:
        """Phân tích context để hiểu tình huống"""
        analysis = {
            'urgency': self._calculate_urgency(context),
            'risk_level': self._calculate_risk(context),
            'resource_availability': self._check_resources(),
            'system_health': self._check_system_health(),
            'historical_patterns': self._find_similar_patterns(context)
        }
        return analysis
    
    def _calculate_urgency(self, context: Dict) -> float:
        """Tính toán mức độ khẩn cấp"""
        urgency = 0.5  # Default
        
        if 'security_alert' in context:
            urgency = 1.0
        elif 'performance_degradation' in context:
            urgency = 0.8
        elif 'user_complaint' in context:
            urgency = 0.6
        
        return urgency
    
    def _calculate_risk(self, context: Dict) -> str:
        """Đánh giá mức độ rủi ro"""
        if 'critical' in context.get('severity', '').lower():
            return 'critical'
        elif 'high' in context.get('severity', '').lower():
            return 'high'
        elif 'medium' in context.get('severity', '').lower():
            return 'medium'
        return 'low'
    
    def _check_resources(self) -> Dict:
        """Kiểm tra tài nguyên hệ thống"""
        import psutil
        
        return {
            'cpu_available': 100 - psutil.cpu_percent(),
            'memory_available': psutil.virtual_memory().available / (1024**3),  # GB
            'disk_available': psutil.disk_usage('/').free / (1024**3),  # GB
            'agents_available': sum(
                1 for a in self.agents.values() 
                if a.state == AgentState.IDLE
            )
        }
    
    def _check_system_health(self) -> Dict:
        """Kiểm tra sức khỏe hệ thống"""
        total_tasks = sum(m.tasks_completed + m.tasks_failed for m in self.agent_metrics.values())
        failed_tasks = sum(m.tasks_failed for m in self.agent_metrics.values())
        
        error_rate = failed_tasks / total_tasks if total_tasks > 0 else 0
        
        return {
            'error_rate': error_rate,
            'agents_healthy': sum(
                1 for m in self.agent_metrics.values() 
                if m.state != AgentState.ERROR
            ),
            'queue_depth': self.task_queue.qsize(),
            'status': 'healthy' if error_rate < 0.05 else 'degraded'
        }
    
    def _find_similar_patterns(self, context: Dict) -> List[Dict]:
        """Tìm các pattern tương tự trong lịch sử"""
        similar = []
        
        for decision in self.decision_history[-100:]:  # Last 100 decisions
            similarity = self._calculate_similarity(context, decision.get('context', {}))
            if similarity > 0.7:
                similar.append({
                    'decision': decision,
                    'similarity': similarity
                })
        
        return sorted(similar, key=lambda x: x['similarity'], reverse=True)[:5]
    
    def _calculate_similarity(self, ctx1: Dict, ctx2: Dict) -> float:
        """Tính độ tương đồng giữa hai context"""
        # Simple Jaccard similarity for keys
        keys1 = set(ctx1.keys())
        keys2 = set(ctx2.keys())
        
        if not keys1 and not keys2:
            return 1.0
        
        intersection = len(keys1 & keys2)
        union = len(keys1 | keys2)
        
        return intersection / union if union > 0 else 0.0
    
    def _generate_decision_options(self, context: Dict, analysis: Dict) -> List[Dict]:
        """Sinh ra các phương án quyết định"""
        options = []
        
        # Option 1: Immediate action
        options.append({
            'name': 'immediate_action',
            'description': 'Execute immediate fix',
            'requires_approval': analysis['risk_level'] == 'critical',
            'estimated_time': 60,
            'resources_needed': ['cpu', 'memory']
        })
        
        # Option 2: Scheduled maintenance
        options.append({
            'name': 'scheduled_maintenance',
            'description': 'Schedule during maintenance window',
            'requires_approval': False,
            'estimated_time': 3600,
            'resources_needed': ['cpu']
        })
        
        # Option 3: Further investigation
        options.append({
            'name': 'investigate',
            'description': 'Gather more information before acting',
            'requires_approval': False,
            'estimated_time': 300,
            'resources_needed': []
        })
        
        # Option 4: Escalate to human
        options.append({
            'name': 'escalate',
            'description': 'Escalate to human operators',
            'requires_approval': True,
            'estimated_time': 0,
            'resources_needed': []
        })
        
        return options
    
    def _evaluate_option(self, option: Dict, context: Dict) -> float:
        """Đánh giá một phương án"""
        score = 0.5  # Base score
        
        # Factor 1: Historical success rate
        similar_decisions = [
            d for d in self.decision_history
            if d.get('action', {}).get('name') == option['name']
        ]
        
        if similar_decisions:
            success_rate = sum(
                1 for d in similar_decisions 
                if d.get('outcome') == 'success'
            ) / len(similar_decisions)
            score += success_rate * 0.3
        
        # Factor 2: Resource availability
        resources = self._check_resources()
        if all(r in resources for r in option.get('resources_needed', [])):
            score += 0.2
        
        # Factor 3: Urgency match
        if context.get('urgent') and option['name'] == 'immediate_action':
            score += 0.3
        
        # Factor 4: Risk level
        if context.get('risk_level') == 'critical' and option.get('requires_approval'):
            score -= 0.2  # Penalize options requiring approval for critical issues
        
        return min(max(score, 0.0), 1.0)
    
    def resolve_conflict(self, agent1_id: str, agent2_id: str, conflict: Dict) -> Dict:
        """
        Giải quyết xung đột giữa hai agent.
        
        Strategies:
        - priority_based: Agent có priority cao hơn thắng
        - seniority_based: Agent hoạt động lâu hơn thắng
        - fitness_based: Agent có fitness cao hơn thắng
        - compromise: Tìm giải pháp trung gian
        """
        strategy = self.config.get('conflict_resolution', 'priority_based')
        
        agent1 = self.agents.get(agent1_id)
        agent2 = self.agents.get(agent2_id)
        
        if not agent1 or not agent2:
            return {'error': 'Agent not found'}
        
        resolution = {
            'conflict_id': hashlib.sha256(
                json.dumps(conflict, sort_keys=True).encode()
            ).hexdigest()[:16],
            'timestamp': time.time(),
            'agents': [agent1_id, agent2_id],
            'strategy': strategy,
            'conflict_type': conflict.get('type', 'unknown')
        }
        
        if strategy == 'priority_based':
            # Compare task priorities
            p1 = conflict.get('agent1_priority', 0)
            p2 = conflict.get('agent2_priority', 0)
            
            if p1 > p2:
                resolution['winner'] = agent1_id
                resolution['reason'] = 'Higher priority'
            elif p2 > p1:
                resolution['winner'] = agent2_id
                resolution['reason'] = 'Higher priority'
            else:
                resolution['winner'] = 'both'
                resolution['resolution'] = 'merge'
                resolution['reason'] = 'Equal priority - merge solutions'
        
        elif strategy == 'fitness_based':
            m1 = self.agent_metrics[agent1_id]
            m2 = self.agent_metrics[agent2_id]
            
            if m1.fitness_score > m2.fitness_score:
                resolution['winner'] = agent1_id
            else:
                resolution['winner'] = agent2_id
            
            resolution['reason'] = 'Higher fitness score'
        
        elif strategy == 'compromise':
            resolution['winner'] = 'none'
            resolution['resolution'] = 'compromise'
            resolution['compromise_solution'] = self._generate_compromise(
                agent1, agent2, conflict
            )
        
        self.conflict_resolutions.append(resolution)
        logger.info(f"Conflict resolved: {resolution['conflict_id']}")
        
        return resolution
    
    def _generate_compromise(self, agent1: 'BaseAgent', agent2: 'BaseAgent', 
                             conflict: Dict) -> Dict:
        """Tạo giải pháp thỏa hiệp"""
        # This would involve complex negotiation logic
        return {
            'approach': 'hybrid',
            'components': [
                {'from': agent1.agent_id, 'contribution': 'primary'},
                {'from': agent2.agent_id, 'contribution': 'secondary'}
            ],
            'validation_required': True
        }
    
    async def evolve_system(self) -> Dict:
        """
        Tiến hóa hệ thống tự động.
        
        Quá trình tiến hóa bao gồm:
        1. Đánh giá fitness của các agent
        2. Chọn lọc các agent tốt nhất
        3. Tạo thế hệ mới thông qua mutation và crossover
        4. Thay thế các agent kém hiệu quả
        """
        logger.info("Starting system evolution...")
        
        self.state = AgentState.EVOLVING
        self.current_generation += 1
        
        evolution_record = {
            'generation': self.current_generation,
            'timestamp': time.time(),
            'agents_before': len(self.agents),
            'changes': []
        }
        
        # Step 1: Evaluate fitness
        fitness_scores = {}
        for agent_id, metrics in self.agent_metrics.items():
            fitness = self._calculate_fitness(metrics)
            fitness_scores[agent_id] = fitness
            self.agent_metrics[agent_id].fitness_score = fitness
        
        # Step 2: Sort by fitness
        sorted_agents = sorted(
            fitness_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Step 3: Keep top performers, evolve or replace others
        top_threshold = len(sorted_agents) // 2
        
        for i, (agent_id, fitness) in enumerate(sorted_agents):
            if i < top_threshold:
                # Keep top performers
                continue
            elif fitness < self.safety_thresholds['min_fitness']:
                # Replace underperformers
                old_agent = self.agents[agent_id]
                new_agent = await self._create_evolved_agent(old_agent)
                
                if new_agent:
                    self.unregister_agent(agent_id)
                    self.register_agent(new_agent)
                    
                    evolution_record['changes'].append({
                        'type': 'replace',
                        'old_agent': agent_id,
                        'new_agent': new_agent.agent_id,
                        'fitness_improvement': new_agent.fitness_score - fitness
                    })
        
        # Step 4: Crossover between top performers
        if len(sorted_agents) >= 2:
            parent1 = self.agents[sorted_agents[0][0]]
            parent2 = self.agents[sorted_agents[1][0]]
            
            child = await self._crossover_agents(parent1, parent2)
            if child:
                self.register_agent(child)
                evolution_record['changes'].append({
                    'type': 'crossover',
                    'parents': [parent1.agent_id, parent2.agent_id],
                    'child': child.agent_id
                })
        
        evolution_record['agents_after'] = len(self.agents)
        self.evolution_history.append(evolution_record)
        
        self.state = AgentState.RUNNING
        logger.info(f"Evolution complete: Generation {self.current_generation}")
        
        return evolution_record
    
    def _calculate_fitness(self, metrics: AgentMetrics) -> float:
        """Tính toán fitness score cho một agent"""
        if metrics.tasks_completed + metrics.tasks_failed == 0:
            return 0.5
        
        success_rate = metrics.tasks_completed / (
            metrics.tasks_completed + metrics.tasks_failed
        )
        
        # Combine multiple factors
        fitness = (
            success_rate * 0.4 +
            (1 - metrics.cpu_usage / 100) * 0.2 +
            (1 - metrics.memory_usage / 100) * 0.2 +
            min(metrics.tasks_completed / 100, 1.0) * 0.2
        )
        
        return fitness
    
    async def _create_evolved_agent(self, old_agent: 'BaseAgent') -> Optional['BaseAgent']:
        """Tạo agent mới thông qua mutation"""
        # This would create a mutated version of the agent
        # Implementation depends on specific agent type
        return None
    
    async def _crossover_agents(self, parent1: 'BaseAgent', 
                                 parent2: 'BaseAgent') -> Optional['BaseAgent']:
        """Tạo agent mới từ hai parent"""
        # This would combine traits from both parents
        return None
    
    async def run(self) -> None:
        """Chạy controller chính"""
        logger.info("AgentController starting...")
        self.state = AgentState.RUNNING
        
        # Start background tasks
        tasks = [
            asyncio.create_task(self.process_tasks()),
            asyncio.create_task(self._monitor_system()),
            asyncio.create_task(self._auto_backup()),
        ]
        
        if self.config['auto_evolution']:
            tasks.append(asyncio.create_task(self._scheduled_evolution()))
        
        if self.config['enable_worst_case_simulation']:
            tasks.append(asyncio.create_task(self._run_simulations()))
        
        await asyncio.gather(*tasks)
    
    async def _monitor_system(self) -> None:
        """Giám sát hệ thống liên tục"""
        while not self.emergency_stop:
            try:
                # Check system health
                health = self._check_system_health()
                
                if health['error_rate'] > self.safety_thresholds['max_error_rate']:
                    logger.error("High error rate detected! Triggering emergency response...")
                    await self._emergency_response()
                
                # Update agent metrics
                for agent_id, agent in self.agents.items():
                    self.agent_metrics[agent_id].last_active = time.time()
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in system monitoring: {e}")
                await asyncio.sleep(5)
    
    async def _emergency_response(self) -> None:
        """Phản ứng khẩn cấp khi hệ thống gặp vấn đề nghiêm trọng"""
        logger.critical("EMERGENCY RESPONSE ACTIVATED")
        
        # Stop accepting new tasks
        self.emergency_stop = True
        
        # Complete running tasks gracefully
        for task_id in list(self.running_tasks.keys()):
            logger.info(f"Waiting for task {task_id} to complete...")
        
        # Create emergency fix task
        emergency_task = Task(
            id=f"emergency_{int(time.time())}",
            name="emergency_stabilization",
            agent_type="fixer",
            priority=TaskPriority.CRITICAL,
            payload={'action': 'stabilize_system'}
        )
        
        self.submit_task(emergency_task)
    
    async def _auto_backup(self) -> None:
        """Tự động backup định kỳ"""
        while not self.emergency_stop:
            try:
                await asyncio.sleep(self.config['backup_interval'])
                
                backup_data = {
                    'timestamp': time.time(),
                    'agents': {aid: agent.serialize() for aid, agent in self.agents.items()},
                    'metrics': {aid: vars(m) for aid, m in self.agent_metrics.items()},
                    'decisions': self.decision_history[-100:],
                    'evolution': self.evolution_history[-10:]
                }
                
                backup_path = f"backups/controller_backup_{int(time.time())}.json"
                os.makedirs('backups', exist_ok=True)
                
                with open(backup_path, 'w') as f:
                    json.dump(backup_data, f, indent=2)
                
                logger.info(f"Backup created: {backup_path}")
                
            except Exception as e:
                logger.error(f"Backup failed: {e}")
    
    async def _scheduled_evolution(self) -> None:
        """Tiến hóa định kỳ"""
        while not self.emergency_stop:
            await asyncio.sleep(self.config['evolution_interval'])
            
            if self.config['auto_evolution']:
                logger.info("Triggering scheduled evolution...")
                await self.evolve_system()
    
    async def _run_simulations(self) -> None:
        """Chạy giả lập tình huống xấu nhất định kỳ"""
        while not self.emergency_stop:
            await asyncio.sleep(self.config['simulation_frequency'])
            
            logger.info("Running worst-case simulations...")
            
            # Import and run simulator
            from simulators.worst_case import WorstCaseSimulator
            
            simulator = WorstCaseSimulator(self)
            results = await simulator.run_all_scenarios()
            
            # Analyze results and create improvement tasks if needed
            for scenario, result in results.items():
                if result['success_rate'] < 0.8:
                    logger.warning(f"Low success rate in {scenario}: {result['success_rate']}")
                    
                    # Create improvement task
                    improvement_task = Task(
                        id=f"improve_{scenario}_{int(time.time())}",
                        name=f"improve_{scenario}_resilience",
                        agent_type="optimizer",
                        priority=TaskPriority.HIGH,
                        payload={
                            'scenario': scenario,
                            'weaknesses': result['weaknesses'],
                            'target_success_rate': 0.95
                        }
                    )
                    self.submit_task(improvement_task)
    
    def shutdown(self) -> None:
        """Tắt controller một cách an toàn"""
        logger.info("Shutting down AgentController...")
        
        self.state = AgentState.SHUTDOWN
        self.emergency_stop = True
        
        # Shutdown all agents
        for agent in list(self.agents.values()):
            agent.shutdown()
        
        # Save final state
        self._auto_backup()
        
        logger.info("AgentController shutdown complete")


class BaseAgent:
    """Base class cho tất cả các AI Agent"""
    
    def __init__(self, agent_type: str):
        self.agent_id = hashlib.sha256(
            (agent_type + str(time.time())).encode()
        ).hexdigest()[:16]
        self.agent_type = agent_type
        self.state = AgentState.IDLE
        self.controller: Optional[AgentController] = None
        self.created_at = time.time()
        self.fitness_score = 0.5
        self.generation = 0
        self.mutation_history: List[Dict] = []
    
    async def execute(self, task: Task) -> Any:
        """Thực thi một task - override bởi subclass"""
        raise NotImplementedError
    
    def serialize(self) -> Dict:
        """Serialize agent state"""
        return {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type,
            'state': self.state.name,
            'created_at': self.created_at,
            'fitness_score': self.fitness_score,
            'generation': self.generation
        }
    
    def shutdown(self) -> None:
        """Tắt agent"""
        self.state = AgentState.SHUTDOWN
        logger.info(f"Agent {self.agent_id} shutdown")


# Singleton instance
_controller_instance: Optional[AgentController] = None


def get_controller(config_path: Optional[str] = None) -> AgentController:
    """Get singleton instance of AgentController"""
    global _controller_instance
    if _controller_instance is None:
        _controller_instance = AgentController(config_path)
    return _controller_instance


if __name__ == "__main__":
    # Test run
    controller = get_controller()
    
    # Create a test task
    test_task = Task(
        id="test_001",
        name="test_task",
        agent_type="test",
        priority=TaskPriority.NORMAL,
        payload={'message': 'Hello from autonomous system'}
    )
    
    controller.submit_task(test_task)
    
    # Run controller
    asyncio.run(controller.run())
