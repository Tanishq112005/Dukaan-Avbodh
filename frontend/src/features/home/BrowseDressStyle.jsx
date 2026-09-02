import { Link } from "react-router-dom";

const styles = [
  { name: "Casual", img: "https://images.unsplash.com/photo-1552374196-1ab2a1c593e8?q=80&w=800&auto=format&fit=crop" },
  { name: "Formal", img: "https://images.unsplash.com/photo-1594938291221-94f18cbb5660?q=80&w=800&auto=format&fit=crop" },
  { name: "Party", img: "https://images.unsplash.com/photo-1566288623394-377af472d81b?q=80&w=800&auto=format&fit=crop" },
  { name: "Gym", img: "https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?q=80&w=800&auto=format&fit=crop" },
];

export function BrowseDressStyle() {
  return (
    <section className="py-16 md:py-20 border-t border-hairline">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 className="font-display text-3xl md:text-5xl mb-10">Shop by occasion</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-5">
          {styles.map((s) => (
            <Link
              key={s.name}
              to="/products"
              className="group relative block border border-hairline overflow-hidden"
            >
              <div className="aspect-[3/4] overflow-hidden">
                <img
                  src={s.img}
                  alt={s.name}
                  loading="lazy"
                  decoding="async"
                  width="400"
                  height="533"
                  className="w-full h-full object-cover transition-transform duration-700 ease-out group-hover:scale-105"
                />
              </div>
              <span className="absolute bottom-0 left-0 right-0 bg-paper/95 px-4 py-3 font-display text-lg border-t border-hairline">
                {s.name}
              </span>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
