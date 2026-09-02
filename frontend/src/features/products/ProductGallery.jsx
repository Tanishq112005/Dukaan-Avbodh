export function ProductGallery({ product }) {
  const { id, image_url } = product;
  return (
    <div className="md:w-1/2 flex gap-4">
      <div className="bg-[#EFE8DE] rounded-[28px] w-full aspect-[3/4] overflow-hidden">
        <img src={image_url || `https://picsum.photos/seed/${id}/800/1000`} className="w-full h-full object-cover"/>
      </div>
    </div>
  );
}
