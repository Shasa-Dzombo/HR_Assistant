"""
Email Service - Handles email notifications and communications
"""

import smtplib
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from typing import Dict, List, Any, Optional
import logging
from jinja2 import Environment, FileSystemLoader
from datetime import datetime

from ..config.settings import get_settings


class EmailService:
    """
    Email service for sending notifications, welcome emails, and other communications
    Supports both SMTP and SendGrid
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        
        # Initialize email templates
        template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates', 'email')
        if os.path.exists(template_dir):
            self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
        else:
            self.jinja_env = None
        
        # SendGrid client
        if self.settings.SENDGRID_API_KEY:
            self.sendgrid_client = sendgrid.SendGridAPIClient(api_key=self.settings.SENDGRID_API_KEY)
        else:
            self.sendgrid_client = None
        
        # Email configuration
        self.from_email = self.settings.EMAIL_USERNAME or "hr@company.com"
        self.company_name = self.settings.COMPANY_NAME or "Your Company"
    
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        template: Optional[str] = None,
        template_data: Optional[Dict[str, Any]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """
        Send email using preferred method (SendGrid or SMTP)
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (if not using template)
            template: Template name to use
            template_data: Data for template rendering
            attachments: List of file attachments
            cc: CC recipients
            bcc: BCC recipients
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            # Render template if specified
            if template and self.jinja_env:
                body = self._render_template(template, template_data or {})
            
            # Try SendGrid first, fall back to SMTP
            if self.sendgrid_client:
                return await self._send_via_sendgrid(
                    to, subject, body, attachments, cc, bcc
                )
            else:
                return await self._send_via_smtp(
                    to, subject, body, attachments, cc, bcc
                )
                
        except Exception as e:
            self.logger.error(f"Failed to send email to {to}: {str(e)}")
            return False
    
    async def _send_via_sendgrid(
        self,
        to: str,
        subject: str,
        body: str,
        attachments: Optional[List[Dict[str, Any]]] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """Send email via SendGrid"""
        try:
            from_email = Email(self.from_email, self.company_name)
            to_email = To(to)
            content = Content("text/html", body)
            
            mail = Mail(from_email, to_email, subject, content)
            
            # Add CC recipients
            if cc:
                for cc_email in cc:
                    mail.add_cc(cc_email)
            
            # Add BCC recipients
            if bcc:
                for bcc_email in bcc:
                    mail.add_bcc(bcc_email)
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    mail.add_attachment(self._create_sendgrid_attachment(attachment))
            
            response = self.sendgrid_client.send(mail)
            
            if response.status_code in [200, 202]:
                self.logger.info(f"Email sent successfully to {to}")
                return True
            else:
                self.logger.error(f"SendGrid error: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"SendGrid send failed: {str(e)}")
            return False
    
    async def _send_via_smtp(
        self,
        to: str,
        subject: str,
        body: str,
        attachments: Optional[List[Dict[str, Any]]] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """Send email via SMTP"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to
            msg['Subject'] = subject
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            
            # Add body
            msg.attach(MIMEText(body, 'html'))
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    part = self._create_smtp_attachment(attachment)
                    msg.attach(part)
            
            # Create SMTP connection
            server = smtplib.SMTP(self.settings.SMTP_SERVER, self.settings.SMTP_PORT)
            server.starttls()
            server.login(self.settings.EMAIL_USERNAME, self.settings.EMAIL_PASSWORD)
            
            # Send email
            recipients = [to]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)
            
            server.sendmail(self.from_email, recipients, msg.as_string())
            server.quit()
            
            self.logger.info(f"Email sent successfully to {to} via SMTP")
            return True
            
        except Exception as e:
            self.logger.error(f"SMTP send failed: {str(e)}")
            return False
    
    def _render_template(self, template_name: str, data: Dict[str, Any]) -> str:
        """Render email template with data"""
        try:
            template = self.jinja_env.get_template(f"{template_name}.html")
            
            # Add common template variables
            data.update({
                'company_name': self.company_name,
                'current_date': datetime.now().strftime('%B %d, %Y'),
                'company_website': self.settings.COMPANY_WEBSITE or '#'
            })
            
            return template.render(**data)
            
        except Exception as e:
            self.logger.error(f"Template rendering failed: {str(e)}")
            return f"<html><body><p>Email content unavailable</p></body></html>"
    
    def _create_sendgrid_attachment(self, attachment: Dict[str, Any]):
        """Create SendGrid attachment object"""
        from sendgrid.helpers.mail import Attachment
        
        attachment_obj = Attachment()
        attachment_obj.file_content = attachment.get('content')
        attachment_obj.file_type = attachment.get('type', 'application/octet-stream')
        attachment_obj.file_name = attachment.get('filename')
        attachment_obj.disposition = 'attachment'
        
        return attachment_obj
    
    def _create_smtp_attachment(self, attachment: Dict[str, Any]):
        """Create SMTP attachment object"""
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.get('content'))
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f"attachment; filename= {attachment.get('filename')}"
        )
        
        return part
    
    # Pre-defined email templates
    async def send_welcome_email(
        self, 
        employee_email: str, 
        employee_name: str, 
        start_date: str,
        additional_info: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send welcome email to new employee"""
        template_data = {
            'employee_name': employee_name,
            'start_date': start_date,
            'hr_email': self.from_email,
            **(additional_info or {})
        }
        
        return await self.send_email(
            to=employee_email,
            subject=f"Welcome to {self.company_name}!",
            body="",  # Will be populated by template
            template="welcome_email",
            template_data=template_data
        )
    
    async def send_interview_notification(
        self,
        candidate_email: str,
        candidate_name: str,
        interview_details: Dict[str, Any]
    ) -> bool:
        """Send interview notification to candidate"""
        template_data = {
            'candidate_name': candidate_name,
            'interview_date': interview_details.get('date'),
            'interview_time': interview_details.get('time'),
            'interview_location': interview_details.get('location'),
            'interviewer_name': interview_details.get('interviewer_name'),
            'position': interview_details.get('position'),
            'contact_email': self.from_email
        }
        
        return await self.send_email(
            to=candidate_email,
            subject=f"Interview Scheduled - {interview_details.get('position')}",
            body="",
            template="interview_notification",
            template_data=template_data
        )
    
    async def send_leave_approval_notification(
        self,
        employee_email: str,
        employee_name: str,
        leave_details: Dict[str, Any],
        approved: bool = True
    ) -> bool:
        """Send leave request approval/denial notification"""
        status = "approved" if approved else "denied"
        template_data = {
            'employee_name': employee_name,
            'leave_type': leave_details.get('leave_type'),
            'start_date': leave_details.get('start_date'),
            'end_date': leave_details.get('end_date'),
            'status': status,
            'reason': leave_details.get('reason', ''),
            'manager_comments': leave_details.get('manager_comments', ''),
            'hr_email': self.from_email
        }
        
        return await self.send_email(
            to=employee_email,
            subject=f"Leave Request {status.title()}",
            body="",
            template="leave_notification",
            template_data=template_data
        )
    
    async def send_performance_review_reminder(
        self,
        reviewer_email: str,
        reviewer_name: str,
        employee_name: str,
        due_date: str
    ) -> bool:
        """Send performance review reminder"""
        template_data = {
            'reviewer_name': reviewer_name,
            'employee_name': employee_name,
            'due_date': due_date,
            'hr_email': self.from_email
        }
        
        return await self.send_email(
            to=reviewer_email,
            subject=f"Performance Review Due - {employee_name}",
            body="",
            template="review_reminder",
            template_data=template_data
        )
    
    async def send_onboarding_checklist(
        self,
        new_hire_email: str,
        new_hire_name: str,
        checklist_items: List[Dict[str, Any]],
        start_date: str
    ) -> bool:
        """Send onboarding checklist to new hire"""
        template_data = {
            'new_hire_name': new_hire_name,
            'start_date': start_date,
            'checklist_items': checklist_items,
            'hr_email': self.from_email
        }
        
        return await self.send_email(
            to=new_hire_email,
            subject=f"Welcome to {self.company_name} - Onboarding Checklist",
            body="",
            template="onboarding_checklist",
            template_data=template_data
        )
    
    async def send_system_notification(
        self,
        admin_emails: List[str],
        subject: str,
        message: str,
        severity: str = "info"
    ) -> bool:
        """Send system notification to administrators"""
        template_data = {
            'message': message,
            'severity': severity,
            'timestamp': datetime.now().isoformat(),
            'system_name': 'HR Assistant'
        }
        
        success_count = 0
        for admin_email in admin_emails:
            if await self.send_email(
                to=admin_email,
                subject=f"[HR Assistant] {subject}",
                body="",
                template="system_notification",
                template_data=template_data
            ):
                success_count += 1
        
        return success_count > 0
    
    async def send_bulk_notification(
        self,
        recipients: List[str],
        subject: str,
        body: str,
        template: Optional[str] = None,
        template_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send bulk notification to multiple recipients"""
        results = {
            'total_sent': 0,
            'failed_recipients': [],
            'successful_recipients': []
        }
        
        for recipient in recipients:
            success = await self.send_email(
                to=recipient,
                subject=subject,
                body=body,
                template=template,
                template_data=template_data
            )
            
            if success:
                results['total_sent'] += 1
                results['successful_recipients'].append(recipient)
            else:
                results['failed_recipients'].append(recipient)
        
        return results
    
    def create_email_signature(self) -> str:
        """Create standard email signature"""
        return f"""
        <br><br>
        <div style="border-top: 1px solid #ccc; padding-top: 10px; margin-top: 20px;">
            <p style="font-size: 12px; color: #666;">
                <strong>HR Team</strong><br>
                {self.company_name}<br>
                Email: {self.from_email}<br>
                {self.settings.COMPANY_WEBSITE or ''}
            </p>
        </div>
        """
    
    async def test_email_configuration(self) -> Dict[str, Any]:
        """Test email configuration"""
        test_results = {
            'sendgrid_available': bool(self.sendgrid_client),
            'smtp_configured': all([
                self.settings.SMTP_SERVER,
                self.settings.EMAIL_USERNAME,
                self.settings.EMAIL_PASSWORD
            ]),
            'templates_available': bool(self.jinja_env),
            'test_send_success': False
        }
        
        # Try sending a test email
        try:
            test_success = await self.send_email(
                to=self.from_email,
                subject="HR Assistant - Email Test",
                body="<p>This is a test email from HR Assistant system.</p>"
            )
            test_results['test_send_success'] = test_success
        except Exception as e:
            test_results['test_error'] = str(e)
        
        return test_results