"""
Base Bot Class for HR Assistant System
Provides common functionality for all specialized HR bots
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging
from dataclasses import dataclass

from ..utils.ai_client import AIClient
from ..utils.database import DatabaseManager
from ..utils.email_service import EmailService


@dataclass
class BotResponse:
    """Standard response format for all bot operations"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    action_taken: Optional[str] = None
    next_steps: Optional[List[str]] = None
    confidence_score: Optional[float] = None


class BaseBot(ABC):
    """
    Abstract base class for all HR bots
    Provides common functionality and enforces interface consistency
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        ai_client: AIClient,
        db_manager: DatabaseManager,
        email_service: EmailService
    ):
        self.name = name
        self.description = description
        self.ai_client = ai_client
        self.db_manager = db_manager
        self.email_service = email_service
        self.logger = logging.getLogger(f"bot.{name}")
        self.created_at = datetime.utcnow()
        
    @abstractmethod
    async def process_request(self, request: str, context: Dict[str, Any] = None) -> BotResponse:
        """
        Process a user request using the bot's specialized capabilities
        
        Args:
            request: The user's request or query
            context: Additional context information
            
        Returns:
            BotResponse: Structured response with results and metadata
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return a list of capabilities this bot can handle"""
        pass
    
    def can_handle(self, request: str, context: Dict[str, Any] = None) -> float:
        """
        Determine if this bot can handle the given request
        
        Args:
            request: The user's request
            context: Additional context
            
        Returns:
            float: Confidence score (0.0 - 1.0) indicating ability to handle request
        """
        # Base implementation using keyword matching
        capabilities = [cap.lower() for cap in self.get_capabilities()]
        request_lower = request.lower()
        
        matches = sum(1 for cap in capabilities if cap in request_lower)
        return min(matches / len(capabilities), 1.0) if capabilities else 0.0
    
    async def log_interaction(
        self,
        request: str,
        response: BotResponse,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """Log bot interaction for analytics and improvement"""
        try:
            interaction_data = {
                'bot_name': self.name,
                'user_id': user_id,
                'session_id': session_id,
                'request': request,
                'response_success': response.success,
                'response_message': response.message,
                'confidence_score': response.confidence_score,
                'timestamp': datetime.utcnow()
            }
            
            await self.db_manager.log_bot_interaction(interaction_data)
            self.logger.info(f"Logged interaction for {self.name}")
            
        except Exception as e:
            self.logger.error(f"Failed to log interaction: {str(e)}")
    
    def _extract_intent(self, request: str) -> str:
        """Extract user intent from request using AI"""
        try:
            prompt = f"""
            Analyze the following HR-related request and extract the main intent:
            
            Request: "{request}"
            
            Respond with a single word intent (e.g., "hire", "fire", "schedule", "review", "onboard").
            """
            
            response = self.ai_client.get_completion(prompt)
            return response.strip().lower()
            
        except Exception as e:
            self.logger.error(f"Failed to extract intent: {str(e)}")
            return "unknown"
    
    def _generate_response(self, intent: str, data: Dict[str, Any]) -> str:
        """Generate natural language response based on intent and data"""
        try:
            prompt = f"""
            Generate a professional, helpful response for an HR assistant bot.
            
            Intent: {intent}
            Data: {data}
            
            Provide a clear, concise response that addresses the user's need.
            """
            
            return self.ai_client.get_completion(prompt)
            
        except Exception as e:
            self.logger.error(f"Failed to generate response: {str(e)}")
            return "I apologize, but I encountered an error processing your request."
    
    async def send_notification(
        self,
        recipient: str,
        subject: str,
        message: str,
        template: Optional[str] = None
    ) -> bool:
        """Send email notification"""
        try:
            return await self.email_service.send_email(
                to=recipient,
                subject=subject,
                body=message,
                template=template
            )
        except Exception as e:
            self.logger.error(f"Failed to send notification: {str(e)}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get bot status information"""
        return {
            'name': self.name,
            'description': self.description,
            'capabilities': self.get_capabilities(),
            'created_at': self.created_at.isoformat(),
            'status': 'active'
        }