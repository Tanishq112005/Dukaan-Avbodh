import { Link } from "react-router-dom";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";

export function AuthForm({ title, error, onSubmit, children, buttonText, linkText, linkTo, linkLabel }) {
  return (
    <div className="max-w-md mx-auto py-16 px-4">
      <h1 className="text-4xl font-black mb-6 text-center uppercase">{title}</h1>
      {error && <p className="text-red-500 mb-4 text-center">{error}</p>}
      <form onSubmit={onSubmit} className="space-y-4">
        {children}
        <Button className="w-full py-6 rounded-full text-lg">{buttonText}</Button>
      </form>
      <p className="mt-6 text-center text-gray-500">
        {linkText} <Link to={linkTo} className="text-black underline font-bold">{linkLabel}</Link>
      </p>
    </div>
  );
}
