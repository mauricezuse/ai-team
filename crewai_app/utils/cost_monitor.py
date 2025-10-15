"""
Cost Monitoring System

This module provides real-time cost tracking and budget management for AI agent workflows.
It prevents over-spending on simple tasks by monitoring message costs and enforcing limits.

Based on analysis of workflow 18 (NEGISHI-200):
- Simple task: 99 messages, $6.14 cost (12x over-engineered)
- Target: 20 messages, $1.00 cost (75% message reduction, 84% cost reduction)
"""

import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)

class BudgetStatus(Enum):
    """Budget status indicators."""
    WITHIN_BUDGET = "within_budget"
    APPROACHING_LIMIT = "approaching_limit"
    BUDGET_EXCEEDED = "budget_exceeded"
    MESSAGE_LIMIT_EXCEEDED = "message_limit_exceeded"
    TIME_LIMIT_EXCEEDED = "time_limit_exceeded"

@dataclass
class CostEntry:
    """Individual cost entry for tracking."""
    timestamp: float
    agent: str
    step: str
    message_cost: float
    token_count: int
    message_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BudgetLimits:
    """Budget limits for workflow execution."""
    max_cost: float
    max_messages: int
    max_duration: int  # seconds
    warning_threshold: float = 0.8  # 80% of budget

@dataclass
class CostSummary:
    """Summary of costs and usage."""
    total_cost: float
    total_messages: int
    total_tokens: int
    duration: float
    average_cost_per_message: float
    cost_by_agent: Dict[str, float]
    cost_by_step: Dict[str, float]
    budget_status: BudgetStatus
    efficiency_score: float

