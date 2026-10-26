import { useState } from "react";
import { Search as SearchIcon, ShoppingBag, User, Package, LogOut, Sparkles, X, Menu } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useStore } from "../../../store/useStore.js";
import { Search } from "../Search/Search";

function NavActions({ cartCount, user, handleLogout, onOpenStylist, onToggleMobileSearch }) {
  return (
    <div className="flex items-center gap-2.5 sm:gap-4">
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
        className="flex items-center gap-1.5 bg-stone-900 hover:bg-[#6e1423] text-white px-3 sm:px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all duration-300 cursor-pointer shadow-xs hover:shadow-md"
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
          <span className="absolute top-0 right-0 bg-[#6e1423] text-white text-[10px] font-bold rounded-full w-4.5 h-4.5 flex items-center justify-center shadow-xs">
            {cartCount}
          </span>
        )}
      </Link>

      {/* User Session Actions */}
      <div className="flex items-center gap-2 sm:gap-3">
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
              className="hidden sm:inline-block text-xs font-bold uppercase tracking-wider bg-stone-900 text-white px-4 py-2 rounded-full hover:bg-[#6e1423] transition-colors shadow-xs"
            >
              Join
            </Link>
          </>
        ) : (
          <div className="flex items-center gap-2 sm:gap-2.5">
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
              className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-stone-100 border border-stone-300 text-stone-900 flex items-center justify-center text-xs font-bold"
            >
              {user.name ? user.name.charAt(0).toUpperCase() : <User className="w-4 h-4" />}
            </div>
            <button
              onClick={handleLogout}
              className="text-stone-400 hover:text-red-600 p-1 sm:p-1.5 rounded-full transition-colors cursor-pointer"
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
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const cartCount = cart.reduce((acc, item) => acc + item.qty, 0);
  const navigate = useNavigate();

  const handleLogout = () => {
    if (window.confirm("Do you want to log out?")) {
      logout();
      setMobileMenuOpen(false);
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
    <header className="sticky top-0 z-40 bg-[#FBF8F3]/95 backdrop-blur-md">
      {/* Top Banner Marquee */}
      <div className="bg-stone-950 text-stone-300 text-[10px] sm:text-[11px] font-medium tracking-wider uppercase overflow-hidden border-b border-stone-800">
        <div className="flex whitespace-nowrap animate-marquee py-2">
          {[...tickerItems, ...tickerItems].map((item, i) => (
            <span key={i} className="mx-6 sm:mx-8 flex items-center gap-3">
              <span>{item}</span>
              <span className="w-1 h-1 rounded-full bg-[#C45C26]" />
            </span>
          ))}
        </div>
      </div>

      {/* Main Navbar */}
      <nav className="border-b border-stone-200/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-[64px] sm:h-[68px]">
            {/* Left: Mobile Menu Toggle + Brand Logo */}
            <div className="flex items-center gap-3 sm:gap-8 lg:gap-10">
              <button
                onClick={() => setMobileMenuOpen(true)}
                type="button"
                className="md:hidden p-1.5 rounded-lg text-stone-700 hover:bg-stone-100 cursor-pointer"
                aria-label="Open mobile navigation menu"
              >
                <Menu size={22} />
              </button>

              <Link to="/" className="font-display text-xl sm:text-2xl font-black tracking-tight text-stone-900 flex items-center">
                <span>DUKAAN</span>
                <span className="w-1.5 h-1.5 sm:w-2 sm:h-2 rounded-full bg-[#6e1423] ml-1 mb-1" />
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
                  className="w-full bg-stone-100 rounded-full pl-9 pr-4 py-2 text-sm text-stone-900 outline-none focus:ring-2 focus:ring-stone-900"
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

      {/* Mobile Navigation Drawer */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 flex md:hidden">
          <div
            className="fixed inset-0 bg-stone-950/60 backdrop-blur-xs transition-opacity"
            onClick={() => setMobileMenuOpen(false)}
          />
          <div className="relative w-4/5 max-w-xs h-full bg-white shadow-2xl flex flex-col justify-between p-6 z-10 animate-slide-right">
            <div>
              <div className="flex items-center justify-between pb-5 border-b border-stone-100">
                <Link
                  to="/"
                  onClick={() => setMobileMenuOpen(false)}
                  className="font-display text-xl font-black tracking-tight text-stone-900 flex items-center"
                >
                  <span>DUKAAN</span>
                  <span className="w-1.5 h-1.5 rounded-full bg-[#6e1423] ml-1 mb-1" />
                </Link>
                <button
                  onClick={() => setMobileMenuOpen(false)}
                  className="p-1 rounded-full text-stone-500 hover:bg-stone-100 cursor-pointer"
                >
                  <X size={20} />
                </button>
              </div>

              <div className="py-6 space-y-4">
                <Link
                  to="/"
                  onClick={() => setMobileMenuOpen(false)}
                  className="block text-sm font-bold uppercase tracking-wider text-stone-800 hover:text-[#6e1423] transition-colors"
                >
                  Home
                </Link>
                <Link
                  to="/products"
                  onClick={() => setMobileMenuOpen(false)}
                  className="block text-sm font-bold uppercase tracking-wider text-stone-800 hover:text-[#6e1423] transition-colors"
                >
                  Shop Catalog
                </Link>
                <button
                  onClick={() => {
                    setMobileMenuOpen(false);
                    setIsAgentOpen(true);
                  }}
                  className="w-full text-left flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-[#C45C26]"
                >
                  <Sparkles size={16} />
                  <span>AI Personal Stylist</span>
                </button>
                <Link
                  to="/cart"
                  onClick={() => setMobileMenuOpen(false)}
                  className="block text-sm font-bold uppercase tracking-wider text-stone-800 hover:text-[#6e1423] transition-colors"
                >
                  Shopping Bag ({cartCount})
                </Link>
                {user && (
                  <Link
                    to="/orders"
                    onClick={() => setMobileMenuOpen(false)}
                    className="block text-sm font-bold uppercase tracking-wider text-stone-800 hover:text-[#6e1423] transition-colors"
                  >
                    My Orders
                  </Link>
                )}
                {user?.role === "merchant" && (
                  <Link
                    to="/merchant"
                    onClick={() => setMobileMenuOpen(false)}
                    className="block text-sm font-bold uppercase tracking-wider text-[#6e1423]"
                  >
                    Merchant Studio
                  </Link>
                )}
              </div>
            </div>

            {/* Bottom session area */}
            <div className="pt-6 border-t border-stone-100">
              {user ? (
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-full bg-stone-100 border border-stone-300 text-stone-900 flex items-center justify-center text-xs font-bold">
                      {user.name ? user.name.charAt(0).toUpperCase() : <User className="w-4 h-4" />}
                    </div>
                    <div>
                      <p className="text-xs font-bold text-stone-900">{user.name || "Customer"}</p>
                      <p className="text-[10px] text-stone-400 capitalize">{user.role || "client"}</p>
                    </div>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="text-xs text-red-600 font-semibold cursor-pointer"
                  >
                    Logout
                  </button>
                </div>
              ) : (
                <div className="space-y-2">
                  <Link
                    to="/login"
                    onClick={() => setMobileMenuOpen(false)}
                    className="block w-full py-2.5 text-center text-xs font-bold uppercase tracking-wider text-stone-900 border border-stone-300 rounded-xl"
                  >
                    Sign In
                  </Link>
                  <Link
                    to="/signup"
                    onClick={() => setMobileMenuOpen(false)}
                    className="block w-full py-2.5 text-center text-xs font-bold uppercase tracking-wider text-white bg-stone-900 rounded-xl"
                  >
                    Create Account
                  </Link>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
