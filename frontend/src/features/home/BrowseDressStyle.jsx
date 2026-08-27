export function BrowseDressStyle() {
  return (
    <section className="py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-[#F0F0F0] rounded-[40px] p-8 md:p-16">
          <h2 className="text-3xl md:text-4xl font-black text-center mb-12 uppercase">
            BROWSE BY DRESS STYLE
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-[20px] h-64 p-6 text-2xl font-bold bg-cover bg-center bg-no-repeat" style={{backgroundImage: 'url(https://images.unsplash.com/photo-1552374196-1ab2a1c593e8?q=80&w=400&auto=format&fit=crop)'}}>
              <span className="bg-white/80 px-4 py-1 rounded-md">Casual</span>
            </div>
            <div className="bg-white rounded-[20px] h-64 p-6 text-2xl font-bold md:col-span-2 bg-cover bg-center bg-no-repeat" style={{backgroundImage: 'url(https://images.unsplash.com/photo-1594938291221-94f18cbb5660?q=80&w=800&auto=format&fit=crop)'}}>
              <span className="bg-white/80 px-4 py-1 rounded-md">Formal</span>
            </div>
            <div className="bg-white rounded-[20px] h-64 p-6 text-2xl font-bold md:col-span-2 bg-cover bg-center bg-no-repeat" style={{backgroundImage: 'url(https://images.unsplash.com/photo-1566288623394-377af472d81b?q=80&w=800&auto=format&fit=crop)'}}>
              <span className="bg-white/80 px-4 py-1 rounded-md">Party</span>
            </div>
            <div className="bg-white rounded-[20px] h-64 p-6 text-2xl font-bold bg-cover bg-center bg-no-repeat" style={{backgroundImage: 'url(https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?q=80&w=400&auto=format&fit=crop)'}}>
              <span className="bg-white/80 px-4 py-1 rounded-md">Gym</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
