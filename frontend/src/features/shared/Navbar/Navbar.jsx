import { Search as SearchIcon, ShoppingBag, User } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useStore } from "../../../store/useStore";
import { Search } from "../Search/Search";

function NavActions({ cartCount, user, handleAuth }) {
  return (
    <div className="flex items-center gap-5">
      <SearchIcon className="h-5 w-5 md:hidden text-ink" />
      <Link to="/cart" className="relative">
        <ShoppingBag className="h-5 w-5 text-ink" strokeWidth={1.5} />
        {cartCount > 0 && (
          <span className="absolute -top-2 -right-2 bg-oxblood text-white text-[10px] font-bold rounded-full w-4 h-4 flex items-center justify-center">
            {cartCount}
          </span>
        )}
      </Link>
      <div className="flex items-center gap-4">
        {!user ? (
          <>
            <Link to="/login" className="hidden sm:block text-sm text-ink/70 hover:text-ink">Log in</Link>
            <Link to="/signup" className="text-sm font-semibold bg-ink text-white px-4 py-1.5 hover:bg-oxblood transition-colors">
              Join
            </Link>
          </>
        ) : (
          <div onClick={handleAuth} className="w-8 h-8 border border-ink text-ink rounded-full flex items-center justify-center text-sm font-semibold cursor-pointer hover:bg-ink hover:text-white transition-colors">
            {user.name ? user.name.charAt(0).toUpperCase() : <User className="w-4 h-4" />}
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
    if (e.key === "Enter") navigate("/products");
  };

  const tickerItems = [
    "Free shipping over ₹29999",
    "Talk to the atelier stylist",
    "New drop this week",
    "Negotiate your price, live in chat",
  ];

  return (
    <header className="sticky top-0 z-50 bg-paper">
      <div className="bg-ink text-white text-xs overflow-hidden">
        <div className="flex whitespace-nowrap animate-marquee py-2">
          {[...tickerItems, ...tickerItems].map((item, i) => (
            <span key={i} className="mx-8">{item}</span>
          ))}
        </div>
      </div>
      <nav className="border-b border-hairline">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-[72px]">
            <div className="flex items-center gap-10">
              <Link to="/" className="font-display text-[26px] leading-none tracking-tight">
                Dukaan
              </Link>
              <div className="hidden md:flex gap-8">
                <Link to="/products" className="text-sm text-ink/70 hover:text-ink">Shop</Link>
                <Link to="/products" className="text-sm text-ink/70 hover:text-ink">New in</Link>
                <Link to="/merchant" className="text-sm text-oxblood hover:text-oxblood-dark">Merchant</Link>
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
