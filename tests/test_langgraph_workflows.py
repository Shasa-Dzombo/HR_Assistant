"""
Integration tests for LangGraph HR workflows
Tests the complete workflow execution with mocked dependencies
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from nodes.workflow_manager import HRWorkflowManager
from nodes.workflow_nodes import HRWorkflowState
from src.utils.ai_client import AIClient, AIResponse


@pytest.fixture
def mock_ai_client():
    """Mock AI client for testing"""
    client = Mock(spec=AIClient)
    
    # Mock screening response
    client.get_completion_async.return_value = AIResponse(
        content='{"score": 85, "recommendation": "proceed", "strengths": ["Strong Python skills", "Good communication"], "concerns": ["Limited ML experience"]}',
        model="gemini-2.0-flash-exp",
        tokens_used=150,
        cost_estimate=0.002,
        success=True
    )
    
    return client


@pytest.fixture
def mock_db_manager():
    """Mock database manager for testing"""
    db = AsyncMock()
    
    # Mock candidate data
    db.get_candidate.return_value = {
        "id": "candidate_123",
        "name": "John Doe",
        "email": "john.doe@email.com",
        "experience": "5 years Python development",
        "skills": ["Python", "FastAPI", "PostgreSQL"],
        "education": "BS Computer Science",
        "resume_summary": "Experienced Python developer with web API expertise"
    }
    
    # Mock employee data
    db.get_employee.return_value = {
        "id": "emp_789",
        "name": "Jane Smith",
        "email": "jane.smith@company.com",
        "position": "Senior Developer",
        "department": "Engineering",
        "start_date": "2025-09-24",
        "manager_id": "mgr_101"
    }
    
    # Mock creation methods
    db.create_interview.return_value = "interview_456"
    db.create_onboarding.return_value = "onboarding_789"
    db.create_performance_review.return_value = "review_101"
    
    return db


@pytest.fixture
def mock_email_service():
    """Mock email service for testing"""
    email = AsyncMock()
    
    # Mock all email methods
    email.send_interview_notification.return_value = True
    email.send_welcome_email.return_value = True
    email.send_rejection_notification.return_value = True
    email.send_notification.return_value = True
    
    return email


@pytest.fixture
def workflow_manager(mock_ai_client, mock_db_manager, mock_email_service):
    """Create workflow manager with mocked dependencies"""
    
    with patch('src.nodes.langgraph_workflows.AIClient', return_value=mock_ai_client), \
         patch('src.nodes.langgraph_workflows.DatabaseManager', return_value=mock_db_manager), \
         patch('src.nodes.langgraph_workflows.EmailService', return_value=mock_email_service):
        
        manager = HRWorkflowManager(checkpoint_db_path=":memory:")
        return manager


class TestRecruitmentWorkflow:
    """Test the recruitment workflow"""
    
    @pytest.mark.asyncio
    async def test_successful_recruitment_workflow(self, workflow_manager):
        """Test a successful recruitment workflow execution"""
        
        initial_state = {
            "candidate_id": "candidate_123",
            "job_id": "job_456",
            "metadata": {
                "job_requirements": "Python, FastAPI, 3+ years experience",
                "position_title": "Senior Developer"
            }
        }
        
        result = await workflow_manager.execute_workflow(
            workflow_type="recruitment",
            initial_state=initial_state,
            thread_id="test_recruitment_123"
        )
        
        # Verify workflow completed successfully
        assert result["status"] == "completed"
        assert result["candidate_id"] == "candidate_123"
        assert len(result["messages"]) > 0
        assert "screening_results" in result
        assert len(result["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_recruitment_workflow_with_rejection(self, workflow_manager, mock_ai_client):
        """Test recruitment workflow that results in rejection"""
        
        # Mock AI to return rejection recommendation
        mock_ai_client.get_completion_async.return_value = AIResponse(
            content='{"score": 45, "recommendation": "reject", "concerns": ["Insufficient experience", "Poor communication skills"]}',
            model="gemini-2.0-flash-exp",
            tokens_used=120,
            cost_estimate=0.002,
            success=True
        )
        
        initial_state = {
            "candidate_id": "candidate_456",
            "job_id": "job_789",
            "metadata": {
                "job_requirements": "Senior level requirements",
                "notification_type": "rejection"
            }
        }
        
        result = await workflow_manager.execute_workflow(
            workflow_type="recruitment",
            initial_state=initial_state,
            thread_id="test_recruitment_rejection"
        )
        
        # Verify workflow handled rejection properly
        assert result["status"] == "completed"
        assert "screening_results" in result
        # Should have sent rejection notification
        assert any(notif["type"] == "rejection" for notif in result.get("notifications_sent", []))
    
    @pytest.mark.asyncio
    async def test_recruitment_workflow_missing_candidate(self, workflow_manager, mock_db_manager):
        """Test recruitment workflow with missing candidate"""
        
        # Mock database to return None for candidate
        mock_db_manager.get_candidate.return_value = None
        
        initial_state = {
            "candidate_id": "nonexistent_candidate",
            "job_id": "job_123"
        }
        
        result = await workflow_manager.execute_workflow(
            workflow_type="recruitment",
            initial_state=initial_state,
            thread_id="test_recruitment_missing"
        )
        
        # Verify workflow handled missing candidate
        assert len(result["errors"]) > 0
        assert any("not found" in error for error in result["errors"])


class TestOnboardingWorkflow:
    """Test the onboarding workflow"""
    
    @pytest.mark.asyncio
    async def test_successful_onboarding_workflow(self, workflow_manager):
        """Test a successful onboarding workflow execution"""
        
        initial_state = {
            "employee_id": "emp_789",
            "metadata": {
                "start_date": "2025-09-24",
                "position": "Senior Developer",
                "department": "Engineering"
            }
        }
        
        result = await workflow_manager.execute_workflow(
            workflow_type="onboarding",
            initial_state=initial_state,
            thread_id="test_onboarding_789"
        )
        
        # Verify workflow completed successfully
        assert result["status"] == "completed"
        assert result["employee_id"] == "emp_789"
        assert "onboarding_checklist" in result
        assert len(result["notifications_sent"]) > 0
        assert len(result["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_onboarding_workflow_missing_employee(self, workflow_manager, mock_db_manager):
        """Test onboarding workflow with missing employee"""
        
        # Mock database to return None for employee  
        mock_db_manager.get_employee.return_value = None
        
        initial_state = {
            "employee_id": "nonexistent_employee"
        }
        
        result = await workflow_manager.execute_workflow(
            workflow_type="onboarding",
            initial_state=initial_state,
            thread_id="test_onboarding_missing"
        )
        
        # Verify workflow handled missing employee
        assert len(result["errors"]) > 0
        assert any("not found" in error for error in result["errors"])


class TestPerformanceReviewWorkflow:
    """Test the performance review workflow"""
    
    @pytest.mark.asyncio
    async def test_successful_performance_review_workflow(self, workflow_manager):
        """Test a successful performance review workflow execution"""
        
        initial_state = {
            "employee_id": "emp_789",
            "metadata": {
                "review_period": "Q4 2025",
                "reviewer_id": "mgr_101",
                "review_type": "quarterly"
            }
        }
        
        result = await workflow_manager.execute_workflow(
            workflow_type="performance_review",
            initial_state=initial_state,
            thread_id="test_review_789"
        )
        
        # Verify workflow completed successfully
        assert result["status"] == "completed"
        assert result["employee_id"] == "emp_789"
        assert "performance_review_id" in result
        assert len(result["notifications_sent"]) > 0
        assert len(result["errors"]) == 0


class TestWorkflowStateManagement:
    """Test workflow state persistence and resumption"""
    
    @pytest.mark.asyncio
    async def test_workflow_state_persistence(self, workflow_manager):
        """Test that workflow state is properly persisted"""
        
        thread_id = "test_state_persistence"
        initial_state = {
            "candidate_id": "candidate_state_test",
            "job_id": "job_state_test"
        }
        
        # Execute workflow
        result = await workflow_manager.execute_workflow(
            workflow_type="recruitment",
            initial_state=initial_state,
            thread_id=thread_id
        )
        
        # Get workflow state
        state = await workflow_manager.get_workflow_state("recruitment", thread_id)
        
        # Verify state was persisted
        assert state is not None
        assert state["candidate_id"] == "candidate_state_test"
        assert state["job_id"] == "job_state_test"
        assert "execution_id" in state
        assert "started_at" in state
    
    @pytest.mark.asyncio
    async def test_workflow_state_nonexistent(self, workflow_manager):
        """Test getting state for nonexistent workflow"""
        
        state = await workflow_manager.get_workflow_state("recruitment", "nonexistent_thread")
        
        # Should return None for nonexistent workflow
        assert state is None


class TestWorkflowErrorHandling:
    """Test workflow error handling and resilience"""
    
    @pytest.mark.asyncio
    async def test_workflow_with_ai_error(self, workflow_manager, mock_ai_client):
        """Test workflow handling when AI service fails"""
        
        # Mock AI client to raise an exception
        mock_ai_client.get_completion_async.side_effect = Exception("AI service unavailable")
        
        initial_state = {
            "candidate_id": "candidate_ai_error",
            "job_id": "job_ai_error"
        }
        
        result = await workflow_manager.execute_workflow(
            workflow_type="recruitment",
            initial_state=initial_state,
            thread_id="test_ai_error"
        )
        
        # Verify error was captured but workflow didn't crash
        assert len(result["errors"]) > 0
        assert any("AI service unavailable" in error for error in result["errors"])
    
    @pytest.mark.asyncio
    async def test_workflow_with_database_error(self, workflow_manager, mock_db_manager):
        """Test workflow handling when database fails"""
        
        # Mock database to raise an exception
        mock_db_manager.get_candidate.side_effect = Exception("Database connection failed")
        
        initial_state = {
            "candidate_id": "candidate_db_error",
            "job_id": "job_db_error"
        }
        
        result = await workflow_manager.execute_workflow(
            workflow_type="recruitment",
            initial_state=initial_state,
            thread_id="test_db_error"
        )
        
        # Verify error was captured
        assert len(result["errors"]) > 0
        assert any("Database connection failed" in error for error in result["errors"])


# Integration test runner
@pytest.mark.asyncio
async def test_full_integration():
    """Run a comprehensive integration test"""
    
    print("Running LangGraph HR Workflow Integration Tests...")
    
    # This would be run with actual services in a full integration environment
    # For now, we rely on the unit tests above with mocked dependencies
    
    pass


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])