import requests
import unittest
import sys
import json
import io

class ThriveRemoteAPITester(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(ThriveRemoteAPITester, self).__init__(*args, **kwargs)
        self.base_url = "https://48d504fc-72cd-4ce7-9458-aaa85b7c09c6.preview.emergentagent.com"
        self.tests_run = 0
        self.tests_passed = 0

    def test_root_endpoint(self):
        """Test the root endpoint"""
        response = requests.get(f"{self.base_url}")
        self.assertEqual(response.status_code, 200)
        print(f"✅ Root endpoint test passed")

    def test_jobs_endpoint(self):
        """Test the jobs endpoint"""
        response = requests.get(f"{self.base_url}/api/jobs")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("jobs", data)
        self.assertTrue(len(data["jobs"]) > 0)
        print(f"✅ Jobs endpoint test passed - Found {len(data['jobs'])} jobs")

    def test_applications_endpoint(self):
        """Test the applications endpoint"""
        response = requests.get(f"{self.base_url}/api/applications")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("applications", data)
        self.assertTrue(len(data["applications"]) > 0)
        print(f"✅ Applications endpoint test passed - Found {len(data['applications'])} applications")

    def test_savings_endpoint(self):
        """Test the savings endpoint"""
        response = requests.get(f"{self.base_url}/api/savings")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("current_amount", data)
        self.assertIn("target_amount", data)
        self.assertIn("progress_percentage", data)
        print(f"✅ Savings endpoint test passed - Current: ${data['current_amount']}, Target: ${data['target_amount']}")

    def test_tasks_endpoint(self):
        """Test the tasks endpoint"""
        response = requests.get(f"{self.base_url}/api/tasks")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("tasks", data)
        self.assertTrue(len(data["tasks"]) > 0)
        print(f"✅ Tasks endpoint test passed - Found {len(data['tasks'])} tasks")

    def test_dashboard_stats_endpoint(self):
        """Test the dashboard stats endpoint"""
        response = requests.get(f"{self.base_url}/api/dashboard/stats")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("total_applications", data)
        self.assertIn("interviews_scheduled", data)
        self.assertIn("savings_progress", data)
        print(f"✅ Dashboard stats endpoint test passed")

    def test_job_apply_endpoint(self):
        """Test the job apply endpoint"""
        # First get a job ID
        jobs_response = requests.get(f"{self.base_url}/api/jobs")
        jobs_data = jobs_response.json()
        job_id = jobs_data["jobs"][0]["id"]
        
        # Apply to the job
        response = requests.post(f"{self.base_url}/api/jobs/{job_id}/apply")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("application", data)
        print(f"✅ Job apply endpoint test passed")
        
    def test_achievements_endpoint(self):
        """Test the achievements endpoint"""
        response = requests.get(f"{self.base_url}/api/achievements")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("achievements", data)
        self.assertTrue(len(data["achievements"]) > 0)
        print(f"✅ Achievements endpoint test passed - Found {len(data['achievements'])} achievements")
        
    def test_achievement_unlock_endpoint(self):
        """Test the achievement unlock endpoint"""
        # First get an achievement ID
        achievements_response = requests.get(f"{self.base_url}/api/achievements")
        achievements_data = achievements_response.json()
        # Find a locked achievement
        locked_achievements = [a for a in achievements_data["achievements"] if not a["unlocked"]]
        if locked_achievements:
            achievement_id = locked_achievements[0]["id"]
            
            # Unlock the achievement
            response = requests.post(f"{self.base_url}/api/achievements/{achievement_id}/unlock")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("message", data)
            self.assertIn("achievement", data)
            self.assertTrue(data["achievement"]["unlocked"])
            print(f"✅ Achievement unlock endpoint test passed")
        else:
            print("⚠️ No locked achievements found to test unlock endpoint")
            
    def test_terminal_command_endpoint(self):
        """Test the terminal command endpoint"""
        # Test various commands
        commands = ["help", "jobs", "savings", "tasks", "stats", "konami", "matrix", "surprise"]
        
        for command in commands:
            response = requests.post(
                f"{self.base_url}/api/terminal/command", 
                json={"command": command}
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("output", data)
            self.assertTrue(len(data["output"]) > 0)
            
        print(f"✅ Terminal command endpoint test passed - Tested {len(commands)} commands")
        
    def test_pong_score_endpoint(self):
        """Test the pong score endpoint"""
        # Get current high score
        stats_response = requests.get(f"{self.base_url}/api/dashboard/stats")
        stats_data = stats_response.json()
        current_high_score = stats_data["pong_high_score"]
        
        # Submit a new score
        new_score = current_high_score + 10
        response = requests.post(
            f"{self.base_url}/api/pong/score", 
            json={"score": new_score}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("high_score", data)
        self.assertEqual(data["high_score"], new_score)
        print(f"✅ Pong score endpoint test passed - New high score: {new_score}")
        
    def test_tasks_upload_download_endpoints(self):
        """Test the tasks upload and download endpoints"""
        # First download current tasks
        download_response = requests.get(f"{self.base_url}/api/tasks/download")
        self.assertEqual(download_response.status_code, 200)
        self.assertEqual(download_response.headers["Content-Type"], "application/json")
        
        # Prepare tasks for upload
        tasks_data = [
            {
                "id": "test-task-1",
                "title": "Test Task 1",
                "description": "This is a test task",
                "status": "todo",
                "priority": "high",
                "category": "testing",
                "created_date": "2025-03-15"
            },
            {
                "id": "test-task-2",
                "title": "Test Task 2",
                "description": "This is another test task",
                "status": "in_progress",
                "priority": "medium",
                "category": "testing",
                "created_date": "2025-03-15"
            }
        ]
        
        # Create a file-like object for upload
        tasks_json = json.dumps(tasks_data)
        tasks_file = io.BytesIO(tasks_json.encode('utf-8'))
        tasks_file.name = 'tasks.json'
        
        # Upload tasks
        files = {'file': tasks_file}
        upload_response = requests.post(f"{self.base_url}/api/tasks/upload", files=files)
        self.assertEqual(upload_response.status_code, 200)
        upload_data = upload_response.json()
        self.assertIn("message", upload_data)
        self.assertIn("tasks_count", upload_data)
        self.assertEqual(upload_data["tasks_count"], len(tasks_data))
        
        print(f"✅ Tasks upload/download endpoints test passed")
        
    def test_realtime_notifications_endpoint(self):
        """Test the realtime notifications endpoint"""
        response = requests.get(f"{self.base_url}/api/realtime/notifications")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("notifications", data)
        print(f"✅ Realtime notifications endpoint test passed - Found {len(data['notifications'])} notifications")

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(ThriveRemoteAPITester)
    result = unittest.TextTestRunner().run(suite)
    
    print(f"\n📊 API Tests Summary: {result.testsRun - len(result.errors) - len(result.failures)}/{result.testsRun} tests passed")
    sys.exit(0 if result.wasSuccessful() else 1)
