import { useState, useEffect, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Input } from "../../components/ui/input";
import { AuthForm } from "./AuthForm";
import { PasswordInput } from "./PasswordInput";
import { authService } from "../../services/authService";
import { Mail, KeyRound, ShieldCheck, CheckCircle2, ArrowLeft, RefreshCw } from "lucide-react";

export function ForgotPasswordPage() {
  const [step, setStep] = useState("request"); // "request" | "otp" | "new_password" | "success"
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState(["", "", "", "", "", ""]);
  const [resetToken, setResetToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [error, setError] = useState("");
  const [infoMessage, setInfoMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [timeLeft, setTimeLeft] = useState(300); // 5 minutes
  const [isResending, setIsResending] = useState(false);

  const otpInputRefs = useRef([]);
  const navigate = useNavigate();

  // 5-minute timer countdown during OTP step
  useEffect(() => {
    let timer;
    if (step === "otp" && timeLeft > 0) {
      timer = setInterval(() => {
        setTimeLeft((prev) => prev - 1);
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [step, timeLeft]);

  const formatTimer = (secs) => {
    const mins = Math.floor(secs / 60);
    const remainder = secs % 60;
    return `${mins.toString().padStart(2, "0")}:${remainder.toString().padStart(2, "0")}`;
  };

  // Step 1: Request 6-digit OTP
  const handleRequestOtp = async (e) => {
    e.preventDefault();
    setError("");
    setInfoMessage("");
    setLoading(true);

    try {
      const res = await authService.requestForgotPasswordOtp({ email });
      setStep("otp");
      setTimeLeft(300);
      setOtp(["", "", "", "", "", ""]);
      setInfoMessage(res.message || "A 6-digit password reset code has been sent to your email.");
      setTimeout(() => {
        if (otpInputRefs.current[0]) {
          otpInputRefs.current[0].focus();
        }
      }, 100);
    } catch (err) {
      console.error("Forgot password request error:", err);
      setError(
        err.response?.data?.detail ||
        err.message ||
        "Could not send reset code. Please ensure your email is correct."
      );
    } finally {
      setLoading(false);
    }
  };

  // OTP field handlers
  const handleOtpChange = (index, value) => {
    if (value.length > 1) {
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

    const cleanDigit = value.replace(/\D/g, "");
    const updated = [...otp];
    updated[index] = cleanDigit;
    setOtp(updated);

    if (cleanDigit && index < 5 && otpInputRefs.current[index + 1]) {
      otpInputRefs.current[index + 1].focus();
    }
  };

  const handleOtpKeyDown = (index, e) => {
    if (e.key === "Backspace" && !otp[index] && index > 0 && otpInputRefs.current[index - 1]) {
      otpInputRefs.current[index - 1].focus();
    }
  };

  // Step 2: Verify OTP
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
      const res = await authService.verifyForgotPasswordOtp({
        email,
        otp: fullOtp,
      });

      setResetToken(res.reset_token);
      setStep("new_password");
      setInfoMessage("Verification code accepted. Please enter your new password.");
    } catch (err) {
      console.error("Forgot password OTP verification error:", err);
      setError(
        err.response?.data?.detail ||
        err.message ||
        "Invalid or expired verification code."
      );
    } finally {
      setLoading(false);
    }
  };

  // Resend OTP
  const handleResend = async () => {
    if (isResending) return;
    setError("");
    setIsResending(true);

    try {
      const res = await authService.requestForgotPasswordOtp({ email });
      setTimeLeft(300);
      setOtp(["", "", "", "", "", ""]);
      setInfoMessage(res.message || "A new 6-digit code has been dispatched to your email.");
      if (otpInputRefs.current[0]) {
        otpInputRefs.current[0].focus();
      }
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        err.message ||
        "Could not resend reset code."
      );
    } finally {
      setIsResending(false);
    }
  };

  // Step 3: Set New Password
  const handleResetPassword = async (e) => {
    e.preventDefault();
    setError("");

    if (newPassword.length < 6) {
      setError("Password must contain at least 6 characters.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setError("Passwords do not match. Please verify both fields.");
      return;
    }

    setLoading(true);

    try {
      await authService.resetPassword({
        email,
        new_password: newPassword,
        reset_token: resetToken,
      });

      setStep("success");
    } catch (err) {
      console.error("Password reset error:", err);
      setError(
        err.response?.data?.detail ||
        err.message ||
        "Failed to update password. Your reset session may have expired."
      );
    } finally {
      setLoading(false);
    }
  };

  // =========================================================================
  // VIEW: SUCCESS CONFIRMATION
  // =========================================================================
  if (step === "success") {
    return (
      <div className="max-w-md mx-auto my-12 px-6 py-10 bg-white border border-stone-200/80 rounded-2xl shadow-sm text-center">
        <div className="h-14 w-14 mx-auto mb-4 bg-emerald-50 border border-emerald-200 rounded-full flex items-center justify-center text-emerald-600">
          <CheckCircle2 className="h-8 w-8" />
        </div>
        <h2 className="text-xl font-serif font-bold text-stone-900 mb-2">Password Reset Successful</h2>
        <p className="text-xs text-stone-500 mb-6 leading-relaxed">
          Your Dukaan account password has been securely updated. You can now log in with your new credentials.
        </p>
        <button
          type="button"
          onClick={() => navigate("/login")}
          className="w-full py-3 bg-stone-900 hover:bg-stone-800 text-white font-semibold text-xs tracking-wide uppercase rounded-xl transition-all shadow-xs cursor-pointer"
        >
          Sign In Now
        </button>
      </div>
    );
  }

  // =========================================================================
  // VIEW 1: REQUEST EMAIL
  // =========================================================================
  if (step === "request") {
    return (
      <AuthForm
        title="Reset Password"
        subtitle="Enter your registered email and we'll dispatch a 6-digit verification code."
        error={error}
        onSubmit={handleRequestOtp}
        buttonText={loading ? "Sending Verification Code..." : "Send Verification Code"}
        linkText="Remember your password?"
        linkTo="/login"
        linkLabel="Back to Login"
      >
        <div>
          <label className="block text-[11px] font-bold uppercase tracking-wider text-stone-500 mb-1.5">
            Registered Email Address
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
      </AuthForm>
    );
  }

  // =========================================================================
  // VIEW 2: 6-DIGIT OTP VERIFICATION
  // =========================================================================
  if (step === "otp") {
    return (
      <AuthForm
        title="Enter Verification Code"
        subtitle={`Enter the 6-digit code sent to ${email}`}
        error={error}
        onSubmit={handleVerifyOtp}
        buttonText={loading ? "Verifying..." : "Verify Code & Proceed"}
        linkText="Remember your password?"
        linkTo="/login"
        linkLabel="Back to Login"
      >
        {infoMessage && (
          <div className="flex items-center gap-2 p-3 bg-emerald-50/80 border border-emerald-200/80 rounded-xl text-xs text-emerald-800">
            <ShieldCheck className="h-4 w-4 text-emerald-600 shrink-0" />
            <p className="leading-relaxed">{infoMessage}</p>
          </div>
        )}

        <div className="flex items-center justify-between px-3.5 py-2.5 bg-stone-50 border border-stone-200/80 rounded-xl text-xs">
          <div className="flex items-center gap-2 truncate">
            <Mail className="h-3.5 w-3.5 text-stone-400 shrink-0" />
            <span className="font-medium text-stone-700 truncate">{email}</span>
          </div>
          <button
            type="button"
            onClick={() => {
              setStep("request");
              setError("");
            }}
            className="text-stone-500 hover:text-stone-900 font-semibold flex items-center gap-1 cursor-pointer shrink-0 ml-2"
          >
            <ArrowLeft className="h-3 w-3" />
            Change
          </button>
        </div>

        <div>
          <label className="block text-[11px] font-bold uppercase tracking-wider text-stone-500 mb-2 text-center">
            Enter 6-Digit Code
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

  // =========================================================================
  // VIEW 3: SET NEW PASSWORD
  // =========================================================================
  return (
    <AuthForm
      title="Create New Password"
      subtitle="Enter a strong new password for your Dukaan account."
      error={error}
      onSubmit={handleResetPassword}
      buttonText={loading ? "Updating Password..." : "Update Password"}
      linkText="Cancel reset?"
      linkTo="/login"
      linkLabel="Return to Login"
    >
      <div>
        <label className="block text-[11px] font-bold uppercase tracking-wider text-stone-500 mb-1.5">
          New Password
        </label>
        <PasswordInput
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          placeholder="At least 6 characters"
          required
          disabled={loading}
        />
      </div>

      <div>
        <label className="block text-[11px] font-bold uppercase tracking-wider text-stone-500 mb-1.5">
          Confirm New Password
        </label>
        <PasswordInput
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          placeholder="Re-type new password"
          required
          disabled={loading}
        />
      </div>
    </AuthForm>
  );
}

export default ForgotPasswordPage;
