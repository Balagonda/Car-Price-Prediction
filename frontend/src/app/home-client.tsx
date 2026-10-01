"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { ProtectedRoute } from "@/components/protected-route";

function Home() {
  const router = useRouter();

  const handleCheckValuation = () => {
    router.push("/valuation");
  };

  return (
    <div className="min-h-screen flex flex-col font-sans">
      <Navbar />

      <main className="pt-16">
        {/* Hero Section */}
        <section className="relative overflow-hidden pt-12 md:pt-24 pb-12 md:pb-32 px-4 md:px-16">
          <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
            <div className="z-10 space-y-6">
              <div className="inline-flex items-center gap-2 px-3 py-1 bg-primary/10 rounded-full">
                <span className="material-symbols-outlined text-primary text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>verified</span>
                <span className="text-primary font-bold text-xs uppercase tracking-wider">Trusted by 10k+ Sellers</span>
              </div>
              <h1 className="text-4xl md:text-6xl font-extrabold text-foreground leading-tight">
                Get the Best Value <br /><span className="text-primary">for Your Car</span>
              </h1>
              <p className="text-base md:text-lg text-muted-foreground max-w-lg leading-relaxed">
                Turn your car into cash in just 3 easy steps. Our transparent process ensures you get a fair market valuation and a hassle-free experience.
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                <button 
                  onClick={handleCheckValuation}
                  className="px-8 py-4 bg-primary text-primary-foreground font-bold rounded-xl text-center hover:bg-emerald-800 transition-colors shadow-md text-sm"
                >
                  Check Valuation
                </button>
              </div>
              <div className="flex items-center gap-8 border-t border-border pt-8">
                <div className="flex flex-col">
                  <span className="text-2xl font-bold text-foreground">4.9/5</span>
                  <span className="text-xs text-muted-foreground">User Rating</span>
                </div>
                <div className="h-10 w-px bg-border"></div>
                <div className="flex flex-col">
                  <span className="text-2xl font-bold text-foreground">24h</span>
                  <span className="text-xs text-muted-foreground">Avg. Sale Time</span>
                </div>
              </div>
            </div>
            
            <div className="relative">
              <div className="absolute -top-12 -right-12 w-96 h-96 bg-primary opacity-5 rounded-full blur-3xl"></div>
              <div className="relative rounded-2xl overflow-hidden mint-glow border-4 border-border shadow-2xl hover:rotate-0 transition-transform duration-500">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img 
                  className="w-full h-auto object-cover" 
                  alt="Modern sedan parked in a bright setting" 
                  src="https://lh3.googleusercontent.com/aida-public/AB6AXuBUhUrT69-p5arEiJMSwHaHX1BT4MWrwJuHeJO5qHjtt2rzPcVByhSdPMP2mZlDPJ2DSoHyjTmd5B91BktQaP8dNbtjlUz1A3Ujs2VT9n-4hSJxKXkTPoZGje17EsnZ_J7AtjHfZqs3R-M_MyUr_LuyFXRJHpPmVwbAWviEmDp0xsqAhxm_394x2R-Cqc8Q94CLZ0mOKmfFv59adgZ-0oTO8iLsVPF_knQLdmNqi0ZQBQel9-ziJFWwbnKZqW7HMn3W8rXaSonCCfA"
                />
              </div>
              {/* Floating Badge */}
              <div className="absolute -bottom-6 -left-6 bg-card p-4 rounded-2xl shadow-xl flex items-center gap-4 border border-border">
                <div className="w-12 h-12 bg-primary text-primary-foreground rounded-full flex items-center justify-center">
                  <span className="material-symbols-outlined">trending_up</span>
                </div>
                <div>
                  <p className="font-bold text-sm text-foreground">Market Peak</p>
                  <p className="text-xs text-muted-foreground">Sell for 15% more today</p>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}

export default function ProtectedHome() {
  return (
    <ProtectedRoute>
      <Home />
    </ProtectedRoute>
  );
}
