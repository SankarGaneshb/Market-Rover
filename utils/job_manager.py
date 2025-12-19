"""
Job tracking and management for Market-Rover 2.0
Handles job status, progress tracking, and job lifecycle
"""
import uuid
import time
from typing import Dict, Optional
from threading import Lock
from datetime import datetime


class JobManager:
    """
    Manages analysis jobs with status tracking and progress updates.
    Thread-safe for concurrent job management.
    """
    
    def __init__(self):
        """Initialize the job manager."""
        self.jobs = {}
        self.lock = Lock()
    
    def create_job(self, portfolio_name: str, stock_count: int) -> str:
        """
        Create a new analysis job.
        
        Args:
            portfolio_name: Name of the portfolio file
            stock_count: Number of stocks to analyze
            
        Returns:
            Unique job ID
        """
        job_id = str(uuid.uuid4())
        
        with self.lock:
            self.jobs[job_id] = {
                'id': job_id,
                'portfolio': portfolio_name,
                'stock_count': stock_count,
                'status': 'pending',  # pending, running, completed, failed
                'progress': 0,
                'created_at': datetime.now(),
                'started_at': None,
                'completed_at': None,
                'current_stock': None,
                'result': None,
                'error': None
            }
        
        return job_id
    
    def start_job(self, job_id: str):
        """
        Mark a job as started.
        
        Args:
            job_id: Job ID to start
        """
        with self.lock:
            if job_id in self.jobs:
                self.jobs[job_id]['status'] = 'running'
                self.jobs[job_id]['started_at'] = datetime.now()
    
    def update_progress(self, job_id: str, progress: float, current_stock: Optional[str] = None):
        """
        Update job progress.
        
        Args:
            job_id: Job ID
            progress: Progress percentage (0-100)
            current_stock: Optional current stock being processed
        """
        with self.lock:
            if job_id in self.jobs:
                self.jobs[job_id]['progress'] = min(100, max(0, progress))
                if current_stock:
                    self.jobs[job_id]['current_stock'] = current_stock
    
    def complete_job(self, job_id: str, result: any):
        """
        Mark a job as completed.
        
        Args:
            job_id: Job ID
            result: Analysis result
        """
        with self.lock:
            if job_id in self.jobs:
                self.jobs[job_id]['status'] = 'completed'
                self.jobs[job_id]['progress'] = 100
                self.jobs[job_id]['completed_at'] = datetime.now()
                self.jobs[job_id]['result'] = result
    
    def fail_job(self, job_id: str, error: str):
        """
        Mark a job as failed.
        
        Args:
            job_id: Job ID
            error: Error message
        """
        with self.lock:
            if job_id in self.jobs:
                self.jobs[job_id]['status'] = 'failed'
                self.jobs[job_id]['completed_at'] = datetime.now()
                self.jobs[job_id]['error'] = error
    
    def get_job(self, job_id: str) -> Optional[Dict]:
        """
        Get job information.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job dictionary or None if not found
        """
        with self.lock:
            return self.jobs.get(job_id, None).copy() if job_id in self.jobs else None
    
    def get_all_jobs(self) -> list:
        """
        Get all jobs.
        
        Returns:
            List of job dictionaries
        """
        with self.lock:
            return [job.copy() for job in self.jobs.values()]
    
    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """
        Remove jobs older than specified hours.
        
        Args:
            max_age_hours: Maximum age in hours before cleanup
        """
        current_time = datetime.now()
        
        with self.lock:
            jobs_to_remove = []
            for job_id, job in self.jobs.items():
                age_hours = (current_time - job['created_at']).total_seconds() / 3600
                if age_hours > max_age_hours:
                    jobs_to_remove.append(job_id)
            
            for job_id in jobs_to_remove:
                del self.jobs[job_id]
        
        return len(jobs_to_remove)
