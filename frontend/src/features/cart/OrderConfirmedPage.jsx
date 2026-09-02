import { useEffect } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { CheckCircle } from "lucide-react";
import { Button } from "../../components/ui/button";
import { useStore } from "../../store/useStore";

export function OrderConfirmedPage() {
  const { user, pollPaymentStatus, notifyPaymentComplete, setIsAgentOpen } = useStore();
  const [params] = useSearchParams();

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
    <div className="min-h-[70vh] flex flex-col items-center justify-center text-center px-4">
      <CheckCircle className="w-20 h-20 text-[#C45C26] mb-6" />
      <h1 className="font-display text-4xl md:text-5xl font-extrabold mb-4 uppercase">You're all set</h1>
      <p className="text-lg text-stone-600 mb-2 max-w-md">
        Thank you{user?.name ? `, ${user.name}` : ""}. We're confirming your payment with the stylist.
      </p>
      <p className="text-md text-stone-500 mb-8 max-w-md">
        If you paid just now, the chat will update automatically. Delivery:
        <br/>
        <strong className="text-stone-900">{user?.address || "the address you confirmed in chat"}</strong>
      </p>
      
      <div className="flex gap-3">
        <Link to="/products">
          <Button className="rounded-full py-6 px-10 text-lg bg-stone-900 hover:bg-stone-800">
            Continue shopping
          </Button>
        </Link>
        <Button variant="outline" className="rounded-full py-6 px-8 border-stone-300" onClick={() => setIsAgentOpen(true)}>
          Open stylist
        </Button>
      </div>
    </div>
  );
}
