import { useState } from "react";
import { Search as SearchIcon, ShoppingBag, User, Package, LogOut, Sparkles, X } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useStore } from "../../../store/useStore.js";
import { Search } from "../Search/Search";

function NavActions({ cartCount, user, handleLogout, onOpenStylist, onToggleMobileSearch }) {
  return (
    <div className="flex items-center gap-3 sm:gap-4">
      {/* Mobile search toggle button */}
      <button
        onClick={onToggleMobileSearch}
        type="button"
        className="md:hidden p-2 rounded-full hover:bg-stone-100 text-stone-700 transition-colors cursor-pointer"
        aria-label="Search items"
      >
        <SearchIcon className="h-5 w-5" />
      </button>

      {/* AI Stylist Button */}
      <button
        onClick={onOpenStylist}
        type="button"
        className="flex items-center gap-1.5 bg-stone-900 hover:bg-[#6e1423] text-white px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all duration-300 cursor-pointer shadow-xs hover:shadow-md"
        title="Chat with Dukaan AI Personal Stylist"
      >
        <Sparkles className="w-3.5 h-3.5 text-amber-300 animate-pulse" />
        <span className="hidden sm:inline">AI Stylist</span>
      </button>

      {/* Shopping Bag */}
      <Link
        to="/cart"
        className="relative p-2 rounded-full hover:bg-stone-100 text-stone-900 transition-colors"
        title="Shopping Bag"
      >
        <ShoppingBag className="h-5 w-5" strokeWidth={1.75} />
        {cartCount > 0 && (
          <span className="absolute top-0 right-0 bg-[#6e1423] text-white text-[10px] font-bold rounded-full w-4.5 h-4.5 flex items-center justify-center shadow-xs animate-scale-in">
            {cartCount}
          </span>
        )}
      </Link>

      {/* User Session Actions */}
      <div className="flex items-center gap-3">
        {!user ? (
          <>
            <Link
              to="/login"
              className="hidden sm:block text-xs font-semibold text-stone-700 hover:text-stone-900 uppercase tracking-wider transition-colors"
            >
              Sign In
            </Link>
            <Link
              to="/signup"
              className="text-xs font-bold uppercase tracking-wider bg-stone-900 text-white px-4 py-2 rounded-full hover:bg-[#6e1423] transition-colors shadow-xs"
            >
              Join
            </Link>
          </>
        ) : (
          <div className="flex items-center gap-2.5">
            <Link
              to="/orders"
              className="hidden sm:flex items-center gap-1 text-xs font-medium text-stone-600 hover:text-stone-900 border border-stone-200 px-3 py-1.5 rounded-full transition-colors"
              title="My Orders"
            >
              <Package className="w-3.5 h-3.5" />
              <span>Orders</span>
            </Link>
            <div
              title={`${user.name || user.email} (${user.role || 'customer'})`}
              className="w-8 h-8 rounded-full bg-stone-100 border border-stone-300 text-stone-900 flex items-center justify-center text-xs font-bold"
            >
              {user.name ? user.name.charAt(0).toUpperCase() : <User className="w-4 h-4" />}
            </div>
            <button
              onClick={handleLogout}
              className="text-stone-400 hover:text-red-600 p-1.5 rounded-full transition-colors cursor-pointer"
              title="Log out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export function Navbar() {
  const { user, logout, cart, searchQuery, setSearchQuery, setIsAgentOpen } = useStore();
  const [mobileSearchOpen, setMobileSearchOpen] = useState(false);
  const cartCount = cart.reduce((acc, item) => acc + item.qty, 0);
  const navigate = useNavigate();

  const handleLogout = () => {
    if (window.confirm("Do you want to log out?")) {
      logout();
      navigate("/");
    }
  };

  const handleSearch = (e) => {
    if (e.key === "Enter") {
      navigate("/products");
      setMobileSearchOpen(false);
    }
  };

  const tickerItems = [
    "Free Express Shipping on Orders ₹999+",
    "Live AI Personal Stylist & Price Negotiation",
    "Autumn / Winter '26 Collection Live",
    "14-Day Seamless Doorstep Exchange",
    "100% Authentic Certified Luxury Apparel",
  ];

  return (
    <header className="sticky top-0 z-50 bg-[#FBF8F3]/95 backdrop-blur-md">
      {/* Top Banner Marquee */}
      <div className="bg-stone-950 text-stone-300 text-[11px] font-medium tracking-wider uppercase overflow-hidden border-b border-stone-800">
        <div className="flex whitespace-nowrap animate-marquee py-2">
          {[...tickerItems, ...tickerItems].map((item, i) => (
            <span key={i} className="mx-8 flex items-center gap-3">
              <span>{item}</span>
              <span className="w-1 h-1 rounded-full bg-[#C45C26]" />
            </span>
          ))}
        </div>
      </div>

      {/* Main Navbar */}
      <nav className="border-b border-stone-200/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-[68px]">
            {/* Brand Logo & Navigation Links */}
            <div className="flex items-center gap-8 lg:gap-10">
              <Link to="/" className="font-display text-2xl sm:text-[26px] font-black tracking-tight text-stone-900 flex items-center">
                <span>DUKAAN</span>
                <span className="w-2 h-2 rounded-full bg-[#6e1423] ml-1 mb-1" />
              </Link>
              <div className="hidden md:flex gap-7 items-center">
                <Link to="/products" className="text-xs font-bold uppercase tracking-wider text-stone-600 hover:text-stone-900 transition-colors">
                  Shop Catalog
                </Link>
                {user && (
                  <Link to="/orders" className="text-xs font-bold uppercase tracking-wider text-stone-600 hover:text-stone-900 transition-colors">
                    Orders
                  </Link>
                )}
                {user?.role === "merchant" && (
                  <Link to="/merchant" className="text-xs font-bold uppercase tracking-wider text-[#6e1423] hover:text-stone-900 transition-colors">
                    Merchant Studio
                  </Link>
                )}
              </div>
            </div>

            {/* Desktop Search Bar */}
            <Search searchQuery={searchQuery} setSearchQuery={setSearchQuery} handleSearch={handleSearch} />

            {/* Navbar Actions */}
            <NavActions
              cartCount={cartCount}
              user={user}
              handleLogout={handleLogout}
              onOpenStylist={() => setIsAgentOpen(true)}
              onToggleMobileSearch={() => setMobileSearchOpen(!mobileSearchOpen)}
            />
          </div>

          {/* Mobile Search Expandable Bar */}
          {mobileSearchOpen && (
            <div className="md:hidden pb-3 pt-1 flex items-center gap-2 animate-fade-in">
              <div className="relative flex-1">
                <SearchIcon className="absolute left-3.5 top-3 h-4 w-4 text-stone-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={handleSearch}
                  placeholder="Search garments, styles, brands..."
                  className="w-full bg-stone-100 rounded-full pl-9 pr-4 py-2.5 text-xs text-stone-900 outline-none focus:ring-2 focus:ring-stone-900"
                  autoFocus
                />
              </div>
              <button
                onClick={() => setMobileSearchOpen(false)}
                className="p-2 text-stone-500 hover:text-stone-900"
              >
                <X size={18} />
              </button>
            </div>
          )}
        </div>
      </nav>
    </header>
  );
}
