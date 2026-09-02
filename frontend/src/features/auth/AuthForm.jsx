import { Link } from "react-router-dom";
import { Button } from "../../components/ui/button";

export function AuthForm({ title, error, onSubmit, children, buttonText, linkText, linkTo, linkLabel }) {
  return (
    <div className="max-w-md mx-auto py-16 px-4">
      <p className="text-center text-[11px] tracking-[0.22em] uppercase text-[#C45C26] font-bold mb-3">Dukaan</p>
      <h1 className="font-display text-4xl font-extrabold mb-6 text-center uppercase">{title}</h1>
      {error && <p className="text-red-500 mb-4 text-center">{error}</p>}
      <form onSubmit={onSubmit} className="space-y-4 bg-white border border-stone-200 rounded-[28px] p-6 shadow-sm">
        {children}
        <Button className="w-full py-6 rounded-full text-lg bg-stone-900 hover:bg-stone-800">{buttonText}</Button>
      </form>
      <p className="mt-6 text-center text-stone-500">
        {linkText} <Link to={linkTo} className="text-stone-900 underline font-bold">{linkLabel}</Link>
      </p>
    </div>
  );
}
