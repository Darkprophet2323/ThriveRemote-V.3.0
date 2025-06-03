from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import os
import json
import io
import httpx
import asyncio
from pymongo import MongoClient
import logging
from bson import ObjectId

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

# Collections
users_collection = db.users
jobs_collection = db.jobs
applications_collection = db.applications
tasks_collection = db.tasks
achievements_collection = db.achievements
user_sessions_collection = db.user_sessions
productivity_logs_collection = db.productivity_logs

# Pydantic models
class User(BaseModel):
    user_id: str
    username: str = "RemoteWarrior"
    email: Optional[str] = None
    created_date: str
    last_active: str
    total_sessions: int = 0
    productivity_score: int = 0
    daily_streak: int = 0
    last_streak_date: Optional[str] = None
    savings_goal: float = 5000.0
    current_savings: float = 0.0
    settings: Dict[str, Any] = {}

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
    source: str = "API"
    url: Optional[str] = None

class Application(BaseModel):
    id: str
    user_id: str
    job_id: str
    job_title: str
    company: str
    status: str
    applied_date: str
    follow_up_date: Optional[str] = None
    notes: str = ""

class Task(BaseModel):
    id: str
    user_id: str
    title: str
    description: str
    status: str  # todo, in_progress, completed
    priority: str  # low, medium, high
    category: str
    due_date: Optional[str] = None
    created_date: str
    completed_date: Optional[str] = None

class Achievement(BaseModel):
    id: str
    user_id: str
    achievement_type: str
    title: str
    description: str
    icon: str
    unlocked: bool
    unlock_date: Optional[str] = None

class ProductivityLog(BaseModel):
    id: str
    user_id: str
    action: str
    timestamp: str
    points: int
    metadata: Dict[str, Any] = {}

# Initialize default user if not exists
async def get_or_create_user(user_id: str = "default_user") -> Dict:
    user = users_collection.find_one({"user_id": user_id})
    if not user:
        user_data = {
            "user_id": user_id,
            "username": "RemoteWarrior",
            "created_date": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "total_sessions": 1,
            "productivity_score": 0,
            "daily_streak": 1,
            "last_streak_date": datetime.now().date().isoformat(),
            "savings_goal": 5000.0,
            "current_savings": 0.0,
            "settings": {},
            "achievements_unlocked": 0,
            "pong_high_score": 0,
            "commands_executed": 0,
            "easter_eggs_found": 0
        }
        users_collection.insert_one(user_data)
        
        # Initialize default achievements
        await initialize_achievements(user_id)
        
        user = user_data
    else:
        # Update last active and check streak
        await update_user_activity(user_id)
    
    return user

async def update_user_activity(user_id: str):
    """Update user activity and daily streak"""
    now = datetime.now()
    today = now.date().isoformat()
    
    user = users_collection.find_one({"user_id": user_id})
    if user:
        last_streak_date = user.get("last_streak_date")
        daily_streak = user.get("daily_streak", 0)
        
        if last_streak_date != today:
            yesterday = (now - timedelta(days=1)).date().isoformat()
            if last_streak_date == yesterday:
                # Continue streak
                daily_streak += 1
            else:
                # Reset streak
                daily_streak = 1
            
            users_collection.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "last_active": now.isoformat(),
                        "daily_streak": daily_streak,
                        "last_streak_date": today
                    },
                    "$inc": {"total_sessions": 1}
                }
            )

async def log_productivity_action(user_id: str, action: str, points: int, metadata: Dict = {}):
    """Log user productivity action and award points"""
    log_entry = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "action": action,
        "timestamp": datetime.now().isoformat(),
        "points": points,
        "metadata": metadata
    }
    productivity_logs_collection.insert_one(log_entry)
    
    # Update user productivity score
    users_collection.update_one(
        {"user_id": user_id},
        {"$inc": {"productivity_score": points}}
    )

