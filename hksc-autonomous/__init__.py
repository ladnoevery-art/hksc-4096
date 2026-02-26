"""
HKSC-4096 Autonomous System
===========================
Hệ thống tự trị tự động nâng cấp, tự động phát triển, tự động vá lỗi,
tự động tối ưu, tự động ra quyết định, tự động tiến hóa.

Các thành phần chính:
- AgentController: Trung tâm điều phối
- UpgradeAgent: Tự động nâng cấp
- FixAgent: Tự động vá lỗi
- OptimizationAgent: Tự động tối ưu
- DecisionEngine: Hệ thống ra quyết định
- WorstCaseSimulator: Giả lập tình huống xấu nhất
- EvolutionSystem: Hệ thống tiến hóa
"""

__version__ = '1.0.0'
__author__ = 'HKSC Autonomous Team'

from agents.controller import AgentController, BaseAgent, Task, get_controller
from agents.upgrade_agent import UpgradeAgent
from agents.fix_agent import FixAgent
from agents.optimization_agent import OptimizationAgent
from systems.decision_engine import DecisionEngine, get_decision_engine
from systems.evolution_system import EvolutionSystem, get_evolution_system
from simulators.worst_case import WorstCaseSimulator

__all__ = [
    'AgentController',
    'BaseAgent',
    'Task',
    'get_controller',
    'UpgradeAgent',
    'FixAgent',
    'OptimizationAgent',
    'DecisionEngine',
    'get_decision_engine',
    'EvolutionSystem',
    'get_evolution_system',
    'WorstCaseSimulator',
]
