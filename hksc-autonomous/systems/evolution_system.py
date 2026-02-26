#!/usr/bin/env python3
"""
Auto-Evolution System
=====================
Hệ thống tự động tiến hóa cho HKSC-4096.

Chức năng:
- Tiến hóa code tự động
- Cải thiện thuật toán qua các thế hệ
- Chọn lọc tự nhiên cho các agent
- Mutation và crossover
- Fitness evaluation
"""

import asyncio
import ast
import copy
import hashlib
import json
import logging
import os
import random
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Callable

from agents.controller import BaseAgent, Task, AgentState, TaskPriority

logger = logging.getLogger('HKSC-EvolutionSystem')


@dataclass
class Genome:
    """Genome đại diện cho một cá thể trong quần thể"""
    id: str
    generation: int
    dna: Dict[str, Any]  # Configuration/parameters
    fitness: float = 0.0
    parent_ids: List[str] = field(default_factory=list)
    mutation_history: List[Dict] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    
    def mutate(self, mutation_rate: float = 0.1) -> 'Genome':
        """Tạo mutation của genome"""
        new_dna = copy.deepcopy(self.dna)
        mutations = []
        
        for key, value in new_dna.items():
            if random.random() < mutation_rate:
                if isinstance(value, (int, float)):
                    # Numeric mutation: +/- 10%
                    delta = value * 0.1 * (random.random() - 0.5)
                    new_dna[key] = value + delta
                    mutations.append({
                        'key': key,
                        'old': value,
                        'new': new_dna[key],
                        'type': 'numeric'
                    })
                
                elif isinstance(value, bool):
                    # Boolean mutation: flip
                    new_dna[key] = not value
                    mutations.append({
                        'key': key,
                        'old': value,
                        'new': new_dna[key],
                        'type': 'boolean'
                    })
                
                elif isinstance(value, str) and key.endswith('_strategy'):
                    # Strategy mutation: choose different strategy
                    strategies = {
                        'conflict_resolution': ['priority', 'fitness', 'random'],
                        'selection_method': ['tournament', 'roulette', 'rank'],
                        'mutation_type': ['gaussian', 'uniform', 'adaptive']
                    }
                    if key in strategies:
                        new_dna[key] = random.choice(strategies[key])
                        mutations.append({
                            'key': key,
                            'old': value,
                            'new': new_dna[key],
                            'type': 'strategy'
                        })
        
        return Genome(
            id=hashlib.sha256(f"{self.id}_{time.time()}".encode()).hexdigest()[:16],
            generation=self.generation + 1,
            dna=new_dna,
            parent_ids=[self.id],
            mutation_history=self.mutation_history + mutations
        )
    
    @staticmethod
    def crossover(parent1: 'Genome', parent2: 'Genome') -> 'Genome':
        """Tạo offspring từ 2 parent"""
        child_dna = {}
        
        for key in set(parent1.dna.keys()) | set(parent2.dna.keys()):
            if key in parent1.dna and key in parent2.dna:
                # Uniform crossover
                child_dna[key] = parent1.dna[key] if random.random() < 0.5 else parent2.dna[key]
            elif key in parent1.dna:
                child_dna[key] = parent1.dna[key]
            else:
                child_dna[key] = parent2.dna[key]
        
        return Genome(
            id=hashlib.sha256(f"{parent1.id}_{parent2.id}_{time.time()}".encode()).hexdigest()[:16],
            generation=max(parent1.generation, parent2.generation) + 1,
            dna=child_dna,
            parent_ids=[parent1.id, parent2.id]
        )


@dataclass
class Population:
    """Quần thể các cá thể"""
    generation: int
    individuals: List[Genome] = field(default_factory=list)
    best_fitness: float = 0.0
    avg_fitness: float = 0.0
    diversity: float = 0.0
    
    def select_parents(self, num_parents: int = 2) -> List[Genome]:
        """Chọn parent dùng tournament selection"""
        parents = []
        
        for _ in range(num_parents):
            # Tournament selection
            tournament_size = min(3, len(self.individuals))
            tournament = random.sample(self.individuals, tournament_size)
            winner = max(tournament, key=lambda x: x.fitness)
            parents.append(winner)
        
        return parents
    
    def cull(self, survival_rate: float = 0.5) -> None:
        """Loại bỏ các cá thể yếu"""
        self.individuals.sort(key=lambda x: x.fitness, reverse=True)
        num_survivors = int(len(self.individuals) * survival_rate)
        self.individuals = self.individuals[:num_survivors]
    
    def calculate_stats(self) -> None:
        """Tính toán thống kê quần thể"""
        if not self.individuals:
            return
        
        fitnesses = [i.fitness for i in self.individuals]
        self.best_fitness = max(fitnesses)
        self.avg_fitness = sum(fitnesses) / len(fitnesses)
        
        # Calculate diversity (standard deviation of fitness)
        if len(fitnesses) > 1:
            mean = self.avg_fitness
            variance = sum((f - mean) ** 2 for f in fitnesses) / len(fitnesses)
            self.diversity = variance ** 0.5


