import { ChevronRight, SlidersHorizontal } from "lucide-react";
import { Button } from "../../components/ui/button";
import { useStore } from "../../store/useStore";

export function FilterSidebar() {
  const { selectedType, setSelectedType, maxPrice, setMaxPrice } = useStore();

  const types = ["t-shirt", "short", "shirt", "hoodie", "jeans"];

  return (
    <div className="hidden md:block w-64 flex-shrink-0 sticky top-[110px] self-start max-h-[calc(100vh-120px)] overflow-y-auto">
      <div className="border border-stone-200 bg-white rounded-[24px] p-6 shadow-sm">
        <div className="flex justify-between items-center mb-6">
          <h2 className="font-bold text-lg">Filters</h2>
          <SlidersHorizontal className="h-5 w-5 text-gray-400" />
        </div>
        <hr className="my-4" />
        <div className="space-y-4 text-gray-500">
          <div 
            className={`flex justify-between cursor-pointer ${selectedType === "" ? "text-black font-bold" : ""}`}
            onClick={() => setSelectedType("")}
          >
            <span>All Categories</span>
          </div>
          {types.map(type => (
            <div 
              key={type}
              className={`flex justify-between cursor-pointer capitalize ${selectedType === type ? "text-black font-bold" : ""}`}
              onClick={() => setSelectedType(type)}
            >
              <span>{type}</span><ChevronRight className="h-5 w-5" />
            </div>
          ))}
        </div>
        <hr className="my-6" />
        <h3 className="font-bold mb-4">Price</h3>
        <input 
          type="range" 
          className="w-full accent-black mb-2" 
          min="0" 
          max="6000" 
          value={maxPrice}
          onChange={(e) => setMaxPrice(Number(e.target.value))}
        />
        <div className="flex justify-between font-medium"><span className="text-sm">₹0</span><span className="text-sm">₹{maxPrice}</span></div>
        <hr className="my-6" />
        <Button className="w-full rounded-full bg-black text-white py-6" onClick={() => { setSelectedType(""); setMaxPrice(3000); }}>Clear Filters</Button>
      </div>
    </div>
  );
}
