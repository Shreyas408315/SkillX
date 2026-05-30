import requests
import json

# Test resume parsing
resume_text = '''John Doe
Software Engineer
5 years experience in Python, JavaScript, React
Skills: Python, JavaScript, React, Node.js, SQL'''

try:
    response = requests.post('http://127.0.0.1:8000/api/resume/parse', json={'resume_text': resume_text}, timeout=30)
    print('Resume Parse Status:', response.status_code)
    if response.status_code == 200:
        result = response.json()
        print('Parsed Resume:')
        print(json.dumps(result, indent=2))
    else:
        print('Error:', response.text)
except Exception as e:
    print('Exception:', str(e))

# Test matching
job_description = '''Senior Software Engineer
Required: Python, JavaScript, React, SQL
Preferred: Node.js, AWS'''

try:
    response = requests.post('http://127.0.0.1:8000/api/match/score', json={
        'resume_text': resume_text,
        'job_description': job_description
    }, timeout=30)
    print('\nMatch Score Status:', response.status_code)
    if response.status_code == 200:
        result = response.json()
        print('Match Result:')
        print(json.dumps(result, indent=2))
    else:
        print('Error:', response.text)
except Exception as e:
    print('Exception:', str(e))

# Test gap analysis
try:
    response = requests.post('http://127.0.0.1:8000/api/gap/analyze', json={
        'target_role': 'Senior Software Engineer',
        'resume_skills': ['Python', 'JavaScript', 'React', 'Node.js', 'SQL'],
        'skill_levels': [
            {'name': 'Python', 'proficiency': 80},
            {'name': 'JavaScript', 'proficiency': 75},
            {'name': 'React', 'proficiency': 70},
            {'name': 'Node.js', 'proficiency': 65},
            {'name': 'SQL', 'proficiency': 70}
        ]
    }, timeout=30)
    print('\nGap Analysis Status:', response.status_code)
    if response.status_code == 200:
        result = response.json()
        print('Gap Analysis Result:')
        print(json.dumps(result, indent=2))
    else:
        print('Error:', response.text)
except Exception as e:
    print('Exception:', str(e))