async def initialize_achievements(user_id: str):
    """Initialize achievement system for user"""
    default_achievements = [
        {
            "id": "first_job_apply",
            "user_id": user_id,
            "achievement_type": "job_application",
            "title": "First Step",
            "description": "Applied to your first job",
            "icon": "🎯",
            "unlocked": False
        },
        {
            "id": "savings_milestone_25",
            "user_id": user_id,
            "achievement_type": "savings",
            "title": "Quarter Way There",
            "description": "Reached 25% of savings goal",
            "icon": "💰",
            "unlocked": False
        },
        {
            "id": "savings_milestone_50",
            "user_id": user_id,
            "achievement_type": "savings",
            "title": "Halfway Hero",
            "description": "Reached 50% of savings goal",
            "icon": "💎",
            "unlocked": False
        },
        {
            "id": "task_master",
            "user_id": user_id,
            "achievement_type": "tasks",
            "title": "Task Master",
            "description": "Completed 10 tasks",
            "icon": "✅",
            "unlocked": False
        },
        {
            "id": "terminal_ninja",
            "user_id": user_id,
            "achievement_type": "terminal",
            "title": "Terminal Ninja",
            "description": "Executed 50 terminal commands",
            "icon": "⚡",
            "unlocked": False
        },
        {
            "id": "pong_champion",
            "user_id": user_id,
            "achievement_type": "gaming",
            "title": "Pong Champion",
            "description": "Score 200 points in Pong",
            "icon": "🏆",
            "unlocked": False
        },
        {
            "id": "easter_hunter",
            "user_id": user_id,
            "achievement_type": "easter_eggs",
            "title": "Easter Egg Hunter",
            "description": "Found 5 easter eggs",
            "icon": "🥚",
            "unlocked": False
        },
        {
            "id": "streak_week",
            "user_id": user_id,
            "achievement_type": "streak",
            "title": "Weekly Warrior",
            "description": "Maintained 7-day streak",
            "icon": "🔥",
            "unlocked": False
        }
    ]
    
    for achievement in default_achievements:
        # Only insert if doesn't exist
        existing = achievements_collection.find_one({
            "user_id": user_id, 
            "achievement_type": achievement["achievement_type"]
        })
        if not existing:
            achievements_collection.insert_one(achievement)

# Job fetching service
class JobFetchingService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def fetch_remotive_jobs(self) -> List[Dict]:
        """Fetch real jobs from Remotive API"""
        try:
            response = await self.client.get('https://remotive.io/api/remote-jobs')
            response.raise_for_status()
            data = response.json()
            
            jobs = []
            for job in data.get('jobs', [])[:20]:  # Limit to 20 recent jobs
                normalized_job = {
                    "id": str(uuid.uuid4()),
                    "title": job.get('title', ''),
                    "company": job.get('company_name', ''),
                    "location": job.get('candidate_required_location', 'Remote'),
                    "salary": self._format_salary(job.get('salary')),
                    "type": job.get('job_type', 'Full-time'),
                    "description": job.get('description', '')[:500] + "..." if job.get('description') else '',
                    "skills": job.get('tags', [])[:5],  # Limit skills
                    "posted_date": job.get('publication_date', datetime.now().isoformat()),
                    "application_status": "not_applied",
                    "source": "Remotive",
                    "url": job.get('url', '')
                }
                jobs.append(normalized_job)
            
            return jobs
        except Exception as e:
            logger.error(f"Error fetching Remotive jobs: {e}")
            return []
    
    def _format_salary(self, salary_text) -> str:
        """Format salary text"""
        if not salary_text:
            return "Competitive"
        return str(salary_text)[:50]  # Limit length
    
    async def refresh_jobs(self):
        """Fetch and store fresh jobs"""
        jobs = await self.fetch_remotive_jobs()
        
        if jobs:
            # Clear old jobs and insert new ones
            jobs_collection.delete_many({})
            jobs_collection.insert_many(jobs)
            logger.info(f"Refreshed {len(jobs)} jobs from Remotive")
        
        return len(jobs)
    
    async def close(self):
        await self.client.aclose()

# Initialize job fetching service
job_service = JobFetchingService()

# API Routes

@app.get("/")
async def root():
    return {
        "message": "ThriveRemote API Server Running", 
        "version": "3.0", 
        "features": ["real_jobs", "user_tracking", "live_data"],
        "easter_egg": "Try the Konami code! ⬆⬆⬇⬇⬅➡⬅➡BA"
    }

