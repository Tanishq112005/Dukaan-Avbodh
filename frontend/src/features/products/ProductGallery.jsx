export function ProductGallery({ product }) {
  const { id, image_url } = product;
  return (
    <div className="md:w-1/2 flex gap-4">
      <div className="flex flex-col gap-4 w-1/4">
        <div className="bg-[#F0EEED] rounded-[20px] aspect-square overflow-hidden"><img src={image_url || `https://picsum.photos/seed/${id}/200/200`} className="w-full h-full object-cover mix-blend-multiply"/></div>
        <div className="bg-[#F0EEED] rounded-[20px] aspect-square overflow-hidden"><img src={image_url || `https://picsum.photos/seed/${id}a/200/200`} className="w-full h-full object-cover mix-blend-multiply"/></div>
        <div className="bg-[#F0EEED] rounded-[20px] aspect-square overflow-hidden"><img src={image_url || `https://picsum.photos/seed/${id}b/200/200`} className="w-full h-full object-cover mix-blend-multiply"/></div>
      </div>
      <div className="bg-[#F0EEED] rounded-[20px] w-3/4 aspect-[3/4] overflow-hidden"><img src={image_url || `https://picsum.photos/seed/${id}/800/1000`} className="w-full h-full object-cover mix-blend-multiply"/></div>
    </div>
  );
}
