import { Search as SearchIcon, X } from "lucide-react";
import { Input } from "../../../components/ui/input";

export function Search({ searchQuery, setSearchQuery, handleSearch }) {
  return (
    <div className="hidden md:flex flex-1 max-w-md lg:max-w-lg xl:max-w-xl mx-6 lg:mx-10 relative items-center">
      <SearchIcon className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-stone-400" strokeWidth={1.75} />
      <Input
        placeholder="Search for products, brands, styles..."
        className="pl-10 pr-9 bg-stone-100/80 hover:bg-stone-100 border border-stone-200/80 rounded-full h-10 text-xs sm:text-sm text-stone-900 placeholder:text-stone-400 transition-all focus-visible:bg-white focus-visible:border-stone-400 focus-visible:ring-2 focus-visible:ring-stone-900/10 shadow-xs"
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        onKeyDown={handleSearch}
      />
      {searchQuery && (
        <button
          type="button"
          onClick={() => setSearchQuery("")}
          className="absolute right-3 top-1/2 -translate-y-1/2 p-0.5 rounded-full text-stone-400 hover:text-stone-700 transition-colors cursor-pointer"
          title="Clear search"
        >
          <X size={14} />
        </button>
      )}
    </div>
  );
}
