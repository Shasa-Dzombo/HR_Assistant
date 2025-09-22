"""
HR Assistant Main Application
Provides a command-line interface to interact with HR bots
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from src.bots.bot_manager import BotManager
from src.bots.recruitment_bot import RecruitmentBot
from src.bots.employee_management_bot import EmployeeManagementBot
from src.bots.onboarding_bot import OnboardingBot
from src.bots.performance_bot import PerformanceBot
from src.config.settings import get_settings


def setup_logging():
    """Configure logging for the application"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('hr_assistant.log'),
            logging.StreamHandler()
        ]
    )


class HRAssistantApp:
    """Main HR Assistant application"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        
        # Initialize core services
        from src.utils.ai_client import AIClient
        from src.utils.database import DatabaseManager
        from src.utils.email_service import EmailService
        
        self.ai_client = AIClient()
        self.db_manager = DatabaseManager()
        self.email_service = EmailService()
        
        # Initialize bot manager with required dependencies
        self.bot_manager = BotManager(
            ai_client=self.ai_client,
            db_manager=self.db_manager,
            email_service=self.email_service
        )
        
        # Initialize bots
        self._initialize_bots()
    
    def _initialize_bots(self):
        """Initialize all HR bots through BotManager"""
        try:
            # BotManager already creates all bots in its __init__ method
            # Just assign references for easy access
            self.recruitment_bot = self.bot_manager.bots['recruitment']
            self.employee_bot = self.bot_manager.bots['employee_management']
            self.onboarding_bot = self.bot_manager.bots['onboarding']
            self.performance_bot = self.bot_manager.bots['performance']
            
            self.logger.info("All HR bots initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize bots: {str(e)}")
            raise
    
    def display_menu(self):
        """Display the main menu"""
        print("\n" + "="*50)
        print("🤖 HR Assistant - Main Menu")
        print("="*50)
        print("1. 👥 Recruitment Bot")
        print("2. 📋 Employee Management Bot")
        print("3. 🎯 Onboarding Bot")
        print("4. 📊 Performance Bot")
        print("5. 🔄 Bot Manager (Smart Routing)")
        print("6. ℹ️  Show Bot Capabilities")
        print("7. 📝 View Logs")
        print("0. 🚪 Exit")
        print("="*50)
    
    def display_bot_capabilities(self):
        """Display capabilities of all bots"""
        print("\n" + "="*50)
        print("🤖 Bot Capabilities")
        print("="*50)
        
        bots = {
            "Recruitment Bot": self.recruitment_bot,
            "Employee Management Bot": self.employee_bot,
            "Onboarding Bot": self.onboarding_bot,
            "Performance Bot": self.performance_bot
        }
        
        for bot_name, bot in bots.items():
            print(f"\n{bot_name}:")
            capabilities = bot.get_capabilities()
            for i, capability in enumerate(capabilities, 1):
                print(f"  {i}. {capability}")
    
    async def interact_with_bot(self, bot, bot_name: str):
        """Interactive session with a specific bot"""
        print(f"\n🤖 {bot_name} - Interactive Mode")
        print("Type 'back' to return to main menu")
        print("Type 'help' to see capabilities")
        print("-" * 40)
        
        while True:
            try:
                user_input = input(f"\n[{bot_name}] Enter your request: ").strip()
                
                if user_input.lower() == 'back':
                    break
                elif user_input.lower() == 'help':
                    capabilities = bot.get_capabilities()
                    print(f"\n{bot_name} can help with:")
                    for i, capability in enumerate(capabilities, 1):
                        print(f"  {i}. {capability}")
                    continue
                elif not user_input:
                    print("Please enter a request or 'back' to return.")
                    continue
                
                print(f"\n🤔 Processing your request...")
                
                # Process the request
                response = await bot.process_request(user_input)
                
                # Display response
                print(f"\n✅ Response:")
                print(f"Success: {response.success}")
                print(f"Message: {response.message}")
                
                if response.data:
                    print(f"Data: {response.data}")
                
                if response.suggestions:
                    print(f"Suggestions: {', '.join(response.suggestions)}")
                
                if not response.success and response.error:
                    print(f"❌ Error: {response.error}")
                
            except KeyboardInterrupt:
                print("\n\nReturning to main menu...")
                break
            except Exception as e:
                print(f"❌ An error occurred: {str(e)}")
                self.logger.error(f"Error in bot interaction: {str(e)}")
    
    async def smart_routing_mode(self):
        """Use bot manager for smart routing"""
        print("\n🧠 Smart Routing Mode")
        print("The system will automatically choose the best bot for your request")
        print("Type 'back' to return to main menu")
        print("-" * 50)
        
        while True:
            try:
                user_input = input("\n[Smart Routing] Enter your HR request: ").strip()
                
                if user_input.lower() == 'back':
                    break
                elif not user_input:
                    print("Please enter a request or 'back' to return.")
                    continue
                
                print(f"\n🤔 Analyzing request and routing to best bot...")
                
                # Use bot manager to route the request
                response = await self.bot_manager.process_request(user_input)
                
                # Display response
                handled_by = response.data.get('handled_by', 'Unknown') if response.data else 'Unknown'
                print(f"\n✅ Response from {handled_by} bot:")
                print(f"Success: {response.success}")
                print(f"Message: {response.message}")
                
                if response.data:
                    print(f"Additional Data: {response.data}")
                
                if response.next_steps:
                    print(f"Next Steps: {', '.join(response.next_steps)}")
                
                if response.action_taken:
                    print(f"Action Taken: {response.action_taken}")
                
                if response.confidence_score is not None:
                    print(f"Confidence: {response.confidence_score:.2f}")
                
            except KeyboardInterrupt:
                print("\n\nReturning to main menu...")
                break
            except Exception as e:
                print(f"❌ An error occurred: {str(e)}")
                self.logger.error(f"Error in smart routing: {str(e)}")
    
    def view_logs(self):
        """Display recent log entries"""
        try:
            print("\n📝 Recent Log Entries (last 20 lines):")
            print("-" * 50)
            
            with open('hr_assistant.log', 'r') as f:
                lines = f.readlines()
                recent_lines = lines[-20:] if len(lines) > 20 else lines
                
                for line in recent_lines:
                    print(line.strip())
                    
        except FileNotFoundError:
            print("No log file found yet.")
        except Exception as e:
            print(f"Error reading logs: {str(e)}")
    
    async def run(self):
        """Main application loop"""
        print("🚀 Starting HR Assistant...")
        print(f"⚙️  Configuration loaded: {self.settings.APP_NAME}")
        
        while True:
            try:
                self.display_menu()
                choice = input("\nSelect an option (0-7): ").strip()
                
                if choice == '0':
                    print("\n👋 Goodbye! Thanks for using HR Assistant.")
                    break
                elif choice == '1':
                    await self.interact_with_bot(self.recruitment_bot, "Recruitment Bot")
                elif choice == '2':
                    await self.interact_with_bot(self.employee_bot, "Employee Management Bot")
                elif choice == '3':
                    await self.interact_with_bot(self.onboarding_bot, "Onboarding Bot")
                elif choice == '4':
                    await self.interact_with_bot(self.performance_bot, "Performance Bot")
                elif choice == '5':
                    await self.smart_routing_mode()
                elif choice == '6':
                    self.display_bot_capabilities()
                elif choice == '7':
                    self.view_logs()
                else:
                    print("❌ Invalid option. Please select 0-7.")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye! Thanks for using HR Assistant.")
                break
            except Exception as e:
                print(f"❌ An unexpected error occurred: {str(e)}")
                self.logger.error(f"Unexpected error in main loop: {str(e)}")


async def main():
    """Application entry point"""
    # Setup logging
    setup_logging()
    
    try:
        # Create and run the application
        app = HRAssistantApp()
        await app.run()
        
    except Exception as e:
        logging.error(f"Failed to start HR Assistant: {str(e)}")
        print(f"❌ Failed to start HR Assistant: {str(e)}")
        print("Please check your configuration and try again.")


if __name__ == "__main__":
    print("🤖 HR Assistant v1.0")
    print("=" * 30)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Application interrupted. Goodbye!")
    except Exception as e:
        print(f"❌ Critical error: {str(e)}")
        logging.error(f"Critical error: {str(e)}")