import { useState } from "react";
import { Eye, EyeOff, Lock } from "lucide-react";
import { Input } from "../../components/ui/input";

export function PasswordInput({ value, onChange, placeholder = "Password", disabled, ...props }) {
  const [visible, setVisible] = useState(false);

  return (
    <div className="relative">
      <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-stone-400" />
      <Input
        type={visible ? "text" : "password"}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        disabled={disabled}
        className="pl-10 pr-11 bg-stone-50 hover:bg-stone-50/80 focus-visible:bg-white border-stone-200 rounded-xl text-xs sm:text-sm h-11 transition-all"
        {...props}
      />
      <button
        type="button"
        onClick={() => setVisible((v) => !v)}
        tabIndex={-1}
        className="absolute right-3.5 top-1/2 -translate-y-1/2 text-stone-400 hover:text-stone-700 transition-colors cursor-pointer"
        aria-label={visible ? "Hide password" : "Show password"}
      >
        {visible ? <EyeOff size={16} /> : <Eye size={16} />}
      </button>
    </div>
  );
}
