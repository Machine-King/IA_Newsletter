import requests

url = "http://localhost:8000/update/all"
data = {
    "username": "your_username",
    "password": "your_password",
    "email": "your_email@example.com",
    "full_name": "Your Full Name",
}

response = requests.post(url, json=data)

print("Status code:", response.status_code)
print("Response body:", response.text)
