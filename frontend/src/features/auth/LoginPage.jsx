import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { useStore } from "../../store/useStore";
import { Input } from "../../components/ui/input";
import { AuthForm } from "./AuthForm";
import { PasswordInput } from "./PasswordInput";
export function LoginPage() {
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const { login } = useStore();
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.post(`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/auth/login`, {
        identifier, password
      });
      login({ email: identifier, id: res.data.user_id, role: res.data.role }, res.data.access_token);
      navigate("/");
    } catch (err) {
       console.error("Login error:", err);
       setError("Invalid credentials. Please try again."); }
  };

  return (
    <AuthForm title="Login" error={error} onSubmit={handleLogin} buttonText="Login In" linkText="Don't have an account?" linkTo="/signup" linkLabel="Sign Up">
      <Input placeholder="Email Address" type="email" value={identifier} onChange={(e) => setIdentifier(e.target.value)} required />
<PasswordInput value={password} onChange={(e) => setPassword(e.target.value)} required />
    </AuthForm>
  );
}
