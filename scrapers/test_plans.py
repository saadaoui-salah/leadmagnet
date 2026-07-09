import requests
import os
from dotenv import load_dotenv
load_dotenv()

token = os.getenv('WEBSHARE_API_TOKEN', '')
headers = {'Authorization': f'Token {token}'}

plan_id = 13768706

# Test with CA country filter
resp = requests.get('https://proxy.webshare.io/api/v2/proxy/list/', headers=headers, params={'mode': 'direct', 'page_size': 10, 'plan_id': plan_id, 'country_code__in': 'CA'})
print(f'With CA filter:')
data = resp.json()
print(f'Total: {data.get("count", 0)}')
for p in data.get('results', [])[:5]:
    addr = p.get('proxy_address')
    port = p.get('port')
    country = p.get('country_code')
    print(f'  {addr}:{port} - {country}')

print()

# Test with US country filter
resp2 = requests.get('https://proxy.webshare.io/api/v2/proxy/list/', headers=headers, params={'mode': 'direct', 'page_size': 5, 'plan_id': plan_id, 'country_code__in': 'US'})
print(f'With US filter:')
data2 = resp2.json()
print(f'Total: {data2.get("count", 0)}')
for p in data2.get('results', [])[:5]:
    addr = p.get('proxy_address')
    port = p.get('port')
    country = p.get('country_code')
    print(f'  {addr}:{port} - {country}')