@app.get("/api/jobs")
async def get_jobs(user_id: str = "default_user"):
    """Get real job listings"""
    # Ensure fresh data
    jobs_count = jobs_collection.count_documents({})
    if jobs_count == 0:
        await job_service.refresh_jobs()
    
    jobs = list(jobs_collection.find({}, {"_id": 0}).limit(20))
    return {"jobs": jobs, "total": len(jobs), "source": "live_api"}

@app.post("/api/jobs/refresh")
async def refresh_jobs(user_id: str = "default_user"):
    """Manually refresh job listings"""
    await get_or_create_user(user_id)
    count = await job_service.refresh_jobs()
    
    await log_productivity_action(user_id, "refresh_jobs", 5, {"jobs_count": count})
    
    return {"message": f"Refreshed {count} live job listings", "count": count}

@app.post("/api/jobs/{job_id}/apply")
async def apply_to_job(job_id: str, user_id: str = "default_user"):
    """Apply to a real job"""
    user = await get_or_create_user(user_id)
    
    job = jobs_collection.find_one({"id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Update job status
    jobs_collection.update_one(
        {"id": job_id},
        {"$set": {"application_status": "applied"}}
    )
    
    # Create application record
    application = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "job_id": job_id,
        "job_title": job["title"],
        "company": job["company"],
        "status": "applied",
        "applied_date": datetime.now().isoformat(),
        "notes": f"Applied via ThriveRemote OS to {job['company']}"
    }
    applications_collection.insert_one(application)
    
    # Award points and check achievements
    await log_productivity_action(user_id, "job_application", 15, {
        "job_title": job["title"],
        "company": job["company"]
    })
    
    # Check for first application achievement
    total_applications = applications_collection.count_documents({"user_id": user_id})
    if total_applications == 1:
        await unlock_achievement(user_id, "first_job_apply")
    
    return {
        "message": "Application submitted successfully! Great progress! 🎯",
        "application": application,
        "points_earned": 15
    }

@app.get("/api/applications")
async def get_applications(user_id: str = "default_user"):
    """Get user's job applications"""
    await get_or_create_user(user_id)
    
    applications = list(applications_collection.find(
        {"user_id": user_id}, 
        {"_id": 0}
    ).sort("applied_date", -1))
    
    return {"applications": applications, "total": len(applications)}

@app.get("/api/savings")
async def get_savings(user_id: str = "default_user"):
    """Get user's real savings data"""
    user = await get_or_create_user(user_id)
    
    current_amount = user.get("current_savings", 0.0)
    target_amount = user.get("savings_goal", 5000.0)
    daily_streak = user.get("daily_streak", 1)
    
    # Calculate streak bonus
    streak_bonus = daily_streak * 25  # $25 per streak day
    total_with_bonus = current_amount + streak_bonus
    
    progress_percentage = min((total_with_bonus / target_amount) * 100, 100)
    
    savings_data = {
        "id": user["user_id"],
        "current_amount": total_with_bonus,
        "base_amount": current_amount,
        "target_amount": target_amount,
        "monthly_target": target_amount / 10,  # 10 month goal
        "last_updated": user.get("last_active"),
        "progress_percentage": progress_percentage,
        "months_to_goal": max(1, int((target_amount - total_with_bonus) / (target_amount / 10))),
        "streak_bonus": streak_bonus,
        "daily_streak": daily_streak,
        "monthly_progress": await get_monthly_savings_progress(user_id)
    }
    
    return savings_data

@app.post("/api/savings/update")
async def update_savings(amount: float, user_id: str = "default_user"):
    """Update user's savings amount"""
    user = await get_or_create_user(user_id)
    
    # Update savings
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"current_savings": amount}}
    )
    
    # Award points
    await log_productivity_action(user_id, "savings_update", 10, {"amount": amount})
    
    # Check achievement milestones
    target = user.get("savings_goal", 5000.0)
    progress = (amount / target) * 100
    
    if progress >= 25:
        await unlock_achievement(user_id, "savings_milestone_25")
    if progress >= 50:
        await unlock_achievement(user_id, "savings_milestone_50")
    
    return {
        "message": "Savings updated successfully! 💰",
        "new_amount": amount,
        "progress_percentage": progress,
        "points_earned": 10
    }

