import { Loader2 } from "lucide-react";

export function Loader() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
      <Loader2 className="w-12 h-12 animate-spin text-black" />
      <p className="text-gray-500 font-medium animate-pulse">Loading, please wait...</p>
    </div>
  );
}
