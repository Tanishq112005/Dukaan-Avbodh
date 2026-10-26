import { useEffect } from "react";
import { Link, useSearchParams, useLocation } from "react-router-dom";
import { CheckCircle, ShieldCheck } from "lucide-react";
import { Button } from "../../components/ui/button";
import { useStore } from "../../store/useStore";

export function OrderConfirmedPage() {
  const { user, pollPaymentStatus, notifyPaymentComplete, setIsAgentOpen } = useStore();
  const [params] = useSearchParams();
  const location = useLocation();

  const checkoutState = location.state || {};
  const orderIds = checkoutState.orderIds;
  const totalPaid = checkoutState.total;
  const paymentId = checkoutState.paymentId;

  useEffect(() => {
    const status = params.get("razorpay_payment_link_status");
    if (status === "paid") {
      setIsAgentOpen(true);
      notifyPaymentComplete();
    } else {
      pollPaymentStatus();
    }
  }, [params, pollPaymentStatus, notifyPaymentComplete, setIsAgentOpen]);

  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center text-center px-4 py-12">
      <div className="relative mb-6">
        <div className="w-20 h-20 rounded-full bg-emerald-100 flex items-center justify-center mx-auto text-emerald-600">
          <CheckCircle className="w-12 h-12" />
        </div>
      </div>

      <h1 className="font-display text-4xl md:text-5xl font-extrabold mb-3 uppercase tracking-tight text-stone-900">
        Payment Successful!
      </h1>
      <p className="text-lg text-stone-600 mb-2 max-w-md">
        Thank you{user?.name ? `, ${user.name}` : ""}. Your order has been securely confirmed.
      </p>

      {totalPaid !== undefined && (
        <div className="my-4 py-3 px-6 bg-stone-50 border border-stone-200 rounded-2xl inline-flex items-center gap-4 text-sm text-stone-700">
          {orderIds && orderIds.length > 0 && (
            <span>Order #{orderIds.join(", #")}</span>
          )}
          <span className="font-bold text-stone-900">Total: ₹{Number(totalPaid).toFixed(0)}</span>
          {paymentId && (
            <span className="text-xs text-stone-400 font-mono">Ref: {paymentId}</span>
          )}
        </div>
      )}

      <p className="text-sm text-stone-500 mb-8 max-w-md">
        Delivery destination:
        <br />
        <strong className="text-stone-900 font-medium">
          {user?.address || "The address confirmed in your profile"}
        </strong>
      </p>

      <div className="flex flex-wrap justify-center gap-3">
        <Link to="/orders">
          <Button className="rounded-full py-6 px-8 text-base bg-stone-900 hover:bg-stone-800 text-white">
            View My Orders
          </Button>
        </Link>
        <Link to="/products">
          <Button variant="outline" className="rounded-full py-6 px-8 text-base border-stone-300">
            Continue Shopping
          </Button>
        </Link>
        <Button
          variant="outline"
          className="rounded-full py-6 px-8 text-base border-stone-300"
          onClick={() => setIsAgentOpen(true)}
        >
          Chat with Stylist
        </Button>
      </div>

      <div className="mt-8 flex items-center justify-center gap-1.5 text-xs text-stone-400">
        <ShieldCheck className="w-4 h-4 text-emerald-600" />
        <span>Verified by Razorpay & Dukaan Order Security</span>
      </div>
    </div>
  );
}
