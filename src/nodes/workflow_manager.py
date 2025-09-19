"""
HR Workflow Manager for LangGraph-based Workflows
Orchestrates and manages workflow execution using LangGraph
"""

from typing import Dict, List, Any, Optional
from langgraph.graph import StateGraph, END
import asyncio
import logging
from datetime import datetime
import sqlite3
from pathlib import Path

from .workflow_nodes import HRWorkflowState, HRWorkflowNodes


class HRWorkflowManager:
    """Manages LangGraph-based HR workflows with persistent state"""
    
    def __init__(self, checkpoint_db_path: str = "hr_workflows.db"):
        self.checkpoint_db_path = checkpoint_db_path
        self.checkpointer = None  # Disabled for now due to import issues
        self.nodes = HRWorkflowNodes()
        self.graphs = {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize workflow graphs
        self._initialize_workflows()
    
    def _initialize_workflows(self):
        """Initialize all workflow graphs"""
        try:
            self.graphs = {
                "candidate_screening": self._build_screening_graph(),
                "interview_process": self._build_interview_graph(),
                "employee_onboarding": self._build_onboarding_graph(),
                "performance_review": self._build_performance_review_graph()
            }
            self.logger.info("All workflow graphs initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize workflows: {str(e)}")
            raise
    
    def _build_screening_graph(self) -> StateGraph:
        """Build the candidate screening workflow graph"""
        graph = StateGraph(HRWorkflowState)
        
        # Add nodes
        graph.add_node("screen_candidate", self.nodes.candidate_screening_node)
        graph.add_node("schedule_interview", self.nodes.interview_scheduling_node)
        graph.add_node("send_rejection", self.nodes.notification_node)
        graph.add_node("needs_review", self.nodes.notification_node)
        
        # Add conditional edges from screening
        graph.add_conditional_edges(
            "screen_candidate",
            self.nodes.decision_router_node,
            {
                "schedule_interview": "schedule_interview",
                "send_rejection": "send_rejection",
                "needs_review": "needs_review"
            }
        )
        
        # Add edges to end
        graph.add_edge("schedule_interview", END)
        graph.add_edge("send_rejection", END)
        graph.add_edge("needs_review", END)
        
        # Set entry point
        graph.set_entry_point("screen_candidate")
        
        return graph.compile()  # Checkpointer disabled for now
    
    def _build_interview_graph(self) -> StateGraph:
        """Build the interview process workflow graph"""
        graph = StateGraph(HRWorkflowState)
        
        # Add nodes
        graph.add_node("conduct_interview", self.nodes.interview_scheduling_node)
        graph.add_node("start_onboarding", self.nodes.onboarding_initiation_node)
        graph.add_node("send_rejection", self.nodes.notification_node)
        
        # Add conditional edges from interview
        graph.add_conditional_edges(
            "conduct_interview",
            self.nodes.decision_router_node,
            {
                "start_onboarding": "start_onboarding",
                "send_rejection": "send_rejection"
            }
        )
        
        # Add edges to end
        graph.add_edge("start_onboarding", END)
        graph.add_edge("send_rejection", END)
        
        # Set entry point
        graph.set_entry_point("conduct_interview")
        
        return graph.compile()  # Checkpointer disabled for now
    
    def _build_onboarding_graph(self) -> StateGraph:
        """Build the employee onboarding workflow graph"""
        graph = StateGraph(HRWorkflowState)
        
        # Add nodes
        graph.add_node("initiate_onboarding", self.nodes.onboarding_initiation_node)
        graph.add_node("send_welcome", self.nodes.notification_node)
        
        # Add edges
        graph.add_edge("initiate_onboarding", "send_welcome")
        graph.add_edge("send_welcome", END)
        
        # Set entry point
        graph.set_entry_point("initiate_onboarding")
        
        return graph.compile()  # Checkpointer disabled for now
    
    def _build_performance_review_graph(self) -> StateGraph:
        """Build the performance review workflow graph"""
        graph = StateGraph(HRWorkflowState)
        
        # Add nodes
        graph.add_node("create_review", self.nodes.performance_review_node)
        graph.add_node("notify_completion", self.nodes.notification_node)
        
        # Add edges
        graph.add_edge("create_review", "notify_completion")
        graph.add_edge("notify_completion", END)
        
        # Set entry point
        graph.set_entry_point("create_review")
        
        return graph.compile()  # Checkpointer disabled for now
    
    async def execute_workflow(
        self,
        workflow_type: str,
        initial_state: Dict[str, Any],
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a workflow with LangGraph"""
        try:
            if workflow_type not in self.graphs:
                raise ValueError(f"Unknown workflow type: {workflow_type}")
            
            graph = self.graphs[workflow_type]
            
            # Prepare initial state
            state = HRWorkflowState(
                workflow_id=workflow_type,
                execution_id=thread_id or f"{workflow_type}_{datetime.utcnow().timestamp()}",
                current_step="start",
                status="running",
                messages=[],
                documents=[],
                decisions={},
                metadata=initial_state.get("metadata", {}),
                screening_results={},
                interview_results={},
                onboarding_checklist=[],
                notifications_sent=[],
                errors=[],
                retry_count=0,
                started_at=datetime.utcnow().isoformat(),
                completed_at=None,
                **initial_state
            )
            
            # Execute workflow
            config = {"configurable": {"thread_id": thread_id}} if thread_id else {}
            
            result = await graph.ainvoke(state, config=config)
            
            # Mark as completed
            result["status"] = "completed" if not result.get("errors") else "failed"
            result["completed_at"] = datetime.utcnow().isoformat()
            
            self.logger.info(f"Workflow {workflow_type} completed with status: {result['status']}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {str(e)}")
            return {
                "status": "failed",
                "errors": [str(e)],
                "completed_at": datetime.utcnow().isoformat()
            }
    
    async def get_workflow_state(self, workflow_type: str, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get current state of a workflow"""
        try:
            if workflow_type not in self.graphs:
                return None
            
            graph = self.graphs[workflow_type]
            config = {"configurable": {"thread_id": thread_id}}
            
            # Get latest checkpoint
            checkpoint = await graph.aget_state(config)
            return checkpoint.values if checkpoint else None
            
        except Exception as e:
            self.logger.error(f"Failed to get workflow state: {str(e)}")
            return None
    
    async def resume_workflow(self, workflow_type: str, thread_id: str) -> Dict[str, Any]:
        """Resume a paused or failed workflow"""
        try:
            current_state = await self.get_workflow_state(workflow_type, thread_id)
            if not current_state:
                raise ValueError(f"No state found for workflow {workflow_type} with thread {thread_id}")
            
            # Resume execution
            graph = self.graphs[workflow_type]
            config = {"configurable": {"thread_id": thread_id}}
            
            result = await graph.ainvoke(None, config=config)
            
            self.logger.info(f"Workflow {workflow_type} resumed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to resume workflow: {str(e)}")
            return {"status": "failed", "errors": [str(e)]}
    
    def get_available_workflows(self) -> List[str]:
        """Get list of available workflow types"""
        return list(self.graphs.keys())
    
    async def cancel_workflow(self, workflow_type: str, thread_id: str) -> bool:
        """Cancel a running workflow"""
        try:
            # Note: LangGraph doesn't have built-in cancellation
            # This would typically involve updating the state to mark as cancelled
            current_state = await self.get_workflow_state(workflow_type, thread_id)
            if current_state:
                current_state["status"] = "cancelled"
                current_state["completed_at"] = datetime.utcnow().isoformat()
                # Would need to save this state back to the checkpoint
                self.logger.info(f"Workflow {workflow_type} marked as cancelled")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to cancel workflow: {str(e)}")
            return False
    
    def get_workflow_statistics(self) -> Dict[str, Any]:
        """Get statistics about workflow executions"""
        try:
            # This would query the checkpoint database for statistics
            # For now, return basic info
            return {
                "available_workflows": len(self.graphs),
                "workflow_types": list(self.graphs.keys()),
                "checkpoint_db": self.checkpoint_db_path
            }
        except Exception as e:
            self.logger.error(f"Failed to get workflow statistics: {str(e)}")
            return {}


# Global workflow manager instance
_workflow_manager: Optional[HRWorkflowManager] = None


def get_workflow_manager() -> HRWorkflowManager:
    """Get the global workflow manager instance"""
    global _workflow_manager
    if _workflow_manager is None:
        _workflow_manager = HRWorkflowManager()
    return _workflow_manager


# Convenience functions for common workflow operations
async def start_candidate_screening(candidate_id: str, job_id: str, **kwargs) -> Dict[str, Any]:
    """Start a candidate screening workflow"""
    manager = get_workflow_manager()
    initial_state = {
        "candidate_id": candidate_id,
        "job_id": job_id,
        "metadata": kwargs
    }
    return await manager.execute_workflow("candidate_screening", initial_state)


async def start_employee_onboarding(employee_id: str, **kwargs) -> Dict[str, Any]:
    """Start an employee onboarding workflow"""
    manager = get_workflow_manager()
    initial_state = {
        "employee_id": employee_id,
        "metadata": kwargs
    }
    return await manager.execute_workflow("employee_onboarding", initial_state)


async def start_performance_review(employee_id: str, reviewer_id: str, **kwargs) -> Dict[str, Any]:
    """Start a performance review workflow"""
    manager = get_workflow_manager()
    initial_state = {
        "employee_id": employee_id,
        "metadata": {"reviewer_id": reviewer_id, **kwargs}
    }
    return await manager.execute_workflow("performance_review", initial_state)