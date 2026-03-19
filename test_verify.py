import requests
import json
import base64

res = requests.post("http://localhost:2102/_b_a_c_k_e_n_d/Security/login/", json={
    "employeeId": "test_emp_001",
    "password": "test_password"
})

print(res.json())
