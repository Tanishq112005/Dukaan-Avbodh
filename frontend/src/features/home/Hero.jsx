import { Button } from "../../components/ui/button";
import { Link } from "react-router-dom";

export function Hero() {
  return (
    <div className="bg-[#F2F0F1] pt-10 px-4 md:px-0">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center gap-8">
        <div className="md:w-1/2 md:pl-8">
          <h1 className="text-4xl md:text-6xl font-black leading-none mb-6">
            FIND CLOTHES THAT MATCHES YOUR STYLE
          </h1>
          <p className="text-gray-500 mb-8 max-w-md">
            Browse through our diverse range of meticulously crafted garments, designed to bring out your individuality and cater to your sense of style.
          </p>
          <Link to="/products">
            <Button className="w-full md:w-auto rounded-full px-12 py-6 text-lg">
              Shop Now
            </Button>
          </Link>
          <div className="flex gap-8 mt-12 mb-8">
            <div><p className="text-3xl font-bold">200+</p><p className="text-xs text-gray-500">International Brands</p></div>
            <div><p className="text-3xl font-bold">2,000+</p><p className="text-xs text-gray-500">High-Quality Products</p></div>
            <div><p className="text-3xl font-bold">30,000+</p><p className="text-xs text-gray-500">Happy Customers</p></div>
          </div>
        </div>
        <div className="md:w-1/2 mt-8 md:mt-0 relative">
          <img 
            src="https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?q=80&w=800&auto=format&fit=crop" 
            alt="Fashion Models" 
            className="w-full h-[500px] object-cover object-top" 
          />
        </div>
      </div>
      <div className="bg-black py-8">
        <div className="max-w-7xl mx-auto px-4 flex flex-wrap justify-between items-center text-white font-serif text-2xl md:text-4xl">
          <span>VERSACE</span>
          <span>ZARA</span>
          <span>GUCCI</span>
          <span className="font-sans font-black">PRADA</span>
          <span>Calvin Klein</span>
        </div>
      </div>
    </div>
  );
}
