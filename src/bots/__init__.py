"""
Bot initialization module
"""

from .base_bot import BaseBot, BotResponse
from .bot_manager import BotManager
from .recruitment_bot import RecruitmentBot
from .employee_management_bot import EmployeeManagementBot
from .onboarding_bot import OnboardingBot
from .performance_bot import PerformanceBot

__all__ = [
    'BaseBot',
    'BotResponse', 
    'BotManager',
    'RecruitmentBot',
    'EmployeeManagementBot',
    'OnboardingBot',
    'PerformanceBot'
]