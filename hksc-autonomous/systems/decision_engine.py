#!/usr/bin/env python3
"""
Autonomous Decision Engine
==========================
Hệ thống tự động ra quyết định cho HKSC-4096.

Chức năng:
- Phân tích tình huống phức tạp
- Đánh giá rủi ro và lợi ích
- Ra quyết định tự động với confidence score
- Xử lý xung đột giữa các quyết định
- Học hỏi từ kết quả quyết định trước đó
"""

import json
import logging
import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Callable
from collections import defaultdict

logger = logging.getLogger('HKSC-DecisionEngine')


class DecisionType(Enum):
    """Loại quyết định"""
    UPGRADE = "upgrade"
    DEPLOY = "deploy"
    FIX = "fix"
    OPTIMIZE = "optimize"
    ROLLBACK = "rollback"
    EMERGENCY = "emergency"
    EVOLVE = "evolve"
    IGNORE = "ignore"
    ESCALATE = "escalate"


class DecisionStatus(Enum):
    """Trạng thái quyết định"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    FAILED = "failed"
    REVERTED = "reverted"


@dataclass
class Decision:
    """Đại diện cho một quyết định"""
    id: str
    type: DecisionType
    context: Dict[str, Any]
    options: List[Dict[str, Any]]
    selected_option: int
    confidence: float
    reasoning: str
    risks: List[str]
    benefits: List[str]
    created_at: float = field(default_factory=time.time)
    executed_at: Optional[float] = None
    outcome: Optional[str] = None
    status: DecisionStatus = DecisionStatus.PENDING
    requires_approval: bool = False
    approved_by: Optional[str] = None


@dataclass
class Conflict:
    """Xung đột giữa các quyết định"""
    id: str
    decision_a: str
    decision_b: str
    conflict_type: str
    description: str
    resolution: Optional[str] = None
    resolved_at: Optional[float] = None


class DecisionEngine:
    """
    Engine tự động ra quyết định cho toàn bộ hệ thống HKSC-4096.
    
    Đây là "bộ não" ra quyết định, có khả năng:
    - Tự động phân tích tình huống
    - Đánh giá nhiều phương án
    - Ra quyết định dựa trên dữ liệu
    - Học hỏi từ kết quả
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {
            'min_confidence': 0.75,
            'max_risk_tolerance': 0.3,
            'auto_execute_threshold': 0.9,
            'escalate_threshold': 0.5,
            'learning_enabled': True,
            'conflict_resolution_strategy': 'priority_based'
        }
        
        # Decision tracking
        self.decisions: Dict[str, Decision] = {}
        self.decision_history: List[Decision] = []
        self.outcome_history: List[Dict] = []
        
        # Conflict tracking
        self.conflicts: Dict[str, Conflict] = {}
        
        # Learning data
        self.decision_patterns: Dict[str, Dict] = defaultdict(lambda: {
            'success_count': 0,
            'failure_count': 0,
            'avg_confidence': 0.0,
            'contexts': []
        })
        
        # Decision handlers
        self.handlers: Dict[DecisionType, Callable] = {}
        
        logger.info("DecisionEngine initialized")
    
    def register_handler(self, decision_type: DecisionType, 
                         handler: Callable) -> None:
        """Đăng ký handler cho một loại quyết định"""
        self.handlers[decision_type] = handler
        logger.info(f"Registered handler for {decision_type.value}")
    
    def make_decision(self, context: Dict[str, Any], 
                      decision_type: DecisionType = None) -> Decision:
        """
        Ra quyết định tự động dựa trên context.
        
        Quy trình:
        1. Phân tích context
        2. Sinh các phương án
        3. Đánh giá từng phương án
        4. Chọn phương án tốt nhất
        5. Tính confidence score
        6. Quyết định có cần approval không
        """
        decision_id = self._generate_decision_id(context)
        
        logger.info(f"Making decision: {decision_id}")
        
        # Step 1: Analyze context
        analysis = self._analyze_context(context)
        
        # Step 2: Generate options
        options = self._generate_options(context, analysis, decision_type)
        
        if not options:
            # No options available - escalate
            return self._create_escalation_decision(context, 
                                                     "No viable options generated")
        
        # Step 3: Evaluate options
        scored_options = []
        for i, option in enumerate(options):
            score = self._evaluate_option(option, context, analysis)
            risks = self._assess_risks(option, context)
            benefits = self._assess_benefits(option, context)
            
            scored_options.append({
                'index': i,
                'option': option,
                'score': score,
                'risks': risks,
                'benefits': benefits
            })
        
        # Step 4: Sort by score
        scored_options.sort(key=lambda x: x['score'], reverse=True)
        
        # Step 5: Select best option
        best = scored_options[0]
        confidence = best['score']
        
        # Step 6: Determine if approval needed
        requires_approval = (
            confidence < self.config['auto_execute_threshold'] or
            len(best['risks']) > 2 or
            context.get('critical', False)
        )
        
        # Create decision
        decision = Decision(
            id=decision_id,
            type=decision_type or self._infer_decision_type(context),
            context=context,
            options=options,
            selected_option=best['index'],
            confidence=confidence,
            reasoning=self._generate_reasoning(best, scored_options),
            risks=best['risks'],
            benefits=best['benefits'],
            requires_approval=requires_approval
        )
        
        # Store decision
        self.decisions[decision_id] = decision
        self.decision_history.append(decision)
        
        # Auto-execute if confident enough and no approval needed
        if not requires_approval and confidence >= self.config['min_confidence']:
            self.execute_decision(decision_id)
        
        logger.info(f"Decision made: {decision_id} (confidence: {confidence:.2f}, "
                   f"requires_approval: {requires_approval})")
        
        return decision
    
    def _generate_decision_id(self, context: Dict) -> str:
        """Tạo ID duy nhất cho quyết định"""
        content = json.dumps(context, sort_keys=True) + str(time.time())
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _analyze_context(self, context: Dict) -> Dict:
        """Phân tích context để hiểu tình huống"""
        analysis = {
            'urgency': self._calculate_urgency(context),
            'risk_level': self._calculate_risk_level(context),
            'system_health': self._assess_system_health(context),
            'resource_availability': self._check_resources(context),
            'historical_similarity': self._find_similar_decisions(context),
            'constraints': self._identify_constraints(context),
            'opportunities': self._identify_opportunities(context)
        }
        
        return analysis
    
    def _calculate_urgency(self, context: Dict) -> float:
        """Tính mức độ khẩn cấp (0-1)"""
        urgency = 0.0
        
        # Security issues
        if context.get('security_alert'):
            urgency = 1.0
        elif context.get('severity') == 'critical':
            urgency = 0.9
        elif context.get('severity') == 'high':
            urgency = 0.7
        
        # Performance degradation
        if context.get('performance_degradation'):
            perf_drop = context.get('performance_drop_percent', 0)
            urgency = max(urgency, min(perf_drop / 100, 0.8))
        
        # User impact
        if context.get('affected_users'):
            affected = context.get('affected_users', 0)
            urgency = max(urgency, min(affected / 1000, 0.6))
        
        # Time sensitivity
        if context.get('deadline'):
            time_left = context.get('deadline') - time.time()
            if time_left < 3600:  # Less than 1 hour
                urgency = max(urgency, 0.9)
            elif time_left < 86400:  # Less than 1 day
                urgency = max(urgency, 0.6)
        
        return urgency
    
    def _calculate_risk_level(self, context: Dict) -> str:
        """Tính mức độ rủi ro"""
        risk_score = 0
        
        # Factors that increase risk
        if context.get('affects_production'):
            risk_score += 3
        if context.get('involves_funds'):
            risk_score += 3
        if context.get('data_modification'):
            risk_score += 2
        if context.get('irreversible'):
            risk_score += 2
        if context.get('untested'):
            risk_score += 1
        
        # Map to risk level
        if risk_score >= 6:
            return 'critical'
        elif risk_score >= 4:
            return 'high'
        elif risk_score >= 2:
            return 'medium'
        return 'low'
    
    def _assess_system_health(self, context: Dict) -> Dict:
        """Đánh giá sức khỏe hệ thống"""
        return {
            'status': context.get('system_status', 'unknown'),
            'error_rate': context.get('error_rate', 0),
            'cpu_usage': context.get('cpu_usage', 0),
            'memory_usage': context.get('memory_usage', 0),
            'active_incidents': context.get('active_incidents', 0)
        }
    
    def _check_resources(self, context: Dict) -> Dict:
        """Kiểm tra tài nguyên khả dụng"""
        return {
            'cpu_available': 100 - context.get('cpu_usage', 0),
            'memory_available': context.get('memory_available', 0),
            'disk_available': context.get('disk_available', 0),
            'budget_available': context.get('budget_available', 0),
            'team_capacity': context.get('team_capacity', 0)
        }
    
    def _find_similar_decisions(self, context: Dict) -> List[Dict]:
        """Tìm các quyết định tương tự trong lịch sử"""
        similar = []
        
        for decision in self.decision_history[-100:]:
            similarity = self._calculate_similarity(context, decision.context)
            if similarity > 0.6:
                similar.append({
                    'decision_id': decision.id,
                    'similarity': similarity,
                    'outcome': decision.outcome,
                    'confidence': decision.confidence
                })
        
        return sorted(similar, key=lambda x: x['similarity'], reverse=True)[:5]
    
    def _calculate_similarity(self, ctx1: Dict, ctx2: Dict) -> float:
        """Tính độ tương đồng giữa hai context"""
        # Simple Jaccard similarity
        keys1 = set(ctx1.keys())
        keys2 = set(ctx2.keys())
        
        if not keys1 and not keys2:
            return 1.0
        
        intersection = len(keys1 & keys2)
        union = len(keys1 | keys2)
        
        return intersection / union if union > 0 else 0.0
    
    def _identify_constraints(self, context: Dict) -> List[str]:
        """Xác định các ràng buộc"""
        constraints = []
        
        if context.get('maintenance_window'):
            constraints.append('maintenance_window')
        if context.get('budget_limit'):
            constraints.append('budget_limit')
        if context.get('compliance_requirements'):
            constraints.append('compliance')
        if context.get('dependencies'):
            constraints.append('dependencies')
        
        return constraints
    
    def _identify_opportunities(self, context: Dict) -> List[str]:
        """Xác định các cơ hội"""
        opportunities = []
        
        if context.get('performance_improvement_potential'):
            opportunities.append('performance')
        if context.get('cost_reduction_potential'):
            opportunities.append('cost_reduction')
        if context.get('security_enhancement'):
            opportunities.append('security')
        if context.get('feature_addition'):
            opportunities.append('features')
        
        return opportunities
    
    def _generate_options(self, context: Dict, analysis: Dict, 
                          decision_type: DecisionType = None) -> List[Dict]:
        """Sinh các phương án quyết định"""
        options = []
        
        # Option 1: Immediate action
        options.append({
            'name': 'immediate_action',
            'description': 'Execute fix immediately',
            'action': 'execute_now',
            'estimated_time': 60,
            'resources_needed': ['cpu', 'memory'],
            'rollback_possible': True
        })
        
        # Option 2: Scheduled maintenance
        options.append({
            'name': 'scheduled_maintenance',
            'description': 'Schedule during next maintenance window',
            'action': 'schedule',
            'estimated_time': 3600,
            'resources_needed': ['cpu'],
            'rollback_possible': True
        })
        
        # Option 3: Gradual rollout
        options.append({
            'name': 'gradual_rollout',
            'description': 'Roll out gradually with monitoring',
            'action': 'canary',
            'estimated_time': 7200,
            'resources_needed': ['cpu', 'memory', 'monitoring'],
            'rollback_possible': True
        })
        
        # Option 4: Further investigation
        options.append({
            'name': 'investigate',
            'description': 'Gather more information before acting',
            'action': 'research',
            'estimated_time': 1800,
            'resources_needed': [],
            'rollback_possible': True
        })
        
        # Option 5: Escalate to human
        options.append({
            'name': 'escalate',
            'description': 'Escalate to human operators',
            'action': 'escalate',
            'estimated_time': 0,
            'resources_needed': [],
            'rollback_possible': True
        })
        
        # Option 6: Do nothing
        options.append({
            'name': 'wait_and_see',
            'description': 'Monitor the situation',
            'action': 'monitor',
            'estimated_time': 0,
            'resources_needed': ['monitoring'],
            'rollback_possible': True
        })
        
        return options
    
    def _evaluate_option(self, option: Dict, context: Dict, 
                         analysis: Dict) -> float:
        """Đánh giá một phương án (0-1)"""
        score = 0.5  # Base score
        
        # Factor 1: Historical success rate
        pattern = self.decision_patterns.get(option['name'])
        if pattern:
            total = pattern['success_count'] + pattern['failure_count']
            if total > 0:
                success_rate = pattern['success_count'] / total
                score += success_rate * 0.2
        
        # Factor 2: Resource availability match
        resources = analysis['resource_availability']
        needed = option.get('resources_needed', [])
        available = sum(1 for r in needed if resources.get(f'{r}_available', 0) > 0)
        resource_score = available / len(needed) if needed else 1.0
        score += resource_score * 0.15
        
        # Factor 3: Urgency match
        urgency = analysis['urgency']
        if urgency > 0.7 and option['name'] == 'immediate_action':
            score += 0.2
        elif urgency < 0.3 and option['name'] == 'wait_and_see':
            score += 0.1
        
        # Factor 4: Risk consideration
        risk_level = analysis['risk_level']
        if risk_level == 'critical' and option.get('rollback_possible'):
            score += 0.1
        
        # Factor 5: Time efficiency
        if option['estimated_time'] < 300:  # Less than 5 minutes
            score += 0.05
        
        # Factor 6: Similar decision outcomes
        similar = analysis['historical_similarity']
        if similar and similar[0]['outcome'] == 'success':
            score += 0.1
        
        return min(max(score, 0.0), 1.0)
    
    def _assess_risks(self, option: Dict, context: Dict) -> List[str]:
        """Đánh giá rủi ro của một phương án"""
        risks = []
        
        if option['name'] == 'immediate_action':
            risks.append('May cause service disruption')
            risks.append('Limited testing time')
        
        if option['name'] == 'scheduled_maintenance':
            risks.append('Issue persists until maintenance window')
            risks.append('May affect more users')
        
        if not option.get('rollback_possible'):
            risks.append('Cannot rollback if fails')
        
        if context.get('affects_production'):
            risks.append('Affects production environment')
        
        return risks
    
    def _assess_benefits(self, option: Dict, context: Dict) -> List[str]:
        """Đánh giá lợi ích của một phương án"""
        benefits = []
        
        if option['name'] == 'immediate_action':
            benefits.append('Quick resolution')
            benefits.append('Minimizes user impact')
        
        if option['name'] == 'scheduled_maintenance':
            benefits.append('More time for testing')
            benefits.append('Lower risk during off-peak')
        
        if option['name'] == 'gradual_rollout':
            benefits.append('Early detection of issues')
            benefits.append('Limited blast radius')
        
        return benefits
    
    def _generate_reasoning(self, best: Dict, all_options: List[Dict]) -> str:
        """Sinh lý do cho quyết định"""
        reasoning = f"Selected '{best['option']['name']}' with score {best['score']:.2f}. "
        
        reasoning += f"Key factors: "
        
        if best['risks']:
            reasoning += f"Risks: {', '.join(best['risks'][:2])}. "
        
        if best['benefits']:
            reasoning += f"Benefits: {', '.join(best['benefits'][:2])}. "
        
        # Compare with alternatives
        alternatives = [o for o in all_options if o['index'] != best['option'].get('index', 0)]
        if alternatives:
            reasoning += f"Compared to {alternatives[0]['option']['name']} "
            reasoning += f"(score: {alternatives[0]['score']:.2f}), "
            reasoning += f"this option is preferred due to better risk/benefit ratio."
        
        return reasoning
    
    def _infer_decision_type(self, context: Dict) -> DecisionType:
        """Suy luận loại quyết định từ context"""
        if context.get('security_alert'):
            return DecisionType.FIX
        elif context.get('upgrade_available'):
            return DecisionType.UPGRADE
        elif context.get('deploy_ready'):
            return DecisionType.DEPLOY
        elif context.get('performance_issue'):
            return DecisionType.OPTIMIZE
        elif context.get('rollback_needed'):
            return DecisionType.ROLLBACK
        elif context.get('emergency'):
            return DecisionType.EMERGENCY
        else:
            return DecisionType.IGNORE
    
    def _create_escalation_decision(self, context: Dict, 
                                     reason: str) -> Decision:
        """Tạo quyết định escalate"""
        decision_id = self._generate_decision_id(context)
        
        decision = Decision(
            id=decision_id,
            type=DecisionType.ESCALATE,
            context=context,
            options=[],
            selected_option=0,
            confidence=0.0,
            reasoning=f"Escalated to human: {reason}",
            risks=[],
            benefits=[],
            requires_approval=True
        )
        
        self.decisions[decision_id] = decision
        return decision
    
    def execute_decision(self, decision_id: str) -> Dict:
        """Thực thi một quyết định"""
        if decision_id not in self.decisions:
            return {'error': f'Decision {decision_id} not found'}
        
        decision = self.decisions[decision_id]
        
        if decision.requires_approval and not decision.approved_by:
            return {'error': 'Decision requires approval'}
        
        logger.info(f"Executing decision: {decision_id}")
        
        decision.status = DecisionStatus.EXECUTED
        decision.executed_at = time.time()
        
        # Get handler
        handler = self.handlers.get(decision.type)
        
        if handler:
            try:
                result = handler(decision)
                decision.outcome = 'success'
                
                # Record success for learning
                if self.config['learning_enabled']:
                    self._record_outcome(decision, True)
                
                return {'success': True, 'result': result}
            
            except Exception as e:
                decision.status = DecisionStatus.FAILED
                decision.outcome = f'failed: {str(e)}'
                
                if self.config['learning_enabled']:
                    self._record_outcome(decision, False)
                
                return {'success': False, 'error': str(e)}
        else:
            return {'error': f'No handler for decision type {decision.type}'}
    
    def _record_outcome(self, decision: Decision, success: bool) -> None:
        """Ghi nhận kết quả để học hỏi"""
        option_name = decision.options[decision.selected_option]['name'] if decision.options else 'unknown'
        
        pattern = self.decision_patterns[option_name]
        
        if success:
            pattern['success_count'] += 1
        else:
            pattern['failure_count'] += 1
        
        # Update average confidence
        total = pattern['success_count'] + pattern['failure_count']
        pattern['avg_confidence'] = (
            (pattern['avg_confidence'] * (total - 1) + decision.confidence) / total
        )
        
        # Store context for future reference
        pattern['contexts'].append({
            'context': decision.context,
            'success': success,
            'timestamp': time.time()
        })
        
        # Keep only recent contexts
        pattern['contexts'] = pattern['contexts'][-100:]
    
    def resolve_conflict(self, decision_a_id: str, 
                         decision_b_id: str) -> Conflict:
        """Giải quyết xung đột giữa hai quyết định"""
        if decision_a_id not in self.decisions or decision_b_id not in self.decisions:
            return Conflict(
                id='invalid',
                decision_a=decision_a_id,
                decision_b=decision_b_id,
                conflict_type='not_found',
                description='One or both decisions not found'
            )
        
        decision_a = self.decisions[decision_a_id]
        decision_b = self.decisions[decision_b_id]
        
        conflict_id = f"conflict_{decision_a_id}_{decision_b_id}"
        
        # Analyze conflict
        conflict_type = self._analyze_conflict_type(decision_a, decision_b)
        
        conflict = Conflict(
            id=conflict_id,
            decision_a=decision_a_id,
            decision_b=decision_b_id,
            conflict_type=conflict_type,
            description=f"Conflict between {decision_a.type.value} and {decision_b.type.value}"
        )
        
        # Resolve based on strategy
        strategy = self.config['conflict_resolution_strategy']
        
        if strategy == 'priority_based':
            resolution = self._resolve_by_priority(decision_a, decision_b)
        elif strategy == 'confidence_based':
            resolution = self._resolve_by_confidence(decision_a, decision_b)
        elif strategy == 'urgency_based':
            resolution = self._resolve_by_urgency(decision_a, decision_b)
        else:
            resolution = self._resolve_by_priority(decision_a, decision_b)
        
        conflict.resolution = resolution
        conflict.resolved_at = time.time()
        
        self.conflicts[conflict_id] = conflict
        
        logger.info(f"Conflict resolved: {conflict_id} -> {resolution}")
        
        return conflict
    
    def _analyze_conflict_type(self, a: Decision, b: Decision) -> str:
        """Phân tích loại xung đột"""
        if a.type == b.type:
            return 'same_type'
        
        if a.type == DecisionType.ROLLBACK and b.type == DecisionType.DEPLOY:
            return 'rollback_vs_deploy'
        
        if a.type == DecisionType.UPGRADE and b.type == DecisionType.FIX:
            return 'upgrade_vs_fix'
        
        return 'general'
    
    def _resolve_by_priority(self, a: Decision, b: Decision) -> str:
        """Giải quyết dựa trên priority của decision type"""
        priority_order = {
            DecisionType.EMERGENCY: 1,
            DecisionType.FIX: 2,
            DecisionType.ROLLBACK: 3,
            DecisionType.UPGRADE: 4,
            DecisionType.DEPLOY: 5,
            DecisionType.OPTIMIZE: 6,
            DecisionType.EVOLVE: 7,
            DecisionType.IGNORE: 8
        }
        
        a_priority = priority_order.get(a.type, 99)
        b_priority = priority_order.get(b.type, 99)
        
        if a_priority < b_priority:
            return f"execute_{a.id}"
        elif b_priority < a_priority:
            return f"execute_{b.id}"
        else:
            return "execute_both_sequential"
    
    def _resolve_by_confidence(self, a: Decision, b: Decision) -> str:
        """Giải quyết dựa trên confidence score"""
        if a.confidence > b.confidence:
            return f"execute_{a.id}"
        elif b.confidence > a.confidence:
            return f"execute_{b.id}"
        else:
            return "execute_both_sequential"
    
    def _resolve_by_urgency(self, a: Decision, b: Decision) -> str:
        """Giải quyết dựa trên urgency"""
        a_urgency = a.context.get('urgency', 0)
        b_urgency = b.context.get('urgency', 0)
        
        if a_urgency > b_urgency:
            return f"execute_{a.id}"
        elif b_urgency > a_urgency:
            return f"execute_{b.id}"
        else:
            return "execute_both_sequential"
    
    def get_decision_stats(self) -> Dict:
        """Lấy thống kê về các quyết định"""
        total = len(self.decision_history)
        
        if total == 0:
            return {'total': 0}
        
        successful = sum(1 for d in self.decision_history if d.outcome == 'success')
        failed = sum(1 for d in self.decision_history if d.outcome and 'failed' in d.outcome)
        
        by_type = {}
        for d in self.decision_history:
            t = d.type.value
            if t not in by_type:
                by_type[t] = {'count': 0, 'success': 0}
            by_type[t]['count'] += 1
            if d.outcome == 'success':
                by_type[t]['success'] += 1
        
        return {
            'total': total,
            'successful': successful,
            'failed': failed,
            'success_rate': successful / total if total > 0 else 0,
            'avg_confidence': sum(d.confidence for d in self.decision_history) / total,
            'by_type': by_type,
            'pending_approval': sum(1 for d in self.decisions.values() 
                                   if d.requires_approval and d.status == DecisionStatus.PENDING)
        }


# Singleton instance
_engine_instance: Optional[DecisionEngine] = None


def get_decision_engine(config: Optional[Dict] = None) -> DecisionEngine:
    """Get singleton instance of DecisionEngine"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = DecisionEngine(config)
    return _engine_instance
