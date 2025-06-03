from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import os
import json
import io
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

class Achievement(BaseModel):
    id: str
    title: str
    description: str
    icon: str
    unlocked: bool
    unlock_date: Optional[str] = None

# Global state for real-time features
user_stats = {
    "daily_streak": 7,
    "total_sessions": 42,
    "productivity_score": 85,
    "easter_eggs_found": 0,
    "achievements_unlocked": 3,
    "pong_high_score": 150,
    "commands_executed": 23,
    "last_login": datetime.now().isoformat()
}

# Mock data for remote jobs (enhanced)
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
    },
    {
        "id": str(uuid.uuid4()),
        "title": "Blockchain Developer",
        "company": "CryptoInnovate",
        "location": "Remote Worldwide",
        "salary": "$120,000 - $150,000",
        "type": "Full-time",
        "description": "Build DeFi applications and smart contracts. Experience with Solidity and Web3 technologies required.",
        "skills": ["Solidity", "Web3", "JavaScript", "React"],
        "posted_date": "2025-03-10",
        "application_status": "not_applied"
    }
]

# Achievements system
ACHIEVEMENTS = [
    {
        "id": "first_job_apply",
        "title": "First Step",
        "description": "Applied to your first job",
        "icon": "🎯",
        "unlocked": True,
        "unlock_date": "2025-03-15"
    },
    {
        "id": "savings_milestone",
        "title": "Halfway There",
        "description": "Reached 50% of savings goal",
        "icon": "💰",
        "unlocked": True,
        "unlock_date": "2025-03-14"
    },
    {
        "id": "task_master",
        "title": "Task Master",
        "description": "Completed 10 tasks",
        "icon": "✅",
        "unlocked": True,
        "unlock_date": "2025-03-13"
    },
    {
        "id": "terminal_ninja",
        "title": "Terminal Ninja",
        "description": "Executed 50 terminal commands",
        "icon": "⚡",
        "unlocked": False
    },
    {
        "id": "pong_champion",
        "title": "Pong Champion",
        "description": "Score 200 points in Pong",
        "icon": "🏆",
        "unlocked": False
    },
    {
        "id": "easter_hunter",
        "title": "Easter Egg Hunter",
        "description": "Found 5 easter eggs",
        "icon": "🥚",
        "unlocked": False
    }
]

# API Routes

@app.get("/")
async def root():
    return {"message": "ThriveRemote API Server Running", "version": "2.0", "easter_egg": "Try the Konami code! ⬆⬆⬇⬇⬅➡⬅➡BA"}

@app.get("/api/jobs")
async def get_jobs():
    return {"jobs": MOCK_JOBS, "total": len(MOCK_JOBS)}

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
    
    # Update stats
    user_stats["productivity_score"] += 5
    
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
    
    return {"message": "Application submitted successfully!", "application": application, "achievement_unlocked": False}

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
        },
        {
            "id": str(uuid.uuid4()),
            "job_id": MOCK_JOBS[5]["id"],
            "job_title": "Blockchain Developer",
            "company": "CryptoInnovate",
            "status": "applied",
            "applied_date": "2025-03-10",
            "notes": "Exciting Web3 opportunity"
        }
    ]
    return {"applications": applications}

@app.get("/api/savings")
async def get_savings():
    current_time = datetime.now()
    savings_data = {
        "id": str(uuid.uuid4()),
        "current_amount": 2750.00 + (user_stats["daily_streak"] * 10),  # Dynamic based on streak
        "target_amount": 5000.00,
        "monthly_target": 500.00,
        "last_updated": current_time.isoformat(),
        "progress_percentage": min(((2750.00 + (user_stats["daily_streak"] * 10)) / 5000.0) * 100, 100),
        "months_to_goal": 5,
        "streak_bonus": user_stats["daily_streak"] * 10,
        "monthly_progress": [
            {"month": "Jan 2025", "amount": 1800, "streak_days": 31},
            {"month": "Feb 2025", "amount": 2300, "streak_days": 28},
            {"month": "Mar 2025", "amount": 2750 + (user_stats["daily_streak"] * 10), "streak_days": user_stats["daily_streak"]}
        ]
    }
    return savings_data

@app.post("/api/savings/update")
async def update_savings(amount: float):
    user_stats["productivity_score"] += 2
    return {
        "message": "Savings updated successfully! 💰",
        "new_amount": amount,
        "progress_percentage": (amount / 5000.0) * 100,
        "streak_bonus": user_stats["daily_streak"] * 10
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
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Play Pong for stress relief",
            "description": "Take a fun break and beat your high score",
            "status": "todo",
            "priority": "low",
            "category": "wellness",
            "created_date": "2025-03-15"
        }
    ]
    return {"tasks": tasks}

