"""
HR Workflow Nodes for LangGraph-based Workflows
Contains individual workflow nodes and state definitions
"""

from typing import Dict, List, Any, Optional, TypedDict, Literal
from langchain_core.messages import HumanMessage, AIMessage
import logging
from datetime import datetime

from ..utils.ai_client import AIClient
from ..utils.database import DatabaseManager
from ..utils.email_service import EmailService


class HRWorkflowState(TypedDict):
    """State structure for HR workflows using LangGraph"""
    
    # Core workflow data
    workflow_id: str
    execution_id: str
    current_step: str
    status: Literal["running", "completed", "failed", "paused"]
    
    # HR-specific data
    candidate_id: Optional[str]
    employee_id: Optional[str]
    job_id: Optional[str]
    interview_id: Optional[str]
    performance_review_id: Optional[str]
    
    # Workflow context
    messages: List[Dict[str, Any]]
    documents: List[Dict[str, Any]]
    decisions: Dict[str, Any]
    metadata: Dict[str, Any]
    
    # Results and outputs
    screening_results: Dict[str, Any]
    interview_results: Dict[str, Any]
    onboarding_checklist: List[Dict[str, Any]]
    notifications_sent: List[Dict[str, Any]]
    
    # Error handling
    errors: List[str]
    retry_count: int
    
    # Timestamps
    started_at: str
    completed_at: Optional[str]