async def get_monthly_savings_progress(user_id: str) -> List[Dict]:
    """Get monthly savings progress"""
    # This would typically come from savings transaction logs
    # For now, return computed progress based on current state
    user = users_collection.find_one({"user_id": user_id})
    current = user.get("current_savings", 0.0)
    
    # Simulate monthly progression
    months = ["Jan 2025", "Feb 2025", "Mar 2025"]
    progress = []
    
    for i, month in enumerate(months):
        amount = (current / 3) * (i + 1)  # Distribute across months
        progress.append({
            "month": month,
            "amount": round(amount, 2),
            "streak_days": min(user.get("daily_streak", 1), 31)
        })
    
    return progress

@app.get("/api/tasks")
async def get_tasks(user_id: str = "default_user"):
    """Get user's tasks"""
    await get_or_create_user(user_id)
    
    tasks = list(tasks_collection.find(
        {"user_id": user_id}, 
        {"_id": 0}
    ).sort("created_date", -1))
    
    # If no tasks, create some defaults
    if not tasks:
        await create_default_tasks(user_id)
        tasks = list(tasks_collection.find(
            {"user_id": user_id}, 
            {"_id": 0}
        ).sort("created_date", -1))
    
    return {"tasks": tasks}

async def create_default_tasks(user_id: str):
    """Create default tasks for new user"""
    default_tasks = [
        {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "title": "Update Resume",
            "description": "Add latest skills and experience",
            "status": "todo",
            "priority": "high",
            "category": "job_search",
            "due_date": (datetime.now() + timedelta(days=7)).date().isoformat(),
            "created_date": datetime.now().isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "title": "Set Monthly Savings Goal",
            "description": "Define realistic monthly savings target",
            "status": "in_progress",
            "priority": "medium",
            "category": "finance",
            "created_date": datetime.now().isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "title": "Explore ThriveRemote Features",
            "description": "Try the terminal, play Pong, and discover easter eggs",
            "status": "todo",
            "priority": "low",
            "category": "platform",
            "created_date": datetime.now().isoformat()
        }
    ]
    
    tasks_collection.insert_many(default_tasks)

@app.post("/api/tasks")
async def create_task(task_data: dict, user_id: str = "default_user"):
    """Create a new task"""
    await get_or_create_user(user_id)
    
    task = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "title": task_data.get("title", "New Task"),
        "description": task_data.get("description", ""),
        "status": "todo",
        "priority": task_data.get("priority", "medium"),
        "category": task_data.get("category", "general"),
        "due_date": task_data.get("due_date"),
        "created_date": datetime.now().isoformat()
    }
    
    tasks_collection.insert_one(task)
    await log_productivity_action(user_id, "task_created", 5, {"task_title": task["title"]})
    
    return {"message": "Task created! 📋", "task": task, "points_earned": 5}

@app.put("/api/tasks/{task_id}/complete")
async def complete_task(task_id: str, user_id: str = "default_user"):
    """Mark task as completed"""
    await get_or_create_user(user_id)
    
    task = tasks_collection.find_one({"id": task_id, "user_id": user_id})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update task
    tasks_collection.update_one(
        {"id": task_id, "user_id": user_id},
        {
            "$set": {
                "status": "completed",
                "completed_date": datetime.now().isoformat()
            }
        }
    )
    
    # Award points
    await log_productivity_action(user_id, "task_completed", 20, {"task_title": task["title"]})
    
    # Check achievements
    completed_count = tasks_collection.count_documents({
        "user_id": user_id, 
        "status": "completed"
    })
    
    if completed_count >= 10:
        await unlock_achievement(user_id, "task_master")
    
    return {
        "message": "Task completed! Great work! ✅",
        "points_earned": 20,
        "total_completed": completed_count
    }

