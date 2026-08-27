import { useState } from "react";
import axios from "axios";
import { useStore } from "../../store/useStore";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";

export function MerchantDashboard() {
  const { token, user } = useStore();
  const [formData, setFormData] = useState({
    name: "",
    price: "",
    stock: "",
    type: "t-shirt",
    brand: "",
    description: "",
    sizes: "S,M,L,XL",
    rating: "4.5",
    discount: "0",
    image_url: ""
  });
  const [msg, setMsg] = useState("");

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        price: parseFloat(formData.price),
        stock: parseInt(formData.stock),
        rating: parseFloat(formData.rating),
        discount: parseInt(formData.discount),
      };
      
      await axios.post("http://localhost:8000/product/add", payload, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMsg("Product added successfully!");
      setFormData({
        name: "", price: "", stock: "", type: "t-shirt", brand: "", 
        description: "", sizes: "S,M,L,XL", rating: "4.5", discount: "0", image_url: ""
      });
    } catch (err) {
      console.error(err);
      setMsg("Failed to add product. Make sure you are logged in as a Merchant.");
    }
  };

  if (!token) {
    return <div className="p-16 text-center text-red-500 font-bold">Please login first!</div>;
  }

  return (
    <div className="max-w-2xl mx-auto py-16 px-4">
      <h1 className="text-4xl font-black mb-8">Merchant Dashboard</h1>
      <div className="bg-[#F0F0F0] p-8 rounded-[20px]">
        <h2 className="text-2xl font-bold mb-6">Add New Product</h2>
        {msg && <p className="mb-4 font-bold text-black">{msg}</p>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Input name="name" placeholder="Product Name" value={formData.name} onChange={handleChange} required />
            <Input name="price" type="number" placeholder="Price (₹)" value={formData.price} onChange={handleChange} required />
            <Input name="stock" type="number" placeholder="Stock Quantity" value={formData.stock} onChange={handleChange} required />
            <select name="type" className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm" value={formData.type} onChange={handleChange}>
              <option value="t-shirt">T-shirt</option>
              <option value="shirt">Shirt</option>
              <option value="short">Short</option>
              <option value="hoodie">Hoodie</option>
              <option value="jeans">Jeans</option>
            </select>
            <Input name="brand" placeholder="Brand (e.g. ZARA)" value={formData.brand} onChange={handleChange} />
            <Input name="sizes" placeholder="Sizes (e.g. S,M,L)" value={formData.sizes} onChange={handleChange} />
            <Input name="rating" type="number" step="0.1" placeholder="Rating (0-5)" value={formData.rating} onChange={handleChange} />
            <Input name="discount" type="number" placeholder="Discount (%)" value={formData.discount} onChange={handleChange} />
          </div>
          <Input name="image_url" placeholder="Image URL (optional)" value={formData.image_url} onChange={handleChange} />
          <textarea 
            name="description" 
            placeholder="Product Description" 
            className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            value={formData.description} 
            onChange={handleChange} 
          />
          <Button type="submit" className="w-full py-6 rounded-full text-lg mt-4">Upload Product</Button>
        </form>
      </div>
    </div>
  );
}
