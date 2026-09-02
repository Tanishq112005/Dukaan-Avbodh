import { Button } from "../../components/ui/button";
import { Link } from "react-router-dom";

export function Hero() {
  return (
    <div className="bg-paper">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-10 md:pt-14">
        <div className="grid md:grid-cols-12 gap-8 md:gap-6 items-center">
          {/* Left: copy */}
          <div className="md:col-span-6 lg:col-span-7">
            <h1 className="font-display text-[12vw] leading-[0.95] md:text-[3.6vw] md:leading-[0.95] tracking-tight uppercase">
              Find clothes
              <br />
              that matches
              <br />
              your style
            </h1>

            <p className="text-ink/60 max-w-md mt-5 md:mt-6 leading-relaxed">
              Browse through our diverse range of meticulously crafted garments,
              designed to bring out your individuality and cater to your sense
              of style.
            </p>

            <Link to="/products">
              <Button className="rounded-full px-10 h-14 text-base bg-ink hover:bg-oxblood mt-6 md:mt-8">
                Shop Now
              </Button>
            </Link>

            <div className="flex flex-wrap gap-x-8 gap-y-4 mt-10 md:mt-12 pt-8 border-t border-hairline">
              <div>
                <p className="font-display text-2xl md:text-3xl">200+</p>
                <p className="text-xs text-ink/50 mt-1">International Brands</p>
              </div>
              <div>
                <p className="font-display text-2xl md:text-3xl">2,000+</p>
                <p className="text-xs text-ink/50 mt-1">
                  High-Quality Products
                </p>
              </div>
              <div>
                <p className="font-display text-2xl md:text-3xl">30,000+</p>
                <p className="text-xs text-ink/50 mt-1">Happy Customers</p>
              </div>
            </div>
          </div>

          {/* Right: image */}
          <div className="md:col-span-6 lg:col-span-5 flex justify-center md:justify-end">
            <img
              src="https://e-commerce.alkanaziz.com/images/hero/hero-small.png"
              alt="Model wearing the new season edit"
              className="w-full max-h-[46vh] md:max-h-[665px] object-contain object-bottom"
              width="1200"
              height="1400"
              fetchpriority="high"
            />
          </div>
        </div>
      </div>

      <div className="bg-ink py-6 border-y border-hairline mt-10 md:mt-14">
        <div className="max-w-7xl mx-auto px-4 flex flex-wrap justify-between items-center gap-y-3 text-white/90 font-display text-xl md:text-3xl">
          <span>Versace</span>
          <span>Zara</span>
          <span>Gucci</span>
          <span>Prada</span>
          <span>Calvin Klein</span>
        </div>
      </div>
    </div>
  );
}
