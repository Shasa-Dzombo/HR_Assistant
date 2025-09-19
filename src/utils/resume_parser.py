"""
Resume Parser - Extracts information from resume documents
"""

import os
import re
import spacy
from typing import Dict, List, Any, Optional
import PyPDF2
from docx import Document
from datetime import datetime
import logging
import json

from ..config.settings import get_settings


class ResumeParser:
    """
    Parser for extracting structured information from resume documents
    Supports PDF, DOCX, and text formats
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        
        # Load spaCy model for NLP
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            self.logger.warning("spaCy model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None
        
        # Common sections in resumes
        self.section_patterns = {
            'experience': r'(experience|work history|employment|professional experience)',
            'education': r'(education|academic|qualifications|degree)',
            'skills': r'(skills|technical skills|competencies|technologies)',
            'contact': r'(contact|personal info|details)',
            'summary': r'(summary|objective|profile|about)'
        }
        
        # Skill categories and keywords
        self.skill_categories = {
            'programming': [
                'python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'go',
                'react', 'angular', 'vue', 'node.js', 'django', 'flask', 'spring'
            ],
            'databases': [
                'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'oracle',
                'sqlite', 'nosql', 'elasticsearch'
            ],
            'cloud': [
                'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform',
                'jenkins', 'git', 'devops'
            ],
            'data_science': [
                'machine learning', 'deep learning', 'tensorflow', 'pytorch',
                'pandas', 'numpy', 'sklearn', 'data analysis', 'statistics'
            ],
            'soft_skills': [
                'leadership', 'communication', 'teamwork', 'problem solving',
                'project management', 'analytical thinking', 'creativity'
            ]
        }
    
    async def parse_resume(self, file_path: str) -> Dict[str, Any]:
        """
        Parse resume and extract structured information
        
        Args:
            file_path: Path to resume file
            
        Returns:
            Dict with extracted resume information
        """
        try:
            # Extract text from file
            text = await self._extract_text_from_file(file_path)
            
            if not text:
                return {'error': 'Could not extract text from file'}
            
            # Parse different sections
            parsed_data = {
                'raw_text': text,
                'contact_info': self._extract_contact_info(text),
                'summary': self._extract_summary(text),
                'experience': self._extract_experience(text),
                'education': self._extract_education(text),
                'skills': self._extract_skills(text),
                'languages': self._extract_languages(text),
                'certifications': self._extract_certifications(text),
                'achievements': self._extract_achievements(text),
                'parsed_at': datetime.utcnow().isoformat()
            }
            
            # Extract basic info for easy access
            contact = parsed_data['contact_info']
            parsed_data.update({
                'name': contact.get('name'),
                'email': contact.get('email'),
                'phone': contact.get('phone'),
                'location': contact.get('location')
            })
            
            # Calculate experience level
            parsed_data['experience_level'] = self._calculate_experience_level(
                parsed_data['experience']
            )
            
            # Score the resume
            parsed_data['resume_score'] = self._calculate_resume_score(parsed_data)
            
            return parsed_data
            
        except Exception as e:
            self.logger.error(f"Resume parsing failed: {str(e)}")
            return {'error': f'Parsing failed: {str(e)}'}
    
    async def _extract_text_from_file(self, file_path: str) -> str:
        """Extract text content from various file formats"""
        file_extension = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_extension == '.pdf':
                return self._extract_from_pdf(file_path)
            elif file_extension in ['.docx', '.doc']:
                return self._extract_from_docx(file_path)
            elif file_extension == '.txt':
                with open(file_path, 'r', encoding='utf-8') as file:
                    return file.read()
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
                
        except Exception as e:
            self.logger.error(f"Text extraction failed: {str(e)}")
            return ""
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            self.logger.error(f"PDF extraction failed: {str(e)}")
        
        return text
    
    def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            doc = Document(file_path)
            text = []
            for paragraph in doc.paragraphs:
                text.append(paragraph.text)
            return "\n".join(text)
        except Exception as e:
            self.logger.error(f"DOCX extraction failed: {str(e)}")
            return ""
    
    def _extract_contact_info(self, text: str) -> Dict[str, Any]:
        """Extract contact information"""
        contact_info = {}
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            contact_info['email'] = emails[0]
        
        # Extract phone numbers
        phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phones = re.findall(phone_pattern, text)
        if phones:
            contact_info['phone'] = ''.join(phones[0]) if isinstance(phones[0], tuple) else phones[0]
        
        # Extract name (usually in first few lines)
        lines = text.split('\n')[:5]
        for line in lines:
            line = line.strip()
            if line and not re.search(r'@|phone|email|address', line.lower()):
                # Check if line looks like a name
                words = line.split()
                if 2 <= len(words) <= 4 and all(word.isalpha() or word.endswith('.') for word in words):
                    contact_info['name'] = line
                    break
        
        # Extract location/address
        location_patterns = [
            r'([A-Za-z\s]+,\s*[A-Za-z]{2}(?:\s+\d{5})?)',  # City, State ZIP
            r'([A-Za-z\s]+,\s*[A-Za-z\s]+)'  # City, Country
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, text)
            if matches:
                contact_info['location'] = matches[0]
                break
        
        return contact_info
    
    def _extract_summary(self, text: str) -> str:
        """Extract professional summary or objective"""
        summary_section = self._find_section(text, 'summary')
        if summary_section:
            # Get first paragraph after summary header
            lines = summary_section.split('\n')
            summary_lines = []
            for line in lines[1:]:  # Skip header
                line = line.strip()
                if line and not self._is_section_header(line):
                    summary_lines.append(line)
                elif summary_lines:  # Stop at next section
                    break
            
            return ' '.join(summary_lines)
        
        return ""
    
    def _extract_experience(self, text: str) -> List[Dict[str, Any]]:
        """Extract work experience"""
        experience_section = self._find_section(text, 'experience')
        experiences = []
        
        if not experience_section:
            return experiences
        
        # Split into potential job entries
        lines = experience_section.split('\n')
        current_job = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line is a job title/company
            if self._looks_like_job_title(line):
                if current_job:
                    experiences.append(current_job)
                
                current_job = {'raw_text': line}
                
                # Try to parse job title and company
                job_info = self._parse_job_line(line)
                current_job.update(job_info)
            
            elif current_job and not self._is_section_header(line):
                # Add to job description
                if 'description' not in current_job:
                    current_job['description'] = []
                current_job['description'].append(line)
        
        # Add last job
        if current_job:
            experiences.append(current_job)
        
        # Clean up descriptions
        for exp in experiences:
            if 'description' in exp:
                exp['description'] = ' '.join(exp['description'])
        
        return experiences
    
    def _extract_education(self, text: str) -> List[Dict[str, Any]]:
        """Extract education information"""
        education_section = self._find_section(text, 'education')
        education = []
        
        if not education_section:
            return education
        
        lines = education_section.split('\n')
        current_edu = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for degree/institution
            if self._looks_like_education_entry(line):
                if current_edu:
                    education.append(current_edu)
                
                current_edu = {'raw_text': line}
                edu_info = self._parse_education_line(line)
                current_edu.update(edu_info)
            
            elif current_edu and not self._is_section_header(line):
                # Additional education details
                if 'details' not in current_edu:
                    current_edu['details'] = []
                current_edu['details'].append(line)
        
        if current_edu:
            education.append(current_edu)
        
        return education
    
    def _extract_skills(self, text: str) -> Dict[str, List[str]]:
        """Extract skills organized by category"""
        skills_section = self._find_section(text, 'skills')
        skills = {category: [] for category in self.skill_categories}
        
        # Search in skills section first
        search_text = skills_section if skills_section else text
        search_text_lower = search_text.lower()
        
        # Find skills by category
        for category, keywords in self.skill_categories.items():
            for keyword in keywords:
                if keyword.lower() in search_text_lower:
                    skills[category].append(keyword)
        
        # Remove empty categories
        skills = {k: v for k, v in skills.items() if v}
        
        # Also extract any explicitly listed skills
        if skills_section:
            explicit_skills = self._extract_explicit_skills(skills_section)
            if explicit_skills:
                skills['other'] = explicit_skills
        
        return skills
    
    def _extract_languages(self, text: str) -> List[str]:
        """Extract language skills"""
        languages = []
        
        # Common language indicators
        language_patterns = [
            r'languages?:?\s*([^\n]+)',
            r'fluent in:?\s*([^\n]+)',
            r'bilingual:?\s*([^\n]+)'
        ]
        
        for pattern in language_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Parse language list
                langs = re.split(r'[,;]', match)
                for lang in langs:
                    lang = lang.strip()
                    if lang and len(lang.split()) <= 3:  # Reasonable language name
                        languages.append(lang)
        
        # Remove duplicates
        return list(set(languages))
    
    def _extract_certifications(self, text: str) -> List[str]:
        """Extract certifications"""
        certifications = []
        
        # Look for certification keywords
        cert_patterns = [
            r'certified?\s+([^\n,]+)',
            r'certification:?\s*([^\n]+)',
            r'(AWS|Microsoft|Google|Oracle|Cisco|CompTIA)\s+\w+',
            r'([A-Z]{2,}\s+certified)'
        ]
        
        for pattern in cert_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = ' '.join(match)
                cert = match.strip()
                if cert and len(cert.split()) <= 6:
                    certifications.append(cert)
        
        return list(set(certifications))
    
    def _extract_achievements(self, text: str) -> List[str]:
        """Extract achievements and accomplishments"""
        achievements = []
        
        # Look for bullet points with achievement indicators
        achievement_indicators = [
            'achieved', 'improved', 'increased', 'reduced', 'led', 'managed',
            'developed', 'created', 'implemented', 'delivered', 'awarded'
        ]
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            # Look for bullet points or numbered items
            if re.match(r'^[•\-\*\d\.]', line):
                line_lower = line.lower()
                if any(indicator in line_lower for indicator in achievement_indicators):
                    achievements.append(line)
        
        return achievements[:10]  # Limit to top 10
    
    def _find_section(self, text: str, section_type: str) -> Optional[str]:
        """Find a specific section in the resume"""
        pattern = self.section_patterns.get(section_type, section_type)
        
        # Find section header
        lines = text.split('\n')
        section_start = -1
        section_end = len(lines)
        
        for i, line in enumerate(lines):
            if re.search(pattern, line, re.IGNORECASE) and self._is_section_header(line):
                section_start = i
                break
        
        if section_start == -1:
            return None
        
        # Find next section header
        for i in range(section_start + 1, len(lines)):
            if self._is_section_header(lines[i]) and not re.search(pattern, lines[i], re.IGNORECASE):
                section_end = i
                break
        
        return '\n'.join(lines[section_start:section_end])
    
    def _is_section_header(self, line: str) -> bool:
        """Check if line is a section header"""
        line = line.strip()
        if not line:
            return False
        
        # Common section header patterns
        header_indicators = [
            line.isupper(),  # ALL CAPS
            len(line.split()) <= 3,  # Short phrases
            line.endswith(':'),  # Colon ending
            re.match(r'^[A-Z][a-z]+(\s+[A-Z][a-z]+)*$', line)  # Title Case
        ]
        
        return any(header_indicators) and any(
            pattern in line.lower() 
            for pattern in self.section_patterns.values()
        )
    
    def _looks_like_job_title(self, line: str) -> bool:
        """Check if line looks like a job title/company"""
        # Look for common job title patterns
        job_indicators = [
            'manager', 'developer', 'engineer', 'analyst', 'director',
            'specialist', 'coordinator', 'assistant', 'lead', 'senior'
        ]
        
        return any(indicator in line.lower() for indicator in job_indicators)
    
    def _looks_like_education_entry(self, line: str) -> bool:
        """Check if line looks like an education entry"""
        edu_indicators = [
            'bachelor', 'master', 'phd', 'doctorate', 'degree', 'university',
            'college', 'institute', 'school', 'b.s.', 'm.s.', 'b.a.', 'm.a.'
        ]
        
        return any(indicator in line.lower() for indicator in edu_indicators)
    
    def _parse_job_line(self, line: str) -> Dict[str, Any]:
        """Parse job title and company from line"""
        job_info = {}
        
        # Try to separate title and company
        if ' at ' in line:
            parts = line.split(' at ', 1)
            job_info['title'] = parts[0].strip()
            job_info['company'] = parts[1].strip()
        elif ' - ' in line:
            parts = line.split(' - ', 1)
            job_info['title'] = parts[0].strip()
            job_info['company'] = parts[1].strip()
        else:
            job_info['title'] = line.strip()
        
        # Try to extract dates
        date_pattern = r'(\d{4})\s*[-–]\s*(\d{4}|present)'
        dates = re.findall(date_pattern, line, re.IGNORECASE)
        if dates:
            start_year, end_year = dates[0]
            job_info['start_year'] = start_year
            job_info['end_year'] = end_year if end_year.lower() != 'present' else 'present'
        
        return job_info
    
    def _parse_education_line(self, line: str) -> Dict[str, Any]:
        """Parse education degree and institution"""
        edu_info = {}
        
        # Look for degree type
        degree_patterns = [
            r'(bachelor|b\.?[as]\.?)\s+(?:of\s+)?([^\n,]+)',
            r'(master|m\.?[as]\.?)\s+(?:of\s+)?([^\n,]+)',
            r'(phd|ph\.d\.?|doctorate)\s+(?:in\s+)?([^\n,]+)'
        ]
        
        for pattern in degree_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                edu_info['degree_type'] = match.group(1)
                edu_info['field'] = match.group(2).strip()
                break
        
        # Look for institution
        if ' from ' in line:
            parts = line.split(' from ', 1)
            edu_info['institution'] = parts[1].strip()
        elif ',' in line:
            parts = line.split(',')
            if len(parts) >= 2:
                edu_info['institution'] = parts[1].strip()
        
        # Look for graduation year
        year_pattern = r'(\d{4})'
        years = re.findall(year_pattern, line)
        if years:
            edu_info['graduation_year'] = years[-1]  # Take last year found
        
        return edu_info
    
    def _extract_explicit_skills(self, skills_section: str) -> List[str]:
        """Extract explicitly listed skills from skills section"""
        skills = []
        
        # Look for comma-separated or bullet-pointed skills
        lines = skills_section.split('\n')
        for line in lines[1:]:  # Skip header
            line = line.strip()
            if line and not self._is_section_header(line):
                # Split by common separators
                skill_items = re.split(r'[,;•\-\*]', line)
                for item in skill_items:
                    skill = item.strip()
                    if skill and len(skill.split()) <= 3:  # Reasonable skill name
                        skills.append(skill)
        
        return skills
    
    def _calculate_experience_level(self, experiences: List[Dict[str, Any]]) -> str:
        """Calculate experience level based on work history"""
        if not experiences:
            return 'entry'
        
        total_years = 0
        current_year = datetime.now().year
        
        for exp in experiences:
            start_year = exp.get('start_year')
            end_year = exp.get('end_year', 'present')
            
            if start_year:
                try:
                    start = int(start_year)
                    end = current_year if end_year == 'present' else int(end_year)
                    years = max(0, end - start)
                    total_years += years
                except ValueError:
                    pass
        
        if total_years < 2:
            return 'entry'
        elif total_years < 5:
            return 'mid'
        elif total_years < 10:
            return 'senior'
        else:
            return 'executive'
    
    def _calculate_resume_score(self, parsed_data: Dict[str, Any]) -> int:
        """Calculate overall resume quality score (0-100)"""
        score = 0
        
        # Contact information (20 points)
        contact = parsed_data.get('contact_info', {})
        if contact.get('name'):
            score += 5
        if contact.get('email'):
            score += 5
        if contact.get('phone'):
            score += 5
        if contact.get('location'):
            score += 5
        
        # Professional summary (10 points)
        if parsed_data.get('summary'):
            score += 10
        
        # Work experience (30 points)
        experiences = parsed_data.get('experience', [])
        if experiences:
            score += 15
            # Bonus for detailed descriptions
            if any('description' in exp for exp in experiences):
                score += 15
        
        # Education (20 points)
        education = parsed_data.get('education', [])
        if education:
            score += 20
        
        # Skills (15 points)
        skills = parsed_data.get('skills', {})
        if skills:
            score += 10
            # Bonus for multiple skill categories
            if len(skills) > 2:
                score += 5
        
        # Additional sections (5 points)
        if parsed_data.get('certifications'):
            score += 2
        if parsed_data.get('languages'):
            score += 2
        if parsed_data.get('achievements'):
            score += 1
        
        return min(score, 100)  # Cap at 100