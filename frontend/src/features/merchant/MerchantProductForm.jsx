import { useState } from "react";
import { useStore } from "../../store/useStore";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { productService } from "../../services/productService";

export function MerchantProductForm() {
  const { user } = useStore();
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
    image_url: "",
  });
  const [msg, setMsg] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (e) =>
    setFormData({ ...formData, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setMsg("");

    try {
      const payload = {
        name: formData.name,
        price: parseFloat(formData.price) || 0,
        stock: parseInt(formData.stock, 10) || 0,
        type: formData.type,
        brand: formData.brand || "DUKAAN",
        description: formData.description,
        sizes: formData.sizes,
        rating: parseFloat(formData.rating) || 4.5,
        discount: parseInt(formData.discount, 10) || 0,
        image_url:
          formData.image_url ||
          "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=800",
      };

      await productService.addProduct(payload);
      setMsg("Product added successfully!");
      setFormData({
        name: "",
        price: "",
        stock: "",
        type: "t-shirt",
        brand: "",
        description: "",
        sizes: "S,M,L,XL",
        rating: "4.5",
        discount: "0",
        image_url: "",
      });
    } catch (err) {
      console.error("Error adding product:", err);
      setMsg(
        err.message ||
          "Failed to add product. Make sure you are logged in as a Merchant."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-[#F0F0F0] p-8 rounded-[20px]">
      <h2 className="text-2xl font-bold mb-6">Add New Product</h2>
      {msg && (
        <p
          className={`mb-4 font-semibold text-sm ${
            msg.includes("successfully") ? "text-green-700" : "text-red-600"
          }`}
        >
          {msg}
        </p>
      )}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <Input
            name="name"
            placeholder="Product Name"
            value={formData.name}
            onChange={handleChange}
            required
            disabled={isSubmitting}
          />
          <Input
            name="price"
            type="number"
            placeholder="Price (₹)"
            value={formData.price}
            onChange={handleChange}
            required
            disabled={isSubmitting}
          />
          <Input
            name="stock"
            type="number"
            placeholder="Stock Quantity"
            value={formData.stock}
            onChange={handleChange}
            required
            disabled={isSubmitting}
          />
          <select
            name="type"
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            value={formData.type}
            onChange={handleChange}
            disabled={isSubmitting}
          >
            <option value="t-shirt">T-shirt</option>
            <option value="shirt">Shirt</option>
            <option value="short">Short</option>
            <option value="hoodie">Hoodie</option>
            <option value="jeans">Jeans</option>
          </select>
          <Input
            name="brand"
            placeholder="Brand (e.g. ZARA)"
            value={formData.brand}
            onChange={handleChange}
            disabled={isSubmitting}
          />
          <Input
            name="sizes"
            placeholder="Sizes (e.g. S,M,L)"
            value={formData.sizes}
            onChange={handleChange}
            disabled={isSubmitting}
          />
          <Input
            name="rating"
            type="number"
            step="0.1"
            placeholder="Rating (0-5)"
            value={formData.rating}
            onChange={handleChange}
            disabled={isSubmitting}
          />
          <Input
            name="discount"
            type="number"
            placeholder="Discount (%)"
            value={formData.discount}
            onChange={handleChange}
            disabled={isSubmitting}
          />
        </div>
        <Input
          name="image_url"
          placeholder="Image URL (optional)"
          value={formData.image_url}
          onChange={handleChange}
          disabled={isSubmitting}
        />
        <textarea
          name="description"
          placeholder="Product Description"
          className="w-full h-24 p-3 rounded-md border border-input text-sm"
          value={formData.description}
          onChange={handleChange}
          disabled={isSubmitting}
        />
        <Button
          type="submit"
          disabled={isSubmitting || user?.role !== "merchant"}
          className="w-full bg-black hover:bg-stone-800 text-white"
        >
          {isSubmitting ? "Adding Product..." : "Create Product"}
        </Button>
        {user?.role !== "merchant" && (
          <p className="text-xs text-stone-500 text-center">
            Note: You must be logged in as a merchant to add products.
          </p>
        )}
      </form>
    </div>
  );
}
