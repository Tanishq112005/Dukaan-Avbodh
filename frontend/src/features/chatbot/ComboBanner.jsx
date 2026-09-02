export function ComboBanner({ comboOffer }) {
  if (!comboOffer) return null;
  return (
    <div className="bg-[#F3E7DC] border border-[#E4D0BE] rounded-2xl p-3 text-sm text-stone-800 shadow-sm">
      <div className="flex items-center gap-2 mb-1.5">
        <span className="text-xs font-black tracking-[0.16em] uppercase text-[#C45C26]">Bundle</span>
        <strong className="font-semibold tracking-tight">Limited combo offer</strong>
      </div>
      <p className="opacity-90 mb-2">
        Buy {comboOffer.products?.map(p => p.name).join(" + ") || "these items"} together for a <span className="font-bold">{Math.abs(comboOffer.effective_discount_percent).toFixed(2)}%</span> discount.
      </p>
      <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-hide">
        {comboOffer.products?.map(p => (
          <a key={p.id} href={`/product/${p.id}`} title={p.name} className="flex-shrink-0 relative group block">
            <img src={p.image || `https://via.placeholder.com/60?text=${p.name.charAt(0)}`} alt={p.name} className="w-12 h-12 rounded-md object-cover border border-[#E4D0BE] bg-white" />
          </a>
        ))}
      </div>
    </div>
  );
}
