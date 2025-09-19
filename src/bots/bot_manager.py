"""
Bot Manager - Coordinates multiple HR bots and routes requests
"""

from typing import Dict, List, Any, Optional
import asyncio
from datetime import datetime

from .base_bot import BaseBot, BotResponse
from .recruitment_bot import RecruitmentBot
from .employee_management_bot import EmployeeManagementBot
from .onboarding_bot import OnboardingBot
from .performance_bot import PerformanceBot
from ..utils.ai_client import AIClient
from ..utils.database import DatabaseManager
from ..utils.email_service import EmailService


class BotManager:
    """
    Central manager for all HR bots
    Routes requests to appropriate bots and coordinates multi-bot workflows
    """
    
    def __init__(
        self,
        ai_client: AIClient,
        db_manager: DatabaseManager,
        email_service: EmailService
    ):
        self.ai_client = ai_client
        self.db_manager = db_manager
        self.email_service = email_service
        
        # Initialize all bots
        self.bots = {
            'recruitment': RecruitmentBot(ai_client, db_manager, email_service),
            'employee_management': EmployeeManagementBot(ai_client, db_manager, email_service),
            'onboarding': OnboardingBot(ai_client, db_manager, email_service),
            'performance': PerformanceBot(ai_client, db_manager, email_service)
        }
        
        self.request_history = []
    
    async def process_request(
        self, 
        request: str, 
        context: Dict[str, Any] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> BotResponse:
        """
        Process user request by routing to most appropriate bot
        
        Args:
            request: User's request or query
            context: Additional context information
            user_id: ID of the requesting user
            session_id: Session identifier
            
        Returns:
            BotResponse: Combined response from appropriate bot(s)
        """
        try:
            context = context or {}
            
            # Determine which bot(s) can handle the request
            bot_scores = await self._evaluate_bot_capabilities(request, context)
            
            # Route to the best bot
            best_bot_name = max(bot_scores, key=bot_scores.get)
            best_bot = self.bots[best_bot_name]
            
            # Check if this requires multi-bot coordination
            if await self._requires_multi_bot_coordination(request, context):
                return await self._handle_multi_bot_request(request, context, user_id, session_id)
            
            # Process with single bot
            response = await best_bot.process_request(request, context)
            
            # Log the interaction
            await self._log_interaction(
                request, response, best_bot_name, user_id, session_id
            )
            
            # Add routing information to response
            response.data = response.data or {}
            response.data['handled_by'] = best_bot_name
            response.data['confidence_scores'] = bot_scores
            
            return response
            
        except Exception as e:
            return BotResponse(
                success=False,
                message="I encountered an error processing your request. Please try again or contact support.",
                confidence_score=0.0
            )
    
    async def _evaluate_bot_capabilities(
        self, 
        request: str, 
        context: Dict[str, Any]
    ) -> Dict[str, float]:
        """Evaluate which bots can handle the request"""
        scores = {}
        
        # Get capability scores from each bot
        for bot_name, bot in self.bots.items():
            try:
                score = bot.can_handle(request, context)
                scores[bot_name] = score
            except Exception as e:
                scores[bot_name] = 0.0
        
        # Use AI to enhance routing decision
        enhanced_scores = await self._ai_enhanced_routing(request, context, scores)
        
        return enhanced_scores
    
    async def _ai_enhanced_routing(
        self, 
        request: str, 
        context: Dict[str, Any], 
        initial_scores: Dict[str, float]
    ) -> Dict[str, float]:
        """Use AI to improve bot routing decisions"""
        prompt = f"""
        Analyze this HR request and determine which bot should handle it:
        
        Request: "{request}"
        Context: {context}
        
        Available bots:
        - recruitment: Handles hiring, candidates, job postings, interviews
        - employee_management: Handles employee records, policies, benefits, leave
        - onboarding: Handles new hire processes, documentation, orientation
        - performance: Handles reviews, goals, feedback, development
        
        Current scores: {initial_scores}
        
        Return JSON with updated confidence scores (0.0-1.0) for each bot.
        Consider the specific intent and domain of the request.
        """
        
        try:
            response = self.ai_client.get_completion(prompt)
            ai_scores = eval(response)  # Note: In production, use json.loads with proper validation
            
            # Combine AI scores with initial scores
            combined_scores = {}
            for bot_name in self.bots.keys():
                initial = initial_scores.get(bot_name, 0.0)
                ai_score = ai_scores.get(bot_name, 0.0)
                combined_scores[bot_name] = (initial + ai_score) / 2
            
            return combined_scores
            
        except Exception as e:
            # Fall back to initial scores if AI enhancement fails
            return initial_scores
    
    async def _requires_multi_bot_coordination(
        self, 
        request: str, 
        context: Dict[str, Any]
    ) -> bool:
        """Determine if request requires coordination between multiple bots"""
        multi_bot_keywords = [
            "hire and onboard",
            "recruit and train",
            "performance and goals",
            "onboard and setup",
            "review and develop",
            "end-to-end",
            "complete process"
        ]
        
        request_lower = request.lower()
        return any(keyword in request_lower for keyword in multi_bot_keywords)
    
    async def _handle_multi_bot_request(
        self, 
        request: str, 
        context: Dict[str, Any],
        user_id: Optional[str],
        session_id: Optional[str]
    ) -> BotResponse:
        """Handle requests that require multiple bots"""
        
        # Identify the workflow pattern
        workflow_type = await self._identify_workflow_type(request)
        
        if workflow_type == "hire_to_onboard":
            return await self._handle_hire_to_onboard_workflow(request, context, user_id, session_id)
        elif workflow_type == "onboard_to_performance":
            return await self._handle_onboard_to_performance_workflow(request, context, user_id, session_id)
        elif workflow_type == "complete_employee_lifecycle":
            return await self._handle_complete_lifecycle_workflow(request, context, user_id, session_id)
        else:
            # Fall back to single bot handling
            bot_scores = await self._evaluate_bot_capabilities(request, context)
            best_bot_name = max(bot_scores, key=bot_scores.get)
            return await self.bots[best_bot_name].process_request(request, context)
    
    async def _handle_hire_to_onboard_workflow(
        self, 
        request: str, 
        context: Dict[str, Any],
        user_id: Optional[str],
        session_id: Optional[str]
    ) -> BotResponse:
        """Handle hire-to-onboard workflow"""
        workflow_steps = []
        
        try:
            # Step 1: Handle recruitment part
            recruitment_response = await self.bots['recruitment'].process_request(request, context)
            workflow_steps.append({
                'step': 'recruitment',
                'response': recruitment_response,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            if recruitment_response.success and recruitment_response.data:
                # Step 2: If hiring is successful, initiate onboarding
                candidate_data = recruitment_response.data
                onboarding_context = {
                    **context,
                    'new_hire_info': candidate_data,
                    'triggered_by': 'recruitment_completion'
                }
                
                onboarding_request = f"Start onboarding process for new hire from recruitment"
                onboarding_response = await self.bots['onboarding'].process_request(
                    onboarding_request, onboarding_context
                )
                
                workflow_steps.append({
                    'step': 'onboarding',
                    'response': onboarding_response,
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            # Combine responses
            combined_response = self._combine_workflow_responses(workflow_steps)
            
            # Log multi-bot interaction
            await self._log_multi_bot_interaction(
                request, workflow_steps, user_id, session_id
            )
            
            return combined_response
            
        except Exception as e:
            return BotResponse(
                success=False,
                message="Failed to complete hire-to-onboard workflow. Please try individual steps.",
                data={'workflow_steps': workflow_steps},
                confidence_score=0.3
            )
    
    async def _identify_workflow_type(self, request: str) -> str:
        """Identify the type of multi-bot workflow needed"""
        request_lower = request.lower()
        
        if any(phrase in request_lower for phrase in ["hire and onboard", "recruit and onboard"]):
            return "hire_to_onboard"
        elif any(phrase in request_lower for phrase in ["onboard and performance", "onboard and goals"]):
            return "onboard_to_performance"
        elif any(phrase in request_lower for phrase in ["complete process", "end-to-end", "full lifecycle"]):
            return "complete_employee_lifecycle"
        else:
            return "unknown"
    
    def _combine_workflow_responses(self, workflow_steps: List[Dict[str, Any]]) -> BotResponse:
        """Combine responses from multiple workflow steps"""
        all_successful = all(step['response'].success for step in workflow_steps)
        
        # Combine messages
        messages = []
        for step in workflow_steps:
            step_name = step['step'].title()
            response = step['response']
            if response.success:
                messages.append(f"{step_name}: {response.message}")
            else:
                messages.append(f"{step_name}: Failed - {response.message}")
        
        combined_message = "\n".join(messages)
        
        # Combine next steps
        all_next_steps = []
        for step in workflow_steps:
            if step['response'].next_steps:
                all_next_steps.extend(step['response'].next_steps)
        
        # Combine data
        combined_data = {
            'workflow_steps': workflow_steps,
            'workflow_type': 'multi_bot_coordination',
            'steps_completed': len([s for s in workflow_steps if s['response'].success]),
            'total_steps': len(workflow_steps)
        }
        
        # Calculate overall confidence
        confidences = [step['response'].confidence_score or 0.5 for step in workflow_steps]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
        
        return BotResponse(
            success=all_successful,
            message=combined_message,
            data=combined_data,
            action_taken="multi_bot_workflow_completed" if all_successful else "multi_bot_workflow_partial",
            next_steps=all_next_steps[:5],  # Limit to top 5 next steps
            confidence_score=avg_confidence
        )
    
    async def _log_interaction(
        self,
        request: str,
        response: BotResponse,
        bot_name: str,
        user_id: Optional[str],
        session_id: Optional[str]
    ):
        """Log bot interaction for analytics"""
        interaction_data = {
            'request': request,
            'response': response.dict(),
            'bot_name': bot_name,
            'user_id': user_id,
            'session_id': session_id,
            'timestamp': datetime.utcnow(),
            'type': 'single_bot'
        }
        
        self.request_history.append(interaction_data)
        
        try:
            await self.db_manager.log_bot_interaction(interaction_data)
        except Exception as e:
            pass  # Don't fail the main request if logging fails
    
    async def _log_multi_bot_interaction(
        self,
        request: str,
        workflow_steps: List[Dict[str, Any]],
        user_id: Optional[str],
        session_id: Optional[str]
    ):
        """Log multi-bot workflow interaction"""
        interaction_data = {
            'request': request,
            'workflow_steps': workflow_steps,
            'user_id': user_id,
            'session_id': session_id,
            'timestamp': datetime.utcnow(),
            'type': 'multi_bot_workflow'
        }
        
        self.request_history.append(interaction_data)
        
        try:
            await self.db_manager.log_multi_bot_interaction(interaction_data)
        except Exception as e:
            pass  # Don't fail the main request if logging fails
    
    def get_available_bots(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all available bots"""
        bot_info = {}
        for name, bot in self.bots.items():
            bot_info[name] = bot.get_status()
        return bot_info
    
    def get_bot_capabilities(self) -> Dict[str, List[str]]:
        """Get capabilities of all bots"""
        capabilities = {}
        for name, bot in self.bots.items():
            capabilities[name] = bot.get_capabilities()
        return capabilities
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        return {
            'available_bots': len(self.bots),
            'bot_status': {name: 'active' for name in self.bots.keys()},
            'total_interactions': len(self.request_history),
            'last_interaction': self.request_history[-1]['timestamp'] if self.request_history else None,
            'capabilities': self.get_bot_capabilities()
        }