class EvolutionSystem:
    """
    Hệ thống tự động tiến hóa cho HKSC-4096.
    
    Các thành phần:
    1. Population: Quần thể các cá thể (configurations)
    2. Selection: Chọn lọc các cá thể tốt nhất
    3. Mutation: Đột biến ngẫu nhiên
    4. Crossover: Lai ghép
    5. Fitness Evaluation: Đánh giá fitness
    6. Evolution Loop: Vòng lặp tiến hóa
    """
    
    def __init__(self, controller=None):
        self.controller = controller
        
        self.config = {
            'population_size': 20,
            'mutation_rate': 0.15,
            'crossover_rate': 0.7,
            'elitism': 0.1,  # Top 10% survive unchanged
            'max_generations': 100,
            'target_fitness': 0.95,
            'fitness_threshold': 0.7,
            'diversity_threshold': 0.05,
            'evaluation_runs': 5
        }
        
        # Population
        self.population: Optional[Population] = None
        self.generation = 0
        
        # Evolution history
        self.history: List[Dict] = []
        self.best_genome: Optional[Genome] = None
        
        # Fitness evaluators
        self.fitness_evaluators: Dict[str, Callable] = {}
        
        logger.info("EvolutionSystem initialized")
    
    def register_fitness_evaluator(self, name: str, evaluator: Callable) -> None:
        """Đăng ký hàm đánh giá fitness"""
        self.fitness_evaluators[name] = evaluator
        logger.info(f"Registered fitness evaluator: {name}")
    
    def create_initial_population(self, base_config: Dict[str, Any]) -> Population:
        """Tạo quần thể ban đầu"""
        individuals = []
        
        # Create individuals with variations
        for i in range(self.config['population_size']):
            dna = copy.deepcopy(base_config)
            
            # Add some random variations
            for key, value in dna.items():
                if isinstance(value, (int, float)):
                    dna[key] = value * (1 + 0.2 * (random.random() - 0.5))
            
            genome = Genome(
                id=f"gen0_{i}",
                generation=0,
                dna=dna
            )
            individuals.append(genome)
        
        self.population = Population(generation=0, individuals=individuals)
        return self.population
    
    async def evolve(self, generations: Optional[int] = None) -> Genome:
        """
        Chạy quá trình tiến hóa.
        
        Returns:
            Genome tốt nhất sau quá trình tiến hóa
        """
        max_gen = generations or self.config['max_generations']
        
        logger.info(f"Starting evolution for {max_gen} generations")
        
        for gen in range(max_gen):
            self.generation = gen
            
            logger.info(f"Generation {gen}: Evaluating {len(self.population.individuals)} individuals")
            
            # Step 1: Evaluate fitness
            await self._evaluate_population()
            
            # Update stats
            self.population.calculate_stats()
            
            # Record history
            self.history.append({
                'generation': gen,
                'best_fitness': self.population.best_fitness,
                'avg_fitness': self.population.avg_fitness,
                'diversity': self.population.diversity,
                'population_size': len(self.population.individuals)
            })
            
            logger.info(f"Generation {gen}: Best={self.population.best_fitness:.4f}, "
                       f"Avg={self.population.avg_fitness:.4f}, "
                       f"Diversity={self.population.diversity:.4f}")
            
            # Check termination conditions
            if self.population.best_fitness >= self.config['target_fitness']:
                logger.info(f"Target fitness reached at generation {gen}")
                break
            
            if self.population.diversity < self.config['diversity_threshold']:
                logger.warning(f"Low diversity detected: {self.population.diversity:.4f}")
                # Inject random individuals to increase diversity
                await self._inject_random_individuals(3)
            
            # Step 2: Create next generation
            await self._create_next_generation()
        
        # Return best genome
        best = max(self.population.individuals, key=lambda x: x.fitness)
        self.best_genome = best
        
        logger.info(f"Evolution complete. Best fitness: {best.fitness:.4f}")
        
        return best
    
    async def _evaluate_population(self) -> None:
        """Đánh giá fitness cho toàn bộ quần thể"""
        tasks = []
        
        for individual in self.population.individuals:
            task = self._evaluate_individual(individual)
            tasks.append(task)
        
        await asyncio.gather(*tasks)
    
    async def _evaluate_individual(self, individual: Genome) -> None:
        """Đánh giá fitness cho một cá thể"""
        # Run multiple evaluations and average
        fitness_scores = []
        
        for _ in range(self.config['evaluation_runs']):
            score = await self._run_evaluation(individual.dna)
            fitness_scores.append(score)
        
        individual.fitness = sum(fitness_scores) / len(fitness_scores)
    
    async def _run_evaluation(self, dna: Dict) -> float:
        """Chạy một lần đánh giá"""
        score = 0.0
        
        # Evaluate using registered evaluators
        for name, evaluator in self.fitness_evaluators.items():
            try:
                partial_score = await evaluator(dna)
                score += partial_score
            except Exception as e:
                logger.debug(f"Evaluator {name} failed: {e}")
        
        # Normalize to 0-1
        num_evaluators = len(self.fitness_evaluators)
        if num_evaluators > 0:
            score = score / num_evaluators
        
        return min(max(score, 0.0), 1.0)
    
    async def _create_next_generation(self) -> None:
        """Tạo thế hệ tiếp theo"""
        new_individuals = []
        
        # Sort by fitness
        self.population.individuals.sort(key=lambda x: x.fitness, reverse=True)
        
        # Elitism: Keep top individuals
        elite_count = int(self.config['population_size'] * self.config['elitism'])
        new_individuals.extend(self.population.individuals[:elite_count])
        
        # Generate offspring
        while len(new_individuals) < self.config['population_size']:
            # Selection
            parents = self.population.select_parents(2)
            
            # Crossover
            if random.random() < self.config['crossover_rate']:
                child = Genome.crossover(parents[0], parents[1])
            else:
                child = copy.deepcopy(parents[0])
                child.id = hashlib.sha256(f"{child.id}_{time.time()}".encode()).hexdigest()[:16]
            
            # Mutation
            child = child.mutate(self.config['mutation_rate'])
            child.generation = self.generation + 1
            
            new_individuals.append(child)
        
        # Update population
        self.population = Population(
            generation=self.generation + 1,
            individuals=new_individuals
        )
    
    async def _inject_random_individuals(self, count: int) -> None:
        """Thêm cá thể ngẫu nhiên để tăng diversity"""
        base_dna = self.population.individuals[0].dna if self.population.individuals else {}
        
        for i in range(count):
            dna = copy.deepcopy(base_dna)
            
            # Randomize significantly
            for key, value in dna.items():
                if isinstance(value, (int, float)):
                    dna[key] = value * (1 + random.uniform(-0.5, 0.5))
            
            genome = Genome(
                id=f"random_{self.generation}_{i}",
                generation=self.generation,
                dna=dna
            )
            
            self.population.individuals.append(genome)
        
        logger.info(f"Injected {count} random individuals")
    
    def get_evolution_report(self) -> Dict:
        """Tạo báo cáo tiến hóa"""
        return {
            'generations': self.generation,
            'history': self.history,
            'best_genome': {
                'id': self.best_genome.id if self.best_genome else None,
                'fitness': self.best_genome.fitness if self.best_genome else 0,
                'dna': self.best_genome.dna if self.best_genome else {},
                'generation': self.best_genome.generation if self.best_genome else 0
            },
            'improvement': self._calculate_improvement(),
            'convergence': self._check_convergence()
        }
    
    def _calculate_improvement(self) -> float:
        """Tính mức độ cải thiện"""
        if len(self.history) < 2:
            return 0.0
        
        initial = self.history[0]['best_fitness']
        final = self.history[-1]['best_fitness']
        
        if initial == 0:
            return 0.0
        
        return (final - initial) / initial
    
    def _check_convergence(self) -> Dict:
        """Kiểm tra hội tụ"""
        if len(self.history) < 10:
            return {'converged': False, 'generations_stable': 0}
        
        recent = self.history[-10:]
        fitnesses = [h['best_fitness'] for h in recent]
        
        # Check if fitness is stable
        max_diff = max(fitnesses) - min(fitnesses)
        
        return {
            'converged': max_diff < 0.01,
            'generations_stable': 10,
            'max_diff': max_diff
        }
    
    async def evolve_agent(self, agent: BaseAgent) -> BaseAgent:
        """Tiến hóa một agent cụ thể"""
        logger.info(f"Evolving agent: {agent.agent_id}")
        
        # Extract agent's configuration as DNA
        base_dna = {
            'task_timeout': 300,
            'max_retries': 3,
            'priority_weights': {
                'critical': 1.0,
                'high': 0.8,
                'normal': 0.5,
                'low': 0.3
            },
            'batch_size': 10,
            'learning_rate': 0.1
        }
        
        # Create population
        self.create_initial_population(base_dna)
        
        # Evolve
        best = await self.evolve(generations=20)
        
        # Apply best configuration to agent
        evolved_agent = copy.deepcopy(agent)
        evolved_agent.fitness_score = best.fitness
        evolved_agent.generation = best.generation
        
        logger.info(f"Agent evolved: {evolved_agent.agent_id} (fitness: {best.fitness:.4f})")
        
        return evolved_agent
    
    async def evolve_code(self, file_path: str) -> str:
        """Tiến hóa code trong một file"""
        logger.info(f"Evolving code: {file_path}")
        
        # Read file
        with open(file_path, 'r') as f:
            original_code = f.read()
        
        # Parse AST
        try:
            tree = ast.parse(original_code)
        except SyntaxError:
            return original_code
        
        # Apply optimizations (mutations)
        evolved_tree = self._mutate_ast(tree)
        
        # Convert back to code
        evolved_code = ast.unparse(evolved_tree)
        
        # Validate evolved code
        if self._validate_code(evolved_code):
            return evolved_code
        
        return original_code
    
    def _mutate_ast(self, tree: ast.AST) -> ast.AST:
        """Đột biến AST"""
        # This is a simplified version
        # In practice, would apply various code transformations
        return tree
    
    def _validate_code(self, code: str) -> bool:
        """Validate evolved code"""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False
    
    async def run_continuous(self) -> None:
        """Chạy tiến hóa liên tục"""
        while True:
            try:
                if self.population is None:
                    # Initialize with default config
                    base_config = {
                        'check_interval': 3600,
                        'auto_upgrade': True,
                        'optimization_threshold': 0.1
                    }
                    self.create_initial_population(base_config)
                
                # Run one generation
                await self._evaluate_population()
                self.population.calculate_stats()
                
                # Check if improvement is needed
                if self.population.best_fitness < self.config['fitness_threshold']:
                    await self._create_next_generation()
                    logger.info(f"Evolved to generation {self.generation}")
                
                await asyncio.sleep(3600)  # Check every hour
            
            except Exception as e:
                logger.error(f"Error in continuous evolution: {e}")
                await asyncio.sleep(300)


