import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useStore } from "../../store/useStore";
import { Input } from "../../components/ui/input";
import { AuthForm } from "./AuthForm";
import { PasswordInput } from "./PasswordInput";
import { authService } from "../../services/authService";
import { User, Mail, MapPin, ShoppingBag, Store, ShieldCheck, ArrowLeft, RefreshCw, KeyRound } from "lucide-react";

export function SignupPage() {
  const [step, setStep] = useState("form"); // "form" | "otp"
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [address, setAddress] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("customer");
  
  // OTP state: 6 separate digits
  const [otp, setOtp] = useState(["", "", "", "", "", ""]);
  const otpInputRefs = useRef([]);

  const [error, setError] = useState("");
  const [infoMessage, setInfoMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [timeLeft, setTimeLeft] = useState(300); // 5 minutes (300 seconds)
  const [isResending, setIsResending] = useState(false);

  const { login, thread_id } = useStore();
  const navigate = useNavigate();

  // 5-minute countdown timer effect during OTP stage
  useEffect(() => {
    let timer;
    if (step === "otp" && timeLeft > 0) {
      timer = setInterval(() => {
        setTimeLeft((prev) => prev - 1);
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [step, timeLeft]);

  // Format seconds to mm:ss
  const formatTimer = (secs) => {
    const mins = Math.floor(secs / 60);
    const remainder = secs % 60;
    return `${mins.toString().padStart(2, "0")}:${remainder.toString().padStart(2, "0")}`;
  };

  // Step 1: Submit details and request 6-digit OTP
  const handleRequestOtp = async (e) => {
    e.preventDefault();
    setError("");
    setInfoMessage("");
    setLoading(true);

    try {
      const res = await authService.requestSignupOtp({
        name,
        email,
        password,
        role,
        address,
        thread_id,
      });

      setStep("otp");
      setTimeLeft(300);
      setOtp(["", "", "", "", "", ""]);
      setInfoMessage(res.message || "A 6-digit code has been sent to your email. Valid for 5 minutes.");
      // Focus first OTP input on next tick
      setTimeout(() => {
        if (otpInputRefs.current[0]) {
          otpInputRefs.current[0].focus();
        }
      }, 100);
    } catch (err) {
      console.error("Signup OTP request error:", err);
      setError(
        err.response?.data?.detail ||
        err.message ||
        "Could not send verification code. Please verify your details."
      );
    } finally {
      setLoading(false);
    }
  };

  // Handle digit input in 6-digit OTP fields
  const handleOtpChange = (index, value) => {
    if (value.length > 1) {
      // If user pasted multi-digit string
      const pastedDigits = value.replace(/\D/g, "").slice(0, 6).split("");
      const updated = [...otp];
      pastedDigits.forEach((d, i) => {
        if (i < 6) updated[i] = d;
      });
      setOtp(updated);
      const nextIdx = Math.min(pastedDigits.length, 5);
      if (otpInputRefs.current[nextIdx]) {
        otpInputRefs.current[nextIdx].focus();
      }
      return;
    }

    // Single digit input
    const cleanDigit = value.replace(/\D/g, "");
    const updated = [...otp];
    updated[index] = cleanDigit;
    setOtp(updated);

    // Auto-advance to next input if digit entered
    if (cleanDigit && index < 5 && otpInputRefs.current[index + 1]) {
      otpInputRefs.current[index + 1].focus();
    }
  };

  // Handle backspace navigation in OTP fields
  const handleOtpKeyDown = (index, e) => {
    if (e.key === "Backspace" && !otp[index] && index > 0 && otpInputRefs.current[index - 1]) {
      otpInputRefs.current[index - 1].focus();
    }
  };

  // Step 2: Verify OTP and activate account
  const handleVerifyOtp = async (e) => {
    e.preventDefault();
    const fullOtp = otp.join("");
    if (fullOtp.length !== 6) {
      setError("Please enter the complete 6-digit verification code.");
      return;
    }

    setError("");
    setInfoMessage("");
    setLoading(true);

    try {
      const data = await authService.verifySignupOtp({
        email,
        otp: fullOtp,
      });

      login(
        {
          name: data.name || name,
          email: data.email || email,
          address: data.address || address,
          id: data.user_id,
          role: data.role || role,
        },
        data.access_token
      );

      if (data.role === "merchant") {
        navigate("/merchant");
      } else {
        navigate("/");
      }
    } catch (err) {
      console.error("OTP verification error:", err);
      setError(
        err.response?.data?.detail ||
        err.message ||
        "Invalid or expired verification code. Please check and retry."
      );
    } finally {
      setLoading(false);
    }
  };

  // Resend fresh OTP
  const handleResend = async () => {
    if (isResending) return;
    setError("");
    setIsResending(true);

    try {
      const res = await authService.resendSignupOtp({ email });
      setTimeLeft(300);
      setOtp(["", "", "", "", "", ""]);
      setInfoMessage(res.message || "A fresh 6-digit code has been dispatched to your email.");
      if (otpInputRefs.current[0]) {
        otpInputRefs.current[0].focus();
      }
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        err.message ||
        "Could not resend OTP. Please try again."
      );
    } finally {
      setIsResending(false);
    }
  };

  // =========================================================================
  // VIEW 1: REGISTRATION FORM
  // =========================================================================
  if (step === "form") {
    return (
      <AuthForm
        title="Create Account"
        subtitle="Step into the future of luxury commerce with real-time AI styling."
        error={error}
        onSubmit={handleRequestOtp}
        buttonText={loading ? "Sending Verification Code..." : "Create My Dukaan Account"}
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

        {/* Account Role Selector */}
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

  // =========================================================================
  // VIEW 2: 6-DIGIT OTP VERIFICATION
  // =========================================================================
  return (
    <AuthForm
      title="Verify Your Email"
      subtitle={`We sent a 6-digit verification code to ${email}`}
      error={error}
      onSubmit={handleVerifyOtp}
      buttonText={loading ? "Verifying Code..." : "Verify & Complete Signup"}
      linkText="Already verified?"
      linkTo="/login"
      linkLabel="Log In"
    >
      {/* Informational Banner */}
      {infoMessage && (
        <div className="flex items-center gap-2 p-3 bg-emerald-50/80 border border-emerald-200/80 rounded-xl text-xs text-emerald-800">
          <ShieldCheck className="h-4 w-4 text-emerald-600 shrink-0" />
          <p className="leading-relaxed">{infoMessage}</p>
        </div>
      )}

      {/* Recipient summary and Change Email action */}
      <div className="flex items-center justify-between px-3.5 py-2.5 bg-stone-50 border border-stone-200/80 rounded-xl text-xs">
        <div className="flex items-center gap-2 truncate">
          <Mail className="h-3.5 w-3.5 text-stone-400 shrink-0" />
          <span className="font-medium text-stone-700 truncate">{email}</span>
        </div>
        <button
          type="button"
          onClick={() => {
            setStep("form");
            setError("");
          }}
          className="text-stone-500 hover:text-stone-900 font-semibold flex items-center gap-1 cursor-pointer shrink-0 ml-2"
        >
          <ArrowLeft className="h-3 w-3" />
          Change
        </button>
      </div>

      {/* 6-Digit OTP Inputs */}
      <div>
        <label className="block text-[11px] font-bold uppercase tracking-wider text-stone-500 mb-2 text-center">
          Enter 6-Digit Verification Code
        </label>
        <div className="flex justify-between items-center gap-2 sm:gap-2.5 max-w-[320px] mx-auto my-2">
          {otp.map((digit, idx) => (
            <input
              key={idx}
              ref={(el) => (otpInputRefs.current[idx] = el)}
              type="text"
              inputMode="numeric"
              maxLength={6}
              value={digit}
              onChange={(e) => handleOtpChange(idx, e.target.value)}
              onKeyDown={(e) => handleOtpKeyDown(idx, e)}
              disabled={loading}
              className="w-10 h-12 sm:w-11 sm:h-13 text-center text-lg sm:text-xl font-bold bg-stone-50 hover:bg-stone-50/90 focus:bg-white border-2 border-stone-200 focus:border-stone-900 rounded-xl outline-none transition-all shadow-xs"
            />
          ))}
        </div>
      </div>

      {/* Expiry Timer and Resend */}
      <div className="flex items-center justify-between text-xs pt-1">
        <div className="flex items-center gap-1.5 text-stone-500">
          <span className="font-mono font-semibold text-stone-800 bg-stone-100 px-2 py-0.5 rounded-md">
            {formatTimer(timeLeft)}
          </span>
          <span className="text-[11px]">{timeLeft > 0 ? "remaining" : "expired"}</span>
        </div>

        <button
          type="button"
          onClick={handleResend}
          disabled={isResending || loading}
          className="flex items-center gap-1 text-stone-600 hover:text-stone-900 font-semibold cursor-pointer disabled:opacity-50"
        >
          <RefreshCw className={`h-3 w-3 ${isResending ? "animate-spin" : ""}`} />
          <span>{isResending ? "Sending..." : "Resend Code"}</span>
        </button>
      </div>
    </AuthForm>
  );
}
