"use client";
import { useState } from "react";

import { useUiStore, Role } from "@/stores/uiStore";
import { Sidebar } from "@/components/layout/Sidebar";
import { RedAlertOverlay } from "@/components/alerts/RedAlertOverlay";
import { LiveReportToaster } from "@/components/alerts/LiveReportToaster";
import { ShieldAlert, Wrench, Plane, ActivitySquare, Train } from "lucide-react";
import { motion } from "framer-motion";

export function AppWrapper({ children }: { children: React.ReactNode }) {
  const { userRole, setUserRole } = useUiStore();

  if (!userRole) {
    return <LoginScreen onLogin={setUserRole} />;
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <main className="flex-1 overflow-y-auto ambient-grid relative">
          <div className="mx-auto max-w-[1400px] p-5">
            {children}
          </div>
        </main>
      </div>
      <RedAlertOverlay />
      <LiveReportToaster />
    </div>
  );
}

function LoginScreen({ onLogin }: { onLogin: (role: Role) => void }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (username === "admin" && password === "admin123") {
      onLogin("admin");
    } else if (username === "maint" && password === "maint123") {
      onLogin("maintenance");
    } else if (username === "drone" && password === "drone123") {
      onLogin("drone_op");
    } else {
      setError("Invalid credentials. Please use the demo accounts below.");
    }
  };

  return (
    <div className="flex h-screen w-full items-center justify-center bg-[#0d0d0d] relative overflow-hidden font-mono">
      {/* Subtle red glow behind the modal to match reference */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-red-600/5 rounded-full blur-[100px] pointer-events-none" />
      
      <motion.div 
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        className="z-10 bg-[#121212] border border-white/[0.08] rounded-2xl w-[440px] shadow-2xl overflow-hidden flex flex-col items-center pt-10 pb-8 px-10"
      >
        {/* Logo Card */}
        <div className="bg-white rounded-xl px-4 py-3 flex flex-col items-center justify-center mb-6 shadow-md mx-auto">
          <div className="flex items-center gap-3">
            {/* The user will drop their uploaded logo into apps/web/public/logo.png */}
            <img 
              src="/logo.png" 
              alt="RailMind AI Logo" 
              className="h-12 w-auto object-contain"
            />
            <div className="flex flex-col items-start border-l-2 border-cyan-500/30 pl-3">
              <span className="text-[#002b5e] font-sans font-bold text-sm leading-none tracking-tighter">RailMind</span>
              <span className="text-[#00e5ff] font-sans font-bold text-[17px] leading-tight tracking-tight uppercase">Intelligence</span>
            </div>
          </div>
        </div>

        <h1 className="text-white text-lg font-bold tracking-[0.2em] mb-2 uppercase">RailMind</h1>
        <p className="text-zinc-500 text-[10px] tracking-[0.15em] mb-10 uppercase">Sentinel Command Platform</p>

        <form onSubmit={handleSubmit} className="w-full space-y-5">
          <div>
            <label className="block text-[10px] font-bold text-zinc-500 tracking-wider mb-2 uppercase">Operator ID</label>
            <input 
              type="text" 
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full bg-[#0a0a0a] border border-white/10 rounded-md px-4 py-3 text-zinc-300 text-sm focus:outline-none focus:border-red-500 transition-colors placeholder:text-zinc-700 font-sans"
              placeholder="operator@railmind.gov.in"
            />
          </div>
          <div>
            <label className="block text-[10px] font-bold text-zinc-500 tracking-wider mb-2 uppercase">Password</label>
            <input 
              type="password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-[#0a0a0a] border border-white/10 rounded-md px-4 py-3 text-zinc-300 text-sm focus:outline-none focus:border-red-500 transition-colors placeholder:text-zinc-700 font-sans"
              placeholder="••••••••"
            />
          </div>
          
          {error && (
            <p className="text-red-500 text-[11px] text-center font-sans">{error}</p>
          )}

          <button 
            type="submit"
            className="w-full bg-[#e60000] hover:bg-[#ff0000] text-white text-[12px] font-bold tracking-wider py-3.5 rounded-md transition-colors uppercase mt-4"
          >
            Secure Login
          </button>
        </form>

        {/* Demo Credentials Box */}
        <div className="w-full mt-10 bg-[#080808] border border-white/5 rounded-xl p-5">
          <p className="text-center text-[9px] text-zinc-500 tracking-[0.1em] mb-4 uppercase font-bold">Judge Credentials</p>
          
          <div className="space-y-3 text-[11px]">
            <div className="flex justify-between items-center">
              <span className="text-[#0a84ff]">Admin (Full Access)</span>
              <span className="text-zinc-400">admin / admin123</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-[#ffd60a]">Maint (Track Health)</span>
              <span className="text-zinc-400">maint / maint123</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-[#ff453a]">Drone (Fleet Control)</span>
              <span className="text-zinc-400">drone / drone123</span>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