@app.post("/api/tasks/upload")
async def upload_tasks(file: UploadFile = File(...)):
    try:
        content = await file.read()
        tasks_data = json.loads(content.decode('utf-8'))
        
        # Validate tasks format
        if not isinstance(tasks_data, list):
            raise HTTPException(status_code=400, detail="Tasks must be a list")
        
        user_stats["productivity_score"] += 10
        return {
            "message": f"Successfully uploaded {len(tasks_data)} tasks! 📋",
            "tasks_count": len(tasks_data),
            "achievement_unlocked": len(tasks_data) > 10
        }
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tasks/download")
async def download_tasks():
    tasks = await get_tasks()
    tasks_json = json.dumps(tasks["tasks"], indent=2)
    
    buffer = io.BytesIO()
    buffer.write(tasks_json.encode('utf-8'))
    buffer.seek(0)
    
    return StreamingResponse(
        io.BytesIO(tasks_json.encode('utf-8')),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=thriveremote_tasks.json"}
    )

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    current_time = datetime.now()
    return {
        "total_applications": 3,
        "interviews_scheduled": 1,
        "savings_progress": min(((2750.00 + (user_stats["daily_streak"] * 10)) / 5000.0) * 100, 100),
        "tasks_completed_today": 3,
        "active_jobs_watching": 18,
        "monthly_savings": 2750.00 + (user_stats["daily_streak"] * 10),
        "days_to_goal": 150,
        "skill_development_hours": 45,
        "daily_streak": user_stats["daily_streak"],
        "productivity_score": user_stats["productivity_score"],
        "achievements_unlocked": user_stats["achievements_unlocked"],
        "pong_high_score": user_stats["pong_high_score"],
        "last_updated": current_time.isoformat()
    }

@app.get("/api/achievements")
async def get_achievements():
    return {"achievements": ACHIEVEMENTS}

@app.post("/api/achievements/{achievement_id}/unlock")
async def unlock_achievement(achievement_id: str):
    achievement = next((a for a in ACHIEVEMENTS if a["id"] == achievement_id), None)
    if not achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")
    
    if not achievement["unlocked"]:
        achievement["unlocked"] = True
        achievement["unlock_date"] = datetime.now().isoformat()
        user_stats["achievements_unlocked"] += 1
        user_stats["productivity_score"] += 15
        
    return {"message": "Achievement unlocked! 🏆", "achievement": achievement}

