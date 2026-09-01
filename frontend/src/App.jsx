import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { Navbar } from "./components/layout/Navbar";
import { Footer } from "./components/layout/Footer";
import { AgentWidget } from "./components/layout/AgentWidget";
import { HomePage } from "./features/home/HomePage";
import { ProductListPage } from "./features/products/ProductListPage";
import { ProductDetailPage } from "./features/products/ProductDetailPage";
import { CartPage } from "./features/cart/CartPage";
import { LoginPage } from "./features/auth/LoginPage";
import { SignupPage } from "./features/auth/SignupPage";
import { MerchantDashboard } from "./features/merchant/MerchantDashboard";

import { OrderConfirmedPage } from "./features/cart/OrderConfirmedPage";

function App() {
  return (
    <Router>
      <div className="min-h-screen flex flex-col relative">
        <Navbar />
        <main className="flex-grow">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignupPage />} />
            <Route path="/products" element={<ProductListPage />} />
            <Route path="/product/:id" element={<ProductDetailPage />} />
            <Route path="/cart" element={<CartPage />} />
            <Route path="/order-confirmed" element={<OrderConfirmedPage />} />
            <Route path="/merchant" element={<MerchantDashboard />} />
          </Routes>
        </main>
        <Footer />
        <AgentWidget />
      </div>
    </Router>
  );
}

export default App;
