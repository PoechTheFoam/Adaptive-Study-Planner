"""
Example client usage for the Adaptive Learning Platform API

Shows how to use the API endpoints in your frontend or integration tests.
"""
import requests
import json
import time
from typing import Dict, Optional

# API Base URL
BASE_URL = "http://127.0.0.1:8000"


class AdaptiveLearningClient:
    """Client for interacting with the Adaptive Learning Platform"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.user_id = None
    
    def create_user(
        self,
        name: str,
        skill_level: str,
        goal: str,
        initial_topic: str
    ) -> Optional[Dict]:
        """Create a new user"""
        response = requests.post(
            f"{self.base_url}/user/create",
            json={
                "name": name,
                "skill_level": skill_level,
                "goal": goal,
                "initial_topic": initial_topic
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.user_id = data["user_id"]
            print(f"✅ User created: {data['name']} (ID: {self.user_id})")
            return data
        else:
            print(f"❌ Error: {response.text}")
            return None
    
    def get_question(self, topic: Optional[str] = None) -> Optional[Dict]:
        """Get a question for the user"""
        if not self.user_id:
            print("❌ User not created yet. Call create_user first.")
            return None
        
        response = requests.post(
            f"{self.base_url}/get_question",
            json={
                "user_id": self.user_id,
                "topic": topic
            }
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error: {response.text}")
            return None
    
    def get_hint(self, exercise_id: str, hint_number: int = 1) -> Optional[str]:
        """Get a hint for a question"""
        if not self.user_id:
            print("❌ User not created yet.")
            return None
        
        response = requests.post(
            f"{self.base_url}/get_hint",
            params={
                "user_id": self.user_id,
                "exercise_id": exercise_id,
                "hint_number": hint_number
            }
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error: {response.text}")
            return None
    
    def submit_answer(
        self,
        exercise_id: str,
        user_answer: str,
        response_time: float,
        hints_used: int = 0
    ) -> Optional[Dict]:
        """Submit an answer to a question"""
        if not self.user_id:
            print("❌ User not created yet.")
            return None
        
        response = requests.post(
            f"{self.base_url}/submit_answer",
            json={
                "user_id": self.user_id,
                "exercise_id": exercise_id,
                "user_answer": user_answer,
                "response_time": response_time,
                "hints_used": hints_used
            }
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error: {response.text}")
            return None
    
    def get_next_action(self) -> Optional[Dict]:
        """Get next recommended action"""
        if not self.user_id:
            print("❌ User not created yet.")
            return None
        
        response = requests.post(
            f"{self.base_url}/next_action",
            params={"user_id": self.user_id}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error: {response.text}")
            return None
    
    def get_profile(self) -> Optional[Dict]:
        """Get user profile"""
        if not self.user_id:
            print("❌ User not created yet.")
            return None
        
        response = requests.get(
            f"{self.base_url}/user/profile",
            params={"user_id": self.user_id}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error: {response.text}")
            return None
    
    def get_progress(self) -> Optional[Dict]:
        """Get user progress across topics"""
        if not self.user_id:
            print("❌ User not created yet.")
            return None
        
        response = requests.get(
            f"{self.base_url}/user/progress",
            params={"user_id": self.user_id}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error: {response.text}")
            return None
    
    def get_topics(self) -> Optional[Dict]:
        """Get available topics"""
        response = requests.get(f"{self.base_url}/topics")
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error: {response.text}")
            return None


def main():
    """Example workflow"""
    print("\n" + "="*70)
    print("🎓 Adaptive Learning Platform - Client Example")
    print("="*70 + "\n")
    
    # Create client
    client = AdaptiveLearningClient()
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        print(f"✅ Server is running!")
    except:
        print(f"❌ Server is not running at {BASE_URL}")
        print(f"   Start the server with: python main.py")
        return
    
    # 1. Create user
    print("\n📝 Step 1: Creating user...")
    user = client.create_user(
        name="Alice",
        skill_level="beginner",
        goal="mastery",
        initial_topic="arithmetic"
    )
    
    if not user:
        print("Failed to create user")
        return
    
    # 2. Get available topics
    print("\n📚 Available topics:")
    topics = client.get_topics()
    if topics:
        print(f"   {', '.join(topics['topics'])}")
    
    # 3. Get a question
    print(f"\n❓ Step 2: Getting question...")
    question = client.get_question()
    
    if not question:
        print("Failed to get question")
        return
    
    print(f"   Topic: {question['topic']}")
    print(f"   Difficulty: {question['difficulty']}")
    print(f"   Question: {question['question']}")
    print(f"   Available hints: {question['hints_available']}")
    
    exercise_id = question['exercise_id']
    
    # 4. Optionally get a hint
    print(f"\n💡 Step 3: Getting hint...")
    hint = client.get_hint(exercise_id, hint_number=1)
    if hint:
        print(f"   Hint: {hint['hint']}")
    
    # 5. Submit answer (example)
    print(f"\n✍️  Step 4: Submitting answer...")
    # Simulate user thinking and answering
    time.sleep(1)  # Simulate thinking time
    response_time = 5.0  # seconds
    
    result = client.submit_answer(
        exercise_id=exercise_id,
        user_answer="42",  # Example answer
        response_time=response_time,
        hints_used=1
    )
    
    if result:
        print(f"   Correct: {result['is_correct']}")
        print(f"   Feedback: {result['feedback']}")
        print(f"   Mastery Score: {result['mastery_score']:.1f}%")
        print(f"   Explanation: {result['explanation'][:100]}...")
    
    # 6. Get next action
    print(f"\n🤖 Step 5: Getting next action recommendation...")
    next_action = client.get_next_action()
    if next_action:
        print(f"   Action: {next_action['action']}")
        print(f"   Recommended Difficulty: {next_action['recommended_difficulty']}")
        print(f"   Feedback: {next_action['feedback']}")
    
    # 7. Check profile
    print(f"\n👤 Step 6: Checking user profile...")
    profile = client.get_profile()
    if profile:
        print(f"   Name: {profile['name']}")
        print(f"   Current Topic: {profile['current_topic']}")
        print(f"   Current Difficulty: {profile['current_difficulty']}")
        print(f"   Overall Mastery: {profile['overall_mastery']:.1f}%")
    
    # 8. Check progress
    print(f"\n📈 Step 7: Checking progress...")
    progress = client.get_progress()
    if progress:
        print(f"   Overall Mastery: {progress['overall_mastery']:.1f}%")
        if progress['topics']:
            for topic in progress['topics']:
                print(f"   - {topic['topic']}: {topic['accuracy']} accuracy")
    
    print("\n" + "="*70)
    print("✅ Example workflow completed!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
