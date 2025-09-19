"""
LangChain integration for Gemini AI
Provides LangChain-compatible interface for Gemini models
"""

from typing import Dict, List, Any, Optional, AsyncIterator
from langchain_core.language_models.llms import LLM
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.outputs import ChatResult, ChatGeneration, LLMResult, Generation
from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai
from pydantic import Field

from ..config.settings import get_settings


class GeminiLangChainAdapter(BaseChatModel):
    """
    LangChain adapter for Google Gemini models
    Provides compatibility with LangGraph and other LangGraph tools
    """
    
    model_name: str = Field(default="gemini-2.0-flash-exp")
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=1000)
    model: Any = Field(default=None, exclude=True)  # Gemini model instance
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        settings = get_settings()
        
        # Configure Gemini
        genai.configure(api_key=settings.GEMINI_API_KEY)
        # Use object.__setattr__ to set the model field
        object.__setattr__(self, 'model', genai.GenerativeModel(self.model_name))
    
    @property
    def _llm_type(self) -> str:
        return "gemini"
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate chat completion synchronously"""
        try:
            # Convert LangChain messages to Gemini format
            prompt = self._convert_messages_to_prompt(messages)
            
            # Configure generation
            generation_config = genai.types.GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
            )
            
            # Generate response
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            # Convert response
            ai_message = AIMessage(content=response.text)
            generation = ChatGeneration(message=ai_message)
            
            return ChatResult(generations=[generation])
            
        except Exception as e:
            # Return error message
            error_message = AIMessage(content=f"Error: {str(e)}")
            generation = ChatGeneration(message=error_message)
            return ChatResult(generations=[generation])
    
    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate chat completion asynchronously"""
        try:
            # Convert LangChain messages to Gemini format
            prompt = self._convert_messages_to_prompt(messages)
            
            # Configure generation
            generation_config = genai.types.GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
            )
            
            # Generate response asynchronously
            response = await self.model.generate_content_async(
                prompt,
                generation_config=generation_config
            )
            
            # Convert response
            ai_message = AIMessage(content=response.text)
            generation = ChatGeneration(message=ai_message)
            
            return ChatResult(generations=[generation])
            
        except Exception as e:
            # Return error message
            error_message = AIMessage(content=f"Error: {str(e)}")
            generation = ChatGeneration(message=error_message)
            return ChatResult(generations=[generation])
    
    def _convert_messages_to_prompt(self, messages: List[BaseMessage]) -> str:
        """Convert LangChain messages to a single prompt string"""
        prompt_parts = []
        
        for message in messages:
            if isinstance(message, SystemMessage):
                prompt_parts.append(f"System: {message.content}")
            elif isinstance(message, HumanMessage):
                prompt_parts.append(f"Human: {message.content}")
            elif isinstance(message, AIMessage):
                prompt_parts.append(f"Assistant: {message.content}")
            else:
                prompt_parts.append(f"Message: {message.content}")
        
        return "\n\n".join(prompt_parts)


class GeminiLLMAdapter(LLM):
    """
    Simple LLM adapter for Gemini (non-chat interface)
    """
    
    model_name: str = Field(default="gemini-2.0-flash-exp")
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=1000)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        settings = get_settings()
        
        # Configure Gemini
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(self.model_name)
    
    @property
    def _llm_type(self) -> str:
        return "gemini-llm"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> str:
        """Generate completion synchronously"""
        try:
            # Configure generation
            generation_config = genai.types.GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
            )
            
            # Generate response
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            return response.text
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def _acall(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> str:
        """Generate completion asynchronously"""
        try:
            # Configure generation
            generation_config = genai.types.GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
            )
            
            # Generate response asynchronously
            response = await self.model.generate_content_async(
                prompt,
                generation_config=generation_config
            )
            
            return response.text
            
        except Exception as e:
            return f"Error: {str(e)}"


# Factory functions for easy instantiation
def get_gemini_chat_model(**kwargs) -> GeminiLangChainAdapter:
    """Get a Gemini chat model for LangChain/LangGraph"""
    return GeminiLangChainAdapter(**kwargs)


def get_gemini_llm(**kwargs) -> GeminiLLMAdapter:
    """Get a Gemini LLM for LangChain"""
    return GeminiLLMAdapter(**kwargs)