import requests

url = "http://127.0.0.1:5000/detect"

image_path = r"C:\Users\Lina\Pictures\DCIM\катя\обработано\DSC_0120-2.jpg"

with open(image_path, "rb") as img:
    response = requests.post(url, files={"file": img})

print("Status:", response.status_code)
print("Response:")
print(response.json())