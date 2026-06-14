"use client";

import { motion } from "framer-motion";
import { useState } from "react";
import {
  Globe,
  AlertTriangle,
  Shield,
  MessageCircle,
  TrendingUp,
  MapPin,
  ExternalLink,
  Eye,
  ArrowUpRight,
  ArrowDownRight,
  Languages,
  Filter,
} from "lucide-react";

const spring = { type: "spring" as const, stiffness: 300, damping: 30 };
const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.07, delayChildren: 0.1 } },
};
const fadeUp = {
  hidden: { opacity: 0, y: 20, scale: 0.98 },
  show: { opacity: 1, y: 0, scale: 1, transition: { ...spring, duration: 0.55 } },
};

const posts = [
  {
    id: "1", platform: "twitter", author: "@MumbaiLocal_updates",
    content: "⚠️ Heavy boulder spotted on tracks between Kasara-Igatpuri section. Trains halted. Passengers stranded!",
    language: "en", time: "28m ago", classification: "hazard_report", confidence: 95, severity: "critical",
    verified: true, location: "Kasara, Maharashtra", engagement: { likes: 1245, retweets: 567 },
  },
  {
    id: "2", platform: "twitter", author: "@RailwayAlert_IN",
    content: "BREAKING: Reports of water logging near Konkan Railway KM-215. Multiple trains delayed.",
    language: "en", time: "12m ago", classification: "hazard_report", confidence: 91, severity: "warning",
    verified: true, location: "Ratnagiri, Maharashtra", engagement: { likes: 234, retweets: 89 },
  },
  {
    id: "3", platform: "facebook", author: "Allahabad Railway Passengers",
    content: "ट्रेन 12301 हावड़ा राजधानी एक्सप्रेस 3 घंटे लेट है। प्लेटफॉर्म पर भारी भीड़।",
    language: "hi", time: "1h 15m ago", classification: "passenger_report", confidence: 82, severity: "warning",
    verified: true, location: "Prayagraj, UP", engagement: { likes: 89, retweets: 0 },
  },
  {
    id: "4", platform: "news", author: "NDTV",
    content: "Konkan Railway services disrupted due to heavy rainfall; several trains cancelled or diverted",
    language: "en", time: "2h ago", classification: "news_report", confidence: 97, severity: "warning",
    verified: true, location: "Konkan Coast", engagement: { likes: 0, retweets: 0 },
  },
  {
    id: "5", platform: "twitter", author: "@fake_news_bot",
    content: "MASSIVE train crash near Delhi!! 100s dead!! #breaking #emergency",
    language: "en", time: "45m ago", classification: "misinformation", confidence: 88, severity: "info",
    verified: false, location: null, engagement: { likes: 12, retweets: 3 },
  },
  {
    id: "6", platform: "twitter", author: "@ChennaiRailFan",
    content: "ரயில் எண் 12621 தமிழ்நாடு எக்ஸ்பிரஸ் 45 நிமிடம் தாமதமாக இயங்குகிறது.",
    language: "ta", time: "3h ago", classification: "passenger_report", confidence: 79, severity: "info",
    verified: true, location: "Chennai", engagement: { likes: 45, retweets: 12 },
  },
];

const classConfig: Record<string, { color: string; bg: string; ring: string; label: string; icon: React.ElementType }> = {
  hazard_report: { color: "text-[#ff453a]", bg: "bg-[#ff453a]/[0.08]", ring: "ring-[#ff453a]/10", label: "Hazard", icon: AlertTriangle },
  passenger_report: { color: "text-[#ffd60a]", bg: "bg-[#ffd60a]/[0.08]", ring: "ring-[#ffd60a]/10", label: "Passenger", icon: MessageCircle },
  news_report: { color: "text-[#0a84ff]", bg: "bg-[#0a84ff]/[0.08]", ring: "ring-[#0a84ff]/10", label: "News", icon: Globe },
  misinformation: { color: "text-[#636366]", bg: "bg-[#636366]/[0.08]", ring: "ring-[#636366]/10", label: "Misinfo", icon: Shield },
};

const langNames: Record<string, string> = { en: "English", hi: "Hindi", ta: "Tamil", te: "Telugu", bn: "Bengali", mr: "Marathi" };

