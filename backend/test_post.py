import asyncio
import urllib.request
import json
from urllib.error import HTTPError

def get_token():
    req = urllib.request.Request('http://127.0.0.1:8000/api/v1/auth/login', method='POST')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    data = 'username=admin%40autoworth.ai&password=Admin%4012345'.encode('utf-8')
    try:
        resp = urllib.request.urlopen(req, data=data)
        return json.loads(resp.read())['access_token']
    except Exception as e:
        print("Login failed:", e)
        if isinstance(e, HTTPError):
            print(e.read())
        return None

def test_post(token):
    req = urllib.request.Request('http://127.0.0.1:8000/api/v1/predictions/6d132c0c-cb1e-4633-9dfd-f9e1827cc014/list', method='POST')
    req.add_header('Authorization', f'Bearer {token}')
    req.add_header('Content-Type', 'application/json')
    req.data = b'{}'
    try:
        resp = urllib.request.urlopen(req)
        print("Success:", resp.read())
    except HTTPError as e:
        print("HTTPError:", e.code, e.read().decode())
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    token = get_token()
    if token:
        test_post(token)
