import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import styled from "styled-components";
import { jwtDecode } from "jwt-decode";

const Container = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
`;

const FormWrapper = styled.div`
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
  width: 400px;
  text-align: center;
`;

const Title = styled.h2`
  margin-bottom: 1.5rem;
  color: #333;
`;

const Input = styled.input`
  width: 100%;
  padding: 10px;
  margin: 8px 0;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 16px;
`;

const Button = styled.button`
  width: 100%;
  padding: 10px;
  background: rgb(59, 50, 75);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  transition: 0.3s;

  &:hover {
    background: #dd2476;
  }
`;

const Login = () => {
  const [formData, setFormData] = useState({
    employeeId: "",
    password: "",
  });
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.employeeId || !formData.password) {
      setError("Please enter both Employee ID and Password.");
      return;
    }

    try {
      const res = await axios.post("http://127.0.0.1:8000/login/", formData, {
        headers: { "Content-Type": "application/json" },
  
      });

      const { token, user } = res.data;

      localStorage.setItem("token", token);
      localStorage.setItem("user", JSON.stringify(user));

      const decoded = jwtDecode(token);
      console.log("Decoded Token:", decoded);

      navigate("/Profile");
    } catch (err) {
      console.error("Login error:", err.response?.data || err);
      setError(err.response?.data?.message || "Invalid credentials");
    }
  };

  return (
    <Container>
      <FormWrapper>
        <Title>Employee Login</Title>
        {error && <p style={{ color: "red" }}>{error}</p>}
        <form onSubmit={handleSubmit}>
          <Input
            type="text"
            name="employeeId"
            placeholder="Employee ID"
            onChange={handleChange}
            required
          />
          <Input
            type="password"
            name="password"
            placeholder="Password"
            onChange={handleChange}
            required
          />
          <Button type="submit">Sign In</Button>
        </form>
      </FormWrapper>
    </Container>
  );
};

export default Login;