@app.post("/api/tasks/upload")
async def upload_tasks(file: UploadFile = File(...), user_id: str = "default_user"):
    """Upload tasks from JSON file"""
    await get_or_create_user(user_id)
    
    try:
        content = await file.read()
        tasks_data = json.loads(content.decode('utf-8'))
        
        if not isinstance(tasks_data, list):
            raise HTTPException(status_code=400, detail="Tasks must be a list")
        
        # Process and save tasks
        for task_data in tasks_data:
            task = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "title": task_data.get("title", "Imported Task"),
                "description": task_data.get("description", ""),
                "status": task_data.get("status", "todo"),
                "priority": task_data.get("priority", "medium"),
                "category": task_data.get("category", "imported"),
                "due_date": task_data.get("due_date"),
                "created_date": datetime.now().isoformat()
            }
            tasks_collection.insert_one(task)
        
        await log_productivity_action(user_id, "tasks_imported", 15, {"count": len(tasks_data)})
        
        return {
            "message": f"Successfully uploaded {len(tasks_data)} tasks! 📋",
            "tasks_count": len(tasks_data),
            "points_earned": 15
        }
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tasks/download")
async def download_tasks(user_id: str = "default_user"):
    """Download user's tasks as JSON"""
    await get_or_create_user(user_id)
    
    tasks = list(tasks_collection.find({"user_id": user_id}, {"_id": 0}))
    tasks_json = json.dumps(tasks, indent=2)
    
    return StreamingResponse(
        io.BytesIO(tasks_json.encode('utf-8')),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=thriveremote_tasks_{user_id}.json"}
    )

@app.get("/api/dashboard/stats")
async def get_dashboard_stats(user_id: str = "default_user"):
    """Get real user dashboard statistics"""
    user = await get_or_create_user(user_id)
    
    # Get real counts
    total_applications = applications_collection.count_documents({"user_id": user_id})
    total_tasks = tasks_collection.count_documents({"user_id": user_id})
    completed_tasks = tasks_collection.count_documents({"user_id": user_id, "status": "completed"})
    unlocked_achievements = achievements_collection.count_documents({"user_id": user_id, "unlocked": True})
    
    # Calculate savings progress
    current_savings = user.get("current_savings", 0.0)
    savings_goal = user.get("savings_goal", 5000.0)
    streak_bonus = user.get("daily_streak", 1) * 25
    total_savings = current_savings + streak_bonus
    savings_progress = min((total_savings / savings_goal) * 100, 100)
    
    return {
        "total_applications": total_applications,
        "interviews_scheduled": applications_collection.count_documents({
            "user_id": user_id, 
            "status": {"$in": ["interviewing", "interview_scheduled"]}
        }),
        "savings_progress": savings_progress,
        "tasks_completed_today": completed_tasks,
        "active_jobs_watching": jobs_collection.count_documents({}),
        "monthly_savings": total_savings,
        "days_to_goal": max(1, int((savings_goal - total_savings) / 50)),  # $50 per day goal
        "skill_development_hours": user.get("productivity_score", 0) / 10,  # Convert points to hours
        "daily_streak": user.get("daily_streak", 1),
        "productivity_score": user.get("productivity_score", 0),
        "achievements_unlocked": unlocked_achievements,
        "pong_high_score": user.get("pong_high_score", 0),
        "last_updated": datetime.now().isoformat(),
        "total_tasks": total_tasks,
        "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    }

@app.get("/api/achievements")
async def get_achievements(user_id: str = "default_user"):
    """Get user's achievements"""
    await get_or_create_user(user_id)
    
    achievements = list(achievements_collection.find(
        {"user_id": user_id}, 
        {"_id": 0}
    ).sort("unlocked", -1))
    
    return {"achievements": achievements}

async def unlock_achievement(user_id: str, achievement_id: str):
    """Unlock an achievement for user"""
    result = achievements_collection.update_one(
        {"user_id": user_id, "id": achievement_id, "unlocked": False},
        {
            "$set": {
                "unlocked": True,
                "unlock_date": datetime.now().isoformat()
            }
        }
    )
    
    if result.modified_count > 0:
        # Update user achievement count
        users_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"achievements_unlocked": 1}}
        )
        
        # Award bonus points
        await log_productivity_action(user_id, "achievement_unlocked", 50, {"achievement_id": achievement_id})
        
        return True
    return False

