import { Input } from "../ui/input";
import { Button } from "../ui/button";

export function Footer() {
  return (
    <footer className="bg-[#F0F0F0] mt-24 pt-16 pb-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-black rounded-[20px] p-8 -mt-32 mb-16 flex flex-col md:flex-row justify-between items-center gap-6">
          <h2 className="text-3xl md:text-4xl font-black text-white max-w-md uppercase">
            STAY UPTO DATE ABOUT OUR LATEST OFFERS
          </h2>
          <div className="flex flex-col gap-3 w-full max-w-sm">
            <Input placeholder="Enter your email address" className="bg-white rounded-full h-12" />
            <Button variant="secondary" className="rounded-full h-12 w-full text-black bg-white hover:bg-gray-200">
              Subscribe to Newsletter
            </Button>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-5 gap-8 mb-12">
          <div className="md:col-span-2">
            <h3 className="text-3xl font-black mb-4">SHOP.CO</h3>
            <p className="text-gray-500 text-sm max-w-xs mb-6">
              We have clothes that suits your style and which you're proud to wear. From women to men.
            </p>
          </div>
          <div>
            <h4 className="font-bold tracking-widest text-sm mb-4">COMPANY</h4>
            <ul className="space-y-3 text-sm text-gray-500">
              <li>About</li>
              <li>Features</li>
              <li>Works</li>
              <li>Career</li>
            </ul>
          </div>
          <div>
            <h4 className="font-bold tracking-widest text-sm mb-4">HELP</h4>
            <ul className="space-y-3 text-sm text-gray-500">
              <li>Customer Support</li>
              <li>Delivery Details</li>
              <li>Terms & Conditions</li>
              <li>Privacy Policy</li>
            </ul>
          </div>
          <div>
            <h4 className="font-bold tracking-widest text-sm mb-4">FAQ</h4>
            <ul className="space-y-3 text-sm text-gray-500">
              <li>Account</li>
              <li>Manage Deliveries</li>
              <li>Orders</li>
              <li>Payment</li>
            </ul>
          </div>
        </div>
        <div className="border-t border-gray-300 pt-6 flex flex-col md:flex-row justify-between items-center">
          <p className="text-sm text-gray-500">Shop.co © 2000-2023, All Rights Reserved</p>
        </div>
      </div>
    </footer>
  );
}
