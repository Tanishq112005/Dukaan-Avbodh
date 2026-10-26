import { Link } from "react-router-dom";

export function Footer() {
  return (
    <footer className="bg-stone-950 text-white mt-12 pt-12 pb-10 border-t border-stone-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Main Footer Links */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8 mb-12">
          {/* Brand Info */}
          <div className="col-span-2">
            <Link to="/" className="font-display text-2xl font-black tracking-tight text-white flex items-center mb-4">
              <span>DUKAAN</span>
              <span className="w-2 h-2 rounded-full bg-[#C45C26] ml-1 mb-1" />
            </Link>
            <p className="text-stone-400 text-xs sm:text-sm max-w-sm leading-relaxed mb-4">
              Modern designer garments tailored for individuality, powered by real-time conversational AI to help you discover, match, and negotiate the ideal look.
            </p>
            <div className="flex items-center gap-3 text-xs text-stone-400">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>Atelier Stylist Online 24/7</span>
            </div>
          </div>

          {/* Column 1: Collections */}
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-stone-300 mb-4">Collections</p>
            <ul className="space-y-2.5 text-xs text-stone-400">
              <li><Link to="/products" className="hover:text-white transition-colors">T-Shirts & Polos</Link></li>
              <li><Link to="/products" className="hover:text-white transition-colors">Casual & Formal Shirts</Link></li>
              <li><Link to="/products" className="hover:text-white transition-colors">Denim & Trousers</Link></li>
              <li><Link to="/products" className="hover:text-white transition-colors">Hoodies & Outerwear</Link></li>
            </ul>
          </div>

          {/* Column 2: Experience */}
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-stone-300 mb-4">Experience</p>
            <ul className="space-y-2.5 text-xs text-stone-400">
              <li><Link to="/products" className="hover:text-white transition-colors">Complete Catalog</Link></li>
              <li><Link to="/cart" className="hover:text-white transition-colors">Shopping Bag</Link></li>
              <li><Link to="/orders" className="hover:text-white transition-colors">Order Tracking</Link></li>
              <li><Link to="/merchant" className="hover:text-white transition-colors">Merchant Portal</Link></li>
            </ul>
          </div>

          {/* Column 3: Legal & Trust */}
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-stone-300 mb-4">Customer Care</p>
            <ul className="space-y-2.5 text-xs text-stone-400">
              <li><span className="hover:text-white cursor-pointer transition-colors">Privacy Policy</span></li>
              <li><span className="hover:text-white cursor-pointer transition-colors">Terms of Service</span></li>
              <li><span className="hover:text-white cursor-pointer transition-colors">Shipping & Delivery</span></li>
              <li><span className="hover:text-white cursor-pointer transition-colors">Payment Protection</span></li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="border-t border-stone-800 pt-8 flex flex-col sm:flex-row justify-between items-center gap-4 text-xs text-stone-500">
          <p>Dukaan Atelier © 2026. All rights reserved.</p>
          <div className="flex items-center gap-4 text-stone-400">
            <span>256-bit Encrypted Checkout</span>
            <span>·</span>
            <span>Razorpay Secure Payments</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