# Pre-defined fitness evaluators
async def evaluate_performance(dna: Dict) -> float:
    """Đánh giá hiệu suất"""
    # Simulate performance test
    score = 0.5
    
    # Higher batch size = better throughput
    if 'batch_size' in dna:
        score += min(dna['batch_size'] / 100, 0.3)
    
    # Lower timeout = faster response
    if 'task_timeout' in dna:
        score += max(0, 0.2 - dna['task_timeout'] / 3000)
    
    return min(score, 1.0)


async def evaluate_reliability(dna: Dict) -> float:
    """Đánh giá độ tin cậy"""
    score = 0.5
    
    # Higher retries = more reliable
    if 'max_retries' in dna:
        score += min(dna['max_retries'] / 10, 0.3)
    
    return min(score, 1.0)


async def evaluate_efficiency(dna: Dict) -> float:
    """Đánh giá hiệu quả"""
    score = 0.5
    
    # Lower check interval = more responsive
    if 'check_interval' in dna:
        score += max(0, 0.3 - dna['check_interval'] / 7200)
    
    return min(score, 1.0)


# Singleton instance
_evolution_instance: Optional[EvolutionSystem] = None


def get_evolution_system(controller=None) -> EvolutionSystem:
    """Get singleton instance of EvolutionSystem"""
    global _evolution_instance
    if _evolution_instance is None:
        _evolution_instance = EvolutionSystem(controller)
        
        # Register default evaluators
        _evolution_instance.register_fitness_evaluator('performance', evaluate_performance)
        _evolution_instance.register_fitness_evaluator('reliability', evaluate_reliability)
        _evolution_instance.register_fitness_evaluator('efficiency', evaluate_efficiency)
    
    return _evolution_instance
