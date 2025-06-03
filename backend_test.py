import requests
import unittest
import sys
import json
import io
import time

class ThriveRemoteAPITester(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(ThriveRemoteAPITester, self).__init__(*args, **kwargs)
        self.base_url = "https://48d504fc-72cd-4ce7-9458-aaa85b7c09c6.preview.emergentagent.com"
        self.tests_run = 0
        self.tests_passed = 0
        self.username = f"test_user_{int(time.time())}"
        self.password = "TestPass123!"
        self.session_token = None
        self.user_id = None

    def test_01_root_endpoint(self):
        """Test the root endpoint"""
        response = requests.get(f"{self.base_url}")
        self.assertEqual(response.status_code, 200)
        print(f"✅ Root endpoint test passed")

    def test_02_register_endpoint(self):
        """Test the register endpoint"""
        register_data = {
            "username": self.username,
            "password": self.password,
            "email": f"{self.username}@example.com"
        }
        
        response = requests.post(f"{self.base_url}/api/auth/register", json=register_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("session_token", data)
        self.assertIn("user_id", data)
        
        # Save session token and user_id for future tests
        self.session_token = data["session_token"]
        self.user_id = data["user_id"]
        
        print(f"✅ Register endpoint test passed - Created user {self.username}")
        
    def test_03_login_endpoint(self):
        """Test the login endpoint"""
        login_data = {
            "username": self.username,
            "password": self.password
        }
        
        response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("session_token", data)
        
        # Update session token
        self.session_token = data["session_token"]
        
        print(f"✅ Login endpoint test passed - Logged in as {self.username}")

    def test_04_current_user_endpoint(self):
        """Test the current user endpoint"""
        response = requests.get(f"{self.base_url}/api/user/current?session_token={self.session_token}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["user_id"], self.user_id)
        self.assertEqual(data["username"], self.username)
        
        print(f"✅ Current user endpoint test passed")

    def test_05_refresh_jobs_endpoint(self):
        """Test the refresh jobs endpoint to ensure we have jobs data"""
        response = requests.post(f"{self.base_url}/api/jobs/refresh?session_token={self.session_token}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("count", data)
        print(f"✅ Jobs refresh endpoint test passed - Refreshed {data['count']} jobs")
        
        # Wait a moment for jobs to be processed
        time.sleep(1)

    def test_06_jobs_endpoint(self):
        """Test the jobs endpoint"""
        response = requests.get(f"{self.base_url}/api/jobs?session_token={self.session_token}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("jobs", data)
        
        # Check if jobs exist, but don't fail if empty (API might be down)
        job_count = len(data["jobs"])
        if job_count > 0:
            print(f"✅ Jobs endpoint test passed - Found {job_count} jobs")
        else:
            print(f"⚠️ Jobs endpoint returned 0 jobs - API might be unavailable")
            
        return data["jobs"]

    def test_07_job_apply_endpoint(self):
        """Test the job apply endpoint"""
        # First get jobs
        jobs = self.test_06_jobs_endpoint()
        
        if not jobs:
            print("⚠️ Skipping job apply test - No jobs available")
            self.skipTest("No jobs available")
            return
            
        job_id = jobs[0]["id"]
        
        # Apply to the job
        response = requests.post(
            f"{self.base_url}/api/jobs/{job_id}/apply?session_token={self.session_token}"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("application", data)
        print(f"✅ Job apply endpoint test passed")

    def test_05_applications_endpoint(self):
        """Test the applications endpoint"""
        response = requests.get(f"{self.base_url}/api/applications", params={"user_id": self.user_id})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("applications", data)
        
        # We don't require applications to exist, just check the endpoint works
        print(f"✅ Applications endpoint test passed - Found {len(data['applications'])} applications")

    def test_06_savings_endpoint(self):
        """Test the savings endpoint"""
        response = requests.get(f"{self.base_url}/api/savings", params={"user_id": self.user_id})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("current_amount", data)
        self.assertIn("target_amount", data)
        self.assertIn("progress_percentage", data)
        print(f"✅ Savings endpoint test passed - Current: ${data['current_amount']}, Target: ${data['target_amount']}")
        
        return data

    def test_07_update_savings_endpoint(self):
        """Test updating savings"""
        new_amount = 1000.0
        response = requests.post(
            f"{self.base_url}/api/savings/update", 
            params={"user_id": self.user_id, "amount": new_amount}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("new_amount", data)
        self.assertEqual(data["new_amount"], new_amount)
        print(f"✅ Update savings endpoint test passed - New amount: ${new_amount}")
        
        # Verify the update
        updated_savings = self.test_06_savings_endpoint()
        self.assertEqual(updated_savings["current_amount"], new_amount)

    def test_08_tasks_endpoint(self):
        """Test the tasks endpoint"""
        response = requests.get(f"{self.base_url}/api/tasks", params={"user_id": self.user_id})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("tasks", data)
        print(f"✅ Tasks endpoint test passed - Found {len(data['tasks'])} tasks")
        
        return data["tasks"]

    def test_09_create_task_endpoint(self):
        """Test creating a task"""
        task_data = {
            "title": "Test Task",
            "description": "This is a test task",
            "priority": "high",
            "category": "testing"
        }
        
        response = requests.post(
            f"{self.base_url}/api/tasks", 
            json=task_data,
            params={"user_id": self.user_id}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("task", data)
        self.assertEqual(data["task"]["title"], task_data["title"])
        print(f"✅ Create task endpoint test passed")
        
        return data["task"]

    def test_10_complete_task_endpoint(self):
        """Test completing a task"""
        # Create a task first
        task = self.test_09_create_task_endpoint()
        task_id = task["id"]
        
        # Complete the task
        response = requests.put(
            f"{self.base_url}/api/tasks/{task_id}/complete", 
            params={"user_id": self.user_id}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("points_earned", data)
        print(f"✅ Complete task endpoint test passed - Points earned: {data['points_earned']}")

    def test_11_dashboard_stats_endpoint(self):
        """Test the dashboard stats endpoint"""
        response = requests.get(f"{self.base_url}/api/dashboard/stats", params={"user_id": self.user_id})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("total_applications", data)
        self.assertIn("interviews_scheduled", data)
        self.assertIn("savings_progress", data)
        print(f"✅ Dashboard stats endpoint test passed")

    def test_12_achievements_endpoint(self):
        """Test the achievements endpoint"""
        response = requests.get(f"{self.base_url}/api/achievements", params={"user_id": self.user_id})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("achievements", data)
        print(f"✅ Achievements endpoint test passed - Found {len(data['achievements'])} achievements")
        
        return data["achievements"]
        
    def test_13_achievement_unlock_endpoint(self):
        """Test the achievement unlock endpoint"""
        # First get achievements
        achievements = self.test_12_achievements_endpoint()
        
        # Find a locked achievement
        locked_achievements = [a for a in achievements if not a["unlocked"]]
        if not locked_achievements:
            print("⚠️ No locked achievements found to test unlock endpoint")
            self.skipTest("No locked achievements available")
            return
            
        achievement_id = locked_achievements[0]["id"]
        
        # Unlock the achievement
        response = requests.post(
            f"{self.base_url}/api/achievements/{achievement_id}/unlock",
            params={"user_id": self.user_id}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("achievement", data)
        self.assertTrue(data["achievement"]["unlocked"])
        print(f"✅ Achievement unlock endpoint test passed")

    def test_14_terminal_command_endpoint(self):
        """Test the terminal command endpoint"""
        # Test various commands
        commands = ["help", "jobs", "savings", "tasks", "stats", "konami", "matrix", "surprise"]
        
        for command in commands:
            response = requests.post(
                f"{self.base_url}/api/terminal/command", 
                json={"command": command},
                params={"user_id": self.user_id}
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("output", data)
            self.assertTrue(len(data["output"]) > 0)
            
        print(f"✅ Terminal command endpoint test passed - Tested {len(commands)} commands")
        
    def test_15_pong_score_endpoint(self):
        """Test the pong score endpoint"""
        # Submit a score
        score = 150
        response = requests.post(
            f"{self.base_url}/api/pong/score", 
            json={"score": score},
            params={"user_id": self.user_id}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("high_score", data)
        self.assertEqual(data["high_score"], score)
        print(f"✅ Pong score endpoint test passed - Score: {score}")
        
    def test_16_tasks_upload_download_endpoints(self):
        """Test the tasks upload and download endpoints"""
        # First download current tasks
        download_response = requests.get(
            f"{self.base_url}/api/tasks/download",
            params={"user_id": self.user_id}
        )
        self.assertEqual(download_response.status_code, 200)
        self.assertEqual(download_response.headers["Content-Type"], "application/json")
        
        # Prepare tasks for upload
        tasks_data = [
            {
                "title": "Test Task 1",
                "description": "This is a test task",
                "status": "todo",
                "priority": "high",
                "category": "testing"
            },
            {
                "title": "Test Task 2",
                "description": "This is another test task",
                "status": "in_progress",
                "priority": "medium",
                "category": "testing"
            }
        ]
        
        # Create a file-like object for upload
        tasks_json = json.dumps(tasks_data)
        tasks_file = io.BytesIO(tasks_json.encode('utf-8'))
        tasks_file.name = 'tasks.json'
        
        # Upload tasks
        files = {'file': tasks_file}
        upload_response = requests.post(
            f"{self.base_url}/api/tasks/upload", 
            files=files,
            params={"user_id": self.user_id}
        )
        self.assertEqual(upload_response.status_code, 200)
        upload_data = upload_response.json()
        self.assertIn("message", upload_data)
        self.assertIn("tasks_count", upload_data)
        self.assertEqual(upload_data["tasks_count"], len(tasks_data))
        
        print(f"✅ Tasks upload/download endpoints test passed")
        
    def test_17_realtime_notifications_endpoint(self):
        """Test the realtime notifications endpoint"""
        response = requests.get(
            f"{self.base_url}/api/realtime/notifications",
            params={"user_id": self.user_id}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("notifications", data)
        print(f"✅ Realtime notifications endpoint test passed - Found {len(data['notifications'])} notifications")
        
    def test_18_user_profile_endpoint(self):
        """Test the user profile endpoint"""
        response = requests.get(
            f"{self.base_url}/api/user/profile",
            params={"user_id": self.user_id}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("user_id", data)
        self.assertEqual(data["user_id"], self.user_id)
        print(f"✅ User profile endpoint test passed")
        
    def test_19_update_user_profile_endpoint(self):
        """Test updating user profile"""
        profile_data = {
            "username": "TestUser",
            "email": "test@example.com",
            "savings_goal": 10000.0
        }
        
        response = requests.put(
            f"{self.base_url}/api/user/profile",
            json=profile_data,
            params={"user_id": self.user_id}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        print(f"✅ Update user profile endpoint test passed")
        
        # Verify the update
        profile_response = requests.get(
            f"{self.base_url}/api/user/profile",
            params={"user_id": self.user_id}
        )
        profile_data = profile_response.json()
        self.assertEqual(profile_data["username"], "TestUser")
        self.assertEqual(profile_data["email"], "test@example.com")
        self.assertEqual(profile_data["savings_goal"], 10000.0)

if __name__ == "__main__":
    print("🧪 Running ThriveRemote API Tests...")
    print(f"🔗 Testing against: {ThriveRemoteAPITester().base_url}")
    
    # Run tests in order
    loader = unittest.TestLoader()
    loader.sortTestMethodsUsing = lambda x, y: 1 if x < y else -1 if x > y else 0
    suite = loader.loadTestsFromTestCase(ThriveRemoteAPITester)
    result = unittest.TextTestRunner().run(suite)
    
    print(f"\n📊 API Tests Summary: {result.testsRun - len(result.errors) - len(result.failures)}/{result.testsRun} tests passed")
    
    if result.wasSuccessful():
        print("✅ All backend API tests passed successfully!")
    else:
        print("❌ Some backend API tests failed. See details above.")
    
    sys.exit(0 if result.wasSuccessful() else 1)
