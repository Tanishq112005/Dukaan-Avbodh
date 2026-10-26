import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useStore } from "../../store/useStore";
import { Input } from "../../components/ui/input";
import { AuthForm } from "./AuthForm";
import { PasswordInput } from "./PasswordInput";
import { authService } from "../../services/authService";
import { User, Mail, MapPin, ShoppingBag, Store } from "lucide-react";

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
      subtitle="Step into the future of luxury commerce with real-time AI styling."
      error={error}
      onSubmit={handleSignup}
      buttonText={loading ? "Creating Account..." : "Create My Dukaan Account"}
      linkText="Already have an account?"
      linkTo="/login"
      linkLabel="Log In"
    >
      <div>
        <label className="block text-[11px] font-bold uppercase tracking-wider text-stone-500 mb-1.5">
          Full Name
        </label>
        <div className="relative">
          <User className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-stone-400" />
          <Input
            placeholder="e.g. Alex Morgan"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            disabled={loading}
            className="pl-10 bg-stone-50 hover:bg-stone-50/80 focus-visible:bg-white border-stone-200 rounded-xl text-xs sm:text-sm h-11 transition-all"
          />
        </div>
      </div>

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
          Delivery Address / City
        </label>
        <div className="relative">
          <MapPin className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-stone-400" />
          <Input
            placeholder="e.g. Bandra West, Mumbai"
            type="text"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            disabled={loading}
            className="pl-10 bg-stone-50 hover:bg-stone-50/80 focus-visible:bg-white border-stone-200 rounded-xl text-xs sm:text-sm h-11 transition-all"
          />
        </div>
      </div>

      {/* Account Type Selector Tab */}
      <div>
        <label className="block text-[11px] font-bold uppercase tracking-wider text-stone-500 mb-1.5">
          Account Role
        </label>
        <div className="grid grid-cols-2 gap-2">
          <button
            type="button"
            onClick={() => setRole("customer")}
            disabled={loading}
            className={`flex items-center gap-2 p-2.5 rounded-xl border text-xs font-semibold transition-all cursor-pointer ${
              role === "customer"
                ? "bg-stone-900 text-white border-stone-900 shadow-xs"
                : "bg-stone-50 text-stone-700 border-stone-200 hover:bg-stone-100"
            }`}
          >
            <ShoppingBag size={14} className={role === "customer" ? "text-amber-400" : "text-stone-400"} />
            <div className="text-left">
              <p className="leading-tight">Customer</p>
              <p className={`text-[9px] ${role === "customer" ? "text-stone-300" : "text-stone-400"}`}>Shop & Bargain</p>
            </div>
          </button>

          <button
            type="button"
            onClick={() => setRole("merchant")}
            disabled={loading}
            className={`flex items-center gap-2 p-2.5 rounded-xl border text-xs font-semibold transition-all cursor-pointer ${
              role === "merchant"
                ? "bg-stone-900 text-white border-stone-900 shadow-xs"
                : "bg-stone-50 text-stone-700 border-stone-200 hover:bg-stone-100"
            }`}
          >
            <Store size={14} className={role === "merchant" ? "text-amber-400" : "text-stone-400"} />
            <div className="text-left">
              <p className="leading-tight">Merchant</p>
              <p className={`text-[9px] ${role === "merchant" ? "text-stone-300" : "text-stone-400"}`}>Seller Studio</p>
            </div>
          </button>
        </div>
      </div>

      <div>
        <label className="block text-[11px] font-bold uppercase tracking-wider text-stone-500 mb-1.5">
          Create Password
        </label>
        <PasswordInput
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Choose a strong password"
          required
          disabled={loading}
        />
      </div>
    </AuthForm>
  );
}
