import json
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Job

class LocalJobEngine:
    """SQLite-backed state machine; execution handlers can be registered without a broker."""
    def enqueue(self, db: Session, job_type: str, payload: dict, total: int = 0) -> Job:
        job = Job(job_type=job_type, status="PENDING", payload=json.dumps(payload), total=total)
        db.add(job); db.commit(); db.refresh(job); return job
    def transition(self, db: Session, job: Job, action: str) -> Job:
        mapping = {"pause": ({"PENDING","RUNNING","RETRYING"}, "PAUSED"), "resume": ({"PAUSED"}, "PENDING"), "cancel": ({"PENDING","RUNNING","PAUSED","RETRYING"}, "CANCELLED"), "retry": ({"FAILED"}, "RETRYING")}
        allowed, target = mapping[action]
        if job.status not in allowed: raise ValueError(f"Cannot {action} a {job.status} job")
        job.status = target
        if target in {"CANCELLED"}: job.completed_at = datetime.utcnow()
        db.commit(); db.refresh(job); return job
