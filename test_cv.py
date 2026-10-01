import httpx
import asyncio

async def test_cv_analyze():
    # We need a token. We can create a user or just use a dummy request to see what 422 we get.
    # Without a token, we might get 401. But let's try to bypass or login if needed.
    # Actually, we can just send the request. If it gives 401, we need to login.
    # Let's login first.
    async with httpx.AsyncClient() as client:
        # We saw from test_predict_api.py that it creates a user or logs in.
        # Let's run test_predict_api.py logic to get token.
        res = await client.post("http://127.0.0.1:8000/api/v1/auth/register", json={
            "email": "test_cv@test.com",
            "password": "Password123!",
            "first_name": "Test",
            "last_name": "User"
        })
        if res.status_code == 409:
            res = await client.post("http://127.0.0.1:8000/api/v1/auth/login", data={
                "username": "test_cv@test.com",
                "password": "Password123!"
            })
            token = res.json()["access_token"]
        else:
            token = res.json()["data"]["access_token"]
            
        # Create a dummy prediction to get an ID
        pred_res = await client.post("http://127.0.0.1:8000/api/v1/predictions", json={
            "brand_id": 7,
            "car_model_id": 106,
            "manufacturing_year": 2018,
            "fuel_type": "PETROL",
            "transmission": "AUTOMATIC",
            "owner_type": "FIRST",
            "seller_type": "INDIVIDUAL",
            "category": "SEDAN",
            "kilometers_driven": 50000,
            "insurance_status": "COMPREHENSIVE"
        }, headers={"Authorization": f"Bearer {token}"})
        
        pred_id = pred_res.json()["data"]["id"]
        print("Prediction ID:", pred_id)
        
        # Now try to hit /cv/analyze with httpx.
        # httpx handles multipart correctly.
        files = {'front_image': ('test.jpg', b'dummy content', 'image/jpeg')}
        data = {'prediction_id': pred_id}
        
        cv_res = await client.post("http://127.0.0.1:8000/api/v1/cv/analyze", data=data, files=files, headers={"Authorization": f"Bearer {token}"})
        print("CV Status:", cv_res.status_code)
        print("CV Response:", cv_res.text)

if __name__ == "__main__":
    asyncio.run(test_cv_analyze())