@app.post("/api/achievements/{achievement_id}/unlock")
async def manual_unlock_achievement(achievement_id: str, user_id: str = "default_user"):
    """Manually unlock achievement (for testing)"""
    await get_or_create_user(user_id)
    
    unlocked = await unlock_achievement(user_id, achievement_id)
    
    if unlocked:
        achievement = achievements_collection.find_one({"user_id": user_id, "id": achievement_id})
        return {
            "message": "Achievement unlocked! 🏆",
            "achievement": {k: v for k, v in achievement.items() if k != "_id"},
            "points_earned": 50
        }
    else:
        raise HTTPException(status_code=400, detail="Achievement already unlocked or not found")

@app.post("/api/terminal/command")
async def execute_terminal_command(command: dict, user_id: str = "default_user"):
    """Execute terminal command and track usage"""
    cmd = command.get("command", "").lower().strip()
    user = await get_or_create_user(user_id)
    
    # Increment command counter
    users_collection.update_one(
        {"user_id": user_id},
        {"$inc": {"commands_executed": 1}}
    )
    
    commands_executed = user.get("commands_executed", 0) + 1
    
    # Award points for command usage
    await log_productivity_action(user_id, "terminal_command", 2, {"command": cmd})
    
    # Check terminal ninja achievement
    if commands_executed >= 50:
        await unlock_achievement(user_id, "terminal_ninja")
    
    # Enhanced responses with real data
    responses = {
        "help": {
            "output": [
                "ThriveRemote Terminal v3.0 - Live Data Command Reference:",
                "",
                "🎯 PRODUCTIVITY:",
                "  jobs           - List REAL remote job opportunities",
                "  apply <id>     - Apply to jobs (tracked in your profile)",
                "  savings        - Show YOUR actual savings progress",
                "  tasks          - List YOUR personal tasks",
                "  stats          - Show YOUR live productivity stats",
                "",
                "🎮 FUN & EASTER EGGS:",
                "  pong           - Launch Pong game (scores saved)",
                "  matrix         - Enter the Matrix",
                "  konami         - Try the Konami code sequence",
                "  coffee         - Get a coffee break suggestion",
                "  motivate       - Get a motivational quote",
                "",
                "🔧 SYSTEM:",
                "  clear          - Clear terminal",
                "  time           - Show current time",
                "  version        - Show system version",
                "  whoami         - Show YOUR user info",
                "  profile        - Show YOUR complete profile",
                "",
                "💡 TIP: All your data is saved and tracked in real-time!"
            ]
        },
        "jobs": {
            "output": [
                f"📋 Found {jobs_collection.count_documents({})} REAL remote job opportunities:",
                "These are live jobs from Remotive API!",
                "Use job search app to apply and track your applications"
            ]
        },
        "savings": {
            "output": [
                f"💰 YOUR Savings Progress: ${user.get('current_savings', 0):.2f} / $5,000.00",
                f"📈 Progress: {min((user.get('current_savings', 0) / 5000) * 100, 100):.1f}%",
                f"🔥 Daily Streak: {user.get('daily_streak', 1)} days",
                f"💎 Streak Bonus: ${user.get('daily_streak', 1) * 25}",
                "Update your savings in the Savings Goal app!"
            ]
        },
        "tasks": {
            "output": [
                f"✅ YOU have {tasks_collection.count_documents({'user_id': user_id})} tasks",
                f"📝 Completed: {tasks_collection.count_documents({'user_id': user_id, 'status': 'completed'})}",
                "Use Task Manager to add, complete, and organize"
            ]
        },
        "stats": {
            "output": [
                "📊 YOUR LIVE PRODUCTIVITY STATS:",
                f"🔥 Daily Streak: {user.get('daily_streak', 1)} days",
                f"📈 Productivity Score: {user.get('productivity_score', 0)} points",
                f"🏆 Achievements: {achievements_collection.count_documents({'user_id': user_id, 'unlocked': True})}/8",
                f"⚡ Commands Executed: {commands_executed}",
                f"🎮 Pong High Score: {user.get('pong_high_score', 0)}",
                f"🎯 Total Sessions: {user.get('total_sessions', 1)}",
                f"💼 Job Applications: {applications_collection.count_documents({'user_id': user_id})}",
                "All data updates in real-time!"
            ]
        },
        "profile": {
            "output": [
                f"👤 USER PROFILE: {user.get('username', 'RemoteWarrior')}",
                f"📅 Member Since: {user.get('created_date', '')[:10]}",
                f"⏰ Last Active: {user.get('last_active', '')[:16]}",
                f"🔥 Current Streak: {user.get('daily_streak', 1)} days",
                f"💰 Savings: ${user.get('current_savings', 0):.2f}",
                f"📈 Productivity: {user.get('productivity_score', 0)} points",
                "Your journey to remote work success!"
            ]
        },
        "pong": {
            "output": [
                "🎮 Launching Pong game...",
                f"Beat your high score: {user.get('pong_high_score', 0)} points!",
                "Scores are automatically saved to your profile"
            ]
        },
        "matrix": {
            "output": [
                "🟢 Welcome to the Matrix...",
                "01001000 01100101 01101100 01101100 01101111",
                "Wake up, Neo... The remote work revolution has begun.",
                "💊 Red pill: Keep grinding. Blue pill: Take a break.",
                "+5 productivity points for finding this easter egg!"
            ]
        },
        "konami": {
            "output": [
                "🎮 Konami Code detected!",
                "⬆⬆⬇⬇⬅➡⬅➡BA",
                "🚀 Productivity mode ACTIVATED!",
                "+50 productivity points!",
                "Easter egg found and saved to your profile!"
            ]
        },
        "coffee": {
            "output": [
                "☕ Personalized Coffee Break Suggestions:",
                f"• You've been productive for {user.get('total_sessions', 1)} sessions",
                f"• Your streak: {user.get('daily_streak', 1)} days - keep it up!",
                "• Take a 5-minute walk",
                "• Play a quick Pong game",
                "• Check your real savings progress"
            ]
        },
        "motivate": {
            "output": [
                "💪 PERSONALIZED MOTIVATION:",
                f"\"You're on a {user.get('daily_streak', 1)}-day streak! 🔥\"",
                f"\"Productivity score: {user.get('productivity_score', 0)} and climbing!\"",
                "\"Remote work is the future, and you're living it!\"",
                f"Keep pushing towards your ${user.get('savings_goal', 5000)} goal! 💰"
            ]
        },
        "surprise": {
            "output": [
                "🎉 SURPRISE! Random easter egg activated!",
                "🦄 You found a unicorn in the terminal!",
                "✨ Magic productivity boost applied! (+10 points)",
                "🎁 Hidden achievement progress updated!",
                "This discovery is saved to your profile!"
            ]
        },
        "time": {
            "output": [f"🕐 Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]
        },
        "version": {
            "output": [
                "ThriveRemote OS v3.0 - LIVE DATA EDITION",
                "🚀 Features: Real jobs, user tracking, live stats",
                "Built for serious remote work professionals"
            ]
        },
        "whoami": {
            "output": [
                f"👤 {user.get('username', 'RemoteWarrior')}",
                f"🔥 Streak: {user.get('daily_streak', 1)} days",
                f"📊 Productivity: {user.get('productivity_score', 0)} points",
                f"🎯 Status: Remote Work Champion!"
            ]
        },
        "clear": {
            "output": ["Terminal cleared! ✨"]
        }
    }
    
    if cmd in responses:
        # Special handling for easter eggs
        if cmd in ["konami", "matrix", "surprise"]:
            users_collection.update_one(
                {"user_id": user_id},
                {"$inc": {"easter_eggs_found": 1}}
            )
            
            points = 50 if cmd == "konami" else 10
            await log_productivity_action(user_id, "easter_egg", points, {"type": cmd})
            
            # Check easter egg hunter achievement
            easter_eggs_found = user.get("easter_eggs_found", 0) + 1
            if easter_eggs_found >= 5:
                await unlock_achievement(user_id, "easter_hunter")
        
        return responses[cmd]
    else:
        return {
            "output": [
                f"Command not found: {cmd}",
                "💡 Type 'help' for available commands",
                "🎮 Try 'surprise' for a random easter egg!",
                f"Commands executed: {commands_executed}"
            ]
        }

@app.post("/api/pong/score")
async def update_pong_score(score_data: dict, user_id: str = "default_user"):
    """Update user's Pong high score"""
    score = score_data.get("score", 0)
    user = await get_or_create_user(user_id)
    
    current_high = user.get("pong_high_score", 0)
    
    if score > current_high:
        users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"pong_high_score": score}}
        )
        
        await log_productivity_action(user_id, "pong_high_score", 15, {"score": score})
        
        # Check achievement
        if score >= 200:
            await unlock_achievement(user_id, "pong_champion")
        
        return {
            "message": "New high score! 🏆",
            "high_score": score,
            "achievement_unlocked": score >= 200,
            "points_earned": 15
        }
    
    return {
        "message": "Good game! 🎮",
        "high_score": current_high,
        "points_earned": 5
    }

