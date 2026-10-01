"use client";

import { useState, useMemo, useEffect } from "react";
import Link from "next/link";
import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { toast } from "sonner";
import { ProtectedRoute } from "@/components/protected-route";
import { apiClient } from "@/lib/api-client";

interface CarListing {
  id: string;
  title: string;
  year: number;
  brand: string;
  bodyType: string;
  fuelType: string;
  transmission: string;
  km: number;
  priceLakh: number;
  location: string;
  certified: boolean;
  image: string;
  owner: string;
  color?: string;
}

const CAR_DATA: CarListing[] = [
  {
    id: "used-2",
    title: "2022 Maruti Baleno Zeta",
    year: 2022,
    brand: "Maruti Suzuki",
    bodyType: "Hatchback",
    fuelType: "Petrol",
    transmission: "Manual",
    km: 19500,
    priceLakh: 7.2,
    location: "Delhi",
    certified: false,
    owner: "2nd Owner",
    image: "https://images10.gaadi.com/usedcar_image/5434165/original/9e1f9d38dfa30cf63f5d676305a63d5d.jpg?imwidth=640",
    color: "gray",
  },
  {
    id: "used-3",
    title: "2020 Honda City VX CVT",
    year: 2020,
    brand: "Honda",
    bodyType: "Sedan",
    fuelType: "Petrol",
    transmission: "Automatic",
    km: 42000,
    priceLakh: 9.85,
    location: "Bangalore",
    certified: true,
    owner: "1st Owner",
    image: "https://images10.gaadi.com/usedcar_image/5434176/original/processed_a977f02bdfa58472edd46dd14f47f3a9.jpeg?imwidth=640",
    color: "white",
  },
  {
    id: "used-4",
    title: "2023 Mercedes-Benz C-Class C200",
    year: 2023,
    brand: "Mercedes-Benz",
    bodyType: "Luxury",
    fuelType: "Petrol",
    transmission: "Automatic",
    km: 12000,
    priceLakh: 52.0,
    location: "Delhi",
    certified: true,
    owner: "1st Owner",
    image: "https://images10.gaadi.com/usedcar_image/5434169/original/a3d1b596aab4486919bfddbbc717c600.jpg?imwidth=640",
    color: "gray",
  },
];

const BRANDS = ["Mercedes-Benz", "BMW", "Audi", "Jeep", "Lexus", "Volvo", "Hyundai", "Maruti Suzuki", "Honda", "Toyota", "Kia", "Tata", "Mahindra"];
const YEARS = [
  { label: "2024 & above", value: 2024 },
  { label: "2022 & above", value: 2022 },
  { label: "2020 & above", value: 2020 },
  { label: "2018 & above", value: 2018 },
  { label: "2016 & above", value: 2016 },
  { label: "2014 & above", value: 2014 },
  { label: "2012 & above", value: 2012 },
  { label: "2010 & above", value: 2010 },
];
const KMS = [
  { label: "10,000 kms or less", value: 10000 },
  { label: "30,000 kms or less", value: 30000 },
  { label: "50,000 kms or less", value: 50000 },
  { label: "75,000 kms or less", value: 75000 },
  { label: "1,00,000 kms or less", value: 100000 },
  { label: "1,25,000 kms or less", value: 125000 },
  { label: "1,50,000 kms or less", value: 150000 },
];
const FUELS = ["Petrol", "Diesel", "CNG", "Electric", "Hybrid"];
const BODIES = ["Hatchback", "Sedan", "SUV", "MUV"];
const TRANSMISSIONS = ["Automatic", "Manual"];
const COLORS = [
  { name: "yellow", class: "bg-yellow-400" },
  { name: "red", class: "bg-red-600" },
  { name: "beige", class: "bg-[#e1c699]" },
  { name: "purple", class: "bg-purple-600" },
  { name: "white", class: "bg-card border border-gray-300" },
  { name: "light-gray", class: "bg-gray-300" },
  { name: "dark-gray", class: "bg-gray-600" },
  { name: "black", class: "bg-black" },
  { name: "blue", class: "bg-blue-600" },
  { name: "green", class: "bg-green-600" },
  { name: "orange", class: "bg-orange-500" },
];
const SAFETY_FEATURES = ["Airbags", "ABS", "Sunroof", "Alloy Wheels", "Cruise Control", "Leather Seats"];
const SEATS = ["5 Seater", "7 Seater", "8 Seater"];
const RTOS = ["MH", "DL", "KA", "UP", "HR"];
const OWNERS = ["1st Owner", "2nd Owner", "3rd Owner"];

function SearchResultsPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [sortBy, setSortBy] = useState<string>("relevance");
  const [selectedCar, setSelectedCar] = useState<CarListing | null>(null);
  const [allCars, setAllCars] = useState<CarListing[]>(CAR_DATA);

  // Load user posted listings from database
  useEffect(() => {
    async function loadListings() {
      try {
        const { data } = await apiClient.get("/predictions/marketplace/listings");
        if (data.data && Array.isArray(data.data) && data.data.length > 0) {
          // Use local sessionStorage image if available (fallback for local missing Cloudinary config)
          const enhancedListings = data.data.map((listing: CarListing) => {
             if (typeof window !== "undefined") {
                 const localImage = sessionStorage.getItem(`preview_image_${listing.id}`);
                 if (localImage) {
                     return { ...listing, image: localImage };
                 }
             }
             return listing;
          });
          
          const enhancedTitles = new Set(enhancedListings.map((l: CarListing) => l.title.toLowerCase()));
          const filteredCarData = CAR_DATA.filter(c => !enhancedTitles.has(c.title.toLowerCase()));
          
          setAllCars([...enhancedListings, ...filteredCarData]);
        }
      } catch (e) {
        console.error("Failed to load user listings from database", e);
      }
    }
    loadListings();
  }, []);

  // Advanced Filters State
  const [minPrice, setMinPrice] = useState(50000);
  const [maxPrice, setMaxPrice] = useState(7000000);
  const [brandSearch, setBrandSearch] = useState("");
  const [selectedBrands, setSelectedBrands] = useState<string[]>([]);
  const [selectedYears, setSelectedYears] = useState<number[]>([]);
  const [selectedKms, setSelectedKms] = useState<number[]>([]);
  const [selectedFuels, setSelectedFuels] = useState<string[]>([]);
  const [selectedBodies, setSelectedBodies] = useState<string[]>([]);
  const [selectedTransmissions, setSelectedTransmissions] = useState<string[]>([]);
  const [selectedColors, setSelectedColors] = useState<string[]>([]);
  const [selectedSafety, setSelectedSafety] = useState<string[]>([]);
  const [selectedSeats, setSelectedSeats] = useState<string[]>([]);
  const [selectedRtos, setSelectedRtos] = useState<string[]>([]);
  const [selectedOwners, setSelectedOwners] = useState<string[]>([]);

  // Accordion Toggle States
  const [accordions, setAccordions] = useState({
    brands: true,
    year: true,
    kms: true,
    fuel: true,
    body: true,
    trans: true,
    color: true,
    safety: true,
    seats: true,
    rto: true,
    owner: true,
  });

  const toggleAccordion = (section: keyof typeof accordions) => {
    setAccordions((prev) => ({ ...prev, [section]: !prev[section] }));
  };

  const filteredBrands = useMemo(() => {
    return BRANDS.filter((brand) => brand.toLowerCase().includes(brandSearch.toLowerCase()));
  }, [brandSearch]);

  const toggleFilter = (list: any[], setList: Function, value: any) => {
    if (list.includes(value)) {
      setList(list.filter((item) => item !== value));
    } else {
      setList([...list, value]);
    }
  };

  const filteredCars = useMemo(() => {
    return allCars.filter((car) => {
      const matchesSearch =
        !searchTerm ||
        car.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        car.brand.toLowerCase().includes(searchTerm.toLowerCase());

      const price = car.priceLakh * 100000;
      const matchesPrice = price >= minPrice && price <= maxPrice;

      const matchesBrand = selectedBrands.length === 0 || selectedBrands.includes(car.brand);

      const matchesYear =
        selectedYears.length === 0 || selectedYears.some((yearLimit) => car.year >= yearLimit);

      const matchesKm =
        selectedKms.length === 0 || selectedKms.some((kmLimit) => car.km <= kmLimit);

      const matchesFuel = selectedFuels.length === 0 || selectedFuels.includes(car.fuelType);

      const matchesBody = selectedBodies.length === 0 || selectedBodies.includes(car.bodyType);

      const matchesTrans =
        selectedTransmissions.length === 0 || selectedTransmissions.includes(car.transmission);

      const matchesColor =
        selectedColors.length === 0 || (car.color && selectedColors.includes(car.color));

      const matchesOwner =
        selectedOwners.length === 0 || selectedOwners.includes(car.owner);

      return (
        matchesSearch &&
        matchesPrice &&
        matchesBrand &&
        matchesYear &&
        matchesKm &&
        matchesFuel &&
        matchesBody &&
        matchesTrans &&
        matchesColor &&
        matchesOwner
      );
    }).sort((a, b) => {
      if (sortBy === "price_low") return a.priceLakh - b.priceLakh;
      if (sortBy === "price_high") return b.priceLakh - a.priceLakh;
      if (sortBy === "km_low") return a.km - b.km;
      if (sortBy === "year_new") return b.year - a.year;
      return 0;
    });
  }, [
    searchTerm,
    minPrice,
    maxPrice,
    selectedBrands,
    selectedYears,
    selectedKms,
    selectedFuels,
    selectedBodies,
    selectedTransmissions,
    selectedColors,
    selectedOwners,
    sortBy,
  ]);

  const handleQuote = (car: CarListing) => {
    setSelectedCar(car);
  };

  const submitQuote = (e: React.FormEvent) => {
    e.preventDefault();
    toast.success(`Quote request submitted for ${selectedCar?.title}! A dealer concierge will call you shortly.`);
    setSelectedCar(null);
  };

  const resetAllFilters = () => {
    setMinPrice(50000);
    setMaxPrice(7000000);
    setSelectedBrands([]);
    setSelectedYears([]);
    setSelectedKms([]);
    setSelectedFuels([]);
    setSelectedBodies([]);
    setSelectedTransmissions([]);
    setSelectedColors([]);
    setSelectedSafety([]);
    setSelectedSeats([]);
    setSelectedRtos([]);
    setSelectedOwners([]);
    setSearchTerm("");
  };

  return (
    <div className="min-h-screen bg-surface-gray text-on-surface flex flex-col font-sans">
      <Navbar />

      <main className="pt-20 pb-16 max-w-7xl mx-auto px-4 md:px-8 w-full flex-1">
        {/* Search Header Bar */}
        <div className="bg-card rounded-2xl p-4 md:p-6 border border-surface-variant mb-8">
          <div className="flex flex-col lg:flex-row items-center gap-4">
            <div className="relative flex-1 w-full">
              <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-on-surface-variant">
                search
              </span>
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search by Make, Model, or Keyword (e.g. BMW, SUV, Creta)..."
                className="w-full bg-surface-container-low pl-12 pr-4 py-3 rounded-xl outline-none text-sm border border-transparent focus:border-primary transition-all text-on-surface"
              />
            </div>

            <div className="flex items-center gap-4 w-full lg:w-auto justify-between lg:justify-end">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-on-surface-variant">Sort By:</span>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="bg-surface-container-low text-xs font-semibold px-3 py-2.5 rounded-xl outline-none text-on-surface cursor-pointer border border-surface-variant"
                >
                  <option value="relevance">Relevance</option>
                  <option value="price_low">Price: Low to High</option>
                  <option value="price_high">Price: High to Low</option>
                  <option value="km_low">Lowest Mileage</option>
                  <option value="year_new">Newest Model Year</option>
                </select>
              </div>

              <span className="text-xs font-bold text-primary px-3 py-1.5 rounded-full bg-mint-soft">
                {filteredCars.length} Cars Available
              </span>
            </div>
          </div>
        </div>

        {/* Main Grid with Sidebar */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Filter Sidebar */}
          <div className="lg:col-span-1 space-y-6 bg-card p-5 rounded-2xl border border-surface-variant h-fit sticky top-24 overflow-y-auto max-h-[80vh] scrollbar-thin">
            <div className="flex items-center justify-between pb-3 border-b border-surface-variant">
              <h3 className="font-bold text-base text-on-surface flex items-center gap-1.5">
                <span className="material-symbols-outlined text-primary text-xl">filter_list</span>
                Filters
              </h3>
              <button
                onClick={resetAllFilters}
                className="text-xs font-semibold text-primary hover:underline"
              >
                Reset All
              </button>
            </div>

            {/* Price Range Slider */}
            <div className="space-y-4">
              <span className="text-xs font-bold text-on-surface uppercase tracking-wider block">Price Range</span>
              <div className="flex justify-between items-center text-xs font-bold text-primary">
                <span>₹{minPrice.toLocaleString("en-IN")}</span>
                <span>₹{maxPrice.toLocaleString("en-IN")}</span>
              </div>
              <div className="flex gap-2">
                <input
                  type="range"
                  min="50000"
                  max="7000000"
                  step="50000"
                  value={maxPrice}
                  onChange={(e) => setMaxPrice(Number(e.target.value))}
                  className="w-full accent-primary cursor-pointer"
                />
              </div>
              <div className="flex justify-between text-[9px] text-on-surface-variant font-semibold">
                <span>Minimum</span>
                <span>Maximum</span>
              </div>
            </div>

            {/* Brands + Models */}
            <div className="border-t border-surface-variant pt-4 space-y-3">
              <button
                onClick={() => toggleAccordion("brands")}
                className="flex items-center justify-between w-full text-xs font-bold text-on-surface uppercase tracking-wider"
              >
                <span>Brands + Models</span>
                <span className={`material-symbols-outlined text-base transition-transform ${accordions.brands ? "rotate-180" : ""}`}>
                  keyboard_arrow_down
                </span>
              </button>

              {accordions.brands && (
                <div className="space-y-3 animate-in fade-in duration-200">
                  <div className="relative">
                    <span className="material-symbols-outlined absolute left-2.5 top-1/2 -translate-y-1/2 text-on-surface-variant text-base">
                      search
                    </span>
                    <input
                      type="text"
                      placeholder="Search"
                      value={brandSearch}
                      onChange={(e) => setBrandSearch(e.target.value)}
                      className="w-full bg-surface-container-low pl-8 pr-3 py-1.5 rounded-lg text-xs outline-none border border-surface-variant"
                    />
                  </div>
                  <div className="max-h-40 overflow-y-auto space-y-2 pr-1 scrollbar-thin">
                    {filteredBrands.map((brand) => (
                      <label key={brand} className="flex items-center justify-between text-xs font-medium text-on-surface cursor-pointer select-none">
                        <div className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            checked={selectedBrands.includes(brand)}
                            onChange={() => toggleFilter(selectedBrands, setSelectedBrands, brand)}
                            className="w-4 h-4 rounded border-gray-300 text-primary accent-primary cursor-pointer"
                          />
                          <span>{brand}</span>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Year Filter */}
            <div className="border-t border-surface-variant pt-4 space-y-3">
              <button
                onClick={() => toggleAccordion("year")}
                className="flex items-center justify-between w-full text-xs font-bold text-on-surface uppercase tracking-wider"
              >
                <span>Year</span>
                <span className={`material-symbols-outlined text-base transition-transform ${accordions.year ? "rotate-180" : ""}`}>
                  keyboard_arrow_down
                </span>
              </button>

              {accordions.year && (
                <div className="space-y-2 animate-in fade-in duration-200">
                  {YEARS.map((y) => (
                    <label key={y.value} className="flex items-center gap-2.5 text-xs font-semibold text-on-surface-variant cursor-pointer select-none">
                      <input
                        type="checkbox"
                        checked={selectedYears.includes(y.value)}
                        onChange={() => toggleFilter(selectedYears, setSelectedYears, y.value)}
                        className="w-4.5 h-4.5 rounded-full border-gray-300 text-primary accent-primary cursor-pointer"
                      />
                      <span>{y.label}</span>
                    </label>
                  ))}
                </div>
              )}
            </div>

            {/* Kms Driven Filter */}
            <div className="border-t border-surface-variant pt-4 space-y-3">
              <button
                onClick={() => toggleAccordion("kms")}
                className="flex items-center justify-between w-full text-xs font-bold text-on-surface uppercase tracking-wider"
              >
                <span>Kms Driven</span>
                <span className={`material-symbols-outlined text-base transition-transform ${accordions.kms ? "rotate-180" : ""}`}>
                  keyboard_arrow_down
                </span>
              </button>

              {accordions.kms && (
                <div className="space-y-2 animate-in fade-in duration-200">
                  {KMS.map((k) => (
                    <label key={k.value} className="flex items-center gap-2.5 text-xs font-semibold text-on-surface-variant cursor-pointer select-none">
                      <input
                        type="checkbox"
                        checked={selectedKms.includes(k.value)}
                        onChange={() => toggleFilter(selectedKms, setSelectedKms, k.value)}
                        className="w-4.5 h-4.5 rounded-full border-gray-300 text-primary accent-primary cursor-pointer"
                      />
                      <span>{k.label}</span>
                    </label>
                  ))}
                </div>
              )}
            </div>

            {/* Fuel Type */}
            <div className="border-t border-surface-variant pt-4 space-y-3">
              <button
                onClick={() => toggleAccordion("fuel")}
                className="flex items-center justify-between w-full text-xs font-bold text-on-surface uppercase tracking-wider"
              >
                <span>Fuel Type</span>
                <span className={`material-symbols-outlined text-base transition-transform ${accordions.fuel ? "rotate-180" : ""}`}>
                  keyboard_arrow_down
                </span>
              </button>

              {accordions.fuel && (
                <div className="space-y-2 animate-in fade-in duration-200">
                  {FUELS.map((fuel) => (
                    <label key={fuel} className="flex items-center gap-2.5 text-xs font-semibold text-on-surface-variant cursor-pointer select-none">
                      <input
                        type="checkbox"
                        checked={selectedFuels.includes(fuel)}
                        onChange={() => toggleFilter(selectedFuels, setSelectedFuels, fuel)}
                        className="w-4.5 h-4.5 rounded-full border-gray-300 text-primary accent-primary cursor-pointer"
                      />
                      <span>{fuel}</span>
                    </label>
                  ))}
                </div>
              )}
            </div>

            {/* Body Type */}
            <div className="border-t border-surface-variant pt-4 space-y-3">
              <button
                onClick={() => toggleAccordion("body")}
                className="flex items-center justify-between w-full text-xs font-bold text-on-surface uppercase tracking-wider"
              >
                <span>Body Type</span>
                <span className={`material-symbols-outlined text-base transition-transform ${accordions.body ? "rotate-180" : ""}`}>
                  keyboard_arrow_down
                </span>
              </button>

              {accordions.body && (
                <div className="space-y-2 animate-in fade-in duration-200">
                  {BODIES.map((body) => (
                    <label key={body} className="flex items-center gap-2.5 text-xs font-semibold text-on-surface-variant cursor-pointer select-none">
                      <input
                        type="checkbox"
                        checked={selectedBodies.includes(body)}
                        onChange={() => toggleFilter(selectedBodies, setSelectedBodies, body)}
                        className="w-4.5 h-4.5 rounded-full border-gray-300 text-primary accent-primary cursor-pointer"
                      />
                      <span>{body}</span>
                    </label>
                  ))}
                </div>
              )}
            </div>

            {/* Transmission */}
            <div className="border-t border-surface-variant pt-4 space-y-3">
              <button
                onClick={() => toggleAccordion("trans")}
                className="flex items-center justify-between w-full text-xs font-bold text-on-surface uppercase tracking-wider"
              >
                <span>Transmission</span>
                <span className={`material-symbols-outlined text-base transition-transform ${accordions.trans ? "rotate-180" : ""}`}>
                  keyboard_arrow_down
                </span>
              </button>

              {accordions.trans && (
                <div className="space-y-2 animate-in fade-in duration-200">
                  {TRANSMISSIONS.map((trans) => (
                    <label key={trans} className="flex items-center gap-2.5 text-xs font-semibold text-on-surface-variant cursor-pointer select-none">
                      <input
                        type="checkbox"
                        checked={selectedTransmissions.includes(trans)}
                        onChange={() => toggleFilter(selectedTransmissions, setSelectedTransmissions, trans)}
                        className="w-4.5 h-4.5 rounded-full border-gray-300 text-primary accent-primary cursor-pointer"
                      />
                      <span>{trans}</span>
                    </label>
                  ))}
                </div>
              )}
            </div>

            {/* Color swatches */}
            <div className="border-t border-surface-variant pt-4 space-y-3">
              <button
                onClick={() => toggleAccordion("color")}
                className="flex items-center justify-between w-full text-xs font-bold text-on-surface uppercase tracking-wider"
              >
                <span>Color</span>
                <span className={`material-symbols-outlined text-base transition-transform ${accordions.color ? "rotate-180" : ""}`}>
                  keyboard_arrow_down
                </span>
              </button>

              {accordions.color && (
                <div className="flex flex-wrap gap-2 animate-in fade-in duration-200 pt-1">
                  {COLORS.map((c) => (
                    <button
                      key={c.name}
                      onClick={() => toggleFilter(selectedColors, setSelectedColors, c.name)}
                      className={`w-7 h-7 rounded-lg transition-transform ${c.class} ${
                        selectedColors.includes(c.name) ? "ring-2 ring-primary scale-110" : "hover:scale-105"
                      }`}
                      title={c.name}
                    />
                  ))}
                </div>
              )}
            </div>

            {/* Safety & Features */}
            <div className="border-t border-surface-variant pt-4 space-y-3">
              <button
                onClick={() => toggleAccordion("safety")}
                className="flex items-center justify-between w-full text-xs font-bold text-on-surface uppercase tracking-wider"
              >
                <span>Safety & Features</span>
                <span className={`material-symbols-outlined text-base transition-transform ${accordions.safety ? "rotate-180" : ""}`}>
                  keyboard_arrow_down
                </span>
              </button>

              {accordions.safety && (
                <div className="space-y-2 animate-in fade-in duration-200">
                  {SAFETY_FEATURES.map((feature) => (
                    <label key={feature} className="flex items-center gap-2.5 text-xs font-semibold text-on-surface-variant cursor-pointer select-none">
                      <input
                        type="checkbox"
                        checked={selectedSafety.includes(feature)}
                        onChange={() => toggleFilter(selectedSafety, setSelectedSafety, feature)}
                        className="w-4.5 h-4.5 rounded-full border-gray-300 text-primary accent-primary cursor-pointer"
                      />
                      <span>{feature}</span>
                    </label>
                  ))}
                </div>
              )}
            </div>

            {/* Seats */}
            <div className="border-t border-surface-variant pt-4 space-y-3">
              <button
                onClick={() => toggleAccordion("seats")}
                className="flex items-center justify-between w-full text-xs font-bold text-on-surface uppercase tracking-wider"
              >
                <span>Seats</span>
                <span className={`material-symbols-outlined text-base transition-transform ${accordions.seats ? "rotate-180" : ""}`}>
                  keyboard_arrow_down
                </span>
              </button>

              {accordions.seats && (
                <div className="space-y-2 animate-in fade-in duration-200">
                  {SEATS.map((seat) => (
                    <label key={seat} className="flex items-center gap-2.5 text-xs font-semibold text-on-surface-variant cursor-pointer select-none">
                      <input
                        type="checkbox"
                        checked={selectedSeats.includes(seat)}
                        onChange={() => toggleFilter(selectedSeats, setSelectedSeats, seat)}
                        className="w-4.5 h-4.5 rounded-full border-gray-300 text-primary accent-primary cursor-pointer"
                      />
                      <span>{seat}</span>
                    </label>
                  ))}
                </div>
              )}
            </div>

            {/* RTO */}
            <div className="border-t border-surface-variant pt-4 space-y-3">
              <button
                onClick={() => toggleAccordion("rto")}
                className="flex items-center justify-between w-full text-xs font-bold text-on-surface uppercase tracking-wider"
              >
                <span>RTO</span>
                <span className={`material-symbols-outlined text-base transition-transform ${accordions.rto ? "rotate-180" : ""}`}>
                  keyboard_arrow_down
                </span>
              </button>

              {accordions.rto && (
                <div className="space-y-2 animate-in fade-in duration-200">
                  {RTOS.map((rto) => (
                    <label key={rto} className="flex items-center gap-2.5 text-xs font-semibold text-on-surface-variant cursor-pointer select-none">
                      <input
                        type="checkbox"
                        checked={selectedRtos.includes(rto)}
                        onChange={() => toggleFilter(selectedRtos, setSelectedRtos, rto)}
                        className="w-4.5 h-4.5 rounded-full border-gray-300 text-primary accent-primary cursor-pointer"
                      />
                      <span>{rto}</span>
                    </label>
                  ))}
                </div>
              )}
            </div>

            {/* Owner */}
            <div className="border-t border-surface-variant pt-4 space-y-3">
              <button
                onClick={() => toggleAccordion("owner")}
                className="flex items-center justify-between w-full text-xs font-bold text-on-surface uppercase tracking-wider"
              >
                <span>Owner</span>
                <span className={`material-symbols-outlined text-base transition-transform ${accordions.owner ? "rotate-180" : ""}`}>
                  keyboard_arrow_down
                </span>
              </button>

              {accordions.owner && (
                <div className="space-y-2 animate-in fade-in duration-200">
                  {OWNERS.map((owner) => (
                    <label key={owner} className="flex items-center gap-2.5 text-xs font-semibold text-on-surface-variant cursor-pointer select-none">
                      <input
                        type="checkbox"
                        checked={selectedOwners.includes(owner)}
                        onChange={() => toggleFilter(selectedOwners, setSelectedOwners, owner)}
                        className="w-4.5 h-4.5 rounded-full border-gray-300 text-primary accent-primary cursor-pointer"
                      />
                      <span>{owner}</span>
                    </label>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Car Cards Results List */}
          <div className="lg:col-span-3 space-y-6">
            {filteredCars.length === 0 ? (
              <div className="bg-card rounded-2xl p-12 text-center border border-surface-variant">
                <span className="material-symbols-outlined text-5xl text-on-surface-variant mb-3">search_off</span>
                <h3 className="text-lg font-bold text-on-surface">No Cars Found Matching Criteria</h3>
                <p className="text-xs text-on-surface-variant mt-1">Try resetting your filters.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {filteredCars.map((car) => (
                  <div key={car.id} className="bg-card rounded-2xl overflow-hidden border border-surface-variant mint-glow group flex flex-col justify-between">
                    <div>
                      <div className="relative h-48 bg-surface-gray overflow-hidden">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img
                          src={car.image}
                          alt={car.title}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        />
                        {car.certified && (
                          <span className="absolute top-3 left-3 bg-primary text-white text-[10px] font-bold px-2.5 py-1 rounded-full flex items-center gap-1 shadow-sm">
                            <span className="material-symbols-outlined text-xs">verified</span>
                            IBB Certified
                          </span>
                        )}
                        <span className="absolute top-3 right-3 bg-card/90 backdrop-blur-md text-on-surface text-[10px] font-bold px-2.5 py-1 rounded-full shadow-sm">
                          {car.location}
                        </span>
                      </div>

                      <div className="p-5 space-y-3">
                        <h3 className="font-bold text-base text-on-surface group-hover:text-primary transition-colors">
                          {car.title}
                        </h3>

                        <div className="flex flex-wrap gap-2 text-[11px] text-on-surface-variant">
                          <span className="px-2 py-0.5 rounded-md bg-surface-container">
                            {car.km.toLocaleString()} km
                          </span>
                          <span className="px-2 py-0.5 rounded-md bg-surface-container">
                            {car.fuelType}
                          </span>
                          <span className="px-2 py-0.5 rounded-md bg-surface-container">
                            {car.transmission}
                          </span>
                          <span className="px-2 py-0.5 rounded-md bg-surface-container">
                            {car.owner}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="p-5 pt-0 flex items-center justify-between border-t border-surface-variant mt-3 pt-4">
                      <div>
                        <span className="text-[11px] text-on-surface-variant block">Fair Market Value</span>
                        <span className="text-xl font-extrabold text-primary">₹{car.priceLakh} Lakh</span>
                      </div>

                      <div className="flex gap-2">
                        <button
                          onClick={() => handleQuote(car)}
                          className="px-3.5 py-2 rounded-xl bg-primary-container text-on-primary-container font-bold text-xs hover:bg-emerald-500 transition-colors flex items-center gap-1"
                        >
                          Get Quote
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Quote Modal */}
      {selectedCar && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-card rounded-2xl p-6 md:p-8 max-w-md w-full border border-surface-variant shadow-2xl relative animate-in fade-in zoom-in">
            <button
              onClick={() => setSelectedCar(null)}
              className="absolute top-4 right-4 text-on-surface-variant hover:text-on-surface"
            >
              <span className="material-symbols-outlined">close</span>
            </button>

            <h3 className="text-xl font-bold text-on-surface mb-1">Get Instant Dealer Quote</h3>
            <p className="text-xs text-on-surface-variant mb-4">
              Request official price & inspection sheet for <strong className="text-primary">{selectedCar.title}</strong>
            </p>

            <form onSubmit={submitQuote} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-on-surface-variant">Your Full Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Rahul Sharma"
                  className="w-full bg-surface-container-low p-3 rounded-xl text-sm outline-none border border-surface-variant focus:border-primary"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-on-surface-variant">Phone Number</label>
                <input
                  type="tel"
                  required
                  placeholder="e.g. +91 9876543210"
                  className="w-full bg-surface-container-low p-3 rounded-xl text-sm outline-none border border-surface-variant focus:border-primary"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-on-surface-variant">Preferred City</label>
                <input
                  type="text"
                  defaultValue={selectedCar.location}
                  className="w-full bg-surface-container-low p-3 rounded-xl text-sm outline-none border border-surface-variant focus:border-primary"
                />
              </div>

              <button
                type="submit"
                className="w-full bg-primary text-white font-bold py-3.5 rounded-xl hover:bg-emerald-800 transition-colors shadow-md text-sm mt-2"
              >
                Submit Request
              </button>
            </form>
          </div>
        </div>
      )}

      <Footer />
    </div>
  );
}

export default function ProtectedSearchResultsPageClient() {
  return (
    <ProtectedRoute>
      <SearchResultsPage />
    </ProtectedRoute>
  );
}
