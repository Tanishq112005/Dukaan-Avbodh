import { Search as SearchIcon } from "lucide-react";
import { Input } from "../../../components/ui/input";

export function Search({ searchQuery, setSearchQuery, handleSearch }) {
  return (
    <div className="hidden md:flex flex-1 max-w-md mx-8 relative">
      <SearchIcon className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
      <Input 
        placeholder="Search for products..." 
        className="pl-10 bg-[#EFE8DE] border-none rounded-full h-11" 
        value={searchQuery} 
        onChange={(e) => setSearchQuery(e.target.value)} 
        onKeyDown={handleSearch} 
      />
    </div>
  );
}
