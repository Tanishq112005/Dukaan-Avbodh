import { Link } from "react-router-dom";
import { Button } from "../../components/ui/button";
import { AuthShowcase } from "./AuthShowcase";
import { Sparkles, ArrowRight } from "lucide-react";

export function AuthForm({
  title,
  subtitle,
  error,
  onSubmit,
  children,
  buttonText,
  linkText,
  linkTo,
  linkLabel,
  demoAccounts,
}) {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12 lg:py-14">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-10 xl:gap-14 items-stretch">
        {/* Left Column: Authentication Form Panel */}
        <div className="lg:col-span-6 xl:col-span-5 flex flex-col justify-center">
          <div className="w-full max-w-md mx-auto lg:mx-0">
            {/* Dukaan Brand Kicker */}
            <div className="inline-flex items-center gap-2 mb-3">
              <span className="text-xs font-bold tracking-[0.25em] uppercase text-[#C45C26]">
                Dukaan Atelier
              </span>
              <span className="w-1.5 h-1.5 rounded-full bg-[#6e1423]" />
            </div>

            {/* Display Headline */}
            <h1 className="font-display text-3xl sm:text-4xl font-extrabold uppercase tracking-tight text-stone-900 leading-tight mb-2">
              {title}
            </h1>

            {/* Subtitle */}
            <p className="text-stone-500 text-xs sm:text-sm leading-relaxed mb-6">
              {subtitle || "Your personal AI stylist for luxury apparel & real-time bargaining."}
            </p>

            {/* Optional Demo Credentials Helper */}
            {demoAccounts && demoAccounts.length > 0 && (
              <div className="mb-6 p-3 bg-stone-100/90 rounded-2xl border border-stone-200/80 shadow-xs">
                <p className="text-[10px] font-bold uppercase tracking-wider text-stone-500 mb-2 flex items-center gap-1.5">
                  <Sparkles size={11} className="text-[#C45C26]" />
                  <span>Quick Demo Access</span>
                </p>
                <div className="flex flex-wrap gap-2">
                  {demoAccounts.map((account) => (
                    <button
                      key={account.label}
                      type="button"
                      onClick={account.onSelect}
                      className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-white hover:bg-stone-900 text-stone-700 hover:text-white border border-stone-200 transition-all cursor-pointer shadow-xs"
                    >
                      {account.label}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Error Notification */}
            {error && (
              <div className="mb-4 p-3 rounded-xl bg-red-50 border border-red-200 text-red-600 text-xs font-medium animate-fade-in flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-red-500 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Main Interactive Form Card */}
            <form onSubmit={onSubmit} className="space-y-4">
              <div className="bg-white border border-stone-200/90 rounded-2xl p-5 sm:p-6 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.05)] space-y-3.5">
                {children}

                <Button
                  type="submit"
                  className="w-full py-3.5 mt-2 rounded-xl text-xs sm:text-sm font-bold tracking-wider uppercase bg-stone-900 hover:bg-[#6e1423] text-white shadow-md hover:shadow-lg transition-all duration-300 cursor-pointer flex items-center justify-center gap-2"
                >
                  <span>{buttonText}</span>
                  <ArrowRight size={14} />
                </Button>
              </div>
            </form>

            {/* Bottom Switcher */}
            <div className="mt-5 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-stone-500 font-medium">
              <p>
                {linkText}{" "}
                <Link
                  to={linkTo}
                  className="text-stone-900 font-bold hover:text-[#6e1423] underline underline-offset-4 transition-colors"
                >
                  {linkLabel}
                </Link>
              </p>
              {linkTo === "/signup" && (
                <Link
                  to="/forgot-password"
                  className="text-stone-500 hover:text-[#C45C26] transition-colors hover:underline"
                >
                  Forgot your password?
                </Link>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Running Clothes & AI Agent Showcase */}
        <div className="lg:col-span-6 xl:col-span-7 hidden lg:block">
          <AuthShowcase />
        </div>
      </div>
    </div>
  );
}