@app.get("/api/realtime/notifications")
async def get_notifications(user_id: str = "default_user"):
    """Get real-time notifications for user"""
    user = await get_or_create_user(user_id)
    notifications = []
    
    # Streak notifications
    streak = user.get("daily_streak", 1)
    if streak >= 7:
        notifications.append({
            "id": "streak_week",
            "type": "achievement",
            "title": f"Weekly Streak! 🔥",
            "message": f"{streak} days strong! Keep going!",
            "timestamp": datetime.now().isoformat()
        })
        # Check for streak achievement
        await unlock_achievement(user_id, "streak_week")
    
    # Productivity notifications
    productivity = user.get("productivity_score", 0)
    if productivity >= 100:
        notifications.append({
            "id": "productivity_milestone",
            "type": "success",
            "title": "Productivity Beast! 🚀",
            "message": f"{productivity} points and climbing!",
            "timestamp": datetime.now().isoformat()
        })
    
    # Job application reminders
    pending_apps = applications_collection.count_documents({
        "user_id": user_id, 
        "status": "applied"
    })
    if pending_apps > 0:
        notifications.append({
            "id": "pending_applications",
            "type": "info",
            "title": "Follow-up Reminder 📋",
            "message": f"You have {pending_apps} pending applications",
            "timestamp": datetime.now().isoformat()
        })
    
    return {"notifications": notifications}

