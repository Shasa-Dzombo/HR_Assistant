from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from uuid import uuid4
import logging


class DatabaseManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.employees = {}
        self.candidates = {}
        self.jobs = {}
        self.interviews = {}
        self.performance_reviews = {}
        self.onboarding_records = {}
        self.cache = {}
        self.logger.info("DatabaseManager initialized with in-memory storage")
    
    async def create_employee(self, employee_data: Dict[str, Any]) -> str:
        employee_id = str(uuid4())
        employee_record = {
            **employee_data,
            'employee_id': employee_id,
            'created_at': datetime.utcnow().isoformat(),
            'status': employee_data.get('status', 'active')
        }
        self.employees[employee_id] = employee_record
        self.logger.info(f"Created employee record: {employee_id}")
        return employee_id
    
    async def get_employee(self, employee_id: str) -> Optional[Dict[str, Any]]:
        return self.employees.get(employee_id)
    
    async def update_employee(self, employee_id: str, update_data: Dict[str, Any]) -> bool:
        if employee_id in self.employees:
            self.employees[employee_id].update(update_data)
            self.employees[employee_id]['updated_at'] = datetime.utcnow().isoformat()
            self.logger.info(f"Updated employee: {employee_id}")
            return True
        return False
    
    async def search_employees(self, search_term: str) -> List[Dict[str, Any]]:
        results = []
        search_lower = search_term.lower()
        for employee in self.employees.values():
            if (search_lower in employee.get('name', '').lower() or 
                search_lower in employee.get('department', '').lower() or
                search_lower in employee.get('title', '').lower()):
                results.append(employee)
        return results
    
    async def create_candidate(self, candidate_data: Dict[str, Any]) -> str:
        candidate_id = str(uuid4())
        candidate_record = {
            **candidate_data,
            'candidate_id': candidate_id,
            'created_at': datetime.utcnow().isoformat(),
            'status': candidate_data.get('status', 'new')
        }
        self.candidates[candidate_id] = candidate_record
        self.logger.info(f"Created candidate record: {candidate_id}")
        return candidate_id
    
    async def get_candidate(self, candidate_id: str) -> Optional[Dict[str, Any]]:
        return self.candidates.get(candidate_id)
    
    async def update_candidate(self, candidate_id: str, update_data: Dict[str, Any]) -> bool:
        if candidate_id in self.candidates:
            self.candidates[candidate_id].update(update_data)
            self.candidates[candidate_id]['updated_at'] = datetime.utcnow().isoformat()
            self.logger.info(f"Updated candidate: {candidate_id}")
            return True
        return False
    
    async def create_job_posting(self, job_data: Dict[str, Any]) -> str:
        job_id = str(uuid4())
        job_record = {
            **job_data,
            'job_id': job_id,
            'created_at': datetime.utcnow().isoformat(),
            'status': job_data.get('status', 'active')
        }
        self.jobs[job_id] = job_record
        self.logger.info(f"Created job posting: {job_id}")
        return job_id
    
    async def get_job_posting(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self.jobs.get(job_id)
    
    async def get_active_jobs(self) -> List[Dict[str, Any]]:
        return [job for job in self.jobs.values() if job.get('status') == 'active']
    
    async def create_interview(self, interview_data: Dict[str, Any]) -> str:
        interview_id = str(uuid4())
        interview_record = {
            **interview_data,
            'interview_id': interview_id,
            'created_at': datetime.utcnow().isoformat(),
            'status': interview_data.get('status', 'scheduled')
        }
        self.interviews[interview_id] = interview_record
        self.logger.info(f"Created interview record: {interview_id}")
        return interview_id
    
    async def get_interview(self, interview_id: str) -> Optional[Dict[str, Any]]:
        return self.interviews.get(interview_id)
    
    async def update_interview(self, interview_id: str, update_data: Dict[str, Any]) -> bool:
        if interview_id in self.interviews:
            self.interviews[interview_id].update(update_data)
            self.interviews[interview_id]['updated_at'] = datetime.utcnow().isoformat()
            self.logger.info(f"Updated interview: {interview_id}")
            return True
        return False
    
    async def create_performance_review(self, review_data: Dict[str, Any]) -> str:
        review_id = str(uuid4())
        review_record = {
            **review_data,
            'review_id': review_id,
            'created_at': datetime.utcnow().isoformat(),
            'status': review_data.get('status', 'scheduled')
        }
        self.performance_reviews[review_id] = review_record
        self.logger.info(f"Created performance review: {review_id}")
        return review_id
    
    async def get_performance_review(self, review_id: str) -> Optional[Dict[str, Any]]:
        return self.performance_reviews.get(review_id)
    
    async def get_employee_reviews(self, employee_id: str) -> List[Dict[str, Any]]:
        return [review for review in self.performance_reviews.values() 
                if review.get('employee_id') == employee_id]
    
    async def create_onboarding_record(self, onboarding_data: Dict[str, Any]) -> str:
        onboarding_id = str(uuid4())
        onboarding_record = {
            **onboarding_data,
            'onboarding_id': onboarding_id,
            'created_at': datetime.utcnow().isoformat(),
            'status': onboarding_data.get('status', 'in_progress')
        }
        self.onboarding_records[onboarding_id] = onboarding_record
        self.logger.info(f"Created onboarding record: {onboarding_id}")
        return onboarding_id
    
    async def get_onboarding_record(self, onboarding_id: str) -> Optional[Dict[str, Any]]:
        return self.onboarding_records.get(onboarding_id)
    
    async def update_onboarding_record(self, onboarding_id: str, update_data: Dict[str, Any]) -> bool:
        if onboarding_id in self.onboarding_records:
            self.onboarding_records[onboarding_id].update(update_data)
            self.onboarding_records[onboarding_id]['updated_at'] = datetime.utcnow().isoformat()
            self.logger.info(f"Updated onboarding record: {onboarding_id}")
            return True
        return False
    
    async def cache_set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        self.cache[key] = {
            'value': value,
            'expires_at': datetime.utcnow() + timedelta(seconds=ttl)
        }
        return True
    
    async def cache_get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            cache_item = self.cache[key]
            if datetime.utcnow() < cache_item['expires_at']:
                return cache_item['value']
            else:
                del self.cache[key]
        return None
    
    async def cache_delete(self, key: str) -> bool:
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def get_statistics(self) -> Dict[str, int]:
        return {
            'employees': len(self.employees),
            'candidates': len(self.candidates),
            'jobs': len(self.jobs),
            'interviews': len(self.interviews),
            'performance_reviews': len(self.performance_reviews),
            'onboarding_records': len(self.onboarding_records),
            'cache_items': len(self.cache)
        }
    
    def clear_all_data(self) -> bool:
        self.employees.clear()
        self.candidates.clear()
        self.jobs.clear()
        self.interviews.clear()
        self.performance_reviews.clear()
        self.onboarding_records.clear()
        self.cache.clear()
        self.logger.warning("All database data cleared")
        return True
