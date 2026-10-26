import { SlidersHorizontal, X, RotateCcw } from "lucide-react";
import { useStore } from "../../store/useStore";

export function FilterSidebar({ isMobile = false, onClose }) {
  const { selectedType, setSelectedType, maxPrice, setMaxPrice } = useStore();

  const categories = [
    { key: "", label: "All Items" },
    { key: "t-shirt", label: "T-Shirts" },
    { key: "shirt", label: "Shirts" },
    { key: "jeans", label: "Denim & Jeans" },
    { key: "hoodie", label: "Hoodies & Sweats" },
    { key: "short", label: "Shorts" },
  ];

  const handleReset = () => {
    setSelectedType("");
    setMaxPrice(6000);
    if (onClose) onClose();
  };

  const content = (
    <div className="bg-white border border-stone-200/80 rounded-2xl p-5 sm:p-6 shadow-[0_2px_12px_-2px_rgba(0,0,0,0.04)]">
      {/* Header */}
      <div className="flex justify-between items-center pb-4 border-b border-stone-100">
        <div className="flex items-center gap-2">
          <SlidersHorizontal className="h-4 w-4 text-[#C45C26]" />
          <h3 className="font-bold text-sm uppercase tracking-wider text-stone-900">Filter By</h3>
        </div>
        {isMobile && onClose ? (
          <button
            onClick={onClose}
            className="p-1.5 rounded-full hover:bg-stone-100 text-stone-500 cursor-pointer"
            title="Close filters"
          >
            <X size={18} />
          </button>
        ) : (
          (selectedType !== "" || maxPrice < 6000) && (
            <button
              onClick={handleReset}
              className="text-[11px] font-semibold text-stone-400 hover:text-[#6e1423] transition-colors flex items-center gap-1 cursor-pointer"
            >
              <RotateCcw size={11} />
              <span>Reset</span>
            </button>
          )
        )}
      </div>

      {/* Categories */}
      <div className="py-5 border-b border-stone-100">
        <p className="text-xs font-bold uppercase tracking-wider text-stone-400 mb-3">Categories</p>
        <div className="space-y-1.5">
          {categories.map((c) => {
            const isSelected = selectedType.toLowerCase() === c.key.toLowerCase();
            return (
              <button
                key={c.key}
                type="button"
                onClick={() => {
                  setSelectedType(c.key);
                  if (isMobile && onClose) onClose();
                }}
                className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium transition-all cursor-pointer ${
                  isSelected
                    ? "bg-stone-900 text-white font-semibold shadow-xs"
                    : "text-stone-600 hover:bg-stone-100 hover:text-stone-900"
                }`}
              >
                <span>{c.label}</span>
                {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-[#C45C26]" />}
              </button>
            );
          })}
        </div>
      </div>

      {/* Price Range Slider */}
      <div className="pt-5 space-y-3">
        <div className="flex items-center justify-between">
          <p className="text-xs font-bold uppercase tracking-wider text-stone-400">Max Budget</p>
          <span className="text-xs font-bold text-stone-900 bg-stone-100 px-2.5 py-0.5 rounded-full">
            ₹{maxPrice.toLocaleString("en-IN")}
          </span>
        </div>

        <input
          type="range"
          min="50"
          max="6000"
          step="50"
          value={maxPrice}
          onChange={(e) => setMaxPrice(Number(e.target.value))}
          className="w-full accent-stone-900 cursor-pointer h-1.5 bg-stone-200 rounded-lg appearance-none"
        />

        <div className="flex justify-between text-[11px] font-medium text-stone-400">
          <span>₹50</span>
          <span>₹6,000</span>
        </div>
      </div>

      {/* Reset Button */}
      {(selectedType !== "" || maxPrice < 6000) && (
        <button
          onClick={handleReset}
          className="w-full mt-6 py-2.5 rounded-xl border border-stone-200 text-stone-700 hover:bg-stone-50 text-xs font-semibold tracking-wider uppercase transition-colors cursor-pointer"
        >
          Clear all filters
        </button>
      )}
    </div>
  );

  if (isMobile) {
    return content;
  }

  return (
    <aside className="hidden md:block w-64 lg:w-72 flex-shrink-0 sticky top-[106px] sm:top-[112px] self-start max-h-[calc(100vh-125px)] overflow-y-auto custom-scrollbar">
      {content}
    </aside>
  );
}