export default function SocialRadarPage() {
  const [filter, setFilter] = useState<string | null>(null);

  const filtered = filter ? posts.filter((p) => p.classification === filter) : posts;

  const stats = [
    { label: "Posts Monitored", value: "2,847", icon: Globe, gradient: "from-[#0a84ff]/10 to-[#5e5ce6]/10", iconColor: "#0a84ff", change: "+342", up: true },
    { label: "Hazard Reports", value: "2", icon: AlertTriangle, gradient: "from-[#ff453a]/10 to-[#ff6961]/10", iconColor: "#ff453a", change: "1 critical", up: false },
    { label: "Misinfo Blocked", value: "1", icon: Shield, gradient: "from-[#636366]/10 to-[#48484a]/10", iconColor: "#636366", change: "Auto-flagged", up: true },
    { label: "Languages", value: "22", icon: Languages, gradient: "from-[#30d158]/10 to-[#34c759]/10", iconColor: "#30d158", change: "Active", up: true },
  ];

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-5">
      <motion.div variants={fadeUp} className="flex items-end justify-between">
        <div>
          <h1 className="font-display text-[22px] font-semibold tracking-[-0.02em]">
            Social Media Crisis Radar
          </h1>
          <p className="mt-0.5 text-[13px] text-white/30">
            Real-time monitoring across X, Facebook & news — 22 Indian languages
          </p>
        </div>
        <div className="flex items-center gap-1.5 rounded-full bg-[#30d158]/[0.08] px-3 py-1.5 ring-1 ring-[#30d158]/10">
          <span className="relative flex h-[5px] w-[5px]">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#30d158] opacity-40" />
            <span className="relative inline-flex h-[5px] w-[5px] rounded-full bg-[#30d158]" />
          </span>
          <span className="text-[11px] font-medium text-[#30d158]/80">Scanning</span>
        </div>
      </motion.div>

      <motion.div variants={fadeUp} className="grid grid-cols-4 gap-3">
        {stats.map((s) => (
          <motion.div key={s.label} whileHover={{ y: -3, transition: spring }} className="glass glass-hover rounded-2xl p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-[11px] font-medium tracking-wide text-white/25 uppercase">{s.label}</p>
                <p className="mt-1.5 font-display text-[26px] font-semibold tracking-[-0.03em] text-white">{s.value}</p>
                <div className="mt-1 flex items-center gap-1">
                  {s.up ? <ArrowUpRight className="h-3 w-3 text-[#30d158]" /> : <ArrowDownRight className="h-3 w-3 text-[#ff453a]" />}
                  <span className={`text-[11px] font-medium ${s.up ? "text-[#30d158]/70" : "text-[#ff453a]/70"}`}>{s.change}</span>
                </div>
              </div>
              <div className={`rounded-xl bg-gradient-to-br ${s.gradient} p-2.5`}>
                <s.icon className="h-[18px] w-[18px]" style={{ color: s.iconColor }} />
              </div>
            </div>
          </motion.div>
        ))}
      </motion.div>

      {/* Filters */}
      <motion.div variants={fadeUp} className="flex items-center gap-2">
        <Filter className="h-3.5 w-3.5 text-white/20" />
        <button onClick={() => setFilter(null)} className={`pill text-[10px] ring-1 transition-all ${!filter ? "bg-white/[0.08] text-white/60 ring-white/10" : "bg-white/[0.02] text-white/25 ring-white/[0.04] hover:bg-white/[0.05]"}`}>All</button>
        {Object.entries(classConfig).map(([key, cfg]) => (
          <button key={key} onClick={() => setFilter(filter === key ? null : key)} className={`pill text-[10px] ring-1 transition-all ${filter === key ? `${cfg.bg} ${cfg.color} ${cfg.ring}` : "bg-white/[0.02] text-white/25 ring-white/[0.04] hover:bg-white/[0.05]"}`}>
            {cfg.label}
          </button>
        ))}
      </motion.div>

      {/* Feed */}
      <motion.div variants={fadeUp} className="glass rounded-2xl overflow-hidden">
        <div className="flex items-center justify-between px-5 py-3">
          <span className="text-[13px] font-medium text-white/60">Live Feed</span>
          <span className="font-mono text-[10px] text-white/15">{filtered.length} posts</span>
        </div>
        <div className="divider" />
        {filtered.map((post, i) => {
          const cfg = classConfig[post.classification] || classConfig.hazard_report;
          const CfgIcon = cfg.icon;
          return (
            <motion.div
              key={post.id}
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 + i * 0.06, ...spring }}
              className={`flex items-start gap-4 px-5 py-4 transition-all duration-300 hover:bg-white/[0.02] ${post.classification === "misinformation" ? "opacity-50" : ""}`}
            >
              <div className={`flex h-9 w-9 items-center justify-center rounded-xl shrink-0 ${cfg.bg}`}>
                <CfgIcon className={`h-4 w-4 ${cfg.color}`} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-[12px] font-medium text-white/50">{post.author}</span>
                  <span className="rounded-md bg-white/[0.04] px-1.5 py-[1px] font-mono text-[9px] text-white/20">{post.platform}</span>
                  {post.language !== "en" && (
                    <span className="rounded-md bg-[#bf5af2]/10 px-1.5 py-[1px] text-[9px] text-[#bf5af2]/60">{langNames[post.language] || post.language}</span>
                  )}
                  <span className={`pill text-[9px] ring-1 ${cfg.bg} ${cfg.color} ${cfg.ring}`}>{cfg.label}</span>
                  {post.classification === "misinformation" && (
                    <span className="pill text-[9px] bg-[#636366]/10 text-[#636366] ring-1 ring-[#636366]/10 line-through">BLOCKED</span>
                  )}
                  {post.verified && post.classification !== "misinformation" && (
                    <span className="pill text-[9px] bg-[#30d158]/10 text-[#30d158]/70 ring-1 ring-[#30d158]/10">✓ Verified</span>
                  )}
                </div>
                <p className={`mt-1.5 text-[13px] leading-relaxed ${post.classification === "misinformation" ? "text-white/20 line-through" : "text-white/40"}`}>
                  {post.content}
                </p>
                <div className="mt-2 flex items-center gap-4 text-[10px] text-white/20">
                  <span>{post.time}</span>
                  {post.location && (
                    <span className="flex items-center gap-1"><MapPin className="h-2.5 w-2.5" />{post.location}</span>
                  )}
                  <span className="font-mono">{post.confidence}% conf</span>
                  {post.engagement.likes > 0 && <span>❤ {post.engagement.likes.toLocaleString()}</span>}
                  {post.engagement.retweets > 0 && <span>🔁 {post.engagement.retweets}</span>}
                </div>
              </div>
              <span className="font-mono text-[10px] text-white/15 shrink-0">{post.time}</span>
            </motion.div>
          );
        })}
      </motion.div>
    </motion.div>
  );
}
