import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { 
  Shield, Activity, Layers, BarChart3, Database, 
  Zap, Cpu, Network, Info, Globe, Bell, 
  ArrowRight, ShieldCheck, ShieldAlert, CpuIcon,
  Search, Filter, Download, Settings, RefreshCcw,
  ChevronRight, Terminal
} from 'lucide-react';
import { 
  AreaChart, Area, ResponsiveContainer,
  Radar, RadarChart, PolarGrid, PolarAngleAxis,
  XAxis, YAxis, Tooltip
} from 'recharts';
import { motion, AnimatePresence } from 'framer-motion';
import './App.css';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [activeTab, setActiveTab] = useState('live');
  const [traffic, setTraffic] = useState([]);
  const [stats, setStats] = useState({ total: 0, threats: 0 });
  const [chartData, setChartData] = useState([]);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [benchmarks, setBenchmarks] = useState(null);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    axios.get(`${API_BASE_URL}/get_benchmarks`).then(res => setBenchmarks(res.data));
    fetchHistory();
    const interval = setInterval(fetchTraffic, 4000);
    const handleMouseMove = (e) => setMousePos({ x: e.clientX, y: e.clientY });
    window.addEventListener('mousemove', handleMouseMove);
    return () => {
      clearInterval(interval);
      window.removeEventListener('mousemove', handleMouseMove);
    };
  }, []);

  const fetchTraffic = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/simulate_traffic?count=4`);
      const newTraffic = response.data;
      setTraffic(prev => [...newTraffic, ...prev].slice(0, 10));
      const threats = newTraffic.filter(t => t.predicted_label === 1);
      setStats(prev => ({ total: prev.total + newTraffic.length, threats: prev.threats + threats.length }));
      setChartData(prev => [...prev, { 
        time: new Date().toLocaleTimeString(), 
        threats: threats.length
      }].slice(-15));
      if (threats.length > 0) fetchHistory();
    } catch (error) { console.error(error); }
  };

  const fetchHistory = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/threat_history?limit=15`);
      setHistory(response.data);
    } catch (error) { console.error(error); }
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center p-8 selection:bg-purple-500/30">
      <div className="canvas-container" />
      <div className="mesh-gradient" />
      
      <motion.div 
        initial={{ opacity: 0, scale: 0.99 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.8, ease: "circOut" }}
        className="glass-shell w-full max-w-[1300px] h-[88vh] flex shadow-[0_0_80px_rgba(0,0,0,0.4)]"
      >
        {/* Slim Sidebar */}
        <aside className="w-20 border-r border-white/[0.05] flex flex-col items-center py-10 bg-black/40">
          <div className="w-10 h-10 rounded-xl bg-white flex items-center justify-center mb-12 shadow-lg shadow-white/5">
            <Shield className="text-black" size={20} />
          </div>

          <nav className="flex-1 space-y-8">
            <SidebarItem icon={<Activity size={22} />} active={activeTab === 'live'} onClick={() => setActiveTab('live')} label="Surveillance" />
            <SidebarItem icon={<Layers size={22} />} active={activeTab === 'methodology'} onClick={() => setActiveTab('methodology')} label="Workflow" />
            <SidebarItem icon={<BarChart3 size={22} />} active={activeTab === 'benchmarks'} onClick={() => setActiveTab('benchmarks')} label="Analytics" />
            <SidebarItem icon={<Database size={22} />} active={activeTab === 'history'} onClick={() => setActiveTab('history')} label="History" />
          </nav>

          <div className="mt-auto p-4">
            <button className="w-10 h-10 rounded-xl border border-white/10 flex items-center justify-center text-white/20 hover:text-white transition-colors">
              <Settings size={18} />
            </button>
          </div>
        </aside>

        {/* Main Workspace */}
        <section className="flex-1 flex flex-col overflow-hidden">
          {/* Minimalist Header */}
          <header className="px-12 py-8 flex justify-between items-center">
            <div>
              <p className="text-[10px] font-bold text-white/30 uppercase tracking-[0.3em] mb-1">Neural Node: CICIDS-A1</p>
              <h2 className="text-2xl font-semibold tracking-tight text-white/90">
                {activeTab === 'live' ? 'Live Stream' : 
                 activeTab === 'methodology' ? 'System Workflow' :
                 activeTab === 'benchmarks' ? 'Model Benchmarks' : 'Threat Logs'}
              </h2>
            </div>
            <div className="flex gap-12 items-center">
              <HeaderStat label="Detected" value={stats.threats} danger />
              <HeaderStat label="Scanned" value={stats.total} />
              <div className="h-8 w-[1px] bg-white/5" />
              <div className="flex items-center gap-3">
                <div className="status-indicator bg-emerald-500 pulse" />
                <span className="text-[10px] font-bold text-white/40 uppercase tracking-widest">System Online</span>
              </div>
            </div>
          </header>

          {/* Scrollable Content */}
          <div className="flex-1 overflow-y-auto px-12 pb-12 custom-scrollbar">
            <AnimatePresence mode="wait">
              {activeTab === 'live' && (
                <motion.div key="live" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="grid grid-cols-12 gap-8">
                  <div className="col-span-8 space-y-4">
                    <div className="flex items-center justify-between opacity-40 mb-4">
                      <span className="text-[10px] font-bold uppercase tracking-[0.2em] flex items-center gap-2">
                        <Terminal size={12} /> Sequential Flow Analysis
                      </span>
                      <span className="text-[10px] font-bold uppercase tracking-widest">Auto-Refreshes: 4.0s</span>
                    </div>
                    
                    {traffic.map((t, i) => (
                      <motion.div 
                        initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}
                        key={i} className={`p-4 rounded-2xl border transition-all flex items-center justify-between ${t.predicted_label ? 'bg-red-500/[0.03] border-red-500/20' : 'bg-white/[0.01] border-white/5 hover:border-white/10'}`}
                      >
                        <div className="flex items-center gap-5">
                          <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${t.predicted_label ? 'text-red-500 bg-red-500/10 shadow-[0_0_15px_rgba(239,68,68,0.15)]' : 'text-emerald-500 bg-emerald-500/10'}`}>
                            {t.predicted_label ? <ShieldAlert size={18} /> : <ShieldCheck size={18} />}
                          </div>
                          <div>
                            <p className="text-sm font-mono font-bold text-white/80">{t.src_ip}</p>
                            <p className="text-[10px] font-bold text-white/20 uppercase mt-0.5">{t.protocol === 6 ? 'TCP' : 'UDP'} • Port {t.dst_port}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-10">
                          <div className="text-right hidden sm:block">
                            <p className="text-[9px] font-bold text-white/20 uppercase tracking-widest mb-1">Confidence</p>
                            <div className="w-24 h-0.5 bg-white/5 rounded-full overflow-hidden">
                              <div className={`h-full ${t.predicted_label ? 'bg-red-500' : 'bg-emerald-500'}`} style={{ width: `${t.confidence * 100}%` }} />
                            </div>
                          </div>
                          <span className={`text-[10px] font-black uppercase tracking-widest ${t.predicted_label ? 'text-red-500' : 'text-white/20'}`}>
                            {t.predicted_label ? 'Flagged' : 'Verified'}
                          </span>
                          <ChevronRight size={14} className="text-white/10" />
                        </div>
                      </motion.div>
                    ))}
                  </div>

                  <div className="col-span-4 space-y-8">
                    <div className="p-8 rounded-3xl bg-white/[0.02] border border-white/5">
                      <h3 className="text-xs font-bold text-white/30 uppercase tracking-widest mb-8 flex items-center gap-2">
                        <Zap size={14} className="text-purple-400" /> Activity Pulse
                      </h3>
                      <div className="h-40">
                        <ResponsiveContainer>
                          <AreaChart data={chartData}>
                            <Area type="monotone" dataKey="threats" stroke="#8b5cf6" fill="rgba(139, 92, 246, 0.1)" strokeWidth={2} />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                    </div>

                    <div className="p-8 rounded-3xl bg-white/[0.02] border border-white/5">
                      <h3 className="text-xs font-bold text-white/30 uppercase tracking-widest mb-6">Decision Logic</h3>
                      <div className="space-y-4">
                        {[
                          { label: 'Flow Volume', val: 92 },
                          { label: 'Packet Rate', val: 78 },
                          { label: 'Port Scan', val: 45 }
                        ].map((f, i) => (
                          <div key={i} className="space-y-1.5">
                            <div className="flex justify-between text-[9px] font-bold text-white/40 uppercase">
                              <span>{f.label}</span>
                              <span className="text-purple-400">{f.val}%</span>
                            </div>
                            <div className="h-1 bg-white/5 rounded-full">
                              <div className="h-full bg-purple-500/40" style={{ width: `${f.val}%` }} />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}

              {activeTab === 'methodology' && (
                <motion.div key="meth" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-4xl mx-auto space-y-12">
                  <div className="grid grid-cols-2 gap-12 py-10">
                    <div className="space-y-8">
                      <h3 className="text-xl font-semibold mb-8 text-white/80">Project Core</h3>
                      <p className="text-sm text-white/40 leading-relaxed">
                        This system utilizes the **CICIDS2017** benchmark dataset for high-fidelity network traffic analysis. By extracting 78 bidirectional flow features, we achieve real-time classification of botnet behavior including DDoS, C2 Heartbeats, and Port Scanning.
                      </p>
                      <div className="flex gap-4">
                        <div className="px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-[10px] font-bold uppercase">78 Features</div>
                        <div className="px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-[10px] font-bold uppercase">XGBoost Optimized</div>
                      </div>
                    </div>
                    <div className="space-y-6">
                      {[
                        "Raw PCAP Ingestion", "Feature Extraction", "Neural Inference", "Auto-Mitigation"
                      ].map((s, i) => (
                        <div key={i} className="flex items-center gap-5 group">
                          <div className="w-8 h-8 rounded-lg border border-white/10 flex items-center justify-center text-[10px] font-black group-hover:border-purple-500 transition-colors">{i+1}</div>
                          <span className="text-sm font-medium text-white/60 group-hover:text-white transition-colors">{s}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </motion.div>
              )}

              {activeTab === 'benchmarks' && benchmarks && (
                <motion.div key="bench" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-8">
                  <div className="grid grid-cols-2 gap-8">
                    <MetricCard name="Random Forest" data={benchmarks.RandomForest} />
                    <MetricCard name="XGBoost Core" data={benchmarks.XGBoost} primary />
                  </div>
                </motion.div>
              )}

              {activeTab === 'history' && (
                <motion.div key="history" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                  <div className="rounded-3xl border border-white/5 bg-white/[0.01] overflow-hidden">
                    <table className="w-full text-left">
                      <thead>
                        <tr className="border-b border-white/5 bg-white/[0.02]">
                          <th className="p-5 text-[10px] font-bold text-white/20 uppercase tracking-widest">Source Entity</th>
                          <th className="p-5 text-[10px] font-bold text-white/20 uppercase tracking-widest">Classification</th>
                          <th className="p-5 text-[10px] font-bold text-white/20 uppercase tracking-widest">Confidence</th>
                          <th className="p-5 text-[10px] font-bold text-white/20 uppercase tracking-widest">Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {history.map((log, i) => (
                          <tr key={i} className="border-b border-white/[0.03] hover:bg-white/[0.01] transition-all">
                            <td className="p-5">
                              <p className="text-xs font-mono font-bold">{log.src_ip}</p>
                              <p className="text-[9px] text-white/20 mt-1 uppercase">{new Date(log.timestamp).toLocaleTimeString()}</p>
                            </td>
                            <td className="p-5">
                              <span className="px-2 py-0.5 rounded-md bg-red-500/10 text-red-500 text-[9px] font-bold uppercase tracking-tight">
                                {log.threat_type}
                              </span>
                            </td>
                            <td className="p-5 text-xs font-mono text-white/40">{(log.confidence * 100).toFixed(1)}%</td>
                            <td className="p-5">
                              <span className="text-[9px] font-bold text-emerald-500 uppercase flex items-center gap-1.5">
                                <ShieldCheck size={10} /> {log.status}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </section>
      </motion.div>
    </div>
  );
}

function SidebarItem({ icon, active, onClick, label }) {
  return (
    <button 
      onClick={onClick} 
      className={`group relative w-12 h-12 rounded-2xl flex items-center justify-center transition-all ${active ? 'bg-white text-black shadow-lg shadow-white/10' : 'text-white/20 hover:text-white hover:bg-white/5'}`}
    >
      {icon}
      <div className="absolute left-16 px-3 py-1.5 rounded-lg bg-white text-black text-[10px] font-bold uppercase opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity whitespace-nowrap z-50">
        {label}
      </div>
    </button>
  );
}

function HeaderStat({ label, value, danger }) {
  return (
    <div className="text-right">
      <p className="text-[10px] font-bold text-white/20 uppercase tracking-widest mb-1">{label}</p>
      <p className={`text-xl font-bold font-mono tracking-tighter ${danger ? 'text-red-500' : 'text-white/80'}`}>{value}</p>
    </div>
  );
}

function MetricCard({ name, data, primary }) {
  return (
    <div className={`p-8 rounded-3xl border ${primary ? 'bg-purple-500/[0.03] border-purple-500/20' : 'bg-white/[0.02] border-white/5'}`}>
      <h4 className="text-sm font-bold text-white/60 mb-8 uppercase tracking-[0.2em]">{name}</h4>
      <div className="grid grid-cols-2 gap-6">
        {Object.entries(data).map(([k, v]) => (
          <div key={k} className="p-4 rounded-2xl bg-black/20 border border-white/[0.03]">
            <p className="text-[9px] font-bold text-white/20 uppercase mb-1">{k}</p>
            <p className="text-lg font-bold font-mono">
              {typeof v === 'number' ? `${(v * 100).toFixed(2)}%` : v}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;

function NavItem({ icon, label, active, onClick }) {
  return (
    <button onClick={onClick} className={`nav-item ${active ? 'active' : ''}`}>
      <span className={`${active ? 'text-purple-400' : 'text-white/20'} transition-colors`}>{icon}</span>
      <span className="text-sm tracking-tight">{label}</span>
      {active && (
        <motion.div 
          layoutId="nav-glow" 
          className="absolute inset-0 bg-gradient-to-r from-purple-500/5 to-transparent rounded-2xl -z-10" 
        />
      )}
    </button>
  );
}

function StatView({ label, value, highlight }) {
  return (
    <div className="text-right">
      <p className="text-[10px] font-bold text-white/20 uppercase tracking-widest mb-1">{label}</p>
      <p className={`text-2xl font-black tracking-tighter ${highlight ? 'text-red-500 drop-shadow-[0_0_10px_rgba(239,68,68,0.3)]' : 'text-white'}`}>{value}</p>
    </div>
  );
}

function BenchmarkItem({ name, metrics, primary }) {
  return (
    <div className={`glass-card p-8 border-white/[0.05] ${primary ? 'bg-purple-500/[0.02] border-purple-500/20' : ''}`}>
      <h4 className="text-lg font-bold mb-8 tracking-tight flex items-center gap-3">
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${primary ? 'bg-purple-500/10 text-purple-400' : 'bg-white/5 text-white/40'}`}>
          <Zap size={18} />
        </div>
        {name}
      </h4>
      <div className="grid grid-cols-2 gap-4">
        {Object.entries(metrics).map(([k, v]) => (
          <div key={k} className="p-4 rounded-2xl bg-white/[0.02] border border-white/[0.03] group hover:bg-white/[0.05] transition-all">
            <p className="text-[10px] text-white/20 font-bold uppercase tracking-widest mb-1 group-hover:text-white/40 transition-colors">{k}</p>
            <p className="text-xl font-bold font-mono text-gradient">
              {typeof v === 'number' ? `${(v * 100).toFixed(2)}%` : v}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
