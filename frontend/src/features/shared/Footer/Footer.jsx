import { Link } from "react-router-dom";

export function Footer() {
  return (
    <footer className="bg-ink text-white mt-4 pt-16 pb-8 border-t border-hairline">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid md:grid-cols-4 gap-10 mb-12">
          <div className="md:col-span-2">
            <h3 className="font-display text-3xl mb-4">Dukaan</h3>
            <p className="text-white/50 text-sm max-w-sm leading-relaxed">
              Clothes that suit your style — and a stylist in the corner of
              the screen who can close the look.
            </p>
          </div>
          <div>
            <p className="text-sm text-white/40 mb-4">Shop</p>
            <div className="space-y-2 text-sm">
              <Link to="/products" className="block text-white/70 hover:text-white">All products</Link>
              <Link to="/cart" className="block text-white/70 hover:text-white">Bag</Link>
            </div>
          </div>
          <div>
            <p className="text-sm text-white/40 mb-4">Studio</p>
            <div className="space-y-2 text-sm">
              <Link to="/merchant" className="block text-white/70 hover:text-white">Merchant</Link>
              <Link to="/login" className="block text-white/70 hover:text-white">Account</Link>
            </div>
          </div>
        </div>
        <div className="border-t border-white/10 pt-6 flex flex-col md:flex-row justify-between items-center gap-3">
          <p className="text-sm text-white/40">Dukaan © 2026. All rights reserved.</p>
          <p className="text-xs text-white/30">Secure checkout, Razorpay</p>
        </div>
      </div>
    </footer>
  );
}
