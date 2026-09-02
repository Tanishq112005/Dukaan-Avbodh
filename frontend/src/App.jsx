import { BrowserRouter as Router, Routes, Route, useLocation } from "react-router-dom";
import { Navbar } from "./features/shared/Navbar/Navbar";
import { Footer } from "./features/shared/Footer/Footer";
import { AgentWidget } from "./features/chatbot/ChatContainer";
import { HomePage } from "./features/home/HomePage";
import { ProductListPage } from "./features/products/ProductListPage";
import { ProductDetailPage } from "./features/products/ProductDetailPage";
import { CartPage } from "./features/cart/CartPage";
import { LoginPage } from "./features/auth/LoginPage";
import { SignupPage } from "./features/auth/SignupPage";
import { MerchantDashboard } from "./features/merchant/MerchantDashboard";
import { OrderConfirmedPage } from "./features/cart/OrderConfirmedPage";
import { useStore } from "./store/useStore.js";
import { Analytics } from "@vercel/analytics/next"
function AppContent() {
  const token = useStore((state) => state.token);

  return (
    <div className="min-h-screen flex flex-col relative bg-[#FBF8F3]">
      <Analytics />
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
      {token && <AgentWidget />}
    </div>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;