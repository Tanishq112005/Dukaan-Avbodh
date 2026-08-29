import { Search, ShoppingCart, User } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { SignedIn, SignedOut, SignInButton, SignUpButton, UserButton } from "@clerk/clerk-react";
import { Input } from "../ui/input";
import { useStore } from "../../store/useStore";

function NavSearch({ searchQuery, setSearchQuery, handleSearch }) {
  return (
    <div className="hidden md:flex flex-1 max-w-md mx-8 relative">
      <Search className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
      <Input placeholder="Search for products..." className="pl-10 bg-gray-100 border-none" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} onKeyDown={handleSearch} />
    </div>
  );
}

function NavActions({ cartCount }) {
  return (
    <div className="flex items-center space-x-4">
      <Search className="h-6 w-6 md:hidden" />
      <Link to="/cart" className="relative">
        <ShoppingCart className="h-6 w-6" />
        {cartCount > 0 && <span className="absolute -top-2 -right-2 bg-black text-white text-xs rounded-full w-4 h-4 flex items-center justify-center">{cartCount}</span>}
      </Link>
      <div className="flex items-center gap-2">
        <SignedOut>
          <SignInButton mode="modal">
            <span className="text-sm cursor-pointer font-bold">Login</span>
          </SignInButton>
          <SignUpButton mode="modal">
            <span className="text-sm cursor-pointer font-bold ml-2">Sign Up</span>
          </SignUpButton>
        </SignedOut>
        <SignedIn>
          <UserButton />
        </SignedIn>
      </div>
    </div>
  );
}

export function Navbar() {
  const { user, logout, cart, searchQuery, setSearchQuery } = useStore();
  const cartCount = cart.reduce((acc, item) => acc + item.qty, 0);
  const navigate = useNavigate();

  const handleAuth = () => {
    if (user) {
      if (window.confirm("Do you want to logout?")) logout();
    } else navigate("/login");
  };

  const handleSearch = (e) => {
    if (e.key === 'Enter') navigate("/products");
  };

  return (
    <nav className="sticky top-0 z-50 bg-white border-b border-gray-200">
      <div className="bg-black text-white text-xs text-center py-2">
        Sign up and get 20% off to your first order. <Link to="/signup" className="underline cursor-pointer">Sign Up Now</Link>
      </div>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center gap-8">
            <Link to="/" className="text-2xl font-black tracking-tighter">SHOP.CO</Link>
            <div className="hidden md:flex space-x-6">
              <Link to="/products" className="text-sm font-medium">Shop</Link>
              <Link to="/products" className="text-sm font-medium">Brands</Link>
              <Link to="/merchant" className="text-sm font-medium text-red-500">Merchant</Link>
            </div>
          </div>
          <NavSearch searchQuery={searchQuery} setSearchQuery={setSearchQuery} handleSearch={handleSearch} />
          <NavActions cartCount={cartCount} />
        </div>
      </div>
    </nav>
  );
}
