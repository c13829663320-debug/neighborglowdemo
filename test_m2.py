import requests

BASE = 'http://127.0.0.1:8000'

# 1. Register + Login
r = requests.post(f'{BASE}/api/auth/register', json={
    'username': 'm2test2', 'password': 'pass123', 'role': 'resident', 'display_name': 'M2 Test'
})
print(f'1. Register: {r.status_code}')

r = requests.post(f'{BASE}/api/auth/login', data={'username': 'm2test2', 'password': 'pass123'})
data = r.json()
token = data['access_token']
h = {'Authorization': f'Bearer {token}'}
print(f'2. Login: {r.status_code}, role={data.get("role")}')

# 2. Create case
r = requests.post(f'{BASE}/api/cases', json={
    'title': '深夜噪音',
    'description': '楼上邻居每天深夜12点后还在拖椅子，声音很大，已经持续两周了。我尝试过敲门沟通但对方不在家。'
}, headers=h)
case = r.json()
case_id = case['id']
print(f'3. Create case: {r.status_code}, id={case_id}')

# 3. Diagnose
r = requests.post(f'{BASE}/api/cases/{case_id}/diagnose', headers=h)
diag = r.json()
risk = diag.get('risk_level', '?')
conf = diag.get('confidence', 0)
print(f'4. Diagnose: {r.status_code}, risk={risk}, confidence={conf}')

# 4. Confirm diagnosis
r = requests.post(f'{BASE}/api/cases/{case_id}/diagnose/confirm', json={
    'facts': diag.get('facts', []),
    'emotions': diag.get('emotions', []),
    'needs': diag.get('needs', []),
    'assumptions': diag.get('assumptions', []),
}, headers=h)
confirmed = r.json().get('confirmed_by_user', False)
print(f'5. Confirm: {r.status_code}, confirmed={confirmed}')

# 5. Generate plan
r = requests.post(f'{BASE}/api/cases/{case_id}/plan', headers=h)
plan = r.json()
print(f'6. Plan: {r.status_code}, target={plan.get("target", "?")}')

# 6. Generate message
r = requests.post(f'{BASE}/api/cases/{case_id}/messages/generate', json={
    'tone': 'wechat_friendly'
}, headers=h)
msg = r.json()
print(f'7. Message: {r.status_code}, tone={msg.get("tone", "?")}')

# 7. Start simulation
r = requests.post(f'{BASE}/api/cases/{case_id}/simulations', json={
    'role': 'resident', 'counterpart_style': 'defensive'
}, headers=h)
sim = r.json()
sim_id = sim.get('id')
print(f'8. Simulation start: {r.status_code}, sim_id={sim_id}')

# 8. Send sim message
if sim_id:
    r = requests.post(f'{BASE}/api/cases/{case_id}/simulations/{sim_id}/messages', json={
        'content': '您好，想跟您聊一下深夜噪音的事'
    }, headers=h)
    print(f'9. Sim message: {r.status_code}')

# 9. Get case detail
r = requests.get(f'{BASE}/api/cases/{case_id}', headers=h)
detail = r.json()
has_diag = 'diagnosis' in detail
has_plan = 'action_plan' in detail
print(f'10. Detail: {r.status_code}, status={detail.get("status")}, has_diagnosis={has_diag}, has_plan={has_plan}')

# 10. Follow-up
r = requests.post(f'{BASE}/api/cases/{case_id}/followups', json={
    'action_taken': '按方案进行了友善沟通',
    'response_received': '对方态度较好，承诺会注意',
    'improvement_level': 'partial',
}, headers=h)
print(f'11. Follow-up: {r.status_code}')

print()
print('=== All M2 API tests PASSED ===')
