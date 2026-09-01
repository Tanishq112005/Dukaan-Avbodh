import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";
import { useStore } from "../../store/useStore";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";

export function SignupPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [address, setAddress] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
 
  const { login } = useStore();
  const navigate = useNavigate();

  const handleSignup = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.post(`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/auth/signup`, {
        name, identifier: email, address, password, role: "customer"
      });
      login({ name, email, address, id: res.data.user_id, role: res.data.role }, res.data.access_token);
      navigate("/");
    } catch (err) {
      setError("Signup failed. Email might be in use.");
    }
  };

  return (
    <div className="max-w-md mx-auto py-16 px-4">
      <h1 className="text-4xl font-black mb-6 text-center uppercase">Create Account</h1>
      {error && <p className="text-red-500 mb-4 text-center">{error}</p>}
      <form onSubmit={handleSignup} className="space-y-4">
        <Input 
          placeholder="Full Name" 
          value={name} 
          onChange={(e) => setName(e.target.value)} 
          required 
        />
        <Input 
          placeholder="Email Address" 
          type="email" 
          value={email} 
          onChange={(e) => setEmail(e.target.value)} 
          required 
        />
        <Input 
          placeholder="Delivery Address / Location" 
          type="text" 
          value={address} 
          onChange={(e) => setAddress(e.target.value)} 
          required 
        />
        <Input 
          placeholder="Password" 
          type="password" 
          value={password} 
          onChange={(e) => setPassword(e.target.value)} 
          required 
        />
        <Button className="w-full py-6 rounded-full text-lg">Sign Up</Button>
      </form>
      <p className="mt-6 text-center text-gray-500">
        Already have an account? <Link to="/login" className="text-black underline font-bold">Login</Link>
      </p>
    </div>
  );
}
