"""
Onboarding Bot - Handles new hire onboarding processes and documentation
"""

from typing import Dict, List, Any, Optional
import json
from datetime import datetime, timedelta

from .base_bot import BaseBot, BotResponse
from ..utils.ai_client import AIClient
from ..utils.database import DatabaseManager
from ..utils.email_service import EmailService
from ..nodes.workflow_manager import HRWorkflowManager


class OnboardingBot(BaseBot):
    """
    Specialized bot for employee onboarding processes
    Handles new hire documentation, task tracking, and workflow automation
    """
    
    def __init__(self, ai_client: AIClient, db_manager: DatabaseManager, email_service: EmailService):
        super().__init__(
            name="OnboardingBot",
            description="Automates new hire onboarding processes and documentation",
            ai_client=ai_client,
            db_manager=db_manager,
            email_service=email_service
        )
        self.workflow_manager = HRWorkflowManager()
    
    def get_capabilities(self) -> List[str]:
        return [
            "new hire onboarding",
            "document collection",
            "task assignment",
            "checklist management",
            "welcome materials",
            "training scheduling",
            "equipment requests",
            "system access setup",
            "orientation planning",
            "progress tracking"
        ]
    
    async def process_request(self, request: str, context: Dict[str, Any] = None) -> BotResponse:
        """Process onboarding-related requests"""
        try:
            intent = self._extract_intent(request)
            context = context or {}
            
            # Route to appropriate handler based on intent
            if intent in ["start", "begin", "initiate", "new"]:
                return await self._handle_onboarding_start(request, context)
            elif intent in ["checklist", "tasks", "todo"]:
                return await self._handle_checklist_management(request, context)
            elif intent in ["document", "form", "paperwork"]:
                return await self._handle_document_collection(request, context)
            elif intent in ["schedule", "training", "orientation"]:
                return await self._handle_training_scheduling(request, context)
            elif intent in ["equipment", "setup", "access"]:
                return await self._handle_equipment_setup(request, context)
            elif intent in ["progress", "status", "update"]:
                return await self._handle_progress_tracking(request, context)
            elif intent in ["welcome", "materials", "packet"]:
                return await self._handle_welcome_materials(request, context)
            else:
                return await self._handle_general_inquiry(request, context)
                
        except Exception as e:
            self.logger.error(f"Error processing onboarding request: {str(e)}")
            return BotResponse(
                success=False,
                message="I encountered an error while processing your onboarding request. Please try again.",
                confidence_score=0.0
            )
    
    async def _handle_onboarding_start(self, request: str, context: Dict[str, Any]) -> BotResponse:
        """Handle new employee onboarding initiation"""
        try:
            new_hire_info = context.get('new_hire_info', {})
            start_date = context.get('start_date')
            department = context.get('department')
            position = context.get('position')
            
            if not new_hire_info:
                return BotResponse(
                    success=False,
                    message="Please provide new hire information to start the onboarding process.",
                    next_steps=[
                        "Provide employee name and contact info",
                        "Specify start date and position",
                        "Include department and manager details"
                    ],
                    confidence_score=0.3
                )
            
            # Create onboarding workflow
            onboarding_id = await self._create_onboarding_workflow(
                new_hire_info, start_date, department, position
            )
            
            # Generate welcome packet
            welcome_packet = await self.document_generator.create_welcome_packet(new_hire_info)
            
            # Create task checklist
            checklist = await self._create_onboarding_checklist(onboarding_id, department, position)
            
            # Schedule automated tasks
            await self._schedule_onboarding_tasks(onboarding_id, start_date)
            
            # Send welcome email
            await self._send_welcome_email(new_hire_info, welcome_packet)
            
            return BotResponse(
                success=True,
                message=f"Onboarding process initiated for {new_hire_info.get('name', 'new employee')}!",
                data={
                    "onboarding_id": onboarding_id,
                    "welcome_packet": welcome_packet,
                    "checklist": checklist,
                    "start_date": start_date
                },
                action_taken="onboarding_workflow_created",
                next_steps=[
                    "Review onboarding checklist",
                    "Prepare workspace",
                    "Schedule first day activities",
                    "Notify relevant teams"
                ],
                confidence_score=0.95
            )
            
        except Exception as e:
            self.logger.error(f"Error starting onboarding: {str(e)}")
            return BotResponse(
                success=False,
                message="Failed to initiate onboarding process. Please try again.",
                confidence_score=0.3
            )
    
    async def _handle_checklist_management(self, request: str, context: Dict[str, Any]) -> BotResponse:
        """Handle onboarding checklist management and updates"""
        try:
            onboarding_id = context.get('onboarding_id')
            employee_id = context.get('employee_id')
            
            if not onboarding_id and not employee_id:
                return BotResponse(
                    success=False,
                    message="Please specify which onboarding checklist you'd like to manage.",
                    next_steps=["Provide onboarding ID", "Specify employee name"],
                    confidence_score=0.3
                )
            
            if "complete" in request.lower() or "done" in request.lower():
                # Mark task as complete
                task_info = await self._extract_task_info(request)
                result = await self._complete_onboarding_task(onboarding_id, task_info)
                
                return BotResponse(
                    success=True,
                    message=f"Task '{task_info.get('task_name')}' marked as complete!",
                    data=result,
                    action_taken="task_completed",
                    next_steps=["Update progress", "Check remaining tasks", "Notify stakeholders"],
                    confidence_score=0.9
                )
            
            elif "add" in request.lower() or "create" in request.lower():
                # Add new task to checklist
                new_task = await self._extract_new_task_info(request)
                task_id = await self._add_onboarding_task(onboarding_id, new_task)
                
                return BotResponse(
                    success=True,
                    message=f"New task added to onboarding checklist: {new_task.get('title')}",
                    data={"task_id": task_id, "task_details": new_task},
                    action_taken="task_added",
                    confidence_score=0.85
                )
            
            else:
                # View checklist
                checklist = await self.db_manager.get_onboarding_checklist(onboarding_id)
                progress = await self._calculate_onboarding_progress(checklist)
                
                return BotResponse(
                    success=True,
                    message=f"Onboarding progress: {progress['completed']}/{progress['total']} tasks completed ({progress['percentage']:.1f}%)",
                    data={
                        "checklist": checklist,
                        "progress": progress
                    },
                    action_taken="checklist_retrieved",
                    next_steps=["Complete pending tasks", "Review priorities", "Update deadlines"],
                    confidence_score=0.9
                )
                
        except Exception as e:
            self.logger.error(f"Error managing checklist: {str(e)}")
            return BotResponse(
                success=False,
                message="Failed to manage onboarding checklist. Please try again.",
                confidence_score=0.3
            )
    
    async def _handle_document_collection(self, request: str, context: Dict[str, Any]) -> BotResponse:
        """Handle document collection and processing"""
        try:
            onboarding_id = context.get('onboarding_id')
            document_type = await self._extract_document_type(request)
            
            if "submit" in request.lower() or "upload" in request.lower():
                # Handle document submission
                uploaded_file = context.get('uploaded_file')
                if not uploaded_file:
                    required_docs = await self._get_required_documents(onboarding_id)
                    
                    return BotResponse(
                        success=False,
                        message="Please upload the required document.",
                        data={"required_documents": required_docs},
                        next_steps=["Upload document", "Verify format", "Check requirements"],
                        confidence_score=0.5
                    )
                
                # Process document submission
                processing_result = await self._process_document_submission(
                    onboarding_id, document_type, uploaded_file
                )
                
                return BotResponse(
                    success=True,
                    message=f"{document_type} submitted successfully!",
                    data=processing_result,
                    action_taken="document_submitted",
                    next_steps=["Verify document", "Update checklist", "Notify HR"],
                    confidence_score=0.9
                )
            
            elif "generate" in request.lower() or "create" in request.lower():
                # Generate required documents
                generated_docs = await self.document_generator.generate_onboarding_documents(
                    onboarding_id, document_type
                )
                
                return BotResponse(
                    success=True,
                    message=f"Generated {document_type} documents for onboarding.",
                    data={"generated_documents": generated_docs},
                    action_taken="documents_generated",
                    next_steps=["Review documents", "Send to employee", "Add to packet"],
                    confidence_score=0.85
                )
            
            else:
                # List required documents
                required_docs = await self._get_required_documents(onboarding_id)
                missing_docs = await self._get_missing_documents(onboarding_id)
                
                return BotResponse(
                    success=True,
                    message=f"Document status: {len(missing_docs)} documents still needed.",
                    data={
                        "required_documents": required_docs,
                        "missing_documents": missing_docs
                    },
                    action_taken="document_status_provided",
                    next_steps=["Submit missing documents", "Follow up with employee", "Set reminders"],
                    confidence_score=0.8
                )
                
        except Exception as e:
            self.logger.error(f"Error handling document collection: {str(e)}")
            return BotResponse(
                success=False,
                message="Failed to process document request. Please try again.",
                confidence_score=0.3
            )
    
    async def _handle_training_scheduling(self, request: str, context: Dict[str, Any]) -> BotResponse:
        """Handle training and orientation scheduling"""
        try:
            onboarding_id = context.get('onboarding_id')
            training_type = await self._extract_training_type(request)
            
            if "schedule" in request.lower():
                # Schedule training session
                training_details = await self._extract_training_details(request)
                session_id = await self._schedule_training_session(onboarding_id, training_details)
                
                # Send calendar invites
                await self._send_training_invites(session_id)
                
                return BotResponse(
                    success=True,
                    message=f"Training session scheduled: {training_details.get('title')}",
                    data={
                        "session_id": session_id,
                        "training_details": training_details
                    },
                    action_taken="training_scheduled",
                    next_steps=["Send calendar invites", "Prepare materials", "Set up room/tools"],
                    confidence_score=0.9
                )
            
            else:
                # Get training plan
                training_plan = await self._get_training_plan(onboarding_id)
                
                return BotResponse(
                    success=True,
                    message="Here's the training plan for this employee:",
                    data={"training_plan": training_plan},
                    action_taken="training_plan_provided",
                    next_steps=["Schedule sessions", "Prepare materials", "Assign trainers"],
                    confidence_score=0.8
                )
                
        except Exception as e:
            self.logger.error(f"Error handling training scheduling: {str(e)}")
            return BotResponse(
                success=False,
                message="Failed to handle training request. Please try again.",
                confidence_score=0.3
            )
    
    async def _handle_equipment_setup(self, request: str, context: Dict[str, Any]) -> BotResponse:
        """Handle equipment and system access setup"""
        try:
            onboarding_id = context.get('onboarding_id')
            setup_type = await self._extract_setup_type(request)
            
            if setup_type == "equipment":
                # Handle equipment requests
                equipment_list = await self._get_required_equipment(onboarding_id)
                equipment_order = await self._create_equipment_order(onboarding_id, equipment_list)
                
                return BotResponse(
                    success=True,
                    message="Equipment order created and submitted to IT.",
                    data={
                        "equipment_order": equipment_order,
                        "equipment_list": equipment_list
                    },
                    action_taken="equipment_ordered",
                    next_steps=["Track order status", "Schedule delivery", "Arrange setup"],
                    confidence_score=0.85
                )
            
            elif setup_type == "access":
                # Handle system access setup
                access_requests = await self._create_access_requests(onboarding_id)
                
                return BotResponse(
                    success=True,
                    message="System access requests submitted to IT Security.",
                    data={"access_requests": access_requests},
                    action_taken="access_requests_created",
                    next_steps=["Wait for approval", "Distribute credentials", "Schedule training"],
                    confidence_score=0.85
                )
            
            else:
                # General setup status
                setup_status = await self._get_setup_status(onboarding_id)
                
                return BotResponse(
                    success=True,
                    message="Current setup status for new employee:",
                    data=setup_status,
                    action_taken="setup_status_provided",
                    confidence_score=0.8
                )
                
        except Exception as e:
            self.logger.error(f"Error handling equipment setup: {str(e)}")
            return BotResponse(
                success=False,
                message="Failed to handle setup request. Please try again.",
                confidence_score=0.3
            )
    
    async def _handle_progress_tracking(self, request: str, context: Dict[str, Any]) -> BotResponse:
        """Handle onboarding progress tracking and reporting"""
        try:
            onboarding_id = context.get('onboarding_id')
            
            # Get comprehensive progress report
            progress_report = await self._generate_progress_report(onboarding_id)
            
            # Identify bottlenecks and issues
            issues = await self._identify_onboarding_issues(progress_report)
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(progress_report, issues)
            
            return BotResponse(
                success=True,
                message=f"Onboarding progress: {progress_report['overall_progress']:.1f}% complete",
                data={
                    "progress_report": progress_report,
                    "issues": issues,
                    "recommendations": recommendations
                },
                action_taken="progress_report_generated",
                next_steps=recommendations[:3] if recommendations else ["Continue monitoring"],
                confidence_score=0.9
            )
            
        except Exception as e:
            self.logger.error(f"Error tracking progress: {str(e)}")
            return BotResponse(
                success=False,
                message="Failed to generate progress report. Please try again.",
                confidence_score=0.3
            )
    
    async def _handle_welcome_materials(self, request: str, context: Dict[str, Any]) -> BotResponse:
        """Handle welcome materials creation and distribution"""
        try:
            new_hire_info = context.get('new_hire_info', {})
            
            # Generate welcome materials
            welcome_materials = await self.document_generator.create_comprehensive_welcome_packet(
                new_hire_info
            )
            
            # Customize based on role and department
            customized_materials = await self._customize_welcome_materials(
                welcome_materials, new_hire_info
            )
            
            return BotResponse(
                success=True,
                message="Welcome materials generated and ready for distribution.",
                data={
                    "welcome_materials": customized_materials,
                    "distribution_list": await self._get_distribution_list(new_hire_info)
                },
                action_taken="welcome_materials_created",
                next_steps=["Review materials", "Send to employee", "Distribute copies"],
                confidence_score=0.9
            )
            
        except Exception as e:
            self.logger.error(f"Error creating welcome materials: {str(e)}")
            return BotResponse(
                success=False,
                message="Failed to create welcome materials. Please try again.",
                confidence_score=0.3
            )
    
    async def _handle_general_inquiry(self, request: str, context: Dict[str, Any]) -> BotResponse:
        """Handle general onboarding inquiries"""
        response_text = await self._generate_onboarding_response(request, context)
        
        return BotResponse(
            success=True,
            message=response_text,
            action_taken="information_provided",
            confidence_score=0.7
        )
    
    # Helper methods
    async def _create_onboarding_workflow(
        self, 
        new_hire_info: Dict[str, Any], 
        start_date: str, 
        department: str, 
        position: str
    ) -> str:
        """Create comprehensive onboarding workflow"""
        workflow_data = {
            'employee_info': new_hire_info,
            'start_date': start_date,
            'department': department,
            'position': position,
            'status': 'initiated',
            'created_at': datetime.utcnow()
        }
        
        return await self.db_manager.create_onboarding_workflow(workflow_data)
    
    async def _create_onboarding_checklist(
        self, 
        onboarding_id: str, 
        department: str, 
        position: str
    ) -> Dict[str, Any]:
        """Create department and role-specific onboarding checklist"""
        # Get template checklist based on department and position
        template = await self.workflow_manager.get_onboarding_template(department, position)
        
        # Customize checklist
        checklist_items = []
        for item in template.get('tasks', []):
            checklist_items.append({
                'task_id': item['id'],
                'title': item['title'],
                'description': item.get('description', ''),
                'category': item.get('category', 'general'),
                'priority': item.get('priority', 'medium'),
                'estimated_duration': item.get('duration', 60),
                'due_date': self._calculate_due_date(item.get('days_from_start', 1)),
                'assignee': item.get('assignee', 'HR'),
                'status': 'pending',
                'dependencies': item.get('dependencies', [])
            })
        
        checklist_data = {
            'onboarding_id': onboarding_id,
            'tasks': checklist_items,
            'created_at': datetime.utcnow()
        }
        
        await self.db_manager.create_onboarding_checklist(checklist_data)
        return checklist_data
    
    async def _schedule_onboarding_tasks(self, onboarding_id: str, start_date: str):
        """Schedule automated onboarding tasks and reminders"""
        # This would integrate with task scheduling system
        tasks_to_schedule = [
            {'task': 'send_welcome_email', 'delay_days': -3},
            {'task': 'prepare_workspace', 'delay_days': -1},
            {'task': 'first_day_checkin', 'delay_days': 0},
            {'task': 'week_one_followup', 'delay_days': 7},
            {'task': 'month_one_review', 'delay_days': 30}
        ]
        
        for task in tasks_to_schedule:
            await self.workflow_manager.schedule_task(
                onboarding_id, 
                task['task'], 
                start_date, 
                task['delay_days']
            )
    
    async def _send_welcome_email(self, new_hire_info: Dict[str, Any], welcome_packet: Dict[str, Any]):
        """Send welcome email to new hire"""
        email_content = f"""
        Welcome to {self.db_manager.get_company_name()}!
        
        Dear {new_hire_info.get('name')},
        
        We're excited to welcome you to our team! Your first day is scheduled for {new_hire_info.get('start_date')}.
        
        Please review the attached welcome packet which contains important information about your first day,
        required documents, and what to expect during your onboarding process.
        
        If you have any questions, please don't hesitate to reach out.
        
        Best regards,
        HR Team
        """
        
        await self.send_notification(
            recipient=new_hire_info.get('email'),
            subject=f"Welcome to {self.db_manager.get_company_name()}!",
            message=email_content,
            template="welcome_email"
        )
    
    def _calculate_due_date(self, days_from_start: int) -> str:
        """Calculate due date based on days from start date"""
        due_date = datetime.utcnow() + timedelta(days=days_from_start)
        return due_date.isoformat()
    
    async def _extract_task_info(self, request: str) -> Dict[str, Any]:
        """Extract task information from request"""
        prompt = f"""
        Extract task completion information from:
        "{request}"
        
        Return JSON with:
        - task_name: name of the task
        - notes: any completion notes
        - completion_date: when it was completed
        
        Return only valid JSON.
        """
        
        try:
            response = self.ai_client.get_completion(prompt)
            return json.loads(response)
        except:
            return {}
    
    async def _complete_onboarding_task(self, onboarding_id: str, task_info: Dict[str, Any]) -> Dict[str, Any]:
        """Mark onboarding task as complete"""
        completion_data = {
            'completed_at': datetime.utcnow(),
            'notes': task_info.get('notes', ''),
            'status': 'completed'
        }
        
        await self.db_manager.update_onboarding_task(
            onboarding_id, 
            task_info.get('task_name'), 
            completion_data
        )
        
        # Check if this triggers any dependent tasks
        await self._check_task_dependencies(onboarding_id, task_info.get('task_name'))
        
        return completion_data
    
    async def _calculate_onboarding_progress(self, checklist: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate onboarding completion progress"""
        tasks = checklist.get('tasks', [])
        total_tasks = len(tasks)
        completed_tasks = len([task for task in tasks if task.get('status') == 'completed'])
        
        return {
            'total': total_tasks,
            'completed': completed_tasks,
            'remaining': total_tasks - completed_tasks,
            'percentage': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        }
    
    async def _extract_document_type(self, request: str) -> str:
        """Extract document type from request"""
        document_types = [
            'i9', 'w4', 'direct deposit', 'emergency contact', 'handbook acknowledgment',
            'benefits enrollment', 'tax forms', 'background check', 'drug test'
        ]
        request_lower = request.lower()
        
        for doc_type in document_types:
            if doc_type in request_lower:
                return doc_type
        
        return 'general'
    
    async def _get_required_documents(self, onboarding_id: str) -> List[Dict[str, Any]]:
        """Get list of required documents for onboarding"""
        return await self.db_manager.get_required_onboarding_documents(onboarding_id)
    
    async def _process_document_submission(
        self, 
        onboarding_id: str, 
        document_type: str, 
        uploaded_file: Any
    ) -> Dict[str, Any]:
        """Process submitted onboarding document"""
        # Validate document
        validation_result = await self.document_generator.validate_document(
            uploaded_file, document_type
        )
        
        if not validation_result['valid']:
            return {
                'success': False,
                'issues': validation_result['issues']
            }
        
        # Store document
        document_id = await self.db_manager.store_onboarding_document(
            onboarding_id, document_type, uploaded_file
        )
        
        # Update checklist
        await self.db_manager.update_document_status(onboarding_id, document_type, 'completed')
        
        return {
            'success': True,
            'document_id': document_id,
            'validation_result': validation_result
        }
    
    async def _generate_onboarding_response(self, request: str, context: Dict[str, Any]) -> str:
        """Generate response for general onboarding inquiries"""
        prompt = f"""
        As an onboarding assistant, respond to this inquiry:
        "{request}"
        
        Context: {json.dumps(context)}
        
        Provide helpful guidance about onboarding processes and requirements.
        """
        
        return self.ai_client.get_completion(prompt)