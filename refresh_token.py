import requests, os
from dotenv import load_dotenv
load_dotenv()
r = requests.post('https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
    json={'app_id': os.getenv('FEISHU_APP_ID'), 'app_secret': os.getenv('FEISHU_APP_SECRET')})
d = r.json()
tok = d.get('tenant_access_token', '')
print(f'code={d["code"]}, expire={d.get("expire")}s')

# Now test wiki
h = {'Authorization': f'Bearer {tok}', 'Content-Type': 'application/json'}
space_id = '7624453064019168209'

# List members
r2 = requests.get(f'https://open.feishu.cn/open-apis/wiki/v2/spaces/{space_id}/members', headers=h, params={'page_size': 50})
d2 = r2.json()
print(f'\nMembers: code={d2.get("code")}')
if d2.get('code') == 0:
    items = d2.get('data', {}).get('items', [])
    print(f'成员数: {len(items)}')
    for item in items:
        m = item.get('member', item)
        print(f'  name={m.get("name","?")}, type={m.get("member_type","?")}, role={m.get("member_role","?")}, id={m.get("member_id", m.get("open_id","?"))}')

# Try create node
r3 = requests.post(f'https://open.feishu.cn/open-apis/wiki/v2/spaces/{space_id}/nodes',
    headers=h, json={'obj_type': 'docx', 'title': '测试节点-验证权限-请删除', 'node_type': 'origin'})
d3 = r3.json()
print(f'\nCreate node: code={d3.get("code")}, msg={d3.get("msg")}')
if d3.get('code') == 0:
    print(f'OK! node_token={d3["data"]["node"]["node_token"]}')
else:
    print(json.dumps(d3, ensure_ascii=False)[:300])
