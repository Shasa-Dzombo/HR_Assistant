"""
Simplified AI Client - Consolidates Gemini functionality
Uses LangChain integration where appropriate, direct Gemini API for simple tasks
"""

from typing import Dict, List, Any, Optional
import json
import logging
from dataclasses import dataclass
import google.generativeai as genai
from langchain_core.messages import HumanMessage, SystemMessage

from .langchain_gemini import get_gemini_chat_model
from ..config.settings import get_settings


@dataclass
class AIResponse:
    """Response from AI service"""
    content: str
    model: str
    tokens_used: int
    cost_estimate: float
    success: bool = True
    error: Optional[str] = None


class AIClient:
    """
    Consolidated AI client for Gemini models
    Uses LangChain for complex workflows, direct API for simple tasks
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        
        # Initialize Gemini direct API
        genai.configure(api_key=self.settings.GEMINI_API_KEY)
        self.model_name = self.settings.GEMINI_MODEL or "gemini-2.0-flash-exp"
        self.direct_model = genai.GenerativeModel(self.model_name)
        
        # Initialize LangChain model for complex workflows
        self.langchain_model = get_gemini_chat_model(
            model_name=self.model_name,
            temperature=0.7
        )
        
        # Token tracking
        self.total_tokens_used = 0
        self.total_cost = 0.0
        
        # Cost per token (Gemini pricing)
        self.token_costs = {
            "gemini-2.0-flash-exp": {"input": 0.00015/1000, "output": 0.0006/1000},
            "gemini-1.5-pro": {"input": 0.00035/1000, "output": 0.00105/1000},
            "gemini-1.5-flash": {"input": 0.000075/1000, "output": 0.0003/1000}
        }
    
    def get_completion(
        self, 
        prompt: str, 
        temperature: float = 0.7,
        max_tokens: int = 1000,
        system_message: Optional[str] = None
    ) -> str:
        """
        Get completion using direct Gemini API (for simple tasks)
        """
        try:
            # Prepare the full prompt
            full_prompt = prompt
            if system_message:
                full_prompt = f"System: {system_message}\n\nUser: {prompt}"
            
            # Configure generation parameters
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
            
            # Generate response
            response = self.direct_model.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            
            # Track usage
            tokens_used = len(full_prompt.split()) + len(response.text.split())
            cost = self._calculate_cost(tokens_used, self.model_name)
            
            self.total_tokens_used += tokens_used
            self.total_cost += cost
            
            self.logger.info(f"AI completion: {tokens_used} tokens, ${cost:.4f}")
            
            return response.text
            
        except Exception as e:
            self.logger.error(f"AI completion failed: {str(e)}")
            return "I apologize, but I'm having trouble processing your request right now."
    
    async def get_completion_async(
        self, 
        prompt: str, 
        temperature: float = 0.7,
        max_tokens: int = 1000,
        system_message: Optional[str] = None
    ) -> AIResponse:
        """
        Get completion asynchronously using direct Gemini API
        """
        try:
            # Prepare the full prompt
            full_prompt = prompt
            if system_message:
                full_prompt = f"System: {system_message}\n\nUser: {prompt}"
            
            # Configure generation parameters
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
            
            # Generate response asynchronously
            response = await self.direct_model.generate_content_async(
                full_prompt,
                generation_config=generation_config
            )
            
            content = response.text
            tokens_used = len(full_prompt.split()) + len(content.split())
            cost = self._calculate_cost(tokens_used, self.model_name)
            
            self.total_tokens_used += tokens_used
            self.total_cost += cost
            
            return AIResponse(
                content=content,
                model=self.model_name,
                tokens_used=tokens_used,
                cost_estimate=cost,
                success=True
            )
            
        except Exception as e:
            self.logger.error(f"Async AI completion failed: {str(e)}")
            return AIResponse(
                content="I apologize, but I'm having trouble processing your request right now.",
                model=self.model_name,
                tokens_used=0,
                cost_estimate=0.0,
                success=False,
                error=str(e)
            )
    
    async def get_langchain_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7
    ) -> str:
        """
        Get completion using LangChain model (for complex workflows)
        """
        try:
            # Convert messages to LangChain format
            lc_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    lc_messages.append(SystemMessage(content=msg["content"]))
                elif msg["role"] == "user":
                    lc_messages.append(HumanMessage(content=msg["content"]))
            
            # Configure model
            self.langchain_model.temperature = temperature
            
            # Get response
            result = await self.langchain_model.ainvoke(lc_messages)
            
            return result.content
            
        except Exception as e:
            self.logger.error(f"LangChain completion failed: {str(e)}")
            return "I apologize, but I'm having trouble processing your request right now."
    
    def get_embeddings(self, texts: List[str], model: str = "text-embedding-004") -> List[List[float]]:
        """
        Get embeddings for text inputs using Gemini embedding model
        """
        try:
            embeddings = []
            total_tokens = 0
            
            for text in texts:
                # Use Gemini's embedding model
                result = genai.embed_content(
                    model=f"models/{model}",
                    content=text,
                    task_type="retrieval_document"
                )
                
                embeddings.append(result['embedding'])
                total_tokens += len(text.split())
            
            self.total_tokens_used += total_tokens
            cost = total_tokens * 0.00001 / 1000  # Gemini embedding pricing estimate
            self.total_cost += cost
            
            self.logger.info(f"Generated {len(embeddings)} embeddings: {total_tokens} tokens, ${cost:.4f}")
            
            return embeddings
            
        except Exception as e:
            self.logger.error(f"Embedding generation failed: {str(e)}")
            return []
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text using structured prompt"""
        prompt = f"""
        Analyze the sentiment of this text and provide a detailed assessment:
        
        Text: "{text}"
        
        Provide your analysis in JSON format with:
        - sentiment: positive/negative/neutral
        - confidence: 0.0-1.0
        - key_emotions: list of detected emotions
        - tone: professional/casual/frustrated/happy/etc
        - summary: brief explanation
        
        Return only valid JSON.
        """
        
        try:
            response = self.get_completion(prompt, temperature=0.3)
            return json.loads(response)
        except:
            return {
                "sentiment": "neutral",
                "confidence": 0.5,
                "key_emotions": [],
                "tone": "unknown",
                "summary": "Could not analyze sentiment"
            }
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities from HR-related text"""
        prompt = f"""
        Extract named entities from this HR-related text:
        
        Text: "{text}"
        
        Return JSON with entities grouped by type:
        - persons: people names
        - organizations: company/department names
        - locations: places, offices
        - dates: dates and times
        - positions: job titles/roles
        - skills: technical skills mentioned
        - other: other relevant entities
        
        Return only valid JSON.
        """
        
        try:
            response = self.get_completion(prompt, temperature=0.2)
            return json.loads(response)
        except:
            return {
                "persons": [],
                "organizations": [],
                "locations": [],
                "dates": [],
                "positions": [],
                "skills": [],
                "other": []
            }
    
    def classify_intent(self, text: str, categories: List[str]) -> Dict[str, Any]:
        """Classify text into predefined categories"""
        prompt = f"""
        Classify this HR request into one of these categories:
        
        Text: "{text}"
        Categories: {', '.join(categories)}
        
        Return JSON with:
        - category: best matching category
        - confidence: 0.0-1.0
        - reasoning: brief explanation
        - alternatives: other possible categories with scores
        
        Return only valid JSON.
        """
        
        try:
            response = self.get_completion(prompt, temperature=0.2)
            return json.loads(response)
        except:
            return {
                "category": categories[0] if categories else "unknown",
                "confidence": 0.5,
                "reasoning": "Could not classify",
                "alternatives": []
            }
    
    def generate_summary(self, text: str, max_length: int = 200) -> str:
        """Generate summary of text"""
        prompt = f"""
        Summarize this text in {max_length} characters or less:
        
        Text: "{text}"
        
        Provide a clear, concise summary that captures the key points.
        """
        
        try:
            return self.get_completion(prompt, temperature=0.3, max_tokens=max_length//3)
        except:
            return "Summary unavailable"
    
    def _calculate_cost(self, tokens: int, model: str) -> float:
        """Calculate cost for token usage"""
        if model not in self.token_costs:
            return 0.0
        
        # Approximate cost (assuming equal input/output split)
        cost_per_token = (self.token_costs[model]["input"] + self.token_costs[model]["output"]) / 2
        return tokens * cost_per_token
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            "total_tokens": self.total_tokens_used,
            "total_cost": self.total_cost,
            "model": self.model_name,
            "average_cost_per_request": self.total_cost / max(1, self.total_tokens_used) * 1000
        }
    
    def reset_usage_stats(self):
        """Reset usage tracking"""
        self.total_tokens_used = 0
        self.total_cost = 0.0
    
    def get_langchain_model(self):
        """Get the LangChain model for external use"""
        return self.langchain_model


# Global AI client instance  
_ai_client: Optional[AIClient] = None


def get_ai_client() -> AIClient:
    """Get the global AI client instance"""
    global _ai_client
    if _ai_client is None:
        _ai_client = AIClient()
    return _ai_client