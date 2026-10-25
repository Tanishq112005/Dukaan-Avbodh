import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useStore } from "../../store/useStore";
import { Input } from "../../components/ui/input";
import { AuthForm } from "./AuthForm";
import { PasswordInput } from "./PasswordInput";
import { authService } from "../../services/authService";

export function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useStore();
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const data = await authService.login({ email, password });
      login(
        {
          email,
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
      console.error("Login error:", err);
      setError(err.message || "Invalid credentials. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthForm
      title="Login"
      error={error}
      onSubmit={handleLogin}
      buttonText={loading ? "Logging in..." : "Log In"}
      linkText="Don't have an account?"
      linkTo="/signup"
      linkLabel="Sign Up"
    >
      <Input
        placeholder="Email Address"
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
        disabled={loading}
      />
      <PasswordInput
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
        disabled={loading}
      />
    </AuthForm>
  );
}
