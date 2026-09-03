import React from 'react';
import { Loader } from "../../components/ui/Loader";

export function OrdersTab({ orders, loading }) {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Recent Orders</h2>
      {loading ? <Loader /> : orders.length === 0 ? <p className="text-gray-400">No orders placed yet.</p> : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {orders.map((order) => (
            <div key={order.id} className="border border-gray-200 rounded-xl p-6 bg-white shadow-sm hover:shadow-md transition">
              <div className="flex flex-col gap-3 mb-4">
                <div className="flex justify-between items-center mb-2">
                  <span className="bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-xs font-bold">Total Discount: {order.discount_applied}%</span>
                </div>
                {order.products?.map((prod, idx) => (
                  <div key={idx} className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-gray-100 rounded-lg overflow-hidden flex-shrink-0">
                      {prod.image_url ? (
                        <img src={prod.image_url} alt={prod.name} className="w-full h-full object-cover mix-blend-multiply" />
                      ) : <div className="w-full h-full bg-gray-200"></div>}
                    </div>
                    <div>
                      <h3 className="font-bold line-clamp-1 text-sm">{prod.name}</h3>
                      <p className="text-xs text-gray-500">Price: ₹{prod.price}</p>
                    </div>
                  </div>
                ))}
              </div>
              <hr className="my-4 border-gray-100" />
              <div className="space-y-2 text-sm text-gray-600 bg-gray-50 p-3 rounded">
                <p><strong className="text-black">Customer:</strong> {order.user.name}</p>
                <p><strong className="text-black">Email:</strong> {order.user.email}</p>
                <p><strong className="text-black">Delivery To:</strong> {order.user.address}</p>
              </div>
              <hr className="my-4 border-gray-100" />
              <div className="space-y-1 text-xs text-gray-400">
                <p>Order ID: #{order.id}</p>
                <p>Razorpay Order: {order.razorpay_order_id || "N/A"}</p>
                <p>Razorpay Payment: {order.razorpay_payment_id || "N/A"}</p>
                <p>Date: {new Date(order.created_at).toLocaleString()}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
