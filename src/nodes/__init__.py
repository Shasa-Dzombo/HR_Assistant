"""
Nodes package - LangGraph-based workflow system
"""

from .workflow_nodes import HRWorkflowState, HRWorkflowNodes
from .workflow_manager import (
    HRWorkflowManager,
    get_workflow_manager,
    start_candidate_screening,
    start_employee_onboarding,
    start_performance_review
)
from .workflow_examples import (
    example_recruitment_workflow,
    example_onboarding_workflow,
    example_performance_review_workflow,
    run_all_examples
)

__all__ = [
    "HRWorkflowState",
    "HRWorkflowNodes",
    "HRWorkflowManager",
    "get_workflow_manager",
    "start_candidate_screening",
    "start_employee_onboarding",
    "start_performance_review",
    "example_recruitment_workflow",
    "example_onboarding_workflow", 
    "example_performance_review_workflow",
    "run_all_examples"
]