"""
Performance Bot - Handles performance reviews, goal tracking, and employee development
"""

from typing import Dict, List, Any, Optional
import json
from datetime import datetime, timedelta

from .base_bot import BaseBot, BotResponse
from ..utils.ai_client import AIClient
from ..utils.database import DatabaseManager
from ..utils.email_service import EmailService


class PerformanceBot(BaseBot):
    """
    Specialized bot for performance management and employee development
    Handles performance reviews, goal setting, and progress tracking
    """
    
    def __init__(self, ai_client: AIClient, db_manager: DatabaseManager, email_service: EmailService):
        super().__init__(
            name="PerformanceBot",
            description="Manages performance reviews, goals, and employee development",
            ai_client=ai_client,
            db_manager=db_manager,
            email_service=email_service
        )
    
    def get_capabilities(self) -> List[str]:
        return [
            "performance reviews",
            "goal setting",
            "progress tracking",
            "feedback collection",
            "development planning",
            "skill assessment",
            "performance analytics",
            "review scheduling",
            "360 feedback",
            "career development"
        ]
    
    async def process_request(self, request: str, context: Dict[str, Any] = None) -> BotResponse:
        """Process performance management requests"""
        try:
            intent = self._extract_intent(request)
            context = context or {}
            
            # Route to appropriate handler based on intent
            if intent in ["review", "evaluation", "assessment"]:
                return await self._handle_performance_review(request, context)
            elif intent in ["goal", "goals", "objective", "objectives"]:
                return await self._handle_goal_management(request, context)
            elif intent in ["feedback", "input", "comment"]:
                return await self._handle_feedback_collection(request, context)
            elif intent in ["development", "growth", "career"]:
                return await self._handle_development_planning(request, context)
            elif intent in ["progress", "tracking", "status"]:
                return await self._handle_progress_tracking(request, context)
            elif intent in ["schedule", "plan", "calendar"]:
                return await self._handle_review_scheduling(request, context)
            elif intent in ["analytics", "report", "metrics"]:
                return await self._handle_performance_analytics(request, context)
            elif intent in ["skills", "competency", "assessment"]:
                return await self._handle_skill_assessment(request, context)
            else:
                return await self._handle_general_inquiry(request, context)
                
        except Exception as e:
            self.logger.error(f"Error processing performance request: {str(e)}")
            return BotResponse(
                success=False,
                message="I encountered an error while processing your performance request. Please try again.",
                confidence_score=0.0
            )
    
    async def _handle_performance_review(self, request: str, context: Dict[str, Any]) -> BotResponse:
        """Handle performance review creation and management"""
        try:
            employee_id = context.get('employee_id')
            review_type = context.get('review_type', 'annual')
            reviewer_id = context.get('reviewer_id')
            
            if "create" in request.lower() or "start" in request.lower():
                # Create new performance review
                if not employee_id:
                    return BotResponse(
                        success=False,
                        message="Please specify which employee to create a performance review for.",
                        next_steps=["Provide employee ID", "Select review type", "Choose reviewers"],
                        confidence_score=0.3
                    )
                
                # Generate review questions based on role and company standards
                review_template = await self._generate_review_template(employee_id, review_type)
                
                # Create review instance
                review_id = await self._create_performance_review(
                    employee_id, reviewer_id, review_template, review_type
                )
                
                # Schedule review process
                await self._schedule_review_process(review_id)
                
                return BotResponse(
                    success=True,
                    message=f"Performance review created for employee. Review ID: {review_id}",
                    data={
                        "review_id": review_id,
                        "review_template": review_template,
                        "review_type": review_type,
                        "due_date": (datetime.utcnow() + timedelta(days=14)).isoformat()
                    },
                    action_taken="performance_review_created",
                    next_steps=[
                        "Notify employee and reviewer",
                        "Set review meetings",
                        "Gather supporting documents",
                        "Complete review form"
                    ],
                    confidence_score=0.9
                )
            
            elif "submit" in request.lower() or "complete" in request.lower():
                # Submit completed review
                review_id = context.get('review_id')
                review_data = context.get('review_data', {})
                
                if not review_id or not review_data:
                    return BotResponse(
                        success=False,
                        message="Please provide review ID and completed review data.",
                        next_steps=["Complete all review sections", "Add ratings and comments"],
                        confidence_score=0.4
                    )
                
                # Process and validate review submission
                validation_result = await self._validate_review_submission(review_data)
                
                if not validation_result['valid']:
                    return BotResponse(
                        success=False,
                        message="Review submission incomplete. Please address the following issues:",
                        data={"validation_issues": validation_result['issues']},
                        next_steps=validation_result['required_actions'],
                        confidence_score=0.6
                    )
                
                # Submit review
                await self._submit_performance_review(review_id, review_data)
                
                # Generate performance insights
                insights = await self.analytics_engine.analyze_performance_review(review_id)
                
                return BotResponse(
                    success=True,
                    message="Performance review submitted successfully!",
                    data={
                        "review_id": review_id,
                        "insights": insights,
                        "next_review_date": self._calculate_next_review_date(review_type)
                    },
                    action_taken="performance_review_submitted",
                    next_steps=[
                        "Schedule follow-up meeting",
                        "Create development plan",
                        "Set new goals",
                        "Track progress"
                    ],
                    confidence_score=0.95
                )
            
            else:
                # View existing reviews
                reviews = await self.db_manager.get_employee_reviews(employee_id)
                
                return BotResponse(
                    success=True,
                    message=f"Found {len(reviews)} performance reviews for this employee.",
                    data={"reviews": reviews},
                    action_taken="reviews_retrieved",
                    next_steps=["Review history", "Create new review", "Analyze trends"],
                    confidence_score=0.8
                )
                
        except Exception as e:
            self.logger.error(f"Error handling performance review: {str(e)}")
            return BotResponse(
                success=False,
                message="Failed to process performance review request. Please try again.",
                confidence_score=0.3
            )
    
    async def _handle_goal_management(self, request: str, context: Dict[str, Any]) -> BotResponse:
        """Handle goal setting and management"""
        try:
            employee_id = context.get('employee_id')
            
            if "set" in request.lower() or "create" in request.lower():
                # Create new goals
                goal_data = await self._extract_goal_data(request)
                
                if not goal_data:
                    return BotResponse(
                        success=False,
                        message="Please provide goal details including title, description, and target date.",
                        next_steps=[
                            "Specify goal title and description",
                            "Set target completion date",
                            "Define success metrics",
                            "Assign priority level"
                        ],
                        confidence_score=0.3
                    )
                
                # Validate goal using SMART criteria
                smart_validation = await self._validate_smart_goal(goal_data)
                
                if not smart_validation['valid']:
                    return BotResponse(
                        success=False,
                        message="Goal doesn't meet SMART criteria. Please improve:",
                        data={"smart_feedback": smart_validation['feedback']},
                        next_steps=smart_validation['improvements'],
                        confidence_score=0.5
                    )
                
                # Create goal
                goal_id = await self.goal_tracker.create_goal(employee_id, goal_data)
                
                # Set up tracking and reminders
                await self._setup_goal_tracking(goal_id)
                
                return BotResponse(
                    success=True,
                    message=f"Goal created successfully: {goal_data.get('title')}",
                    data={
                        "goal_id": goal_id,
                        "goal_details": goal_data,
                        "smart_score": smart_validation['score']
                    },
                    action_taken="goal_created",
                    next_steps=[
                        "Track progress regularly",
                        "Set milestone reminders",
                        "Share with manager",
                        "Link to performance review"
                    ],
                    confidence_score=0.9
                )
            
            elif "update" in request.lower() or "progress" in request.lower():
                # Update goal progress
                goal_id = context.get('goal_id')
                progress_data = await self._extract_progress_data(request)
                
                if not goal_id:
                    return BotResponse(
                        success=False,
                        message="Please specify which goal to update.",
                        next_steps=["Provide goal ID", "Select from goal list"],
                        confidence_score=0.3
                    )
                
                # Update progress
                await self.goal_tracker.update_progress(goal_id, progress_data)
                
                # Analyze progress
                progress_analysis = await self.analytics_engine.analyze_goal_progress(goal_id)
                
                return BotResponse(
                    success=True,
                    message=f"Goal progress updated to {progress_data.get('completion_percentage', 0)}%",
                    data={
                        "goal_id": goal_id,
                        "progress_data": progress_data,
                        "analysis": progress_analysis
                    },
                    action_taken="goal_progress_updated",
                    next_steps=progress_analysis.get('recommendations', []),
                    confidence_score=0.85
                )
            
            else:
                # View goals
                goals = await self.goal_tracker.get_employee_goals(employee_id)
                goal_summary = await self._generate_goal_summary(goals)
                
                return BotResponse(
                    success=True,
                    message=f"Employee has {len(goals)} active goals.",
                    data={
                        "goals": goals,
                        "summary": goal_summary
                    },
                    action_taken="goals_retrieved",
                    next_steps=["Update progress", "Set new goals", "Review achievements"],
                    confidence_score=0.8
                )
                
        except Exception as e:
            self.logger.error(f"Error handling goal management: {str(e)}")
            return BotResponse(
                success=False,
                message="Failed to process goal request. Please try again.",
                confidence_score=0.3
            )
    
    async def _handle_feedback_collection(self, request: str, context: Dict[str, Any]) -> BotResponse:
        """Handle feedback collection and 360-degree reviews"""
        try:
            employee_id = context.get('employee_id')
            feedback_type = context.get('feedback_type', '360')
            
            if "collect" in request.lower() or "request" in request.lower():
                # Initiate feedback collection
                feedback_request_id = await self._create_feedback_request(employee_id, feedback_type)
                
                # Identify feedback providers
                providers = await self._identify_feedback_providers(employee_id, feedback_type)
                
                # Send feedback requests
                await self._send_feedback_requests(feedback_request_id, providers)
                
                return BotResponse(
                    success=True,
                    message=f"Feedback collection initiated. Requests sent to {len(providers)} people.",
                    data={
                        "feedback_request_id": feedback_request_id,
                        "providers": providers,
                        "expected_responses": len(providers)
                    },
                    action_taken="feedback_collection_started",
                    next_steps=[
                        "Monitor response rate",
                        "Send reminders if needed",
                        "Compile results when complete"
                    ],
                    confidence_score=0.9
                )
            
            elif "submit" in request.lower():
                # Submit feedback
                feedback_request_id = context.get('feedback_request_id')
                feedback_data = context.get('feedback_data', {})
                
                if not feedback_data:
                    return BotResponse(
                        success=False,
                        message="Please provide feedback content.",
                        next_steps=["Complete feedback form", "Add specific examples"],
                        confidence_score=0.3
                    )
                
                # Process feedback submission
                await self._submit_feedback(feedback_request_id, feedback_data)
                
                return BotResponse(
                    success=True,
                    message="Feedback submitted successfully. Thank you for your input!",
                    action_taken="feedback_submitted",
                    confidence_score=0.9
                )
            
            else:
                # View feedback results
                feedback_results = await self.db_manager.get_feedback_results(employee_id)
                
                if feedback_results:
                    analysis = await self.analytics_engine.analyze_feedback(feedback_results)
                    
                    return BotResponse(
                        success=True,
                        message="Feedback analysis complete.",
                        data={
                            "feedback_results": feedback_results,
                            "analysis": analysis
                        },
                        action_taken="feedback_analysis_provided",
                        next_steps=["Discuss with employee", "Create development plan", "Set improvement goals"],
                        confidence_score=0.85
                    )
                else:
                    return BotResponse(
                        success=False,
                        message="No feedback results found for this employee.",
                        next_steps=["Initiate feedback collection", "Check request status"],
                        confidence_score=0.7
                    )
                
        except Exception as e:
            self.logger.error(f"Error handling feedback collection: {str(e)}")
            return BotResponse(
                success=False,
                message="Failed to process feedback request. Please try again.",
                confidence_score=0.3
            )
    
    async def _handle_development_planning(self, request: str, context: Dict[str, Any]) -> BotResponse:
        """Handle employee development and career planning"""
        try:
            employee_id = context.get('employee_id')
            
            if "create" in request.lower() or "plan" in request.lower():
                # Create development plan
                current_skills = await self.db_manager.get_employee_skills(employee_id)
                career_goals = await self.db_manager.get_employee_career_goals(employee_id)
                
                # Analyze skill gaps
                skill_gap_analysis = await self.analytics_engine.analyze_skill_gaps(
                    employee_id, current_skills, career_goals
                )
                
                # Generate development recommendations
                development_plan = await self._generate_development_plan(
                    employee_id, skill_gap_analysis
                )
                
                # Create plan in database
                plan_id = await self.db_manager.create_development_plan(employee_id, development_plan)
                
                return BotResponse(
                    success=True,
                    message="Development plan created successfully!",
                    data={
                        "plan_id": plan_id,
                        "development_plan": development_plan,
                        "skill_gaps": skill_gap_analysis
                    },
                    action_taken="development_plan_created",
                    next_steps=[
                        "Review plan with employee",
                        "Schedule training sessions",
                        "Set learning milestones",
                        "Track progress monthly"
                    ],
                    confidence_score=0.9
                )
            
            else:
                # View existing development plans
                plans = await self.db_manager.get_development_plans(employee_id)
                
                return BotResponse(
                    success=True,
                    message=f"Found {len(plans)} development plans for this employee.",
                    data={"development_plans": plans},
                    action_taken="development_plans_retrieved",
                    next_steps=["Review progress", "Update plans", "Add new goals"],
                    confidence_score=0.8
                )
                
        except Exception as e:
            self.logger.error(f"Error handling development planning: {str(e)}")
            return BotResponse(
                success=False,
                message="Failed to process development planning request. Please try again.",
                confidence_score=0.3
            )
    
    async def _handle_progress_tracking(self, request: str, context: Dict[str, Any]) -> BotResponse:
        """Handle progress tracking for goals and development"""
        try:
            employee_id = context.get('employee_id')
            tracking_type = context.get('tracking_type', 'all')  # goals, development, or all
            
            # Get comprehensive progress data
            progress_data = await self._get_comprehensive_progress(employee_id, tracking_type)
            
            # Generate progress insights
            insights = await self.analytics_engine.generate_progress_insights(progress_data)
            
            # Identify areas needing attention
            attention_areas = await self._identify_attention_areas(progress_data)
            
            return BotResponse(
                success=True,
                message="Progress tracking analysis complete.",
                data={
                    "progress_data": progress_data,
                    "insights": insights,
                    "attention_areas": attention_areas
                },
                action_taken="progress_analysis_completed",
                next_steps=[
                    "Address attention areas",
                    "Update goals as needed",
                    "Schedule check-in meetings",
                    "Celebrate achievements"
                ],
                confidence_score=0.85
            )
            
        except Exception as e:
            self.logger.error(f"Error handling progress tracking: {str(e)}")
            return BotResponse(
                success=False,
                message="Failed to generate progress report. Please try again.",
                confidence_score=0.3
            )
    
    async def _handle_performance_analytics(self, request: str, context: Dict[str, Any]) -> BotResponse:
        """Handle performance analytics and reporting"""
        try:
            analytics_type = context.get('analytics_type', 'individual')
            employee_id = context.get('employee_id')
            department = context.get('department')
            time_period = context.get('time_period', '1_year')
            
            if analytics_type == 'individual':
                # Individual performance analytics
                analytics = await self.analytics_engine.generate_individual_analytics(
                    employee_id, time_period
                )
            elif analytics_type == 'department':
                # Department performance analytics
                analytics = await self.analytics_engine.generate_department_analytics(
                    department, time_period
                )
            else:
                # Company-wide analytics
                analytics = await self.analytics_engine.generate_company_analytics(time_period)
            
            # Generate insights and recommendations
            insights = await self.analytics_engine.generate_performance_insights(analytics)
            
            return BotResponse(
                success=True,
                message=f"Performance analytics report generated for {analytics_type} level.",
                data={
                    "analytics": analytics,
                    "insights": insights,
                    "time_period": time_period
                },
                action_taken="performance_analytics_generated",
                next_steps=[
                    "Review key metrics",
                    "Identify improvement opportunities",
                    "Share with stakeholders",
                    "Create action plans"
                ],
                confidence_score=0.9
            )
            
        except Exception as e:
            self.logger.error(f"Error handling performance analytics: {str(e)}")
            return BotResponse(
                success=False,
                message="Failed to generate performance analytics. Please try again.",
                confidence_score=0.3
            )
    
    async def _handle_skill_assessment(self, request: str, context: Dict[str, Any]) -> BotResponse:
        """Handle skill assessments and competency evaluations"""
        try:
            employee_id = context.get('employee_id')
            assessment_type = context.get('assessment_type', 'comprehensive')
            
            if "conduct" in request.lower() or "start" in request.lower():
                # Start skill assessment
                assessment_id = await self._create_skill_assessment(employee_id, assessment_type)
                
                # Generate assessment questions based on role
                questions = await self._generate_assessment_questions(employee_id, assessment_type)
                
                return BotResponse(
                    success=True,
                    message=f"Skill assessment created. {len(questions)} questions generated.",
                    data={
                        "assessment_id": assessment_id,
                        "questions": questions,
                        "estimated_duration": len(questions) * 2  # 2 minutes per question
                    },
                    action_taken="skill_assessment_created",
                    next_steps=[
                        "Complete assessment questions",
                        "Submit responses",
                        "Review results"
                    ],
                    confidence_score=0.9
                )
            
            else:
                # View assessment results
                assessments = await self.db_manager.get_skill_assessments(employee_id)
                
                if assessments:
                    latest_assessment = assessments[0]  # Most recent
                    skill_profile = await self.analytics_engine.generate_skill_profile(latest_assessment)
                    
                    return BotResponse(
                        success=True,
                        message="Skill assessment results retrieved.",
                        data={
                            "assessments": assessments,
                            "skill_profile": skill_profile
                        },
                        action_taken="skill_assessment_results_provided",
                        next_steps=[
                            "Identify skill gaps",
                            "Create learning plan",
                            "Set improvement goals"
                        ],
                        confidence_score=0.85
                    )
                else:
                    return BotResponse(
                        success=False,
                        message="No skill assessments found. Would you like to create one?",
                        next_steps=["Create new assessment", "Import external results"],
                        confidence_score=0.7
                    )
                
        except Exception as e:
            self.logger.error(f"Error handling skill assessment: {str(e)}")
            return BotResponse(
                success=False,
                message="Failed to process skill assessment request. Please try again.",
                confidence_score=0.3
            )
    
    async def _handle_general_inquiry(self, request: str, context: Dict[str, Any]) -> BotResponse:
        """Handle general performance management inquiries"""
        response_text = await self._generate_performance_response(request, context)
        
        return BotResponse(
            success=True,
            message=response_text,
            action_taken="information_provided",
            confidence_score=0.7
        )
    
    # Helper methods
    async def _generate_review_template(self, employee_id: str, review_type: str) -> Dict[str, Any]:
        """Generate performance review template based on role and type"""
        employee_info = await self.db_manager.get_employee(employee_id)
        
        # Get role-specific competencies
        competencies = await self.db_manager.get_role_competencies(employee_info.get('role'))
        
        # Generate questions using AI
        prompt = f"""
        Generate performance review questions for:
        Role: {employee_info.get('role')}
        Department: {employee_info.get('department')}
        Review Type: {review_type}
        
        Include sections for:
        - Job performance and goals
        - Core competencies: {competencies}
        - Professional development
        - Areas for improvement
        - Overall rating
        
        Return as JSON with sections and questions.
        """
        
        try:
            response = self.ai_client.get_completion(prompt)
            return json.loads(response)
        except:
            return self._get_default_review_template(review_type)
    
    def _get_default_review_template(self, review_type: str) -> Dict[str, Any]:
        """Get default review template"""
        return {
            "sections": [
                {
                    "title": "Goal Achievement",
                    "questions": [
                        "How well did you achieve your goals this period?",
                        "What were your major accomplishments?",
                        "What challenges did you face?"
                    ]
                },
                {
                    "title": "Job Performance",
                    "questions": [
                        "Rate performance in key job responsibilities",
                        "Provide examples of excellent work"
                    ]
                },
                {
                    "title": "Development",
                    "questions": [
                        "What skills have you developed?",
                        "What areas need improvement?",
                        "What are your career goals?"
                    ]
                }
            ]
        }
    
    async def _create_performance_review(
        self, 
        employee_id: str, 
        reviewer_id: str, 
        template: Dict[str, Any], 
        review_type: str
    ) -> str:
        """Create performance review in database"""
        review_data = {
            'employee_id': employee_id,
            'reviewer_id': reviewer_id,
            'review_type': review_type,
            'template': template,
            'status': 'in_progress',
            'due_date': (datetime.utcnow() + timedelta(days=14)).isoformat(),
            'created_at': datetime.utcnow()
        }
        
        return await self.db_manager.create_performance_review(review_data)
    
    async def _extract_goal_data(self, request: str) -> Dict[str, Any]:
        """Extract goal data from request"""
        prompt = f"""
        Extract goal information from this request:
        "{request}"
        
        Return JSON with:
        - title: Goal title
        - description: Detailed description
        - target_date: Target completion date
        - metrics: Success metrics
        - priority: high/medium/low
        - category: performance/development/project/etc
        
        Return only valid JSON.
        """
        
        try:
            response = self.ai_client.get_completion(prompt)
            return json.loads(response)
        except:
            return {}
    
    async def _validate_smart_goal(self, goal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate goal against SMART criteria"""
        prompt = f"""
        Evaluate this goal against SMART criteria:
        {json.dumps(goal_data)}
        
        SMART = Specific, Measurable, Achievable, Relevant, Time-bound
        
        Return JSON with:
        - valid: true/false
        - score: 0-100
        - feedback: Areas that need improvement
        - improvements: List of specific improvements needed
        
        Return only valid JSON.
        """
        
        try:
            response = self.ai_client.get_completion(prompt)
            return json.loads(response)
        except:
            return {
                "valid": True,
                "score": 70,
                "feedback": "Goal appears reasonably well-formed",
                "improvements": []
            }
    
    async def _generate_performance_response(self, request: str, context: Dict[str, Any]) -> str:
        """Generate response for general performance inquiries"""
        prompt = f"""
        As a performance management assistant, respond to this inquiry:
        "{request}"
        
        Context: {json.dumps(context)}
        
        Provide helpful guidance about performance management, reviews, goals, and development.
        """
        
        return self.ai_client.get_completion(prompt)