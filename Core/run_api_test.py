import os
from fastapi.testclient import TestClient
from main import app

os.environ['GEMINI_API_KEY'] = 'AIzaSyCpYOuWcF40kCu3Ixs968JDUamwwc3gRmc'
client = TestClient(app)

print('health', client.get('/health').json())

user_resp = client.post('/user/create', json={
    'name': 'WebTestUser',
    'skill_level': 'beginner',
    'goal': 'mastery',
    'initial_topic': 'algebra'
})
print('create_user', user_resp.status_code, user_resp.json())
user = user_resp.json()

q_resp = client.post('/get_question', json={'user_id': user['user_id']})
print('get_question', q_resp.status_code, q_resp.json())

if q_resp.status_code == 200:
    q = q_resp.json()
    ans_resp = client.post('/submit_answer', json={
        'user_id': user['user_id'],
        'exercise_id': q['exercise_id'],
        'user_answer': '42',
        'response_time': 12.3,
        'hints_used': 0
    })
    print('submit_answer', ans_resp.status_code, ans_resp.json())

    na_resp = client.post('/next_action', params={'user_id': user['user_id']})
    print('next_action', na_resp.status_code, na_resp.json())
else:
    print('skip submit/next due question generation failure')