@app.post("/api/terminal/command")
async def execute_terminal_command(command: dict):
    cmd = command.get("command", "").lower().strip()
    user_stats["commands_executed"] += 1
    
    responses = {
        "help": {
            "output": [
                "ThriveRemote Terminal v2.0 - Command Reference:",
                "",
                "🎯 PRODUCTIVITY:",
                "  jobs           - List remote job opportunities",
                "  apply <id>     - Apply to a job by ID",
                "  savings        - Show savings progress and streak bonus",
                "  tasks          - List active tasks",
                "  stats          - Show your productivity stats",
                "",
                "🎮 FUN & EASTER EGGS:",
                "  pong           - Launch Pong game",
                "  matrix         - Enter the Matrix",
                "  konami         - Try the Konami code sequence",
                "  coffee         - Get a coffee break suggestion",
                "  motivate       - Get a motivational quote",
                "",
                "🔧 SYSTEM:",
                "  clear          - Clear terminal",
                "  time           - Show current time",
                "  version        - Show system version",
                "  whoami         - Show user info",
                "",
                "💡 TIP: Try typing 'surprise' for a random easter egg!"
            ]
        },
        "jobs": {
            "output": [f"📋 Found {len(MOCK_JOBS)} remote job opportunities:", "Use 'apply <job_number>' to apply instantly!"]
        },
        "savings": {
            "output": [
                f"💰 Savings Progress: ${2750 + (user_stats['daily_streak'] * 10):.2f} / $5,000.00",
                f"📈 Progress: {min(((2750 + (user_stats['daily_streak'] * 10)) / 5000) * 100, 100):.1f}%",
                f"🔥 Daily Streak: {user_stats['daily_streak']} days",
                f"💎 Streak Bonus: ${user_stats['daily_streak'] * 10}",
                "Keep your streak alive for bigger bonuses!"
            ]
        },
        "tasks": {
            "output": [f"✅ You have 5 active tasks", "2 in progress, 1 completed today", "Use task manager for details"]
        },
        "stats": {
            "output": [
                "📊 YOUR PRODUCTIVITY STATS:",
                f"🔥 Daily Streak: {user_stats['daily_streak']} days",
                f"📈 Productivity Score: {user_stats['productivity_score']}/100",
                f"🏆 Achievements: {user_stats['achievements_unlocked']}/6",
                f"⚡ Commands Executed: {user_stats['commands_executed']}",
                f"🎮 Pong High Score: {user_stats['pong_high_score']}",
                f"🎯 Total Sessions: {user_stats['total_sessions']}"
            ]
        },
        "pong": {
            "output": ["🎮 Launching Pong game...", "Break time! Beat your high score!", "Click the Pong app to play!"]
        },
        "matrix": {
            "output": [
                "🟢 Welcome to the Matrix...",
                "01001000 01100101 01101100 01101100 01101111",
                "Wake up, Neo... The remote work revolution has begun.",
                "💊 Red pill: Keep grinding. Blue pill: Take a break."
            ]
        },
        "konami": {
            "output": [
                "🎮 Konami Code detected!",
                "⬆⬆⬇⬇⬅➡⬅➡BA",
                "🚀 Productivity mode ACTIVATED!",
                "+50 productivity points!"
            ]
        },
        "coffee": {
            "output": [
                "☕ Coffee Break Suggestions:",
                "• Take a 5-minute walk",
                "• Do some stretching",
                "• Play a quick Pong game",
                "• Check your savings progress",
                "Perfect time for a dopamine hit! ☕"
            ]
        },
        "motivate": {
            "output": [
                "💪 MOTIVATION BOOST:",
                "\"Success is not final, failure is not fatal.\"",
                "\"Remote work is the future, and you're living it!\"",
                f"You're on a {user_stats['daily_streak']}-day streak! 🔥",
                "Keep pushing towards your $5K goal! 💰"
            ]
        },
        "surprise": {
            "output": [
                "🎉 SURPRISE! Random easter egg activated!",
                "🦄 You found a unicorn in the terminal!",
                "✨ Magic productivity boost applied!",
                "🎁 Hidden achievement progress: +1"
            ]
        },
        "time": {
            "output": [f"🕐 Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]
        },
        "version": {
            "output": ["ThriveRemote OS v2.0", "🚀 Now with 200% more productivity!", "Built for the remote work revolution"]
        },
        "whoami": {
            "output": [
                "👤 Remote Work Warrior",
                f"🔥 Streak: {user_stats['daily_streak']} days",
                f"📊 Productivity: {user_stats['productivity_score']}/100",
                "🎯 Status: Crushing goals!"
            ]
        },
        "clear": {
            "output": ["Terminal cleared! ✨"]
        }
    }
    
    if cmd in responses:
        if cmd == "konami":
            user_stats["productivity_score"] += 50
            user_stats["easter_eggs_found"] += 1
        elif cmd == "surprise":
            user_stats["easter_eggs_found"] += 1
            
        return responses[cmd]
    else:
        return {
            "output": [
                f"Command not found: {cmd}",
                "💡 Type 'help' for available commands",
                "🎮 Try 'surprise' for a random easter egg!"
            ]
        }

@app.post("/api/pong/score")
async def update_pong_score(score_data: dict):
    score = score_data.get("score", 0)
    if score > user_stats["pong_high_score"]:
        user_stats["pong_high_score"] = score
        user_stats["productivity_score"] += 5
        return {
            "message": "New high score! 🏆",
            "high_score": score,
            "achievement_unlocked": score >= 200
        }
    return {"message": "Good game! 🎮", "high_score": user_stats["pong_high_score"]}

@app.get("/api/realtime/notifications")
async def get_notifications():
    notifications = []
    
    # Streak notifications
    if user_stats["daily_streak"] >= 7:
        notifications.append({
            "id": "streak_week",
            "type": "achievement",
            "title": "Weekly Streak! 🔥",
            "message": f"{user_stats['daily_streak']} days strong!",
            "timestamp": datetime.now().isoformat()
        })
    
    # Productivity notifications
    if user_stats["productivity_score"] >= 90:
        notifications.append({
            "id": "productivity_high",
            "type": "success",
            "title": "Productivity Beast! 🚀",
            "message": "You're in the zone today!",
            "timestamp": datetime.now().isoformat()
        })
    
    return {"notifications": notifications}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
