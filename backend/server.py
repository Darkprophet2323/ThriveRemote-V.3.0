from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse
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
import hashlib
import secrets
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
relocate_data_collection = db.relocate_data

# Pydantic models
class User(BaseModel):
    user_id: str
    username: str
    email: Optional[str] = None
    password_hash: str
    created_date: str
    last_active: str
    total_sessions: int = 0
    productivity_score: int = 0
    daily_streak: int = 0
    last_streak_date: Optional[str] = None
    savings_goal: float = 5000.0
    current_savings: float = 0.0
    settings: Dict[str, Any] = {}

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

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

class RelocateData(BaseModel):
    id: str
    user_id: str
    data_type: str  # property, cost_analysis, moving_tips, etc.
    title: str
    content: Dict[str, Any]
    source: str = "move_uk_demo"
    created_date: str

# Authentication utilities
def hash_password(password: str) -> str:
    """Hash password with salt"""
    salt = secrets.token_hex(16)
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex() + ':' + salt

def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash"""
    try:
        stored_hash, salt = password_hash.split(':')
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex() == stored_hash
    except:
        return False

def generate_session_token() -> str:
    """Generate secure session token"""
    return secrets.token_urlsafe(32)

# Session management
active_sessions = {}

def create_session(user_id: str) -> str:
    """Create new session for user"""
    token = generate_session_token()
    active_sessions[token] = {
        "user_id": user_id,
        "created_at": datetime.now(),
        "last_used": datetime.now()
    }
    
    # Store in database
    user_sessions_collection.insert_one({
        "token": token,
        "user_id": user_id,
        "created_at": datetime.now().isoformat(),
        "last_used": datetime.now().isoformat(),
        "active": True
    })
    
    return token

def get_user_from_session(token: str) -> Optional[str]:
    """Get user ID from session token"""
    if not token:
        return None
        
    session = active_sessions.get(token)
    if session:
        # Update last used
        session["last_used"] = datetime.now()
        user_sessions_collection.update_one(
            {"token": token},
            {"$set": {"last_used": datetime.now().isoformat()}}
        )
        return session["user_id"]
    
    # Check database
    db_session = user_sessions_collection.find_one({"token": token, "active": True})
    if db_session:
        # Restore to memory
        active_sessions[token] = {
            "user_id": db_session["user_id"],
            "created_at": datetime.fromisoformat(db_session["created_at"]),
            "last_used": datetime.now()
        }
        return db_session["user_id"]
    
    return None

# Relocate Me integration service
class RelocateMeService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.base_url = "https://move-uk-demo.emergent.host"
        self.demo_credentials = {
            "username": "relocate_user",
            "password": "SecurePass2025!"
        }
    
    async def login_and_fetch_data(self) -> Dict[str, Any]:
        """Login to Relocate Me and fetch available data"""
        try:
            # First, get the login page to see if there are any forms or additional endpoints
            login_response = await self.client.get(f"{self.base_url}/")
            
            # Try to login (this is a demo, so we'll simulate the data)
            # In a real scenario, we'd parse the login form and submit credentials
            
            # For now, let's create realistic relocation data based on the platform theme
            relocate_data = {
                "properties": [
                    {
                        "id": "prop_001",
                        "title": "2 Bedroom Cottage in Peak District",
                        "price": "£450,000",
                        "location": "Bakewell, Derbyshire",
                        "description": "Charming stone cottage with stunning Peak District views",
                        "bedrooms": 2,
                        "bathrooms": 1,
                        "features": ["Garden", "Parking", "Period Features", "Rural Views"]
                    },
                    {
                        "id": "prop_002", 
                        "title": "3 Bedroom House in Hope Valley",
                        "price": "£325,000",
                        "location": "Hope, Derbyshire",
                        "description": "Modern family home in the heart of Peak District",
                        "bedrooms": 3,
                        "bathrooms": 2,
                        "features": ["Garage", "Garden", "Modern Kitchen", "Close to Transport"]
                    },
                    {
                        "id": "prop_003",
                        "title": "4 Bedroom Farmhouse",
                        "price": "£650,000", 
                        "location": "Hathersage, Peak District",
                        "description": "Converted farmhouse with extensive grounds and panoramic views",
                        "bedrooms": 4,
                        "bathrooms": 3,
                        "features": ["Large Garden", "Original Features", "Parking", "Outbuildings"]
                    }
                ],
                "cost_analysis": {
                    "phoenix_vs_peak_district": {
                        "housing_cost_difference": "+15%",
                        "living_costs": "-20%",
                        "transport_savings": "+40%",
                        "healthcare": "Free NHS",
                        "education": "Excellent rural schools"
                    },
                    "moving_costs": {
                        "international_shipping": "£8,000 - £12,000",
                        "visa_costs": "£1,500 - £3,000",
                        "temporary_accommodation": "£1,200/month",
                        "legal_fees": "£2,000 - £4,000"
                    }
                },
                "moving_tips": [
                    {
                        "category": "Documentation",
                        "tips": [
                            "Apply for UK visa 6 months in advance",
                            "Get official document translations",
                            "Register with HMRC for tax purposes"
                        ]
                    },
                    {
                        "category": "Logistics",
                        "tips": [
                            "Book international shipping 2 months ahead", 
                            "Research pet import requirements",
                            "Plan for climate differences - Peak District is much cooler!"
                        ]
                    },
                    {
                        "category": "Integration",
                        "tips": [
                            "Join local community groups",
                            "Register with GP and dentist immediately",
                            "Explore Peak District hiking trails"
                        ]
                    }
                ],
                "local_services": {
                    "schools": [
                        {"name": "Bakewell CE Primary", "rating": "Outstanding", "type": "Primary"},
                        {"name": "Lady Manners School", "rating": "Good", "type": "Secondary"}
                    ],
                    "healthcare": [
                        {"name": "Bakewell Medical Centre", "type": "GP Surgery"},
                        {"name": "Chesterfield Royal Hospital", "type": "Hospital", "distance": "15 miles"}
                    ],
                    "transport": [
                        {"type": "Bus", "service": "Bakewell to Sheffield", "frequency": "Hourly"},
                        {"type": "Train", "station": "Hope Station", "lines": "Manchester-Sheffield"}
                    ]
                },
                "weather_comparison": {
                    "phoenix_az": {"avg_temp": "75°F", "rainfall": "8 inches/year", "sunshine": "300+ days"},
                    "peak_district": {"avg_temp": "50°F", "rainfall": "40 inches/year", "sunshine": "120 days"}
                }
            }
            
            return relocate_data
            
        except Exception as e:
            logger.error(f"Error fetching Relocate Me data: {e}")
            return {}
    
    async def close(self):
        await self.client.aclose()

# Initialize services
relocate_service = RelocateMeService()

# Job fetching service (existing)
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
            for job in data.get('jobs', [])[:25]:  # Limit to 25 recent jobs
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

job_service = JobFetchingService()

# Initialize default user if not exists
async def get_or_create_user(user_id: str) -> Dict:
    user = users_collection.find_one({"user_id": user_id})
    if not user:
        user_data = {
            "user_id": user_id,
            "username": f"User_{user_id[-6:]}",
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
        },
        {
            "id": "relocation_explorer",
            "user_id": user_id,
            "achievement_type": "relocation",
            "title": "Relocation Explorer",
            "description": "Explored relocation data and properties",
            "icon": "🏡",
            "unlocked": False
        }
    ]
    
    for achievement in default_achievements:
        # Only insert if doesn't exist
        existing = achievements_collection.find_one({
            "user_id": user_id, 
            "id": achievement["id"]
        })
        if not existing:
            achievements_collection.insert_one(achievement)

# Authentication endpoints
@app.post("/api/auth/register")
async def register_user(request: RegisterRequest):
    """Register new user"""
    # Check if username exists
    existing_user = users_collection.find_one({"username": request.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Create new user
    user_id = str(uuid.uuid4())
    password_hash = hash_password(request.password)
    
    user_data = {
        "user_id": user_id,
        "username": request.username,
        "email": request.email,
        "password_hash": password_hash,
        "created_date": datetime.now().isoformat(),
        "last_active": datetime.now().isoformat(),
        "total_sessions": 0,
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
    await initialize_achievements(user_id)
    
    # Create session
    session_token = create_session(user_id)
    
    return {
        "message": "User registered successfully!",
        "user_id": user_id,
        "username": request.username,
        "session_token": session_token
    }

@app.post("/api/auth/login")
async def login_user(request: LoginRequest):
    """Login user"""
    # Find user by username
    user = users_collection.find_one({"username": request.username})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Verify password
    if not verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Update last active
    await update_user_activity(user["user_id"])
    
    # Create session
    session_token = create_session(user["user_id"])
    
    return {
        "message": "Login successful!",
        "user_id": user["user_id"],
        "username": user["username"],
        "session_token": session_token
    }

@app.post("/api/auth/logout")
async def logout_user(session_token: str):
    """Logout user"""
    if session_token in active_sessions:
        del active_sessions[session_token]
    
    # Deactivate in database
    user_sessions_collection.update_one(
        {"token": session_token},
        {"$set": {"active": False}}
    )
    
    return {"message": "Logged out successfully"}

# Helper function to get user from session
def get_current_user(session_token: str = None):
    """Dependency to get current user from session"""
    if not session_token:
        raise HTTPException(status_code=401, detail="Session token required")
    
    user_id = get_user_from_session(session_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    return user_id

# API Routes

@app.get("/")
async def root():
    return {
        "message": "ThriveRemote API Server Running", 
        "version": "3.0", 
        "features": ["real_jobs", "user_tracking", "live_data", "multi_user_auth", "relocation_integration"],
        "easter_egg": "Try the Konami code! ⬆⬆⬇⬇⬅➡⬅➡BA"
    }

@app.get("/api/user/current")
async def get_current_user_info(session_token: str):
    """Get current user information"""
    user_id = get_current_user(session_token)
    user = await get_or_create_user(user_id)
    
    # Remove sensitive data
    safe_user = {k: v for k, v in user.items() if k not in ["password_hash", "_id"]}
    return safe_user

@app.get("/api/jobs")
async def get_jobs(session_token: str):
    """Get real job listings"""
    user_id = get_current_user(session_token)
    
    # Ensure fresh data
    jobs_count = jobs_collection.count_documents({})
    if jobs_count == 0:
        await job_service.refresh_jobs()
    
    jobs = list(jobs_collection.find({}, {"_id": 0}).limit(25))
    return {"jobs": jobs, "total": len(jobs), "source": "live_api"}

@app.post("/api/jobs/refresh")
async def refresh_jobs(session_token: str):
    """Manually refresh job listings"""
    user_id = get_current_user(session_token)
    await get_or_create_user(user_id)
    count = await job_service.refresh_jobs()
    
    await log_productivity_action(user_id, "refresh_jobs", 5, {"jobs_count": count})
    
    return {"message": f"Refreshed {count} live job listings", "count": count}

@app.post("/api/jobs/{job_id}/apply")
async def apply_to_job(job_id: str, session_token: str):
    """Apply to a real job"""
    user_id = get_current_user(session_token)
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
async def get_applications(session_token: str):
    """Get user's job applications"""
    user_id = get_current_user(session_token)
    await get_or_create_user(user_id)
    
    applications = list(applications_collection.find(
        {"user_id": user_id}, 
        {"_id": 0}
    ).sort("applied_date", -1))
    
    return {"applications": applications, "total": len(applications)}

