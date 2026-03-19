import requests
import json

url = "http://localhost:2102/_b_a_c_k_e_n_d/Security/login/"
payload = {
    "employeeId": "test_emp_001",
    "password": "test_password"
}
# Actually I don't know the exact credentials. Let's just create a test JWT using `jwt_crypter.py` to see what happens.