class HRWorkflowNodes:
    """LangGraph nodes for HR workflows"""
    
    def __init__(self):
        self.ai_client = AIClient()
        self.db_manager = DatabaseManager()
        self.email_service = EmailService()
        self.logger = logging.getLogger(__name__)
    
    async def candidate_screening_node(self, state: HRWorkflowState) -> HRWorkflowState:
        """Screen candidates using AI analysis"""
        try:
            candidate_id = state.get("candidate_id")
            if not candidate_id:
                state["errors"].append("No candidate ID provided for screening")
                return state
            
            # Get candidate data
            candidate = await self.db_manager.get_candidate(candidate_id)
            if not candidate:
                state["errors"].append(f"Candidate {candidate_id} not found")
                return state
            
            # AI-powered screening
            screening_prompt = f"""
            Screen this candidate for the position:
            
            Name: {candidate.get('name', 'Unknown')}
            Experience: {candidate.get('experience', 'Not provided')}
            Skills: {candidate.get('skills', [])}
            Education: {candidate.get('education', 'Not provided')}
            Resume Summary: {candidate.get('resume_summary', 'Not provided')}
            
            Job Requirements: {state.get('metadata', {}).get('job_requirements', 'General requirements')}
            
            Provide screening results in JSON format with:
            - score: 0-100
            - strengths: list of strengths
            - concerns: list of concerns
            - recommendation: "proceed", "reject", or "needs_review"
            - reasoning: explanation
            """
            
            screening_response = await self.ai_client.get_completion_async(
                screening_prompt,
                temperature=0.3
            )
            
            # Store screening results
            state["screening_results"] = {
                "candidate_id": candidate_id,
                "ai_analysis": screening_response.content,
                "timestamp": datetime.utcnow().isoformat(),
                "screener": "AI_Assistant"
            }
            
            # Add message to workflow
            state["messages"].append({
                "type": "screening",
                "content": f"Candidate {candidate.get('name')} screened",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            self.logger.info(f"Completed screening for candidate {candidate_id}")
            
        except Exception as e:
            error_msg = f"Screening failed: {str(e)}"
            state["errors"].append(error_msg)
            self.logger.error(error_msg)
        
        return state
    
    async def interview_scheduling_node(self, state: HRWorkflowState) -> HRWorkflowState:
        """Schedule interviews based on screening results"""
        try:
            screening_results = state.get("screening_results", {})
            if not screening_results:
                state["errors"].append("No screening results available for interview scheduling")
                return state
            
            # Check if candidate should proceed to interview
            ai_analysis = screening_results.get("ai_analysis", "")
            if "reject" in ai_analysis.lower():
                state["messages"].append({
                    "type": "decision",
                    "content": "Candidate rejected - no interview needed",
                    "timestamp": datetime.utcnow().isoformat()
                })
                return state
            
            candidate_id = screening_results.get("candidate_id")
            
            # Create interview record
            interview_data = {
                "candidate_id": candidate_id,
                "job_id": state.get("job_id"),
                "type": "initial_screening",
                "status": "scheduled",
                "scheduled_for": None,  # Would be set by actual scheduling logic
                "interviewer_id": None,
                "notes": "Generated from AI screening workflow"
            }
            
            interview_id = await self.db_manager.create_interview(interview_data)
            state["interview_id"] = interview_id
            
            # Send notification to candidate
            candidate = await self.db_manager.get_candidate(candidate_id)
            if candidate and candidate.get("email"):
                await self.email_service.send_interview_notification(
                    candidate["email"],
                    candidate["name"],
                    "We'd like to schedule an interview with you"
                )
                
                state["notifications_sent"].append({
                    "type": "interview_invitation",
                    "recipient": candidate["email"],
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            state["messages"].append({
                "type": "scheduling",
                "content": f"Interview scheduled for candidate {candidate_id}",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            self.logger.info(f"Interview scheduled for candidate {candidate_id}")
            
        except Exception as e:
            error_msg = f"Interview scheduling failed: {str(e)}"
            state["errors"].append(error_msg)
            self.logger.error(error_msg)
        
        return state
    
    async def onboarding_initiation_node(self, state: HRWorkflowState) -> HRWorkflowState:
        """Initiate employee onboarding process"""
        try:
            employee_id = state.get("employee_id")
            if not employee_id:
                state["errors"].append("No employee ID provided for onboarding")
                return state
            
            # Get employee data
            employee = await self.db_manager.get_employee(employee_id)
            if not employee:
                state["errors"].append(f"Employee {employee_id} not found")
                return state
            
            # Create onboarding checklist
            onboarding_tasks = [
                {"task": "Complete I-9 form", "status": "pending", "due_date": None},
                {"task": "Submit tax documents", "status": "pending", "due_date": None},
                {"task": "Review employee handbook", "status": "pending", "due_date": None},
                {"task": "Set up workspace", "status": "pending", "due_date": None},
                {"task": "IT equipment assignment", "status": "pending", "due_date": None},
                {"task": "Benefits enrollment", "status": "pending", "due_date": None},
                {"task": "Department introduction", "status": "pending", "due_date": None}
            ]
            
            # Create onboarding record
            onboarding_data = {
                "employee_id": employee_id,
                "status": "in_progress",
                "checklist": onboarding_tasks,
                "assigned_to": None,  # Would be set by HR
                "started_at": datetime.utcnow().isoformat()
            }
            
            onboarding_id = await self.db_manager.create_onboarding_record(onboarding_data)
            
            state["onboarding_checklist"] = onboarding_tasks
            state["metadata"]["onboarding_id"] = onboarding_id
            
            # Add message to workflow
            state["messages"].append({
                "type": "onboarding",
                "content": f"Onboarding initiated for employee {employee.get('name', employee_id)}",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            self.logger.info(f"Onboarding initiated for employee {employee_id}")
            
        except Exception as e:
            error_msg = f"Onboarding initiation failed: {str(e)}"
            state["errors"].append(error_msg)
            self.logger.error(error_msg)
        
        return state
    
    async def performance_review_node(self, state: HRWorkflowState) -> HRWorkflowState:
        """Create and manage performance reviews"""
        try:
            employee_id = state.get("employee_id")
            if not employee_id:
                state["errors"].append("No employee ID provided for performance review")
                return state
            
            # Get employee data
            employee = await self.db_manager.get_employee(employee_id)
            if not employee:
                state["errors"].append(f"Employee {employee_id} not found")
                return state
            
            # Create performance review record
            review_data = {
                "employee_id": employee_id,
                "reviewer_id": state.get("metadata", {}).get("reviewer_id"),
                "review_period": state.get("metadata", {}).get("review_period", "annual"),
                "status": "scheduled",
                "goals": [],
                "feedback": {},
                "rating": None,
                "created_at": datetime.utcnow().isoformat()
            }
            
            review_id = await self.db_manager.create_performance_review(review_data)
            state["performance_review_id"] = review_id
            
            # Send notification to employee and reviewer
            if employee.get("email"):
                await self.email_service.send_performance_review_notification(
                    employee["email"],
                    employee["name"],
                    "Your performance review has been scheduled"
                )
                
                state["notifications_sent"].append({
                    "type": "performance_review",
                    "recipient": employee["email"],
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # Add message to workflow
            state["messages"].append({
                "type": "performance_review",
                "content": f"Performance review created for employee {employee.get('name', employee_id)}",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            self.logger.info(f"Performance review created for employee {employee_id}")
            
        except Exception as e:
            error_msg = f"Performance review creation failed: {str(e)}"
            state["errors"].append(error_msg)
            self.logger.error(error_msg)
        
        return state
    
    async def decision_router_node(self, state: HRWorkflowState) -> str:
        """Route workflow based on current state and decisions"""
        try:
            current_step = state.get("current_step", "")
            
            # Route based on screening results
            if current_step == "screening":
                screening_results = state.get("screening_results", {})
                ai_analysis = screening_results.get("ai_analysis", "").lower()
                
                if "reject" in ai_analysis:
                    return "send_rejection"
                elif "proceed" in ai_analysis:
                    return "schedule_interview"
                else:
                    return "needs_review"
            
            # Route based on interview results
            elif current_step == "interview":
                interview_results = state.get("interview_results", {})
                decision = interview_results.get("decision", "").lower()
                
                if "hire" in decision:
                    return "start_onboarding"
                else:
                    return "send_rejection"
            
            # Default routing
            elif current_step == "onboarding":
                return "send_welcome"
            elif current_step == "performance_review":
                return "notify_completion"
            
            return "END"
            
        except Exception as e:
            self.logger.error(f"Decision routing failed: {str(e)}")
            return "END"
    
    async def notification_node(self, state: HRWorkflowState) -> HRWorkflowState:
        """Send various notifications based on workflow state"""
        try:
            current_step = state.get("current_step", "")
            
            # Send appropriate notification based on workflow step
            if current_step == "send_welcome":
                employee_id = state.get("employee_id")
                if employee_id:
                    employee = await self.db_manager.get_employee(employee_id)
                    if employee and employee.get("email"):
                        await self.email_service.send_welcome_email(
                            employee["email"],
                            employee["name"]
                        )
                        
                        state["notifications_sent"].append({
                            "type": "welcome",
                            "recipient": employee["email"],
                            "timestamp": datetime.utcnow().isoformat()
                        })
            
            elif current_step == "send_rejection":
                candidate_id = state.get("candidate_id")
                if candidate_id:
                    candidate = await self.db_manager.get_candidate(candidate_id)
                    if candidate and candidate.get("email"):
                        await self.email_service.send_rejection_email(
                            candidate["email"],
                            candidate["name"]
                        )
                        
                        state["notifications_sent"].append({
                            "type": "rejection",
                            "recipient": candidate["email"],
                            "timestamp": datetime.utcnow().isoformat()
                        })
            
            elif current_step == "notify_completion":
                # Generic completion notification
                state["messages"].append({
                    "type": "completion",
                    "content": "Workflow completed successfully",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            self.logger.info(f"Notification sent for step: {current_step}")
            
        except Exception as e:
            error_msg = f"Notification failed: {str(e)}"
            state["errors"].append(error_msg)
            self.logger.error(error_msg)
        
        return state