@app.get("/api/user/profile")
async def get_user_profile(user_id: str = "default_user"):
    """Get complete user profile"""
    user = await get_or_create_user(user_id)
    
    # Remove sensitive fields
    profile = {k: v for k, v in user.items() if k != "_id"}
    
    # Add computed stats
    profile["total_applications"] = applications_collection.count_documents({"user_id": user_id})
    profile["total_tasks"] = tasks_collection.count_documents({"user_id": user_id})
    profile["completed_tasks"] = tasks_collection.count_documents({"user_id": user_id, "status": "completed"})
    profile["unlocked_achievements"] = achievements_collection.count_documents({"user_id": user_id, "unlocked": True})
    
    return profile

@app.put("/api/user/profile")
async def update_user_profile(profile_data: dict, user_id: str = "default_user"):
    """Update user profile"""
    await get_or_create_user(user_id)
    
    # Allow only safe fields to be updated
    allowed_fields = ["username", "email", "savings_goal", "settings"]
    update_data = {k: v for k, v in profile_data.items() if k in allowed_fields}
    
    if update_data:
        users_collection.update_one(
            {"user_id": user_id},
            {"$set": update_data}
        )
    
    return {"message": "Profile updated successfully! ✨"}

# Background task to refresh jobs periodically
@app.on_event("startup")
async def startup_event():
    """Initialize database and refresh jobs on startup"""
    # Ensure jobs are fresh on startup
    try:
        await job_service.refresh_jobs()
        logger.info("Initial job refresh completed")
    except Exception as e:
        logger.error(f"Failed to refresh jobs on startup: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
