"""
Employee Management Bot - Handles employee records, policies, and general HR queries
"""

from typing import Dict, List, Any, Optional
import json
from datetime import datetime, timedelta

from .base_bot import BaseBot, BotResponse
from ..utils.ai_client import AIClient
from ..utils.database import DatabaseManager
from ..utils.email_service import EmailService


class EmployeeManagementBot(BaseBot):
    """
    Specialized bot for employee management and HR policy queries
    Handles employee records, policy questions, and administrative tasks
    """
    
    def __init__(self, ai_client: AIClient, db_manager: DatabaseManager, email_service: EmailService):
        super().__init__(
            name="EmployeeManagementBot",
            description="Handles employee records, HR policies, and administrative tasks",
            ai_client=ai_client,
            db_manager=db_manager,
            email_service=email_service
        )
    
    def get_capabilities(self) -> List[str]:
        return [
            "employee records",
            "policy queries",
            "benefits information",
            "leave management",
            "employee directory",
            "organizational chart",
            "document requests",
            "compliance tracking",
            "employee updates",
            "HR policies"
        ]
    
    async def process_request(self, request: str, context: Dict[str, Any] = None) -> BotResponse:
        """Process employee management requests"""
        try:
            intent = self._extract_intent(request)
            context = context or {}
            
            # Route to appropriate handler based on intent
            if intent in ["policy", "policies", "rule", "rules"]:
                return await self._handle_policy_query(request, context)
            elif intent in ["employee", "record", "profile"]:
                return await self._handle_employee_record(request, context)
            elif intent in ["leave", "vacation", "pto", "sick"]:
                return await self._handle_leave_management(request, context)
            elif intent in ["benefits", "benefit", "insurance", "401k"]:
                return await self._handle_benefits_inquiry(request, context)
            elif intent in ["directory", "contact", "find"]:
                return await self._handle_directory_search(request, context)
            elif intent in ["document", "form", "paperwork"]:
                return await self._handle_document_request(request, context)
            elif intent in ["update", "change", "modify"]:
                return await self._handle_employee_update(request, context)
            else:
                return await self._handle_general_inquiry(request, context)
                
        except Exception as e:
            self.logger.error(f"Error processing employee management request: {str(e)}")
            return BotResponse(
                success=False,
                message="I encountered an error while processing your request. Please try again.",
                confidence_score=0.0
            )
    
    async def _handle_policy_query(self, request: str, context: Dict[str, Any]) -> BotResponse:
        """Handle HR policy queries"""
        try:
            # Extract policy topic from request
            policy_topic = await self._extract_policy_topic(request)
            
            # Search for relevant policies
            policies = await self.policy_engine.search_policies(policy_topic, request)
            
            if not policies:
                return BotResponse(
                    success=False,
                    message=f"I couldn't find specific policies related to '{policy_topic}'. Could you be more specific?",
                    next_steps=["Rephrase your question", "Contact HR directly", "Check employee handbook"],
                    confidence_score=0.3
                )
            
            # Generate comprehensive policy response
            policy_response = await self._generate_policy_response(policies, request)
            
            return BotResponse(
                success=True,
                message=policy_response,
                data={
                    "policy_topic": policy_topic,
                    "relevant_policies": policies,
                    "last_updated": datetime.utcnow().isoformat()
                },
                action_taken="policy_information_provided",
                next_steps=["Review full policy document", "Contact HR for clarification"],
                confidence_score=0.9
            )
            
        except Exception as e:
            self.logger.error(f"Error handling policy query: {str(e)}")
            return BotResponse(
                success=False,
                message="Failed to retrieve policy information. Please try rephrasing your question.",
                confidence_score=0.2
            )
    
    async def _handle_employee_record(self, request: str, context: Dict[str, Any]) -> BotResponse:
        """Handle employee record requests"""
        try:
            employee_id = context.get('employee_id')
            requester_id = context.get('requester_id')
            
            if not employee_id:
                return BotResponse(
                    success=False,
                    message="Please specify which employee record you'd like to access.",
                    next_steps=["Provide employee ID", "Use employee name search"],
                    confidence_score=0.2
                )
            
            # Check permissions
            has_permission = await self._check_record_permissions(requester_id, employee_id)
            if not has_permission:
                return BotResponse(
                    success=False,
                    message="You don't have permission to access this employee record.",
                    action_taken="access_denied",
                    confidence_score=0.9
                )
            
            # Retrieve employee record
            employee = await self.db_manager.get_employee(employee_id)
            if not employee:
                return BotResponse(
                    success=False,
                    message="Employee record not found.",
                    confidence_score=0.8
                )
            
            # Filter sensitive information based on permission level
            filtered_record = await self._filter_employee_data(employee, requester_id)
            
            return BotResponse(
                success=True,
                message=f"Retrieved employee record for {employee.get('name', 'Unknown')}",
                data={
                    "employee_record": filtered_record,
                    "access_level": await self._get_access_level(requester_id)
                },
                action_taken="employee_record_retrieved",
                next_steps=["Review information", "Update if needed", "Generate reports"],
                confidence_score=0.95
            )
            
        except Exception as e:
            self.logger.error(f"Error handling employee record: {str(e)}")
            return BotResponse(
                success=False,
                message="Failed to retrieve employee record. Please try again.",
                confidence_score=0.3
            )
    
    async def _handle_leave_management(self, request: str, context: Dict[str, Any]) -> BotResponse:
        """Handle leave and time-off requests"""
        try:
            employee_id = context.get('employee_id')
            leave_type = await self._extract_leave_type(request)
            
            if "request" in request.lower() or "apply" in request.lower():
                # Handle leave request
                leave_details = await self._extract_leave_details(request)
                leave_request_id = await self._create_leave_request(employee_id, leave_details)
                
                return BotResponse(
                    success=True,
                    message=f"Leave request submitted successfully. Request ID: {leave_request_id}",
                    data={
                        "request_id": leave_request_id,
                        "leave_details": leave_details,
                        "status": "pending"
                    },
                    action_taken="leave_request_submitted",
                    next_steps=["Wait for approval", "Check request status", "Contact manager"],
                    confidence_score=0.9
                )
            
            elif "balance" in request.lower() or "remaining" in request.lower():
                # Handle leave balance inquiry
                leave_balance = await self._get_leave_balance(employee_id, leave_type)
                
                return BotResponse(
                    success=True,
                    message=f"Your {leave_type} balance: {leave_balance['remaining']} days remaining out of {leave_balance['total']} total days",
                    data=leave_balance,
                    action_taken="leave_balance_provided",
                    confidence_score=0.95
                )
            
            else:
                # General leave policy information
                leave_policy = await self.policy_engine.get_leave_policy(leave_type)
                
                return BotResponse(
                    success=True,
                    message=f"Here's information about {leave_type} policy: {leave_policy}",
                    data={"policy": leave_policy},
                    action_taken="leave_policy_provided",
                    confidence_score=0.8
                )
                
        except Exception as e:
            self.logger.error(f"Error handling leave management: {str(e)}")
            return BotResponse(
                success=False,
                message="Failed to process leave request. Please try again.",
                confidence_score=0.3
            )
    
    async def _handle_benefits_inquiry(self, request: str, context: Dict[str, Any]) -> BotResponse:
        """Handle employee benefits inquiries"""
        try:
            employee_id = context.get('employee_id')
            benefit_type = await self._extract_benefit_type(request)
            
            # Get employee's current benefits
            benefits_info = await self.db_manager.get_employee_benefits(employee_id)
            
            if benefit_type:
                # Specific benefit inquiry
                specific_benefit = benefits_info.get(benefit_type, {})
                response_message = await self._generate_benefit_response(benefit_type, specific_benefit)
            else:
                # General benefits overview
                response_message = await self._generate_benefits_overview(benefits_info)
            
            return BotResponse(
                success=True,
                message=response_message,
                data={
                    "benefits_info": benefits_info,
                    "benefit_type": benefit_type
                },
                action_taken="benefits_information_provided",
                next_steps=["Review benefits portal", "Contact benefits team", "Make changes during open enrollment"],
                confidence_score=0.85
            )
            
        except Exception as e:
            self.logger.error(f"Error handling benefits inquiry: {str(e)}")
            return BotResponse(
                success=False,
                message="Failed to retrieve benefits information. Please try again.",
                confidence_score=0.3
            )
    
    async def _handle_directory_search(self, request: str, context: Dict[str, Any]) -> BotResponse:
        """Handle employee directory searches"""
        try:
            search_term = await self._extract_search_term(request)
            
            if not search_term:
                return BotResponse(
                    success=False,
                    message="Please specify who you're looking for (name, department, or role).",
                    next_steps=["Provide name", "Specify department", "Mention job title"],
                    confidence_score=0.3
                )
            
            # Search employee directory
            search_results = await self.db_manager.search_employees(search_term)
            
            if not search_results:
                return BotResponse(
                    success=False,
                    message=f"No employees found matching '{search_term}'.",
                    next_steps=["Try different search terms", "Check spelling", "Use partial names"],
                    confidence_score=0.7
                )
            
            # Format search results
            formatted_results = await self._format_directory_results(search_results)
            
            return BotResponse(
                success=True,
                message=f"Found {len(search_results)} employees matching '{search_term}':",
                data={
                    "search_term": search_term,
                    "results": formatted_results,
                    "count": len(search_results)
                },
                action_taken="directory_search_completed",
                next_steps=["Contact employee", "View full profile", "Save contact"],
                confidence_score=0.9
            )
            
        except Exception as e:
            self.logger.error(f"Error handling directory search: {str(e)}")
            return BotResponse(
                success=False,
                message="Failed to search employee directory. Please try again.",
                confidence_score=0.3
            )
    
    async def _handle_document_request(self, request: str, context: Dict[str, Any]) -> BotResponse:
        """Handle document and form requests"""
        try:
            document_type = await self._extract_document_type(request)
            employee_id = context.get('employee_id')
            
            if not document_type:
                available_docs = await self.document_processor.get_available_documents()
                return BotResponse(
                    success=True,
                    message="Here are the available documents you can request:",
                    data={"available_documents": available_docs},
                    next_steps=["Specify document type", "Download from portal", "Contact HR"],
                    confidence_score=0.8
                )
            
            # Generate or retrieve document
            document_info = await self.document_processor.process_document_request(
                document_type, employee_id
            )
            
            return BotResponse(
                success=True,
                message=f"Your {document_type} is ready for download.",
                data=document_info,
                action_taken="document_generated",
                next_steps=["Download document", "Print if needed", "Submit to relevant parties"],
                confidence_score=0.9
            )
            
        except Exception as e:
            self.logger.error(f"Error handling document request: {str(e)}")
            return BotResponse(
                success=False,
                message="Failed to process document request. Please try again.",
                confidence_score=0.3
            )
    
    async def _handle_employee_update(self, request: str, context: Dict[str, Any]) -> BotResponse:
        """Handle employee information updates"""
        try:
            employee_id = context.get('employee_id')
            update_data = await self._extract_update_data(request)
            
            if not update_data:
                return BotResponse(
                    success=False,
                    message="Please specify what information you'd like to update.",
                    next_steps=["Specify field to update", "Provide new information", "Use employee portal"],
                    confidence_score=0.3
                )
            
            # Validate update permissions
            can_update = await self._validate_update_permissions(employee_id, update_data)
            if not can_update:
                return BotResponse(
                    success=False,
                    message="You don't have permission to update this information. Please contact HR.",
                    action_taken="update_permission_denied",
                    confidence_score=0.9
                )
            
            # Apply updates
            update_result = await self.db_manager.update_employee(employee_id, update_data)
            
            return BotResponse(
                success=True,
                message="Employee information updated successfully.",
                data={
                    "updated_fields": list(update_data.keys()),
                    "update_timestamp": datetime.utcnow().isoformat()
                },
                action_taken="employee_record_updated",
                next_steps=["Verify changes", "Notify relevant parties", "Update systems"],
                confidence_score=0.9
            )
            
        except Exception as e:
            self.logger.error(f"Error handling employee update: {str(e)}")
            return BotResponse(
                success=False,
                message="Failed to update employee information. Please try again.",
                confidence_score=0.3
            )
    
    async def _handle_general_inquiry(self, request: str, context: Dict[str, Any]) -> BotResponse:
        """Handle general HR inquiries"""
        response_text = await self._generate_hr_response(request, context)
        
        return BotResponse(
            success=True,
            message=response_text,
            action_taken="information_provided",
            confidence_score=0.7
        )
    
    # Helper methods
    async def _extract_policy_topic(self, request: str) -> str:
        """Extract policy topic from request"""
        prompt = f"""
        Extract the main HR policy topic from this request:
        "{request}"
        
        Common topics: vacation, sick leave, dress code, remote work, harassment, performance, benefits, overtime, etc.
        Return only the topic name.
        """
        
        try:
            response = self.ai_client.get_completion(prompt)
            return response.strip().lower()
        except:
            return "general"
    
    async def _generate_policy_response(self, policies: List[Dict], request: str) -> str:
        """Generate comprehensive policy response"""
        prompt = f"""
        Based on these HR policies, answer the user's question:
        
        Question: "{request}"
        Policies: {json.dumps(policies)}
        
        Provide a clear, helpful response that directly addresses their question.
        Include relevant policy details and next steps if applicable.
        """
        
        return self.ai_client.get_completion(prompt)
    
    async def _check_record_permissions(self, requester_id: str, employee_id: str) -> bool:
        """Check if requester has permission to access employee record"""
        # Implementation would check role-based permissions
        requester_role = await self.db_manager.get_employee_role(requester_id)
        
        # Allow self-access or manager/HR access
        if requester_id == employee_id:
            return True
        elif requester_role in ['hr', 'manager', 'admin']:
            return True
        
        return False
    
    async def _filter_employee_data(self, employee: Dict, requester_id: str) -> Dict:
        """Filter employee data based on requester permissions"""
        access_level = await self._get_access_level(requester_id)
        
        if access_level == 'full':
            return employee
        elif access_level == 'limited':
            # Return only basic information
            return {
                'name': employee.get('name'),
                'department': employee.get('department'),
                'title': employee.get('title'),
                'email': employee.get('email'),
                'phone': employee.get('phone')
            }
        else:
            # Return minimal information
            return {
                'name': employee.get('name'),
                'department': employee.get('department'),
                'title': employee.get('title')
            }
    
    async def _get_access_level(self, requester_id: str) -> str:
        """Determine access level for requester"""
        role = await self.db_manager.get_employee_role(requester_id)
        
        if role in ['hr', 'admin']:
            return 'full'
        elif role in ['manager', 'supervisor']:
            return 'limited'
        else:
            return 'basic'
    
    async def _extract_leave_type(self, request: str) -> str:
        """Extract leave type from request"""
        leave_types = ['vacation', 'sick', 'personal', 'maternity', 'paternity', 'bereavement', 'jury']
        request_lower = request.lower()
        
        for leave_type in leave_types:
            if leave_type in request_lower:
                return leave_type
        
        return 'general'
    
    async def _extract_leave_details(self, request: str) -> Dict[str, Any]:
        """Extract leave request details"""
        prompt = f"""
        Extract leave request details from:
        "{request}"
        
        Return JSON with:
        - start_date: YYYY-MM-DD
        - end_date: YYYY-MM-DD
        - leave_type: vacation/sick/personal/etc
        - reason: brief reason
        - partial_days: true/false
        
        Return only valid JSON.
        """
        
        try:
            response = self.ai_client.get_completion(prompt)
            return json.loads(response)
        except:
            return {}
    
    async def _create_leave_request(self, employee_id: str, leave_details: Dict[str, Any]) -> str:
        """Create leave request in database"""
        leave_data = {
            'employee_id': employee_id,
            'status': 'pending',
            'created_at': datetime.utcnow(),
            **leave_details
        }
        
        return await self.db_manager.create_leave_request(leave_data)
    
    async def _get_leave_balance(self, employee_id: str, leave_type: str) -> Dict[str, Any]:
        """Get employee's leave balance"""
        return await self.db_manager.get_leave_balance(employee_id, leave_type)
    
    async def _extract_benefit_type(self, request: str) -> Optional[str]:
        """Extract benefit type from request"""
        benefit_types = ['health', 'dental', 'vision', '401k', 'retirement', 'life insurance', 'disability']
        request_lower = request.lower()
        
        for benefit_type in benefit_types:
            if benefit_type in request_lower:
                return benefit_type
        
        return None
    
    async def _generate_benefit_response(self, benefit_type: str, benefit_info: Dict) -> str:
        """Generate response for specific benefit inquiry"""
        prompt = f"""
        Explain this employee benefit:
        
        Benefit Type: {benefit_type}
        Benefit Details: {json.dumps(benefit_info)}
        
        Provide a clear, helpful explanation of coverage, costs, and how to use it.
        """
        
        return self.ai_client.get_completion(prompt)
    
    async def _generate_benefits_overview(self, benefits_info: Dict) -> str:
        """Generate overview of all employee benefits"""
        prompt = f"""
        Provide a comprehensive overview of these employee benefits:
        {json.dumps(benefits_info)}
        
        Summarize key benefits and their value to the employee.
        """
        
        return self.ai_client.get_completion(prompt)
    
    async def _extract_search_term(self, request: str) -> str:
        """Extract search term from directory request"""
        prompt = f"""
        Extract the search term from this employee directory request:
        "{request}"
        
        Return the name, department, or role being searched for.
        Return only the search term.
        """
        
        try:
            response = self.ai_client.get_completion(prompt)
            return response.strip()
        except:
            return ""
    
    async def _format_directory_results(self, results: List[Dict]) -> List[Dict]:
        """Format directory search results for display"""
        formatted = []
        for employee in results:
            formatted.append({
                'name': employee.get('name'),
                'title': employee.get('title'),
                'department': employee.get('department'),
                'email': employee.get('email'),
                'phone': employee.get('phone'),
                'location': employee.get('location')
            })
        return formatted
    
    async def _extract_document_type(self, request: str) -> Optional[str]:
        """Extract document type from request"""
        document_types = [
            'w2', 'paystub', 'employment verification', 'benefits summary',
            'tax form', 'offer letter', 'performance review'
        ]
        request_lower = request.lower()
        
        for doc_type in document_types:
            if doc_type in request_lower:
                return doc_type
        
        return None
    
    async def _extract_update_data(self, request: str) -> Dict[str, Any]:
        """Extract update data from request"""
        prompt = f"""
        Extract employee update information from:
        "{request}"
        
        Return JSON with fields to update and their new values.
        Common fields: address, phone, emergency_contact, direct_deposit, etc.
        
        Return only valid JSON.
        """
        
        try:
            response = self.ai_client.get_completion(prompt)
            return json.loads(response)
        except:
            return {}
    
    async def _validate_update_permissions(self, employee_id: str, update_data: Dict) -> bool:
        """Validate if employee can update the specified fields"""
        restricted_fields = ['salary', 'title', 'department', 'manager_id', 'hire_date']
        
        for field in update_data.keys():
            if field in restricted_fields:
                return False
        
        return True
    
    async def _generate_hr_response(self, request: str, context: Dict[str, Any]) -> str:
        """Generate response for general HR inquiries"""
        prompt = f"""
        As an HR assistant, respond to this inquiry:
        "{request}"
        
        Context: {json.dumps(context)}
        
        Provide helpful, professional guidance about HR matters.
        """
        
        return self.ai_client.get_completion(prompt)