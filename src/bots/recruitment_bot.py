"""
Recruitment Bot - Handles hiring, candidate management, and job postings
"""

from typing import Dict, List, Any, Optional
import json
from datetime import datetime, timedelta

from .base_bot import BaseBot, BotResponse
from ..utils.resume_parser import ResumeParser
from ..utils.ai_client import AIClient
from ..utils.database import DatabaseManager
from ..utils.email_service import EmailService


class RecruitmentBot(BaseBot):
    """
    Specialized bot for recruitment and hiring processes
    Handles candidate screening, interview scheduling, and job management
    """
    
    def __init__(self, ai_client: AIClient, db_manager: DatabaseManager, email_service: EmailService):
        super().__init__(
            name="RecruitmentBot",
            description="Handles candidate screening, job postings, and hiring processes",
            ai_client=ai_client,
            db_manager=db_manager,
            email_service=email_service
        )
        self.resume_parser = ResumeParser()
    
    def get_capabilities(self) -> List[str]:
        return [
            "job posting",
            "candidate screening",
            "resume analysis",
            "interview scheduling",
            "skill matching",
            "candidate ranking",
            "application tracking",
            "job board integration",
            "reference checking",
            "offer management"
        ]
    
    async def process_request(self, request: str, context: Dict[str, Any] = None) -> BotResponse:
        """Process recruitment-related requests"""
        try:
            intent = self._extract_intent(request)
            context = context or {}
            
            # Route to appropriate handler based on intent
            if intent in ["post", "create", "job"]:
                return await self._handle_job_posting(request, context)
            elif intent in ["screen", "candidate", "resume"]:
                return await self._handle_candidate_screening(request, context)
            elif intent in ["schedule", "interview"]:
                return await self._handle_interview_scheduling(request, context)
            elif intent in ["match", "recommend"]:
                return await self._handle_job_matching(request, context)
            elif intent in ["rank", "compare"]:
                return await self._handle_candidate_ranking(request, context)
            else:
                return await self._handle_general_inquiry(request, context)
                
        except Exception as e:
            self.logger.error(f"Error processing recruitment request: {str(e)}")
            return BotResponse(
                success=False,
                message="I encountered an error while processing your recruitment request. Please try again.",
                confidence_score=0.0
            )
    
    async def _handle_job_posting(self, request: str, context: Dict[str, Any]) -> BotResponse:
        """Handle job posting creation and management"""
        try:
            # Extract job details from request using AI
            job_details = await self._extract_job_details(request)
            
            if not job_details:
                return BotResponse(
                    success=False,
                    message="I need more information to create a job posting. Please provide job title, description, requirements, and other details.",
                    next_steps=["Provide job title", "Add job description", "List requirements", "Set salary range"]
                )
            
            # Create job posting
            job_id = await self.db_manager.create_job_posting(job_details)
            
            # Generate posting content
            posting_content = await self._generate_job_posting_content(job_details)
            
            return BotResponse(
                success=True,
                message=f"Job posting created successfully! Job ID: {job_id}",
                data={
                    "job_id": job_id,
                    "job_details": job_details,
                    "posting_content": posting_content
                },
                action_taken="job_posting_created",
                next_steps=["Review posting", "Publish to job boards", "Set up candidate pipeline"],
                confidence_score=0.9
            )
            
        except Exception as e:
            self.logger.error(f"Error handling job posting: {str(e)}")
            return BotResponse(
                success=False,
                message="Failed to create job posting. Please check the provided information.",
                confidence_score=0.3
            )
    
    async def _handle_candidate_screening(self, request: str, context: Dict[str, Any]) -> BotResponse:
        """Handle candidate screening and resume analysis"""
        try:
            resume_file = context.get('resume_file')
            candidate_info = context.get('candidate_info', {})
            job_id = context.get('job_id')
            
            if not resume_file:
                return BotResponse(
                    success=False,
                    message="Please provide a resume file for screening.",
                    next_steps=["Upload resume file", "Specify job position"]
                )
            
            # Parse resume
            parsed_resume = await self.resume_parser.parse_resume(resume_file)
            
            # Screen candidate
            screening_result = await self._screen_candidate(parsed_resume, job_id)
            
            # Store candidate information
            candidate_data = {
                'name': parsed_resume.get('name'),
                'email': parsed_resume.get('email'),
                'phone': parsed_resume.get('phone'),
                'skills': parsed_resume.get('skills', []),
                'experience': parsed_resume.get('experience', []),
                'education': parsed_resume.get('education', []),
                **candidate_info
            }
            
            candidate_id = await self.db_manager.create_candidate(candidate_data)
            
            return BotResponse(
                success=True,
                message=f"Candidate screened successfully. Score: {screening_result['score']}/100",
                data={
                    "candidate_id": candidate_id,
                    "screening_score": screening_result['score'],
                    "strengths": screening_result['strengths'],
                    "concerns": screening_result['concerns'],
                    "parsed_resume": parsed_resume
                },
                action_taken="candidate_screened",
                next_steps=screening_result['next_steps'],
                confidence_score=0.85
            )
            
        except Exception as e:
            self.logger.error(f"Error screening candidate: {str(e)}")
            return BotResponse(
                success=False,
                message="Failed to screen candidate. Please check the resume file and try again.",
                confidence_score=0.2
            )
    
    async def _handle_interview_scheduling(self, request: str, context: Dict[str, Any]) -> BotResponse:
        """Handle interview scheduling"""
        try:
            candidate_id = context.get('candidate_id')
            interviewer_ids = context.get('interviewer_ids', [])
            preferred_times = context.get('preferred_times', [])
            
            if not candidate_id:
                return BotResponse(
                    success=False,
                    message="Please specify the candidate for interview scheduling.",
                    next_steps=["Provide candidate ID", "Select interviewers", "Choose time slots"]
                )
            
            # Find optimal interview time
            optimal_time = await self._find_optimal_interview_time(
                candidate_id, interviewer_ids, preferred_times
            )
            
            if not optimal_time:
                return BotResponse(
                    success=False,
                    message="No suitable interview time found. Please provide alternative time slots.",
                    next_steps=["Check availability", "Suggest alternative times"]
                )
            
            # Schedule interview
            interview_id = await self._schedule_interview(candidate_id, interviewer_ids, optimal_time)
            
            # Send notifications
            await self._send_interview_notifications(interview_id)
            
            return BotResponse(
                success=True,
                message=f"Interview scheduled successfully for {optimal_time}",
                data={
                    "interview_id": interview_id,
                    "scheduled_time": optimal_time,
                    "candidate_id": candidate_id,
                    "interviewer_ids": interviewer_ids
                },
                action_taken="interview_scheduled",
                next_steps=["Send calendar invites", "Prepare interview questions", "Share candidate profile"],
                confidence_score=0.9
            )
            
        except Exception as e:
            self.logger.error(f"Error scheduling interview: {str(e)}")
            return BotResponse(
                success=False,
                message="Failed to schedule interview. Please try again.",
                confidence_score=0.3
            )
    
    async def _handle_job_matching(self, request: str, context: Dict[str, Any]) -> BotResponse:
        """Handle job matching and recommendations"""
        try:
            candidate_id = context.get('candidate_id')
            job_preferences = context.get('job_preferences', {})
            
            if candidate_id:
                # Get matches for specific candidate
                matches = await self.job_matcher.find_matches_for_candidate(candidate_id)
            else:
                # General job recommendations
                matches = await self.job_matcher.get_job_recommendations(job_preferences)
            
            return BotResponse(
                success=True,
                message=f"Found {len(matches)} job matches",
                data={
                    "matches": matches,
                    "total_count": len(matches)
                },
                action_taken="job_matching_performed",
                next_steps=["Review matches", "Apply to suitable positions", "Update preferences"],
                confidence_score=0.8
            )
            
        except Exception as e:
            self.logger.error(f"Error in job matching: {str(e)}")
            return BotResponse(
                success=False,
                message="Failed to find job matches. Please try again.",
                confidence_score=0.2
            )
    
    async def _handle_candidate_ranking(self, request: str, context: Dict[str, Any]) -> BotResponse:
        """Handle candidate ranking and comparison"""
        try:
            job_id = context.get('job_id')
            candidate_ids = context.get('candidate_ids', [])
            
            if not job_id:
                return BotResponse(
                    success=False,
                    message="Please specify the job position for candidate ranking.",
                    next_steps=["Provide job ID", "Select candidates to compare"]
                )
            
            # Rank candidates
            ranked_candidates = await self._rank_candidates(job_id, candidate_ids)
            
            return BotResponse(
                success=True,
                message=f"Ranked {len(ranked_candidates)} candidates for the position",
                data={
                    "ranked_candidates": ranked_candidates,
                    "job_id": job_id
                },
                action_taken="candidate_ranking_completed",
                next_steps=["Review top candidates", "Schedule interviews", "Make hiring decisions"],
                confidence_score=0.85
            )
            
        except Exception as e:
            self.logger.error(f"Error ranking candidates: {str(e)}")
            return BotResponse(
                success=False,
                message="Failed to rank candidates. Please try again.",
                confidence_score=0.3
            )
    
    async def _handle_general_inquiry(self, request: str, context: Dict[str, Any]) -> BotResponse:
        """Handle general recruitment inquiries"""
        response_text = await self._generate_recruitment_response(request, context)
        
        return BotResponse(
            success=True,
            message=response_text,
            action_taken="information_provided",
            confidence_score=0.7
        )
    
    # Helper methods
    async def _extract_job_details(self, request: str) -> Dict[str, Any]:
        """Extract job details from request using AI"""
        prompt = f"""
        Extract job posting details from this request:
        "{request}"
        
        Return a JSON object with these fields:
        - title: Job title
        - description: Job description
        - requirements: List of requirements
        - salary_min: Minimum salary
        - salary_max: Maximum salary
        - location: Job location
        - employment_type: full-time, part-time, contract, etc.
        - department: Department name
        - experience_level: entry, mid, senior, executive
        
        Return only valid JSON.
        """
        
        try:
            response = self.ai_client.get_completion(prompt)
            return json.loads(response)
        except:
            return {}
    
    async def _screen_candidate(self, parsed_resume: Dict[str, Any], job_id: Optional[str]) -> Dict[str, Any]:
        """Screen candidate against job requirements"""
        if job_id:
            job_details = await self.db_manager.get_job_posting(job_id)
        else:
            job_details = {}
        
        # AI-powered screening
        prompt = f"""
        Screen this candidate against the job requirements:
        
        Candidate: {json.dumps(parsed_resume)}
        Job Requirements: {json.dumps(job_details)}
        
        Provide a screening score (0-100) and analysis including:
        - score: Overall match score
        - strengths: List of candidate strengths
        - concerns: List of potential concerns
        - next_steps: Recommended next steps
        
        Return as JSON.
        """
        
        try:
            response = self.ai_client.get_completion(prompt)
            return json.loads(response)
        except:
            return {
                "score": 50,
                "strengths": ["Resume provided"],
                "concerns": ["Unable to fully analyze"],
                "next_steps": ["Manual review required"]
            }
    
    async def _generate_job_posting_content(self, job_details: Dict[str, Any]) -> str:
        """Generate professional job posting content"""
        prompt = f"""
        Create a professional job posting based on these details:
        {json.dumps(job_details)}
        
        Include:
        - Compelling job title and description
        - Clear requirements and qualifications
        - Company benefits and culture
        - Application instructions
        
        Make it engaging and professional.
        """
        
        return self.ai_client.get_completion(prompt)
    
    async def _find_optimal_interview_time(
        self, 
        candidate_id: str, 
        interviewer_ids: List[str], 
        preferred_times: List[str]
    ) -> Optional[str]:
        """Find optimal interview time based on availability"""
        # This would integrate with calendar systems
        # For now, return the first preferred time
        return preferred_times[0] if preferred_times else None
    
    async def _schedule_interview(
        self, 
        candidate_id: str, 
        interviewer_ids: List[str], 
        interview_time: str
    ) -> str:
        """Schedule interview in database and calendar systems"""
        interview_data = {
            'candidate_id': candidate_id,
            'interviewer_ids': interviewer_ids,
            'scheduled_time': interview_time,
            'status': 'scheduled',
            'created_at': datetime.utcnow()
        }
        
        return await self.db_manager.create_interview(interview_data)
    
    async def _send_interview_notifications(self, interview_id: str):
        """Send interview notifications to all participants"""
        interview_details = await self.db_manager.get_interview(interview_id)
        
        # Send to candidate
        candidate_email = interview_details.get('candidate_email')
        if candidate_email:
            await self.send_notification(
                recipient=candidate_email,
                subject="Interview Scheduled",
                message="Your interview has been scheduled. Please check your calendar for details.",
                template="interview_scheduled"
            )
        
        # Send to interviewers
        for interviewer_email in interview_details.get('interviewer_emails', []):
            await self.send_notification(
                recipient=interviewer_email,
                subject="Interview Scheduled",
                message="New interview scheduled. Please check your calendar.",
                template="interviewer_notification"
            )
    
    async def _rank_candidates(self, job_id: str, candidate_ids: List[str]) -> List[Dict[str, Any]]:
        """Rank candidates for a specific job"""
        job_details = await self.db_manager.get_job_posting(job_id)
        candidates = []
        
        for candidate_id in candidate_ids:
            candidate = await self.db_manager.get_candidate(candidate_id)
            score = await self._calculate_candidate_score(candidate, job_details)
            candidates.append({
                'candidate_id': candidate_id,
                'candidate': candidate,
                'score': score
            })
        
        return sorted(candidates, key=lambda x: x['score'], reverse=True)
    
    async def _calculate_candidate_score(self, candidate: Dict[str, Any], job_details: Dict[str, Any]) -> float:
        """Calculate candidate score for job match"""
        # AI-powered scoring algorithm
        prompt = f"""
        Score this candidate for the job (0-100):
        
        Candidate: {json.dumps(candidate)}
        Job: {json.dumps(job_details)}
        
        Consider skills match, experience level, education, and cultural fit.
        Return only the numeric score.
        """
        
        try:
            response = self.ai_client.get_completion(prompt)
            return float(response.strip())
        except:
            return 50.0
    
    async def _generate_recruitment_response(self, request: str, context: Dict[str, Any]) -> str:
        """Generate response for general recruitment inquiries"""
        prompt = f"""
        As an HR recruitment assistant, respond to this inquiry:
        "{request}"
        
        Context: {json.dumps(context)}
        
        Provide helpful, professional guidance about recruitment processes.
        """
        
        return self.ai_client.get_completion(prompt)