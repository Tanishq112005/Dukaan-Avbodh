import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useStore } from "../../store/useStore";
import { Input } from "../../components/ui/input";
import { AuthForm } from "./AuthForm";
import { PasswordInput } from "./PasswordInput";
import { authService } from "../../services/authService";
import { Mail } from "lucide-react";

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

  const demoAccounts = [
    {
      label: "Customer Demo",
      onSelect: () => {
        setEmail("customer@dukaan.com");
        setPassword("password123");
      },
    },
    {
      label: "Merchant Demo",
      onSelect: () => {
        setEmail("merchant@dukaan.com");
        setPassword("password123");
      },
    },
  ];

  return (
    <AuthForm
      title="Welcome Back"
      subtitle="Sign in to curate your luxury wardrobe with our real-time AI stylist."
      error={error}
      onSubmit={handleLogin}
      buttonText={loading ? "Authenticating..." : "Log In to Dukaan"}
      linkText="Don't have an account?"
      linkTo="/signup"
      linkLabel="Create an Account"
      demoAccounts={demoAccounts}
    >
      <div>
        <label className="block text-[11px] font-bold uppercase tracking-wider text-stone-500 mb-1.5">
          Email Address
        </label>
        <div className="relative">
          <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-stone-400" />
          <Input
            placeholder="name@example.com"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            disabled={loading}
            className="pl-10 bg-stone-50 hover:bg-stone-50/80 focus-visible:bg-white border-stone-200 rounded-xl text-xs sm:text-sm h-11 transition-all"
          />
        </div>
      </div>

      <div>
        <label className="block text-[11px] font-bold uppercase tracking-wider text-stone-500 mb-1.5">
          Password
        </label>
        <PasswordInput
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Enter your secret password"
          required
          disabled={loading}
        />
      </div>
    </AuthForm>
  );
}
