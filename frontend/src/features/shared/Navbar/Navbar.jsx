import { Search as SearchIcon, ShoppingCart, User } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useStore } from "../../../store/useStore";
import { Search } from "../Search/Search";

function NavActions({ cartCount, user, handleAuth }) {
  return (
    <div className="flex items-center space-x-4">
      <SearchIcon className="h-5 w-5 md:hidden text-stone-700" />
      <Link to="/cart" className="relative group">
        <ShoppingCart className="h-5 w-5 text-stone-800 group-hover:text-[#C45C26] transition-colors" />
        {cartCount > 0 && (
          <span className="absolute -top-2 -right-2 bg-[#C45C26] text-white text-[10px] font-bold rounded-full w-4 h-4 flex items-center justify-center">
            {cartCount}
          </span>
        )}
      </Link>
      <div className="flex items-center gap-3">
        {!user ? (
          <>
            <Link to="/login" className="text-sm cursor-pointer font-semibold text-stone-700 hover:text-stone-900">Login</Link>
            <Link to="/signup" className="text-sm cursor-pointer font-semibold bg-stone-900 text-white px-4 py-1.5 rounded-full hover:bg-stone-800 transition">Join</Link>
          </>
        ) : (
          <div onClick={handleAuth} className="w-8 h-8 bg-stone-900 text-white rounded-full flex items-center justify-center font-bold cursor-pointer hover:bg-[#C45C26] transition">
            {user.name ? user.name.charAt(0).toUpperCase() : <User className="w-5 h-5" />}
          </div>
        )}
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
    <header className="sticky top-0 z-50">
      <div className="bg-stone-900 text-[#FBF8F3] text-[11px] tracking-[0.22em] uppercase overflow-hidden">
        <div className="flex whitespace-nowrap animate-marquee py-2">
          <span className="mx-8">Free shipping over ₹999</span>
          <span className="mx-8">AI stylist · tap the chat</span>
          <span className="mx-8">New drop · atelier edit</span>
          <span className="mx-8">Negotiate in-chat · up to a styled deal</span>
          <span className="mx-8">Free shipping over ₹999</span>
          <span className="mx-8">AI stylist · tap the chat</span>
          <span className="mx-8">New drop · atelier edit</span>
          <span className="mx-8">Negotiate in-chat · up to a styled deal</span>
        </div>
      </div>
      <nav className="bg-[#FBF8F3]/90 backdrop-blur-md border-b border-stone-200/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-10">
              <Link to="/" className="font-display text-2xl font-extrabold tracking-tight">DUKKAN</Link>
              <div className="hidden md:flex space-x-7">
                <Link to="/products" className="text-sm font-semibold text-stone-700 hover:text-stone-900">Shop</Link>
                <Link to="/products" className="text-sm font-semibold text-stone-700 hover:text-stone-900">New in</Link>
                <Link to="/merchant" className="text-sm font-semibold text-[#C45C26] hover:text-[#a3481b]">Merchant</Link>
              </div>
            </div>
            <Search searchQuery={searchQuery} setSearchQuery={setSearchQuery} handleSearch={handleSearch} />
            <NavActions cartCount={cartCount} user={user} handleAuth={handleAuth} />
          </div>
        </div>
      </nav>
    </header>
  );
}
