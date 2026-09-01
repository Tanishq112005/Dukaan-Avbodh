import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";
import { useStore } from "../../store/useStore";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";

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
      setError("Invalid credentials. Please try again.");
    }
  };

  return (
    <div className="max-w-md mx-auto py-16 px-4">
      <h1 className="text-4xl font-black mb-6 text-center uppercase">Login</h1>
      {error && <p className="text-red-500 mb-4 text-center">{error}</p>}
      <form onSubmit={handleLogin} className="space-y-4">
        <Input 
          placeholder="Email Address" 
          type="email" 
          value={identifier} 
          onChange={(e) => setIdentifier(e.target.value)} 
          required 
        />
        <Input 
          placeholder="Password" 
          type="password" 
          value={password} 
          onChange={(e) => setPassword(e.target.value)} 
          required 
        />
        <Button className="w-full py-6 rounded-full text-lg">Sign In</Button>
      </form>
      <p className="mt-6 text-center text-gray-500">
        Don't have an account? <Link to="/signup" className="text-black underline font-bold">Sign Up</Link>
      </p>
    </div>
  );
}
