import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useStore } from "../../store/useStore";
import { Input } from "../../components/ui/input";
import { AuthForm } from "./AuthForm";
import { PasswordInput } from "./PasswordInput";
import { authService } from "../../services/authService";

export function SignupPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [address, setAddress] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("customer");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const { login } = useStore();
  const navigate = useNavigate();

  const handleSignup = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const data = await authService.signup({
        name,
        email,
        password,
        role,
      });

      login(
        {
          name,
          email,
          address,
          id: data.user_id,
          role: data.role,
        },
        data.access_token
      );

      if (data.role === "merchant") {
        navigate("/merchant");
      } else {
        navigate("/");
      }
    } catch (err) {
      console.error("Signup error:", err);
      setError(err.message || "Signup failed. Email might already be registered.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthForm
      title="Create Account"
      error={error}
      onSubmit={handleSignup}
      buttonText={loading ? "Creating Account..." : "Sign Up"}
      linkText="Already have an account?"
      linkTo="/login"
      linkLabel="Log In"
    >
      <Input
        placeholder="Full Name"
        value={name}
        onChange={(e) => setName(e.target.value)}
        required
        disabled={loading}
      />
      <Input
        placeholder="Email Address"
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
        disabled={loading}
      />
      <Input
        placeholder="Delivery Address / City"
        type="text"
        value={address}
        onChange={(e) => setAddress(e.target.value)}
        disabled={loading}
      />
      <div className="flex items-center gap-4 text-sm text-stone-600 px-1 py-1">
        <span className="font-medium text-stone-800">Account Type:</span>
        <label className="flex items-center gap-1.5 cursor-pointer">
          <input
            type="radio"
            name="role"
            value="customer"
            checked={role === "customer"}
            onChange={(e) => setRole(e.target.value)}
            disabled={loading}
            className="accent-stone-900"
          />
          <span>Customer</span>
        </label>
        <label className="flex items-center gap-1.5 cursor-pointer">
          <input
            type="radio"
            name="role"
            value="merchant"
            checked={role === "merchant"}
            onChange={(e) => setRole(e.target.value)}
            disabled={loading}
            className="accent-stone-900"
          />
          <span>Merchant</span>
        </label>
      </div>
      <PasswordInput
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
        disabled={loading}
      />
    </AuthForm>
  );
}
