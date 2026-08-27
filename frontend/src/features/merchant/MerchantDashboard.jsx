import { useStore } from "../../store/useStore";
import { MerchantProductForm } from "./MerchantProductForm";

export function MerchantDashboard() {
  const { token } = useStore();

  if (!token) {
    return <div className="p-16 text-center text-red-500 font-bold">Please login first!</div>;
  }

  return (
    <div className="max-w-2xl mx-auto py-16 px-4">
      <h1 className="text-4xl font-black mb-8">Merchant Dashboard</h1>
      <MerchantProductForm />
    </div>
  );
}
