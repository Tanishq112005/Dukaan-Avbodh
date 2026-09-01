import { Search as SearchIcon, ShoppingCart, User } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useStore } from "../../../store/useStore";
import { Search } from "../Search/Search";

function NavActions({ cartCount, user, handleAuth }) {
  return (
    <div className="flex items-center space-x-4">
      <SearchIcon className="h-6 w-6 md:hidden" />
      <Link to="/cart" className="relative">
        <ShoppingCart className="h-6 w-6" />
        {cartCount > 0 && <span className="absolute -top-2 -right-2 bg-black text-white text-xs rounded-full w-4 h-4 flex items-center justify-center">{cartCount}</span>}
      </Link>
      <div className="flex items-center gap-2">
        {!user ? (
          <>
            <Link to="/login" className="text-sm cursor-pointer font-bold">Login</Link>
            <Link to="/signup" className="text-sm cursor-pointer font-bold ml-2">Sign Up</Link>
          </>
        ) : (
          <div onClick={handleAuth} className="w-8 h-8 bg-green-800 text-white rounded-full flex items-center justify-center font-bold cursor-pointer hover:bg-green-700 transition">
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
    <nav className="sticky top-0 z-50 bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center gap-8">
            <Link to="/" className="text-2xl font-black tracking-tighter">DUKKAN</Link>
            <div className="hidden md:flex space-x-6">
              <Link to="/products" className="text-sm font-medium">Shop</Link>
              <Link to="/products" className="text-sm font-medium">Brands</Link>
              <Link to="/merchant" className="text-sm font-medium text-red-500">Merchant</Link>
            </div>
          </div>
          <Search searchQuery={searchQuery} setSearchQuery={setSearchQuery} handleSearch={handleSearch} />
          <NavActions cartCount={cartCount} user={user} handleAuth={handleAuth} />
        </div>
      </div>
    </nav>
  );
}