class CostMonitor:
    """
    Real-time cost monitoring and budget management for AI agent workflows.
    
    Prevents over-engineering by enforcing strict limits on simple tasks
    and providing early warnings for budget approaching limits.
    """
    
    def __init__(self, workflow_config: Dict[str, Any]):
        """
        Initialize cost monitor with workflow configuration.
        
        Args:
            workflow_config: Configuration with max_cost, max_messages, max_duration
        """
        self.limits = BudgetLimits(
            max_cost=workflow_config.get('max_cost', 10.0),
            max_messages=workflow_config.get('max_messages', 100),
            max_duration=workflow_config.get('max_duration', 3600),
            warning_threshold=workflow_config.get('warning_threshold', 0.8)
        )
        
        self.cost_entries: List[CostEntry] = []
        self.start_time = time.time()
        self.current_cost = 0.0
        self.current_messages = 0
        self.current_tokens = 0
        
        # Callbacks for budget events
        self.budget_callbacks: List[Callable[[BudgetStatus, CostSummary], None]] = []
        
        logger.info(f"CostMonitor initialized with limits: ${self.limits.max_cost:.2f}, "
                   f"{self.limits.max_messages} messages, {self.limits.max_duration}s")
    
    def add_cost_entry(self, agent: str, step: str, message_cost: float, 
                      token_count: int = 0, metadata: Dict[str, Any] = None) -> BudgetStatus:
        """
        Add a cost entry and check budget status.
        
        Args:
            agent: Agent name that generated the cost
            step: Workflow step name
            message_cost: Cost of the message
            token_count: Number of tokens used
            metadata: Additional metadata
            
        Returns:
            BudgetStatus indicating current budget state
        """
        if metadata is None:
            metadata = {}
        
        # Create cost entry
        entry = CostEntry(
            timestamp=time.time(),
            agent=agent,
            step=step,
            message_cost=message_cost,
            token_count=token_count,
            message_count=1,
            metadata=metadata
        )
        
        # Update totals
        self.cost_entries.append(entry)
        self.current_cost += message_cost
        self.current_messages += 1
        self.current_tokens += token_count
        
        # Check budget status
        status = self._check_budget_status()
        
        # Log cost entry
        logger.info(f"Cost entry added: {agent}.{step} = ${message_cost:.4f} "
                   f"(Total: ${self.current_cost:.2f}/{self.limits.max_cost:.2f}, "
                   f"Messages: {self.current_messages}/{self.limits.max_messages})")
        
        # Trigger callbacks if budget status changed
        if status != BudgetStatus.WITHIN_BUDGET:
            self._trigger_budget_callbacks(status)
        
        return status
    
    def check_budget(self, message_cost: float = 0.0) -> BudgetStatus:
        """
        Check current budget status without adding a new entry.
        
        Args:
            message_cost: Optional projected cost for next message
            
        Returns:
            BudgetStatus indicating current budget state
        """
        projected_cost = self.current_cost + message_cost
        projected_messages = self.current_messages + 1
        
        # Check if adding this cost would exceed limits
        if projected_cost > self.limits.max_cost:
            return BudgetStatus.BUDGET_EXCEEDED
        if projected_messages > self.limits.max_messages:
            return BudgetStatus.MESSAGE_LIMIT_EXCEEDED
        if self._get_elapsed_time() > self.limits.max_duration:
            return BudgetStatus.TIME_LIMIT_EXCEEDED
        
        # Check if approaching limits
        cost_ratio = projected_cost / self.limits.max_cost
        message_ratio = projected_messages / self.limits.max_messages
        
        if cost_ratio >= self.limits.warning_threshold or message_ratio >= self.limits.warning_threshold:
            return BudgetStatus.APPROACHING_LIMIT
        
        return BudgetStatus.WITHIN_BUDGET
    
    def should_terminate(self) -> bool:
        """
        Check if workflow should be terminated due to budget limits.
        
        Returns:
            True if workflow should be terminated
        """
        return (self.current_cost > self.limits.max_cost or 
                self.current_messages > self.limits.max_messages or
                self._get_elapsed_time() > self.limits.max_duration)
    
    def get_cost_summary(self) -> CostSummary:
        """
        Get comprehensive cost summary.
        
        Returns:
            CostSummary with detailed cost analysis
        """
        # Calculate cost by agent
        cost_by_agent = {}
        for entry in self.cost_entries:
            agent = entry.agent
            cost_by_agent[agent] = cost_by_agent.get(agent, 0.0) + entry.message_cost
        
        # Calculate cost by step
        cost_by_step = {}
        for entry in self.cost_entries:
            step = entry.step
            cost_by_step[step] = cost_by_step.get(step, 0.0) + entry.message_cost
        
        # Calculate efficiency score (0-1, higher is better)
        efficiency_score = self._calculate_efficiency_score()
        
        return CostSummary(
            total_cost=self.current_cost,
            total_messages=self.current_messages,
            total_tokens=self.current_tokens,
            duration=self._get_elapsed_time(),
            average_cost_per_message=self.current_cost / max(self.current_messages, 1),
            cost_by_agent=cost_by_agent,
            cost_by_step=cost_by_step,
            budget_status=self._check_budget_status(),
            efficiency_score=efficiency_score
        )
    
    def add_budget_callback(self, callback: Callable[[BudgetStatus, CostSummary], None]):
        """
        Add callback for budget status changes.
        
        Args:
            callback: Function to call when budget status changes
        """
        self.budget_callbacks.append(callback)
    
    def get_remaining_budget(self) -> Dict[str, float]:
        """
        Get remaining budget information.
        
        Returns:
            Dictionary with remaining cost, messages, and time
        """
        return {
            "remaining_cost": max(0, self.limits.max_cost - self.current_cost),
            "remaining_messages": max(0, self.limits.max_messages - self.current_messages),
            "remaining_time": max(0, self.limits.max_duration - self._get_elapsed_time()),
            "cost_ratio": self.current_cost / self.limits.max_cost,
            "message_ratio": self.current_messages / self.limits.max_messages,
            "time_ratio": self._get_elapsed_time() / self.limits.max_duration
        }
    
    def export_cost_data(self) -> Dict[str, Any]:
        """
        Export cost data for analysis and reporting.
        
        Returns:
            Dictionary with cost data and metadata
        """
        return {
            "limits": {
                "max_cost": self.limits.max_cost,
                "max_messages": self.limits.max_messages,
                "max_duration": self.limits.max_duration,
                "warning_threshold": self.limits.warning_threshold
            },
            "current_usage": {
                "total_cost": self.current_cost,
                "total_messages": self.current_messages,
                "total_tokens": self.current_tokens,
                "duration": self._get_elapsed_time()
            },
            "cost_entries": [
                {
                    "timestamp": entry.timestamp,
                    "agent": entry.agent,
                    "step": entry.step,
                    "message_cost": entry.message_cost,
                    "token_count": entry.token_count,
                    "message_count": entry.message_count,
                    "metadata": entry.metadata
                }
                for entry in self.cost_entries
            ],
            "summary": self.get_cost_summary().__dict__
        }
    
    def _check_budget_status(self) -> BudgetStatus:
        """Check current budget status."""
        if self.current_cost > self.limits.max_cost:
            return BudgetStatus.BUDGET_EXCEEDED
        if self.current_messages > self.limits.max_messages:
            return BudgetStatus.MESSAGE_LIMIT_EXCEEDED
        if self._get_elapsed_time() > self.limits.max_duration:
            return BudgetStatus.TIME_LIMIT_EXCEEDED
        
        # Check if approaching limits
        cost_ratio = self.current_cost / self.limits.max_cost
        message_ratio = self.current_messages / self.limits.max_messages
        
        if cost_ratio >= self.limits.warning_threshold or message_ratio >= self.limits.warning_threshold:
            return BudgetStatus.APPROACHING_LIMIT
        
        return BudgetStatus.WITHIN_BUDGET
    
    def _get_elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        return time.time() - self.start_time
    
    def _calculate_efficiency_score(self) -> float:
        """
        Calculate efficiency score (0-1, higher is better).
        
        Based on cost per message, time efficiency, and budget utilization.
        """
        if self.current_messages == 0:
            return 1.0
        
        # Cost efficiency (lower cost per message is better)
        cost_efficiency = max(0, 1.0 - (self.current_cost / self.limits.max_cost))
        
        # Message efficiency (fewer messages is better)
        message_efficiency = max(0, 1.0 - (self.current_messages / self.limits.max_messages))
        
        # Time efficiency (faster completion is better)
        time_efficiency = max(0, 1.0 - (self._get_elapsed_time() / self.limits.max_duration))
        
        # Weighted average
        efficiency_score = (cost_efficiency * 0.5 + message_efficiency * 0.3 + time_efficiency * 0.2)
        
        return round(efficiency_score, 3)
    
    def _trigger_budget_callbacks(self, status: BudgetStatus):
        """Trigger budget status change callbacks."""
        summary = self.get_cost_summary()
        for callback in self.budget_callbacks:
            try:
                callback(status, summary)
            except Exception as e:
                logger.error(f"Error in budget callback: {e}")

# Example usage and testing
if __name__ == "__main__":
    # Test with simple task configuration
    simple_config = {
        "max_cost": 1.00,
        "max_messages": 20,
        "max_duration": 1800,  # 30 minutes
        "warning_threshold": 0.8
    }
    
    monitor = CostMonitor(simple_config)
    
    # Add some cost entries
    monitor.add_cost_entry("planner", "analyze_story", 0.15)
    monitor.add_cost_entry("developer", "implement_task", 0.25)
    monitor.add_cost_entry("frontend", "implement_ui", 0.20)
    
    # Check budget status
    status = monitor.check_budget()
    print(f"Budget Status: {status}")
    
    # Get cost summary
    summary = monitor.get_cost_summary()
    print(f"Total Cost: ${summary.total_cost:.2f}")
    print(f"Total Messages: {summary.total_messages}")
    print(f"Efficiency Score: {summary.efficiency_score}")
    
    # Check if should terminate
    should_terminate = monitor.should_terminate()
    print(f"Should Terminate: {should_terminate}")
    
    # Export cost data
    cost_data = monitor.export_cost_data()
    print(f"Cost Data: {json.dumps(cost_data, indent=2)}")
