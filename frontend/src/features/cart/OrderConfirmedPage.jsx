import { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { CheckCircle } from "lucide-react";
import { Button } from "../../components/ui/button";
import { useStore } from "../../store/useStore";

export function OrderConfirmedPage() {
  const { user } = useStore();
  const navigate = useNavigate();

  useEffect(() => {
    // If not logged in, just send them home safely
    if (!user) {
      navigate("/");
    }
  }, [user, navigate]);

  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center text-center px-4">
      <CheckCircle className="w-24 h-24 text-green-500 mb-6" />
      <h1 className="text-4xl md:text-5xl font-black mb-4 uppercase">Order Confirmed!</h1>
      <p className="text-lg text-gray-600 mb-2 max-w-md">
        Thank you for buying from us, {user?.name || "Customer"}.
      </p>
      <p className="text-md text-gray-500 mb-8 max-w-md">
        Your order is confirmed and will be delivered to: <br/>
        <strong className="text-black">{user?.address || "your registered address"}</strong>
      </p>
      
      <Link to="/products">
        <Button className="rounded-full py-6 px-10 text-lg">
          Continue Shopping
        </Button>
      </Link>
    </div>
  );
}
