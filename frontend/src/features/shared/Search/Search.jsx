import { Search as SearchIcon } from "lucide-react";
import { Input } from "../../../components/ui/input";

export function Search({ searchQuery, setSearchQuery, handleSearch }) {
  return (
    <div className="hidden md:flex flex-1 max-w-md mx-8 relative">
      <SearchIcon className="absolute left-3 top-2.5 h-4 w-4 text-ink/40" strokeWidth={1.5} />
      <Input
        placeholder="Search for products..."
        className="pl-9 bg-transparent border-b border-hairline rounded-none h-10 focus-visible:ring-0 focus-visible:border-ink"
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        onKeyDown={handleSearch}
      />
    </div>
  );
}
