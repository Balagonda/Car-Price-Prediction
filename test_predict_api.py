import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# 1. Register
register_data = {
    "email": "test_predict5@example.com",
    "password": "Password123!",
    "first_name": "Test",
    "last_name": "User"
}
res_reg = requests.post(f"{BASE_URL}/auth/register", json=register_data)
print("Register:", res_reg.status_code, res_reg.text)

if res_reg.status_code == 201:
    v_token = res_reg.json()["data"]["verification_token"]
    res_verify = requests.get(f"{BASE_URL}/auth/verify-email?token={v_token}")
    print("Verify:", res_verify.status_code, res_verify.text)

# 2. Login
login_data = {
    "email": "test_predict5@example.com",
    "password": "Password123!"
}
res = requests.post(f"{BASE_URL}/auth/login", json=login_data)
if not res.ok:
    print("Login failed", res.text)
    exit(1)
    
token = res.json()["data"]["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 3. Predict
predict_data = {
  "brand_id": 1,
  "car_model_id": 1,
  "manufacturing_year": 2018,
  "fuel_type": "Petrol",
  "transmission": "Manual",
  "owner_type": "First Owner",
  "seller_type": "Individual",
  "category": "Sedan",
  "kilometers_driven": 50000,
  "engine_cc": 1200,
  "mileage_kmpl": 18.5,
  "seats": 5,
  "max_power_bhp": 85,
  "insurance_status": "Comprehensive"
}
print("Sending prediction request...")
res = requests.post(f"{BASE_URL}/predictions", json=predict_data, headers=headers)
print("Status:", res.status_code)
try:
    print("Response:", json.dumps(res.json(), indent=2))
except:
    print("Response:", res.text)
