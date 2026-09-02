import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { useStore } from "../../store/useStore";
import { Input } from "../../components/ui/input";
import { AuthForm } from "./AuthForm";
import { PasswordInput } from "./PasswordInput";
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
    } catch (err) { setError("Signup failed. Email might be in use."); }
  };

  return (
    <AuthForm title="Create Account" error={error} onSubmit={handleSignup} buttonText="Sign Up" linkText="Already have an account?" linkTo="/login" linkLabel="Login">
      <Input placeholder="Full Name" value={name} onChange={(e) => setName(e.target.value)} required />
      <Input placeholder="Email Address" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
      <Input placeholder="Delivery Address / Location" type="text" value={address} onChange={(e) => setAddress(e.target.value)} required />
      <PasswordInput value={password} onChange={(e) => setPassword(e.target.value)} required />
    </AuthForm>
  );
}
