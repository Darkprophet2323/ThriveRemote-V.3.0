from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import os
from pymongo import MongoClient
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = MongoClient(MONGO_URL)
db = client.thriveremote

# Pydantic models
class Job(BaseModel):
    id: str
    title: str
    company: str
    location: str
    salary: str
    type: str
    description: str
    skills: List[str]
    posted_date: str
    application_status: str = "not_applied"

class Application(BaseModel):
    id: str
    job_id: str
    job_title: str
    company: str
    status: str
    applied_date: str
    follow_up_date: Optional[str] = None
    notes: str = ""

class SavingsGoal(BaseModel):
    id: str
    current_amount: float
    target_amount: float = 5000.0
    monthly_target: float
    last_updated: str

class Task(BaseModel):
    id: str
    title: str
    description: str
    status: str  # todo, in_progress, completed
    priority: str  # low, medium, high
    category: str
    due_date: Optional[str] = None
    created_date: str

# Mock data for remote jobs
MOCK_JOBS = [
    {
        "id": str(uuid.uuid4()),
        "title": "Senior Frontend Developer",
        "company": "TechFlow Inc",
        "location": "Remote (Arizona Preferred)",
        "salary": "$95,000 - $120,000",
        "type": "Full-time",
        "description": "Build cutting-edge React applications for fintech platform. Work with modern tech stack including React, TypeScript, and GraphQL.",
        "skills": ["React", "TypeScript", "GraphQL", "Node.js"],
        "posted_date": "2025-03-15",
        "application_status": "not_applied"
    },
    {
        "id": str(uuid.uuid4()),
        "title": "Remote Python Developer",
        "company": "DataCorp Solutions",
        "location": "Remote - US",
        "salary": "$85,000 - $110,000",
        "type": "Full-time",
        "description": "Develop data processing pipelines and APIs using Python, FastAPI, and PostgreSQL. Experience with cloud platforms preferred.",
        "skills": ["Python", "FastAPI", "PostgreSQL", "AWS"],
        "posted_date": "2025-03-14",
        "application_status": "not_applied"
    },
    {
        "id": str(uuid.uuid4()),
        "title": "DevOps Engineer (Remote)",
        "company": "CloudScale Technologies",
        "location": "Remote",
        "salary": "$100,000 - $130,000",
        "type": "Full-time",
        "description": "Manage CI/CD pipelines, Kubernetes clusters, and cloud infrastructure. Strong background in automation and monitoring required.",
        "skills": ["Kubernetes", "Docker", "AWS", "Terraform"],
        "posted_date": "2025-03-13",
        "application_status": "not_applied"
    },
    {
        "id": str(uuid.uuid4()),
        "title": "Full Stack Developer",
        "company": "StartupForge",
        "location": "Remote (Arizona Welcome)",
        "salary": "$75,000 - $95,000",
        "type": "Full-time",
        "description": "Join our fast-growing startup building SaaS tools. Full stack development with React, Node.js, and MongoDB.",
        "skills": ["React", "Node.js", "MongoDB", "Express"],
        "posted_date": "2025-03-12",
        "application_status": "applied"
    },
    {
        "id": str(uuid.uuid4()),
        "title": "Remote UX Designer",
        "company": "DesignMasters",
        "location": "Remote",
        "salary": "$70,000 - $90,000",
        "type": "Contract",
        "description": "Create user-centered designs for mobile and web applications. Collaborate with cross-functional teams remotely.",
        "skills": ["Figma", "Adobe XD", "User Research", "Prototyping"],
        "posted_date": "2025-03-11",
        "application_status": "interviewing"
    }
]

# API Routes

@app.get("/")
async def root():
    return {"message": "ThriveRemote API Server Running"}

@app.get("/api/jobs")
async def get_jobs():
    return {"jobs": MOCK_JOBS}

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    job = next((job for job in MOCK_JOBS if job["id"] == job_id), None)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.post("/api/jobs/{job_id}/apply")
async def apply_to_job(job_id: str):
    job = next((job for job in MOCK_JOBS if job["id"] == job_id), None)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job["application_status"] = "applied"
    
    # Create application record
    application = {
        "id": str(uuid.uuid4()),
        "job_id": job_id,
        "job_title": job["title"],
        "company": job["company"],
        "status": "applied",
        "applied_date": datetime.now().isoformat(),
        "notes": ""
    }
    
    return {"message": "Application submitted successfully", "application": application}

@app.get("/api/applications")
async def get_applications():
    applications = [
        {
            "id": str(uuid.uuid4()),
            "job_id": MOCK_JOBS[3]["id"],
            "job_title": "Full Stack Developer",
            "company": "StartupForge",
            "status": "applied",
            "applied_date": "2025-03-12",
            "notes": "Strong match for React/Node skills"
        },
        {
            "id": str(uuid.uuid4()),
            "job_id": MOCK_JOBS[4]["id"],
            "job_title": "Remote UX Designer",
            "company": "DesignMasters",
            "status": "interviewing",
            "applied_date": "2025-03-11",
            "follow_up_date": "2025-03-18",
            "notes": "Phone interview scheduled for next week"
        }
    ]
    return {"applications": applications}

@app.get("/api/savings")
async def get_savings():
    savings_data = {
        "id": str(uuid.uuid4()),
        "current_amount": 2750.00,
        "target_amount": 5000.00,
        "monthly_target": 500.00,
        "last_updated": datetime.now().isoformat(),
        "progress_percentage": 55.0,
        "months_to_goal": 5,
        "monthly_progress": [
            {"month": "Jan 2025", "amount": 1800},
            {"month": "Feb 2025", "amount": 2300},
            {"month": "Mar 2025", "amount": 2750}
        ]
    }
    return savings_data

@app.post("/api/savings/update")
async def update_savings(amount: float):
    # In real app, this would update the database
    return {
        "message": "Savings updated successfully",
        "new_amount": amount,
        "progress_percentage": (amount / 5000.0) * 100
    }

@app.get("/api/tasks")
async def get_tasks():
    tasks = [
        {
            "id": str(uuid.uuid4()),
            "title": "Update Resume",
            "description": "Add recent project experience and skills",
            "status": "in_progress",
            "priority": "high",
            "category": "job_search",
            "due_date": "2025-03-20",
            "created_date": "2025-03-15"
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Follow up with StartupForge",
            "description": "Send thank you email after application",
            "status": "todo",
            "priority": "medium",
            "category": "job_search",
            "due_date": "2025-03-18",
            "created_date": "2025-03-15"
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Review Budget",
            "description": "Analyze monthly expenses and optimize savings",
            "status": "completed",
            "priority": "medium",
            "category": "finance",
            "created_date": "2025-03-10"
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Learn Kubernetes",
            "description": "Complete online course for DevOps role preparation",
            "status": "in_progress",
            "priority": "high",
            "category": "skill_development",
            "due_date": "2025-03-30",
            "created_date": "2025-03-05"
        }
    ]
    return {"tasks": tasks}

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    return {
        "total_applications": 2,
        "interviews_scheduled": 1,
        "savings_progress": 55.0,
        "tasks_completed_today": 3,
        "active_jobs_watching": 15,
        "monthly_savings": 2750.00,
        "days_to_goal": 150,
        "skill_development_hours": 45
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