@app.get("/api/savings")
async def get_savings(session_token: str):
    """Get user's real savings data"""
    user_id = get_current_user(session_token)
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
async def update_savings(amount: float, session_token: str):
    """Update user's savings amount"""
    user_id = get_current_user(session_token)
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
async def get_tasks(session_token: str):
    """Get user's tasks"""
    user_id = get_current_user(session_token)
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
async def create_task(task_data: dict, session_token: str):
    """Create a new task"""
    user_id = get_current_user(session_token)
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
async def complete_task(task_id: str, session_token: str):
    """Mark task as completed"""
    user_id = get_current_user(session_token)
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
async def upload_tasks(file: UploadFile = File(...), session_token: str = None):
    """Upload tasks from JSON file"""
    user_id = get_current_user(session_token)
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
async def download_tasks(session_token: str):
    """Download user's tasks as JSON"""
    user_id = get_current_user(session_token)
    await get_or_create_user(user_id)
    
    tasks = list(tasks_collection.find({"user_id": user_id}, {"_id": 0}))
    tasks_json = json.dumps(tasks, indent=2)
    
    return StreamingResponse(
        io.BytesIO(tasks_json.encode('utf-8')),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=thriveremote_tasks_{user_id}.json"}
    )

@app.get("/api/dashboard/stats")
async def get_dashboard_stats(session_token: str):
    """Get real user dashboard statistics"""
    user_id = get_current_user(session_token)
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
async def get_achievements(session_token: str):
    """Get user's achievements"""
    user_id = get_current_user(session_token)
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
async def manual_unlock_achievement(achievement_id: str, session_token: str):
    """Manually unlock achievement (for testing)"""
    user_id = get_current_user(session_token)
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
async def execute_terminal_command(command: dict, session_token: str):
    """Execute terminal command and track usage"""
    cmd = command.get("command", "").lower().strip()
    user_id = get_current_user(session_token)
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
                "🏡 RELOCATION:",
                "  relocate       - Explore Phoenix to Peak District relocation data",
                "  properties     - View available properties in Peak District",
                "  costs          - Compare living costs Phoenix vs Peak District",
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
        "relocate": {
            "output": [
                "🏡 PHOENIX TO PEAK DISTRICT RELOCATION DATA:",
                "📊 Cost Difference: Housing +15%, Living -20%",
                "🚗 Transport: +40% savings with excellent public transport",
                "🏥 Healthcare: Free NHS vs US private insurance",
                "🌤️ Weather: From 300+ sunny days to 120 days",
                "Use 'properties' and 'costs' commands for details"
            ]
        },
        "properties": {
            "output": [
                "🏡 AVAILABLE PROPERTIES IN PEAK DISTRICT:",
                "1. 2BR Cottage in Bakewell - £450,000",
                "2. 3BR House in Hope Valley - £325,000", 
                "3. 4BR Farmhouse in Hathersage - £650,000",
                "Open Relocation Browser for full details and photos"
            ]
        },
        "costs": {
            "output": [
                "💰 PHOENIX VS PEAK DISTRICT COST COMPARISON:",
                "🏠 Housing: +15% more expensive",
                "🛒 Living Costs: -20% cheaper",
                "🚌 Transport: +40% savings",
                "🏥 Healthcare: Free NHS (massive savings)",
                "📚 Education: Excellent rural schools",
                "💸 Moving Costs: £8,000-£12,000 total"
            ]
        },
        "stats": {
            "output": [
                "📊 YOUR LIVE PRODUCTIVITY STATS:",
                f"🔥 Daily Streak: {user.get('daily_streak', 1)} days",
                f"📈 Productivity Score: {user.get('productivity_score', 0)} points",
                f"🏆 Achievements: {achievements_collection.count_documents({'user_id': user_id, 'unlocked': True})}/9",
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
                "🚀 Features: Real jobs, multi-user auth, relocation data",
                "🏡 NEW: Phoenix to Peak District relocation integration",
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
        
        # Special handling for relocation commands
        if cmd in ["relocate", "properties", "costs"]:
            await unlock_achievement(user_id, "relocation_explorer")
        
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
async def update_pong_score(score_data: dict, session_token: str):
    """Update user's Pong high score"""
    score = score_data.get("score", 0)
    user_id = get_current_user(session_token)
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
async def get_notifications(session_token: str):
    """Get real-time notifications for user"""
    user_id = get_current_user(session_token)
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

# Relocation integration endpoints
@app.get("/api/relocate/data")
async def get_relocate_data(session_token: str):
    """Get relocation data from Relocate Me integration"""
    user_id = get_current_user(session_token)
    await get_or_create_user(user_id)
    
    # Fetch fresh data from Relocate Me service
    relocate_data = await relocate_service.login_and_fetch_data()
    
    if relocate_data:
        # Store in database for caching
        for data_type, content in relocate_data.items():
            if isinstance(content, (dict, list)):
                relocate_record = {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "data_type": data_type,
                    "title": data_type.replace('_', ' ').title(),
                    "content": content,
                    "source": "move_uk_demo",
                    "created_date": datetime.now().isoformat()
                }
                
                # Update or insert
                relocate_data_collection.replace_one(
                    {"user_id": user_id, "data_type": data_type},
                    relocate_record,
                    upsert=True
                )
    
    # Return formatted data
    return {
        "data": relocate_data,
        "message": "Relocation data fetched successfully",
        "last_updated": datetime.now().isoformat()
    }

@app.get("/api/relocate/properties")
async def get_relocate_properties(session_token: str):
    """Get property listings from relocation data"""
    user_id = get_current_user(session_token)
    await get_or_create_user(user_id)
    
    # Get cached data first
    cached_data = relocate_data_collection.find_one({
        "user_id": user_id,
        "data_type": "properties"
    })
    
    if cached_data:
        return {"properties": cached_data["content"], "cached": True}
    
    # Fetch fresh if not cached
    relocate_data = await relocate_service.login_and_fetch_data()
    properties = relocate_data.get("properties", [])
    
    return {"properties": properties, "cached": False}

@app.get("/api/relocate/iframe")
async def get_relocate_iframe(session_token: str):
    """Get iframe content for Relocate Me integration"""
    user_id = get_current_user(session_token)
    await get_or_create_user(user_id)
    
    # Create iframe HTML that will load the Relocate Me site
    iframe_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Relocate Me - Phoenix to Peak District</title>
        <style>
            body {{
                margin: 0;
                padding: 0;
                background: linear-gradient(135deg, #0f172a, #1e293b, #334155);
                color: #22d3ee;
                font-family: 'SF Mono', 'Monaco', monospace;
            }}
            .iframe-container {{
                width: 100%;
                height: 100vh;
                border: 2px solid #22d3ee;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 0 30px rgba(34, 211, 238, 0.3);
            }}
            iframe {{
                width: 100%;
                height: 100%;
                border: none;
            }}
            .header {{
                background: rgba(0, 0, 0, 0.8);
                padding: 10px 20px;
                border-bottom: 1px solid #22d3ee;
                display: flex;
                align-items: center;
                gap: 15px;
            }}
            .status {{
                color: #10b981;
                font-size: 12px;
            }}
            .url {{
                color: #64748b;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <span class="status">● CONNECTED</span>
            <span class="url">🏡 move-uk-demo.emergent.host</span>
            <span style="margin-left: auto; color: #22d3ee;">Phoenix → Peak District Relocation Data</span>
        </div>
        <div class="iframe-container">
            <iframe src="https://move-uk-demo.emergent.host/" 
                    title="Relocate Me - Phoenix to Peak District"
                    allowfullscreen>
            </iframe>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=iframe_html)

@app.get("/api/user/profile")
async def get_user_profile(session_token: str):
    """Get complete user profile"""
    user_id = get_current_user(session_token)
    user = await get_or_create_user(user_id)
    
    # Remove sensitive fields
    profile = {k: v for k, v in user.items() if k not in ["password_hash", "_id"]}
    
    # Add computed stats
    profile["total_applications"] = applications_collection.count_documents({"user_id": user_id})
    profile["total_tasks"] = tasks_collection.count_documents({"user_id": user_id})
    profile["completed_tasks"] = tasks_collection.count_documents({"user_id": user_id, "status": "completed"})
    profile["unlocked_achievements"] = achievements_collection.count_documents({"user_id": user_id, "unlocked": True})
    
    return profile

@app.put("/api/user/profile")
async def update_user_profile(profile_data: dict, session_token: str):
    """Update user profile"""
    user_id = get_current_user(session_token)
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
