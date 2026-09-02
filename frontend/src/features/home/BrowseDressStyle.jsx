import { Link } from "react-router-dom";

const styles = [
  { name: "Casual", span: "", img: "https://images.unsplash.com/photo-1552374196-1ab2a1c593e8?q=80&w=800&auto=format&fit=crop" },
  { name: "Formal", span: "md:col-span-2", img: "https://images.unsplash.com/photo-1594938291221-94f18cbb5660?q=80&w=1200&auto=format&fit=crop" },
  { name: "Party", span: "md:col-span-2", img: "https://images.unsplash.com/photo-1566288623394-377af472d81b?q=80&w=1200&auto=format&fit=crop" },
  { name: "Gym", span: "", img: "https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?q=80&w=800&auto=format&fit=crop" },
];

export function BrowseDressStyle() {
  return (
    <section className="py-8 pb-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-stone-900 rounded-[40px] p-8 md:p-16 text-white">
          <h2 className="font-display text-3xl md:text-5xl font-extrabold text-center mb-12 uppercase">
            Browse by dress style
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {styles.map((s) => (
              <Link
                key={s.name}
                to="/products"
                className={`relative overflow-hidden rounded-[24px] h-64 p-6 text-2xl font-bold bg-cover bg-center group ${s.span}`}
                style={{ backgroundImage: `url(${s.img})` }}
              >
                <div className="absolute inset-0 bg-black/20 group-hover:bg-black/35 transition-colors" />
                <span className="relative bg-white text-stone-900 px-4 py-1.5 rounded-full text-lg">{s.name}</span>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
