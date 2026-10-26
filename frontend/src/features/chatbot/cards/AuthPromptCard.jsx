import React from "react";
import { UserCheck, LogIn, UserPlus, Sparkles, CheckCircle2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useStore } from "../../../store/useStore";

export function AuthPromptCard({ data, onAction }) {
  const navigate = useNavigate();
  const setIsAgentOpen = useStore((state) => state.setIsAgentOpen);

  const title = data?.title || "Sign In to Dukaan";
  const reason =
    data?.reason ||
    data?.message ||
    data?.action_reason ||
    "Please sign in or create an account to unlock all Dukaan member privileges.";
  const loginUrl = data?.login_url || "/login";
  const signupUrl = data?.signup_url || "/signup";
  const benefits =
    Array.isArray(data?.benefits) && data.benefits.length > 0
      ? data.benefits
      : [
          "Sync your shopping bag across all devices",
          "Track live order shipments & delivery stages",
          "Unlock member-exclusive bargaining discounts",
        ];

  const handleLoginClick = () => {
    setIsAgentOpen(false);
    navigate(loginUrl);
    if (onAction) onAction("login_click", { url: loginUrl });
  };

  const handleSignupClick = () => {
    setIsAgentOpen(false);
    navigate(signupUrl);
    if (onAction) onAction("signup_click", { url: signupUrl });
  };

  return (
    <div className="w-full mt-3 bg-gradient-to-br from-stone-50 via-white to-stone-50 border border-stone-200/90 rounded-2xl p-4 shadow-xs relative overflow-hidden text-left">
      {/* Decorative accent glow */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-[#C45C26]/5 rounded-full blur-2xl -mr-8 -mt-8 pointer-events-none" />

      {/* Header */}
      <div className="flex items-center justify-between pb-2.5 mb-3 border-b border-stone-200/60 relative z-10">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-full bg-[#C45C26]/10 flex items-center justify-center text-[#C45C26] shadow-xs">
            <UserCheck size={15} />
          </div>
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-stone-900">{title}</h4>
            <span className="text-[10px] text-stone-500 font-medium">Dukaan Member Access</span>
          </div>
        </div>
        <span className="text-[10px] font-bold tracking-widest text-[#C45C26] bg-[#C45C26]/10 px-2 py-0.5 rounded-full border border-[#C45C26]/20">
          VIP ACCESS
        </span>
      </div>

      {/* Reason / Nudge text */}
      <p className="text-xs text-stone-700 leading-relaxed mb-3 relative z-10 font-normal">
        {reason}
      </p>

      {/* Member Benefits List */}
      {benefits.length > 0 && (
        <div className="mb-3.5 bg-stone-100/70 rounded-xl p-2.5 border border-stone-200/50 relative z-10">
          <div className="text-[10px] font-bold uppercase tracking-wider text-stone-500 mb-1.5 flex items-center gap-1">
            <Sparkles size={11} className="text-[#C45C26]" />
            <span>Member Perks Included</span>
          </div>
          <ul className="space-y-1.5">
            {benefits.map((b, idx) => (
              <li key={idx} className="flex items-start gap-1.5 text-[11px] text-stone-700">
                <CheckCircle2 size={13} className="text-emerald-600 flex-shrink-0 mt-0.5" />
                <span className="leading-tight">{b}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* The Two Prominent Interactive Action Buttons */}
      <div className="grid grid-cols-2 gap-2 relative z-10">
        {/* Button 1: Log In */}
        <button
          type="button"
          onClick={handleLoginClick}
          className="w-full py-2.5 px-3 rounded-xl bg-[#C45C26] hover:bg-[#a84a1b] active:scale-[0.98] text-white text-xs font-bold tracking-wider uppercase flex items-center justify-center gap-1.5 shadow-xs transition-all cursor-pointer"
        >
          <LogIn size={13} />
          <span>Log In</span>
        </button>

        {/* Button 2: Sign Up */}
        <button
          type="button"
          onClick={handleSignupClick}
          className="w-full py-2.5 px-3 rounded-xl bg-stone-900 hover:bg-stone-800 active:scale-[0.98] text-white text-xs font-bold tracking-wider uppercase flex items-center justify-center gap-1.5 shadow-xs transition-all cursor-pointer border border-stone-700/60"
        >
          <UserPlus size={13} />
          <span>Sign Up</span>
        </button>
      </div>

      {/* Footer hint */}
      <div className="mt-2.5 pt-2 border-t border-stone-200/50 flex items-center justify-center text-[10px] text-stone-500 relative z-10">
        <span>Tap Log In to access your account or Sign Up to create one</span>
      </div>
    </div>
  );
}
