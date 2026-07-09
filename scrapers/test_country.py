import requests
import os
from dotenv import load_dotenv
load_dotenv()

token = os.getenv('WEBSHARE_API_TOKEN', '')
headers = {'Authorization': f'Token {token}'}

# Test without country filter
resp1 = requests.get('https://proxy.webshare.io/api/v2/proxy/list/', headers=headers, params={'mode': 'direct', 'page_size': 5})
data1 = resp1.json()
print('Without country filter:')
for p in data1.get('results', [])[:5]:
    addr = p.get('proxy_address')
    port = p.get('port')
    country = p.get('country_code')
    print(f'  {addr}:{port} - Country: {country}')

print()

# Test with CA country filter
resp2 = requests.get('https://proxy.webshare.io/api/v2/proxy/list/', headers=headers, params={'mode': 'direct', 'page_size': 5, 'country_code__in': 'CA'})
data2 = resp2.json()
print('With CA country filter (country_code__in=CA):')
for p in data2.get('results', [])[:5]:
    addr = p.get('proxy_address')
    port = p.get('port')
    country = p.get('country_code')
    print(f'  {addr}:{port} - Country: {country}')

print()

# Test with different param name
resp3 = requests.get('https://proxy.webshare.io/api/v2/proxy/list/', headers=headers, params={'mode': 'direct', 'page_size': 5, 'country_code': 'CA'})
data3 = resp3.json()
print('With CA country filter (country_code=CA):')
for p in data3.get('results', [])[:5]:
    addr = p.get('proxy_address')
    port = p.get('port')
    country = p.get('country_code')
    print(f'  {addr}:{port} - Country: {country}')
