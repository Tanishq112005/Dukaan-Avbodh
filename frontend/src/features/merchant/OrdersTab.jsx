import React from 'react';

export function OrdersTab({ orders, loading }) {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Recent Orders</h2>
      {loading ? <p>Loading orders...</p> : orders.length === 0 ? <p className="text-gray-400">No orders placed yet.</p> : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {orders.map((order) => (
            <div key={order.id} className="border border-gray-200 rounded-xl p-6 bg-white shadow-sm hover:shadow-md transition">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-16 h-16 bg-gray-100 rounded-lg overflow-hidden flex-shrink-0">
                  {order.product.image_url ? (
                    <img src={order.product.image_url} alt={order.product.name} className="w-full h-full object-cover mix-blend-multiply" />
                  ) : <div className="w-full h-full bg-gray-200"></div>}
                </div>
                <div>
                  <h3 className="font-bold line-clamp-1">{order.product.name}</h3>
                  <p className="text-sm text-gray-500">Price: ₹{order.product.price} (Discount: {order.discount_applied}%)</p>
                </div>
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
