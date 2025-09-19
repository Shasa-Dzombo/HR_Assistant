"""
HR Workflow Examples using LangGraph
Demonstrates usage of the new LangGraph-based workflow system
"""

import asyncio
from typing import Dict, Any
from datetime import datetime

from .workflow_manager import get_workflow_manager


async def example_recruitment_workflow():
    """Example of running a complete recruitment workflow"""
    
    workflow_manager = get_workflow_manager()
    
    # Initial state for recruitment workflow
    initial_state = {
        "candidate_id": "candidate_123",
        "job_id": "job_456",
        "metadata": {
            "job_requirements": """
            Required Skills:
            - Python programming (3+ years)
            - Machine learning experience
            - Strong communication skills
            - Bachelor's degree in Computer Science
            
            Preferred:
            - FastAPI experience
            - HR domain knowledge
            - Team leadership experience
            """,
            "position_title": "Senior AI Developer",
            "department": "Engineering"
        }
    }
    
    print("🚀 Starting recruitment workflow...")
    
    # Execute recruitment workflow
    result = await workflow_manager.execute_workflow(
        workflow_type="recruitment",
        initial_state=initial_state,
        thread_id="recruitment_candidate_123"
    )
    
    print(f"✅ Recruitment workflow completed with status: {result['status']}")
    print(f"📧 Notifications sent: {len(result.get('notifications_sent', []))}")
    print(f"💬 Messages: {len(result.get('messages', []))}")
    
    if result.get('errors'):
        print(f"❌ Errors: {result['errors']}")
    
    return result


async def example_onboarding_workflow():
    """Example of running an onboarding workflow"""
    
    workflow_manager = get_workflow_manager()
    
    # Initial state for onboarding workflow
    initial_state = {
        "employee_id": "emp_789",
        "metadata": {
            "start_date": "2025-09-24",
            "position": "Senior AI Developer",
            "department": "Engineering",
            "manager_id": "mgr_101",
            "buddy_id": "emp_555"
        }
    }
    
    print("🎯 Starting onboarding workflow...")
    
    # Execute onboarding workflow
    result = await workflow_manager.execute_workflow(
        workflow_type="onboarding",
        initial_state=initial_state,
        thread_id="onboarding_emp_789"
    )
    
    print(f"✅ Onboarding workflow completed with status: {result['status']}")
    print(f"📋 Onboarding checklist created: {bool(result.get('onboarding_checklist'))}")
    print(f"📧 Welcome notifications sent: {len(result.get('notifications_sent', []))}")
    
    if result.get('errors'):
        print(f"❌ Errors: {result['errors']}")
    
    return result


async def example_performance_review_workflow():
    """Example of running a performance review workflow"""
    
    workflow_manager = get_workflow_manager()
    
    # Initial state for performance review workflow
    initial_state = {
        "employee_id": "emp_789",
        "metadata": {
            "review_period": "Q4 2025",
            "reviewer_id": "mgr_101",
            "review_type": "quarterly",
            "goals_from_last_period": [
                "Complete AI chatbot project",
                "Mentor 2 junior developers",
                "Improve code review process"
            ]
        }
    }
    
    print("📊 Starting performance review workflow...")
    
    # Execute performance review workflow
    result = await workflow_manager.execute_workflow(
        workflow_type="performance_review",
        initial_state=initial_state,
        thread_id="review_emp_789_q4_2025"
    )
    
    print(f"✅ Performance review workflow completed with status: {result['status']}")
    print(f"📝 Review created: {bool(result.get('performance_review_id'))}")
    print(f"📧 Review notifications sent: {len(result.get('notifications_sent', []))}")
    
    if result.get('errors'):
        print(f"❌ Errors: {result['errors']}")
    
    return result


async def example_workflow_state_management():
    """Example of workflow state management and resumption"""
    
    workflow_manager = get_workflow_manager()
    
    print("🔄 Demonstrating workflow state management...")
    
    # Start a workflow
    thread_id = "state_demo_workflow"
    initial_state = {
        "candidate_id": "candidate_999",
        "job_id": "job_888",
        "metadata": {"position": "HR Specialist"}
    }
    
    # Execute workflow (this will save state at each step)
    result = await workflow_manager.execute_workflow(
        workflow_type="recruitment",
        initial_state=initial_state,
        thread_id=thread_id
    )
    
    print(f"✅ Initial workflow execution completed")
    
    # Get current state
    current_state = await workflow_manager.get_workflow_state("recruitment", thread_id)
    
    if current_state:
        print(f"📊 Current workflow state:")
        print(f"   - Status: {current_state.get('status')}")
        print(f"   - Messages: {len(current_state.get('messages', []))}")
        print(f"   - Notifications: {len(current_state.get('notifications_sent', []))}")
        print(f"   - Started: {current_state.get('started_at')}")
        print(f"   - Completed: {current_state.get('completed_at')}")
    
    return result


async def example_parallel_workflows():
    """Example of running multiple workflows in parallel"""
    
    workflow_manager = get_workflow_manager()
    
    print("⚡ Running multiple workflows in parallel...")
    
    # Create multiple workflow tasks
    tasks = []
    
    # Recruitment workflow
    recruitment_task = workflow_manager.execute_workflow(
        workflow_type="recruitment",
        initial_state={
            "candidate_id": "candidate_parallel_1",
            "job_id": "job_parallel",
            "metadata": {"position": "Data Scientist"}
        },
        thread_id="parallel_recruitment_1"
    )
    tasks.append(("recruitment", recruitment_task))
    
    # Onboarding workflow
    onboarding_task = workflow_manager.execute_workflow(
        workflow_type="onboarding",
        initial_state={
            "employee_id": "emp_parallel_1",
            "metadata": {"position": "Software Engineer", "start_date": "2025-09-20"}
        },
        thread_id="parallel_onboarding_1"
    )
    tasks.append(("onboarding", onboarding_task))
    
    # Performance review workflow
    review_task = workflow_manager.execute_workflow(
        workflow_type="performance_review",
        initial_state={
            "employee_id": "emp_parallel_2",
            "metadata": {"review_period": "Q4 2025", "reviewer_id": "mgr_parallel"}
        },
        thread_id="parallel_review_1"
    )
    tasks.append(("performance_review", review_task))
    
    # Wait for all workflows to complete
    results = {}
    for workflow_type, task in tasks:
        result = await task
        results[workflow_type] = result
        print(f"✅ {workflow_type} workflow completed with status: {result['status']}")
    
    print(f"🎉 All {len(results)} parallel workflows completed!")
    
    return results


async def run_all_examples():
    """Run all workflow examples"""
    
    print("=" * 60)
    print("🤖 HR Assistant LangGraph Workflow Examples")
    print("=" * 60)
    
    try:
        # Individual workflow examples
        print("\n1️⃣ Recruitment Workflow Example")
        await example_recruitment_workflow()
        
        print("\n2️⃣ Onboarding Workflow Example")  
        await example_onboarding_workflow()
        
        print("\n3️⃣ Performance Review Workflow Example")
        await example_performance_review_workflow()
        
        print("\n4️⃣ Workflow State Management Example")
        await example_workflow_state_management()
        
        print("\n5️⃣ Parallel Workflows Example")
        await example_parallel_workflows()
        
        print("\n" + "=" * 60)
        print("🎉 All workflow examples completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error running examples: {str(e)}")
        raise


if __name__ == "__main__":
    # Run examples
    asyncio.run(run_all_examples())