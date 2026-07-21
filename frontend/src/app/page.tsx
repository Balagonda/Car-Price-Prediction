import Link from "next/link";
import { ArrowRight, ShieldCheck, TrendingUp, Cpu } from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white overflow-hidden flex flex-col">
      {/* Background gradients */}
      <div 
        className="fixed inset-0 pointer-events-none" 
        style={{
          background: "radial-gradient(circle at 50% -20%, rgba(99,102,241,0.15), transparent 60%)"
        }}
      />
      
      {/* Navigation */}
      <nav className="relative z-10 border-b border-white/5 bg-background/50 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold text-sm" style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)" }}>
              A
            </div>
            <span className="text-white font-semibold tracking-wide">AutoWorth AI</span>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/login" className="text-sm font-medium text-slate-300 hover:text-white transition-colors">
              Sign In
            </Link>
            <Link href="/register" className="text-sm font-medium px-4 py-2 rounded-full bg-white text-black hover:bg-slate-200 transition-colors">
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="relative z-10 flex-1 flex flex-col items-center justify-center px-6 py-20 text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-violet-500/30 bg-violet-500/10 text-violet-300 text-xs font-medium mb-8">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-violet-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-violet-500"></span>
          </span>
          Phase 2 is now Live
        </div>
        
        <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6 max-w-4xl mx-auto" style={{ lineHeight: 1.1 }}>
          Intelligent vehicle valuation <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-violet-400">powered by AI</span>
        </h1>
        
        <p className="text-lg md:text-xl text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed">
          India&apos;s most accurate used car pricing engine. Get transparent, ML-driven valuations and damage analysis in seconds.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 w-full sm:w-auto">
          <Link 
            href="/register" 
            className="flex items-center justify-center gap-2 px-8 py-4 rounded-full font-medium text-white transition-transform hover:scale-105"
            style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)" }}
          >
            Start for free <ArrowRight className="w-4 h-4" />
          </Link>
          <Link 
            href="/login" 
            className="flex items-center justify-center gap-2 px-8 py-4 rounded-full font-medium text-white border border-white/10 bg-white/5 hover:bg-white/10 transition-colors"
          >
            Go to Dashboard
          </Link>
        </div>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto mt-24">
          {[
            { icon: Cpu, title: "Machine Learning", desc: "Trained on millions of Indian car listings for precise market pricing." },
            { icon: ShieldCheck, title: "Transparent Pricing", desc: "SHAP explainability shows exactly why a car is priced the way it is." },
            { icon: TrendingUp, title: "Market Trends", desc: "Real-time adjustments based on current market dynamics and location." },
          ].map((feat, i) => (
            <div key={i} className="p-6 rounded-2xl border border-white/5 bg-white/5 text-left backdrop-blur-sm">
              <div className="w-12 h-12 rounded-xl bg-violet-500/20 flex items-center justify-center mb-4 text-violet-400">
                <feat.icon className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">{feat.title}</h3>
              <p className="text-slate-400 text-sm leading-relaxed">{feat.desc}</p>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
