import requests
import unittest
import sys
import json

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

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(ThriveRemoteAPITester)
    result = unittest.TextTestRunner().run(suite)
    
    print(f"\n📊 API Tests Summary: {result.testsRun - len(result.errors) - len(result.failures)}/{result.testsRun} tests passed")
    sys.exit(0 if result.wasSuccessful() else 1)
