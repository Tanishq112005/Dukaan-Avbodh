import { useState, useEffect } from "react";
import { useSearchParams, useNavigate, Link } from "react-router-dom";
import { useStore } from "../../store/useStore";
import { authService } from "../../services/authService";
import {
  Bot,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Lock,
  ShoppingBag,
  Tag,
  Truck,
  ArrowRight,
  LogIn,
} from "lucide-react";

export function AgentAuthorizePage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const sessionId = searchParams.get("session_id") || "";
  const queryCode = searchParams.get("code") || "";
  const queryAgent = searchParams.get("agent") || "AI Shopping Assistant";

  const { user, token } = useStore();

  const [loading, setLoading] = useState(true);
  const [sessionData, setSessionData] = useState(null);
  const [error, setError] = useState("");
  const [actionLoading, setActionLoading] = useState(false);
  const [decision, setDecision] = useState(null); // "approved" | "rejected"

  useEffect(() => {
    if (!sessionId) {
      setError("No session ID provided. Please launch authorization from your AI agent.");
      setLoading(false);
      return;
    }

    const fetchSession = async () => {
      try {
        setLoading(true);
        const data = await authService.getAgentSession(sessionId);
        setSessionData(data);
        if (data.status === "approved") {
          setDecision("approved");
        } else if (data.status === "rejected") {
          setDecision("rejected");
        }
      } catch (err) {
        console.error("Failed to load agent session:", err);
        setError(err.message || "Session not found or has expired. Please request a new link.");
      } finally {
        setLoading(false);
      }
    };

    fetchSession();
  }, [sessionId]);

  const handleApprove = async () => {
    if (!sessionId) return;
    setActionLoading(true);
    setError("");

    try {
      await authService.approveAgentSession(sessionId);
      setDecision("approved");
    } catch (err) {
      console.error("Approval error:", err);
      setError(err.message || "Failed to approve session. Please try again.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!sessionId) return;
    setActionLoading(true);
    setError("");

    try {
      await authService.rejectAgentSession(sessionId);
      setDecision("rejected");
    } catch (err) {
      console.error("Reject error:", err);
      setError(err.message || "Failed to reject session.");
    } finally {
      setActionLoading(false);
    }
  };

  const agentDisplayName = sessionData?.agent_name || queryAgent;
  const verificationCode = sessionData?.code || queryCode;

  // Render Loading
  if (loading) {
    return (
      <div className="min-h-[70vh] flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-sm border border-stone-200 p-8 max-w-md w-full text-center">
          <div className="animate-spin w-10 h-10 border-4 border-amber-500 border-t-transparent rounded-full mx-auto mb-4" />
          <h2 className="text-xl font-medium text-stone-900">Loading Authorization Request...</h2>
          <p className="text-stone-500 text-sm mt-1">Connecting with Dukaan Agent Gateway</p>
        </div>
      </div>
    );
  }

  // Render Unauthenticated Prompt
  if (!token || !user) {
    const currentRedirect = encodeURIComponent(window.location.pathname + window.location.search);
    return (
      <div className="min-h-[75vh] flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-sm border border-stone-200 p-8 max-w-md w-full text-center">
          <div className="w-14 h-14 bg-amber-50 text-amber-600 rounded-full flex items-center justify-center mx-auto mb-4 border border-amber-100">
            <Lock className="w-7 h-7" />
          </div>

          <h1 className="text-2xl font-serif text-stone-900 mb-2">Sign In Required</h1>
          <p className="text-stone-600 text-sm mb-6 leading-relaxed">
            <strong className="text-stone-900">{agentDisplayName}</strong> wants to connect to your Dukaan account.
            Please sign in directly on Dukaan to continue safely.
          </p>

          {verificationCode && (
            <div className="bg-stone-50 border border-stone-200 rounded-xl p-3 mb-6">
              <span className="text-xs uppercase tracking-wider text-stone-500 font-medium block">
                Verification Code
              </span>
              <span className="text-lg font-mono font-bold text-stone-800 tracking-wider">
                {verificationCode}
              </span>
            </div>
          )}

          <div className="space-y-3">
            <Link
              to={`/login?redirect=${currentRedirect}`}
              className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-stone-900 text-white rounded-xl hover:bg-stone-800 transition font-medium"
            >
              <LogIn className="w-4 h-4" />
              Sign In to Authorize
            </Link>
            <Link
              to={`/signup?redirect=${currentRedirect}`}
              className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-white border border-stone-300 text-stone-700 rounded-xl hover:bg-stone-50 transition text-sm font-medium"
            >
              Create a New Account
            </Link>
          </div>

          <div className="mt-6 flex items-center justify-center gap-2 text-xs text-stone-500">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>Your password and card details are never shared with AI agents.</span>
          </div>
        </div>
      </div>
    );
  }

  // Render Already Approved
  if (decision === "approved") {
    return (
      <div className="min-h-[75vh] flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-sm border border-stone-200 p-8 max-w-md w-full text-center">
          <div className="w-16 h-16 bg-emerald-50 text-emerald-600 rounded-full flex items-center justify-center mx-auto mb-4 border border-emerald-100 animate-bounce">
            <CheckCircle2 className="w-9 h-9" />
          </div>

          <h2 className="text-2xl font-serif text-stone-900 mb-2">Agent Authorized!</h2>
          <p className="text-stone-600 text-sm mb-6 leading-relaxed">
            <strong className="text-stone-900">{agentDisplayName}</strong> has been granted secure access to your Dukaan
            account (<span className="text-stone-800 font-medium">{user.name || user.email}</span>).
          </p>

          <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 text-left mb-6">
            <h4 className="text-xs font-semibold text-emerald-900 uppercase tracking-wider mb-1">Next Step</h4>
            <p className="text-xs text-emerald-800">
              You can now return to your AI agent chat window (e.g. ChatGPT, Claude) and say:
              <br />
              <strong className="font-mono bg-emerald-100 px-1 py-0.5 rounded text-emerald-950 mt-1 inline-block">
                "I've authorized it!"
              </strong>
            </p>
          </div>

          <button
            onClick={() => window.close()}
            className="w-full py-3 px-4 bg-stone-900 text-white rounded-xl hover:bg-stone-800 transition font-medium text-sm"
          >
            Close Tab
          </button>
        </div>
      </div>
    );
  }

  // Render Rejected
  if (decision === "rejected") {
    return (
      <div className="min-h-[75vh] flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-sm border border-stone-200 p-8 max-w-md w-full text-center">
          <div className="w-16 h-16 bg-rose-50 text-rose-600 rounded-full flex items-center justify-center mx-auto mb-4 border border-rose-100">
            <XCircle className="w-9 h-9" />
          </div>

          <h2 className="text-2xl font-serif text-stone-900 mb-2">Access Denied</h2>
          <p className="text-stone-600 text-sm mb-6 leading-relaxed">
            You declined access for <strong className="text-stone-900">{agentDisplayName}</strong>.
            The AI agent will remain in guest browsing mode with no access to your personal cart or orders.
          </p>

          <button
            onClick={() => navigate("/")}
            className="w-full py-3 px-4 bg-stone-100 text-stone-800 rounded-xl hover:bg-stone-200 transition font-medium text-sm"
          >
            Go to Dukaan Home
          </button>
        </div>
      </div>
    );
  }

  // Render Error
  if (error && !sessionData) {
    return (
      <div className="min-h-[75vh] flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-sm border border-stone-200 p-8 max-w-md w-full text-center">
          <div className="w-14 h-14 bg-amber-50 text-amber-600 rounded-full flex items-center justify-center mx-auto mb-4 border border-amber-100">
            <AlertTriangle className="w-7 h-7" />
          </div>

          <h2 className="text-xl font-serif text-stone-900 mb-2">Authorization Link Expired</h2>
          <p className="text-stone-600 text-sm mb-6">{error}</p>

          <button
            onClick={() => navigate("/")}
            className="w-full py-3 px-4 bg-stone-900 text-white rounded-xl hover:bg-stone-800 transition font-medium text-sm"
          >
            Return to Dukaan
          </button>
        </div>
      </div>
    );
  }

  // Render Standard Consent Dialog
  return (
    <div className="min-h-[85vh] flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-md border border-stone-200 p-8 max-w-lg w-full">
        {/* Header with App + Agent icons */}
        <div className="flex items-center justify-between border-b border-stone-100 pb-5 mb-5">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-amber-50 border border-amber-200 rounded-2xl flex items-center justify-center text-amber-700">
              <Bot className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-stone-900">{agentDisplayName}</h1>
              <p className="text-xs text-stone-500">External AI Shopping Agent</p>
            </div>
          </div>
          <div className="flex items-center gap-1.5 text-xs bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-1 rounded-full font-medium">
            <ShieldCheck className="w-3.5 h-3.5" />
            Verified Gateway
          </div>
        </div>

        {/* User Identity Confirmation */}
        <div className="bg-stone-50 border border-stone-200 rounded-xl p-3.5 mb-5 flex items-center justify-between">
          <div className="text-left">
            <span className="text-xs text-stone-500 block">Signed in as:</span>
            <span className="text-sm font-semibold text-stone-900">
              {user.name || "Dukaan Shopper"}
            </span>
            <span className="text-xs text-stone-500 block">{user.email}</span>
          </div>
          {verificationCode && (
            <div className="text-right">
              <span className="text-xs text-stone-500 uppercase tracking-wider block">Code</span>
              <span className="font-mono font-bold text-stone-800 text-sm bg-white border border-stone-200 px-2 py-0.5 rounded">
                {verificationCode}
              </span>
            </div>
          )}
        </div>

        {/* Description */}
        <p className="text-stone-700 text-sm mb-4 leading-relaxed">
          <strong className="text-stone-900">{agentDisplayName}</strong> is requesting permission to act on your behalf on
          Dukaan. This will allow the agent to:
        </p>

        {/* Scopes List */}
        <div className="space-y-3 mb-6">
          <div className="flex items-start gap-3 p-3 bg-stone-50 rounded-xl border border-stone-100">
            <ShoppingBag className="w-5 h-5 text-amber-600 mt-0.5 shrink-0" />
            <div>
              <h4 className="text-xs font-semibold text-stone-900">Manage Shopping Cart</h4>
              <p className="text-xs text-stone-500">View items, add recommended clothing, and update sizes/quantities.</p>
            </div>
          </div>

          <div className="flex items-start gap-3 p-3 bg-stone-50 rounded-xl border border-stone-100">
            <Tag className="w-5 h-5 text-indigo-600 mt-0.5 shrink-0" />
            <div>
              <h4 className="text-xs font-semibold text-stone-900">Apply AI Bargaining Discounts</h4>
              <p className="text-xs text-stone-500">Negotiate lower prices and unlock member-exclusive promotional bundles.</p>
            </div>
          </div>

          <div className="flex items-start gap-3 p-3 bg-stone-50 rounded-xl border border-stone-100">
            <Truck className="w-5 h-5 text-emerald-600 mt-0.5 shrink-0" />
            <div>
              <h4 className="text-xs font-semibold text-stone-900">Orders & Delivery</h4>
              <p className="text-xs text-stone-500">Use your saved shipping address and track active shipments.</p>
            </div>
          </div>
        </div>

        {/* Security Assurance */}
        <div className="bg-amber-50/70 border border-amber-200/80 rounded-xl p-3 mb-6 flex items-start gap-2.5 text-xs text-amber-900">
          <Lock className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
          <span>
            <strong>Zero-Credential Guarantee:</strong> Your Dukaan account password, credit cards, and payment secrets are
            never shared with the AI agent. You can revoke access at any time.
          </span>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3">
          <button
            type="button"
            onClick={handleReject}
            disabled={actionLoading}
            className="flex-1 py-3 px-4 border border-stone-300 text-stone-700 rounded-xl hover:bg-stone-50 transition font-medium text-sm disabled:opacity-50"
          >
            Deny
          </button>
          <button
            type="button"
            onClick={handleApprove}
            disabled={actionLoading}
            className="flex-1 py-3 px-4 bg-stone-900 text-white rounded-xl hover:bg-stone-800 transition font-medium text-sm flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {actionLoading ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <>
                <span>Approve Access</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

export default AgentAuthorizePage;
