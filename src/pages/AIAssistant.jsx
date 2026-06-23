// src/pages/AIAssistant.jsx
import React, { useState, useRef, useEffect, useMemo } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  Send,
  Bot,
  User,
  Sparkles,
  Loader2,
  Compass,
  CloudSun,
  Calendar,
  MapPin,
  DollarSign,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Edit2,
  Check,
  RefreshCw,
  Plane,
  TrainFront,
  Car,
  MessageSquarePlus,
  Zap,
  Globe,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

/* ── Tiny Markdown Renderer ─────────────────────────────────────── */
function renderMarkdown(text) {
  if (!text) return null;
  const lines = text.split('\n');
  const elements = [];
  let key = 0;

  for (let i = 0; i < lines.length; i++) {
    let line = lines[i];

    // Headers
    if (line.startsWith('### ')) {
      elements.push(<h4 key={key++} className="text-sm font-bold text-cyan-300 mt-3 mb-1">{processInline(line.slice(4))}</h4>);
      continue;
    }
    if (line.startsWith('## ')) {
      elements.push(<h3 key={key++} className="text-base font-bold text-cyan-200 mt-3 mb-1">{processInline(line.slice(3))}</h3>);
      continue;
    }
    if (line.startsWith('# ')) {
      elements.push(<h2 key={key++} className="text-lg font-bold text-white mt-3 mb-1">{processInline(line.slice(2))}</h2>);
      continue;
    }

    // Bullet points
    if (line.match(/^[\s]*[-•*]\s/)) {
      const content = line.replace(/^[\s]*[-•*]\s/, '');
      elements.push(
        <div key={key++} className="flex gap-2 items-start ml-1 my-0.5">
          <span className="text-cyan-400 mt-1 text-[10px]">●</span>
          <span className="flex-1">{processInline(content)}</span>
        </div>
      );
      continue;
    }

    // Numbered lists
    if (line.match(/^[\s]*\d+[.)]\s/)) {
      const match = line.match(/^[\s]*(\d+)[.)]\s(.*)/);
      if (match) {
        elements.push(
          <div key={key++} className="flex gap-2 items-start ml-1 my-0.5">
            <span className="text-indigo-400 font-bold text-xs min-w-[18px]">{match[1]}.</span>
            <span className="flex-1">{processInline(match[2])}</span>
          </div>
        );
        continue;
      }
    }

    // Horizontal rules
    if (line.match(/^[-]{3,}$/)) {
      elements.push(<hr key={key++} className="border-white/10 my-2" />);
      continue;
    }

    // Empty lines
    if (line.trim() === '') {
      elements.push(<div key={key++} className="h-2" />);
      continue;
    }

    // Normal paragraph
    elements.push(<p key={key++} className="my-0.5">{processInline(line)}</p>);
  }

  return elements;
}

function processInline(text) {
  if (!text) return text;
  // Process bold, italic, code, and emoji
  const parts = [];
  let remaining = text;
  let key = 0;

  while (remaining.length > 0) {
    // Bold **text**
    const boldMatch = remaining.match(/\*\*(.+?)\*\*/);
    // Code `text`
    const codeMatch = remaining.match(/`(.+?)`/);

    let firstMatch = null;
    let firstIndex = remaining.length;

    if (boldMatch && boldMatch.index < firstIndex) {
      firstMatch = { type: 'bold', match: boldMatch };
      firstIndex = boldMatch.index;
    }
    if (codeMatch && codeMatch.index < firstIndex) {
      firstMatch = { type: 'code', match: codeMatch };
      firstIndex = codeMatch.index;
    }

    if (!firstMatch) {
      parts.push(<React.Fragment key={key++}>{remaining}</React.Fragment>);
      break;
    }

    // Add text before the match
    if (firstIndex > 0) {
      parts.push(<React.Fragment key={key++}>{remaining.substring(0, firstIndex)}</React.Fragment>);
    }

    if (firstMatch.type === 'bold') {
      parts.push(<strong key={key++} className="font-bold text-white">{firstMatch.match[1]}</strong>);
      remaining = remaining.substring(firstIndex + firstMatch.match[0].length);
    } else if (firstMatch.type === 'code') {
      parts.push(
        <code key={key++} className="bg-slate-800 px-1.5 py-0.5 rounded text-cyan-300 text-[12px] font-mono">
          {firstMatch.match[1]}
        </code>
      );
      remaining = remaining.substring(firstIndex + firstMatch.match[0].length);
    }
  }

  return parts;
}

/* ── Typing Indicator Component ──────────────────────────────────── */
function TypingIndicator() {
  return (
    <div className="flex gap-3.5 mr-auto max-w-[85%]">
      <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 border shadow-md bg-slate-900 border-white/10 text-cyan-400">
        <Bot className="w-4 h-4" />
      </div>
      <div className="px-5 py-3 rounded-2xl rounded-tl-none bg-white/5 border border-white/10 backdrop-blur flex items-center gap-1.5">
        <span className="typing-dot" style={{ animationDelay: '0ms' }} />
        <span className="typing-dot" style={{ animationDelay: '150ms' }} />
        <span className="typing-dot" style={{ animationDelay: '300ms' }} />
      </div>
    </div>
  );
}

/* ── Transport Mode Card ─────────────────────────────────────────── */
function TransportModeCard({ icon: Icon, label, value, selected, onClick, color }) {
  return (
    <button
      onClick={onClick}
      className={`flex-1 flex flex-col items-center gap-1.5 py-3 px-2 rounded-2xl border-2 transition-all duration-300 cursor-pointer group ${
        selected
          ? `${color} shadow-lg scale-[1.03]`
          : 'border-white/10 bg-white/[0.03] hover:bg-white/[0.06] hover:border-white/20'
      }`}
    >
      <Icon className={`w-5 h-5 transition-transform duration-300 group-hover:scale-110 ${
        selected ? 'text-white' : 'text-slate-400 group-hover:text-slate-200'
      }`} />
      <span className={`text-[10px] font-bold uppercase tracking-wider ${
        selected ? 'text-white' : 'text-slate-400 group-hover:text-slate-200'
      }`}>{label}</span>
    </button>
  );
}

/* ── Suggestion Chip ─────────────────────────────────────────────── */
function SuggestionChip({ icon: Icon, text, onClick }) {
  return (
    <button
      onClick={onClick}
      className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-white/10 bg-white/[0.04] hover:bg-white/[0.08] hover:border-cyan-500/30 transition-all duration-200 group text-left"
    >
      <Icon className="w-3.5 h-3.5 text-cyan-400 group-hover:text-cyan-300 shrink-0" />
      <span className="text-xs font-medium text-slate-300 group-hover:text-slate-100">{text}</span>
    </button>
  );
}


/* ═══════════════════════════════════════════════════════════════════
   ██  MAIN COMPONENT
   ═══════════════════════════════════════════════════════════════════ */
export default function AIAssistant() {
  const { user } = useAuth();

  // ── Session & Messages State ──────────────────────────────────
  const [sessionId, setSessionId] = useState(() => 'sess-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9));

  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'assistant',
      text: "Welcome to **The Ringmaster's Roundtable** AI Travel Planner! ✨\n\nI can help you plan luxury trips, estimate budgets, check weather, and discover events.\n\nTry asking me something like:\n• Plan a road trip from Delhi to Shimla\n• What's the weather in Goa?\n• Find events in Mumbai",
      toolSteps: []
    }
  ]);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // ── Trip Context State ────────────────────────────────────────
  const [tripContext, setTripContext] = useState({
    origin: "",
    destination: "",
    num_days: "",
    travelers: "",
    budget_type: "",
    start_date: "",
    end_date: "",
    interests: [],
    transport_mode: ""
  });

  const [activeEditField, setActiveEditField] = useState(null);

  // ── Tool Timeline State ───────────────────────────────────────
  const [toolTimeline, setToolTimeline] = useState({
    calculate_route: 'pending',
    get_weather: 'pending',
    find_events: 'pending',
    generate_itinerary: 'pending',
    compute_budget: 'pending'
  });

  // ── Auto-scroll ───────────────────────────────────────────────
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };
  useEffect(() => { scrollToBottom(); }, [messages, loading]);

  // ── New Chat Session ──────────────────────────────────────────
  const handleNewChat = () => {
    const newSessId = 'sess-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    setSessionId(newSessId);
    setMessages([{
      id: 'welcome',
      sender: 'assistant',
      text: "Fresh session started! 🎯\n\nHow can I help you plan your next adventure?",
      toolSteps: []
    }]);
    setTripContext({
      origin: "", destination: "", num_days: "", travelers: "",
      budget_type: "", start_date: "", end_date: "", interests: [], transport_mode: ""
    });
    setToolTimeline({
      calculate_route: 'pending', get_weather: 'pending', find_events: 'pending',
      generate_itinerary: 'pending', compute_budget: 'pending'
    });
    setActiveEditField(null);
    inputRef.current?.focus();
  };

  // ── Context Update Sync ───────────────────────────────────────
  const handleUpdateContextField = async (field, value) => {
    const updatedContext = { ...tripContext, [field]: value };
    setTripContext(updatedContext);

    try {
      const response = await fetch('http://localhost:8000/api/assistant/context/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: user?.uid || "guest_traveller",
          session_id: sessionId,
          trip_context: { [field]: value }
        })
      });
      const data = await response.json();
      if (data.status === 'success') {
        setTripContext(data.trip_context);
      }
    } catch (err) {
      console.error("Failed to sync context edit with backend:", err);
    }
  };

  // ── Transport Mode Handler ────────────────────────────────────
  const handleTransportModeSelect = (mode) => {
    handleUpdateContextField('transport_mode', mode);
  };

  // ── Suggestion Chip Handler ───────────────────────────────────
  const handleSuggestion = (text) => {
    setInput(text);
    inputRef.current?.focus();
  };

  // ── Chat Streaming ────────────────────────────────────────────
  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userQuery = input;
    setInput("");
    setLoading(true);

    setToolTimeline({
      calculate_route: 'pending', get_weather: 'pending', find_events: 'pending',
      generate_itinerary: 'pending', compute_budget: 'pending'
    });

    const userMsgId = 'user-' + Date.now();
    const assistantMsgId = 'assistant-' + Date.now();

    setMessages(prev => [
      ...prev,
      { id: userMsgId, sender: 'user', text: userQuery, toolSteps: [] }
    ]);

    setMessages(prev => [
      ...prev,
      { id: assistantMsgId, sender: 'assistant', text: '', toolSteps: [] }
    ]);

    try {
      const response = await fetch('http://localhost:8000/api/assistant/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userQuery,
          user_id: user?.uid || "guest_traveller",
          session_id: sessionId
        })
      });

      if (!response.body) throw new Error("ReadableStream not supported");

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let activeText = "";
      let activeTools = [];

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith("data: ")) {
            try {
              const data = JSON.parse(trimmed.substring(6));

              if (data.type === 'token') {
                activeText += data.content;
                setMessages(prev =>
                  prev.map(m => m.id === assistantMsgId ? { ...m, text: activeText } : m)
                );
              }
              else if (data.type === 'tool_start') {
                setToolTimeline(prev => ({ ...prev, [data.tool]: 'running' }));
                activeTools.push({
                  name: data.tool, status: 'running', result: null, collapsed: false
                });
                setMessages(prev =>
                  prev.map(m => m.id === assistantMsgId ? { ...m, toolSteps: [...activeTools] } : m)
                );
              }
              else if (data.type === 'tool_end') {
                setToolTimeline(prev => ({ ...prev, [data.tool]: 'completed' }));
                activeTools = activeTools.map(step =>
                  step.name === data.tool
                    ? { ...step, status: 'completed', result: data.result, collapsed: true }
                    : step
                );
                setMessages(prev =>
                  prev.map(m => m.id === assistantMsgId ? { ...m, toolSteps: [...activeTools] } : m)
                );
              }
              else if (data.type === 'trip_context') {
                setTripContext(data.context);
              }
              else if (data.type === 'done') {
                setToolTimeline(prev => {
                  const updated = { ...prev };
                  Object.keys(updated).forEach(k => {
                    if (updated[k] === 'pending') updated[k] = 'skipped';
                  });
                  return updated;
                });
              }
              else if (data.type === 'error') {
                activeText += `\n⚠️ ${data.content}`;
                setMessages(prev =>
                  prev.map(m => m.id === assistantMsgId ? { ...m, text: activeText } : m)
                );
                setToolTimeline(prev => {
                  const updated = { ...prev };
                  Object.keys(updated).forEach(k => {
                    if (updated[k] === 'running') updated[k] = 'failed';
                  });
                  return updated;
                });
              }
            } catch (err) { /* heartbeat / parse skip */ }
          }
        }
      }
    } catch (err) {
      console.error(err);
      setMessages(prev =>
        prev.map(m => m.id === assistantMsgId
          ? { ...m, text: "⚠️ Could not reach the AI Service. Please verify FastAPI is running on Port 8000." }
          : m)
      );
      setToolTimeline(prev => {
        const updated = { ...prev };
        Object.keys(updated).forEach(k => {
          if (updated[k] === 'running' || updated[k] === 'pending') updated[k] = 'failed';
        });
        return updated;
      });
    } finally {
      setLoading(false);
    }
  };

  const toggleToolCollapse = (msgId, toolName) => {
    setMessages(prev =>
      prev.map(m => {
        if (m.id !== msgId) return m;
        return {
          ...m,
          toolSteps: m.toolSteps.map(step =>
            step.name === toolName ? { ...step, collapsed: !step.collapsed } : step
          )
        };
      })
    );
  };

  // ── Mode-Aware Timeline Items ─────────────────────────────────
  const toolTimelineItems = useMemo(() => {
    const mode = tripContext.transport_mode;
    const allItems = [
      { name: 'calculate_route', label: 'Route Conductor', icon: Compass, modes: ['road_trip', 'train', ''] },
      { name: 'get_weather', label: 'Sky Gazer Weather', icon: CloudSun, modes: ['flight', 'train', 'road_trip', ''] },
      { name: 'find_events', label: 'Events Scout', icon: Sparkles, modes: ['flight', 'train', 'road_trip', ''] },
      { name: 'generate_itinerary', label: 'Itinerary Maestro', icon: Calendar, modes: ['flight', 'train', 'road_trip', ''] },
      { name: 'compute_budget', label: 'Quartermaster Budget', icon: DollarSign, modes: ['flight', 'train', 'road_trip', ''] }
    ];
    if (!mode) return allItems;
    return allItems.filter(item => item.modes.includes(mode));
  }, [tripContext.transport_mode]);

  // ── Context Field Renderer ────────────────────────────────────
  const renderContextField = (label, fieldName, icon, placeholder) => {
    const isEditing = activeEditField === fieldName;
    const value = tripContext[fieldName] || "";

    return (
      <div key={fieldName} className="flex flex-col gap-1 border-b border-white/5 pb-2.5 last:border-b-0 last:pb-0">
        <span className="text-[10px] uppercase tracking-widest text-slate-400 font-bold flex items-center gap-1.5">
          {icon}
          {label}
        </span>
        <div className="flex items-center justify-between gap-2 group min-h-[28px]">
          {isEditing ? (
            <div className="flex-1 flex items-center gap-1">
              <input
                className="flex-1 bg-slate-900 border border-cyan-500/50 rounded-lg px-2 py-1 text-xs text-white outline-none focus:border-cyan-400 transition-colors"
                value={value}
                autoFocus
                onChange={e => setTripContext(prev => ({ ...prev, [fieldName]: e.target.value }))}
                onBlur={() => { setActiveEditField(null); handleUpdateContextField(fieldName, value); }}
                onKeyDown={e => {
                  if (e.key === 'Enter') { setActiveEditField(null); handleUpdateContextField(fieldName, value); }
                  if (e.key === 'Escape') setActiveEditField(null);
                }}
                placeholder={placeholder}
              />
              <button className="p-0.5 text-emerald-400 hover:text-emerald-300">
                <Check className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-100">
                {value || <span className="text-slate-500 italic">Not set</span>}
              </span>
              <button
                onClick={() => setActiveEditField(fieldName)}
                className="text-slate-400 hover:text-cyan-400 opacity-0 group-hover:opacity-100 transition-opacity p-0.5"
                title="Edit Parameter"
              >
                <Edit2 className="w-3 h-3" />
              </button>
            </div>
          )}
        </div>
      </div>
    );
  };

  // ── Timeline Item Renderer ────────────────────────────────────
  const renderTimelineItem = (item) => {
    const status = toolTimeline[item.name] || 'pending';
    const IconComp = item.icon;

    let statusColor = 'text-slate-500';
    let badgeColor = 'bg-slate-900 border-slate-800 text-slate-400';
    let BadgeIcon = null;
    let labelText = 'Pending';

    if (status === 'running') {
      statusColor = 'text-cyan-400 animate-pulse';
      badgeColor = 'bg-cyan-500/10 border-cyan-500/20 text-cyan-300';
      BadgeIcon = <Loader2 className="w-3 h-3 animate-spin" />;
      labelText = 'Running...';
    } else if (status === 'completed') {
      statusColor = 'text-emerald-400';
      badgeColor = 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300';
      BadgeIcon = <CheckCircle2 className="w-3 h-3" />;
      labelText = 'Completed';
    } else if (status === 'failed') {
      statusColor = 'text-rose-400';
      badgeColor = 'bg-rose-500/10 border-rose-500/20 text-rose-300';
      BadgeIcon = <XCircle className="w-3 h-3" />;
      labelText = 'Failed';
    } else if (status === 'skipped') {
      statusColor = 'text-amber-400/60';
      badgeColor = 'bg-amber-500/5 border-amber-500/10 text-amber-300/70';
      BadgeIcon = <AlertCircle className="w-3 h-3" />;
      labelText = 'Skipped';
    }

    return (
      <div key={item.name} className="flex items-center justify-between py-2.5 border-b border-white/5 last:border-b-0 relative">
        {/* Connector line */}
        <div className="absolute left-[7px] top-0 bottom-0 w-px bg-white/5" />
        <div className="flex items-center gap-2.5 relative z-10">
          <span className={`${statusColor}`}><IconComp className="w-4 h-4" /></span>
          <span className={`text-[11px] font-semibold tracking-wide ${status === 'pending' ? 'text-slate-400' : 'text-slate-200'}`}>
            {item.label}
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className={`text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border flex items-center gap-1 ${badgeColor}`}>
            {BadgeIcon}
            {labelText}
          </span>
        </div>
      </div>
    );
  };

  // ── Transport Mode Badge Text ─────────────────────────────────
  const transportModeBadge = useMemo(() => {
    const mode = tripContext.transport_mode;
    if (mode === 'flight') return { text: '✈️ Flight Mode', color: 'text-sky-400' };
    if (mode === 'train') return { text: '🚆 Train Mode', color: 'text-amber-400' };
    if (mode === 'road_trip') return { text: '🚗 Road Trip Mode', color: 'text-emerald-400' };
    return null;
  }, [tripContext.transport_mode]);

  // ════════════════════════════════════════════════════════════════
  //  RENDER
  // ════════════════════════════════════════════════════════════════
  return (
    <div className="relative min-h-screen bg-slate-950 text-slate-100 overflow-hidden px-4 pt-24 pb-8 sm:px-8 sm:pt-28 sm:pb-12 lg:px-12">
      {/* Background ambient gradients */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,_rgba(6,182,212,0.12),_transparent_55%)]" aria-hidden="true" />
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_right,_rgba(99,102,241,0.10),_transparent_55%)]" aria-hidden="true" />
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_center,_rgba(168,85,247,0.04),_transparent_70%)]" aria-hidden="true" />

      {/* CSS Animations */}
      <style>{`
        @keyframes typing-bounce {
          0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
          40% { transform: scale(1); opacity: 1; }
        }
        .typing-dot {
          display: inline-block;
          width: 7px;
          height: 7px;
          border-radius: 50%;
          background: linear-gradient(135deg, #06b6d4, #6366f1);
          animation: typing-bounce 1.2s infinite ease-in-out;
        }
        @keyframes msg-slide-in {
          from { opacity: 0; transform: translateY(12px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .msg-animate {
          animation: msg-slide-in 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
        @keyframes pulse-glow {
          0%, 100% { box-shadow: 0 0 0 0 rgba(6, 182, 212, 0.3); }
          50% { box-shadow: 0 0 12px 4px rgba(6, 182, 212, 0.15); }
        }
        .pulse-glow { animation: pulse-glow 2s infinite; }
        .scrollbar-thin::-webkit-scrollbar { width: 4px; }
        .scrollbar-thin::-webkit-scrollbar-track { background: transparent; }
        .scrollbar-thin::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 4px; }
        .scrollbar-thin::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }
      `}</style>

      <main className="relative z-10 max-w-7xl mx-auto space-y-6">

        {/* ═══ Header ═══════════════════════════════════════════════ */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-4 border-b border-white/10 pb-5">
          <div>
            <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.3em] text-white/60">
              <Zap className="w-3 h-3 text-cyan-400" />
              LangGraph Cooperative AI
            </span>
            <h1 className="mt-2 text-3xl font-black leading-tight tracking-tight sm:text-4xl">
              Roundtable{' '}
              <span className="bg-gradient-to-r from-cyan-400 via-sky-400 to-indigo-400 bg-clip-text text-transparent">
                AI Assistant
              </span>
            </h1>
            <p className="mt-1 text-sm text-white/50">
              Plan trips, estimate budgets, and explore destinations with stateful AI conversations.
            </p>
          </div>

          <button
            onClick={handleNewChat}
            className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/5 px-5 py-2.5 text-xs font-semibold uppercase tracking-wider text-slate-300 hover:bg-white/10 hover:border-white/25 transition-all duration-200"
            title="Reset context and messages"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            New Session
          </button>
        </div>

        {/* ═══ Core Layout Grid ═════════════════════════════════════ */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

          {/* ─── Chat Container ─── 8/12 columns ─────────────────── */}
          <div className="lg:col-span-8 flex flex-col h-[680px] border border-white/10 rounded-3xl bg-white/[0.03] backdrop-blur-xl shadow-[0_30px_80px_rgba(0,0,0,0.4)] overflow-hidden">

            {/* Chat Header Bar */}
            <div className="bg-slate-900/70 border-b border-white/10 px-5 py-3.5 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-cyan-500 to-indigo-600 flex items-center justify-center shadow-lg pulse-glow">
                  <Bot className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="font-bold text-sm tracking-wide text-slate-100">Conversational Planner</h3>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-[10px] text-cyan-400 font-semibold flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
                      Live Session
                    </span>
                    {transportModeBadge && (
                      <span className={`text-[10px] font-bold ${transportModeBadge.color} bg-white/5 px-2 py-0.5 rounded-full`}>
                        {transportModeBadge.text}
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <span className="text-[10px] text-slate-500 font-mono">ID: {sessionId.slice(-8)}</span>
            </div>

            {/* Chat Messages Scroll Area */}
            <div className="flex-1 overflow-y-auto p-5 space-y-5 scrollbar-thin">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex gap-3 max-w-[88%] msg-animate ${
                    msg.sender === 'user' ? 'ml-auto flex-row-reverse' : 'mr-auto'
                  }`}
                >
                  {/* Avatar */}
                  <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 border shadow-md ${
                    msg.sender === 'user'
                      ? 'bg-gradient-to-br from-cyan-500 to-indigo-600 text-white border-white/20'
                      : 'bg-slate-900 border-white/10 text-cyan-400'
                  }`}>
                    {msg.sender === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                  </div>

                  {/* Content */}
                  <div className="space-y-2 flex-1 min-w-0">

                    {/* Tool Execution Expanders */}
                    {msg.toolSteps && msg.toolSteps.length > 0 && (
                      <div className="space-y-1.5">
                        {msg.toolSteps.map((step, sIdx) => (
                          <div key={sIdx} className="border border-white/10 rounded-xl overflow-hidden bg-slate-900/50 backdrop-blur-sm">
                            <button
                              onClick={() => toggleToolCollapse(msg.id, step.name)}
                              className="w-full px-3.5 py-2 bg-slate-900/70 flex items-center justify-between text-[11px] font-bold text-slate-300 hover:bg-slate-800/50 transition-colors"
                            >
                              <span className="flex items-center gap-2">
                                {step.status === 'running'
                                  ? <Loader2 className="w-3.5 h-3.5 animate-spin text-cyan-400" />
                                  : <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                                }
                                <code className="bg-slate-950/80 px-1.5 py-0.5 rounded text-cyan-300 text-[10px]">{step.name}()</code>
                              </span>
                              {step.collapsed ? <ChevronDown className="w-3 h-3" /> : <ChevronUp className="w-3 h-3" />}
                            </button>

                            {!step.collapsed && (
                              <div className="p-3 text-[11px] font-mono bg-slate-950/70 text-cyan-300/80 max-h-36 overflow-y-auto leading-relaxed border-t border-white/5 scrollbar-thin">
                                {step.status === 'running' ? (
                                  <span className="italic text-slate-500 flex items-center gap-2">
                                    <Loader2 className="w-3 h-3 animate-spin" />
                                    Calling remote MCP servers...
                                  </span>
                                ) : (
                                  <pre className="whitespace-pre-wrap">{step.result}</pre>
                                )}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Chat Bubble */}
                    {msg.text && (
                      <div className={`px-4 py-3 rounded-2xl text-[13.5px] leading-relaxed shadow-sm ${
                        msg.sender === 'user'
                          ? 'bg-gradient-to-br from-cyan-600 to-indigo-600 text-white rounded-tr-sm border border-white/15'
                          : 'bg-white/[0.05] border border-white/10 backdrop-blur rounded-tl-sm text-slate-200'
                      }`}>
                        <div className="font-medium">
                          {msg.sender === 'assistant' ? renderMarkdown(msg.text) : <p className="whitespace-pre-line">{msg.text}</p>}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {/* Typing Indicator */}
              {loading && <TypingIndicator />}

              {/* Suggestion Chips - shown only after welcome */}
              {messages.length === 1 && !loading && (
                <div className="flex flex-wrap gap-2 pt-2 msg-animate">
                  <SuggestionChip icon={Car} text="Plan a road trip from Delhi to Shimla" onClick={() => handleSuggestion("Plan a road trip from Delhi to Shimla")} />
                  <SuggestionChip icon={CloudSun} text="What's the weather in Goa?" onClick={() => handleSuggestion("What's the weather in Goa?")} />
                  <SuggestionChip icon={DollarSign} text="Estimate budget for Mumbai to Bangalore" onClick={() => handleSuggestion("Estimate budget for Mumbai to Bangalore")} />
                  <SuggestionChip icon={Sparkles} text="Find events in Jaipur" onClick={() => handleSuggestion("Find events in Jaipur")} />
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input Bar */}
            <div className="border-t border-white/10 p-4 bg-slate-900/50">
              <div className="flex gap-2">
                <input
                  ref={inputRef}
                  disabled={loading}
                  className="flex-1 px-5 py-3 bg-white/[0.04] border border-white/10 rounded-2xl outline-none text-sm text-slate-200 font-medium placeholder-slate-500 focus:border-cyan-500/50 focus:bg-white/[0.07] transition-all duration-200"
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleSend()}
                  placeholder="Plan a trip, check weather, or ask anything..."
                />
                <button
                  disabled={loading}
                  onClick={handleSend}
                  className="px-5 py-3 bg-gradient-to-r from-cyan-500 via-sky-500 to-indigo-500 hover:from-cyan-600 hover:to-indigo-600 text-white font-bold rounded-2xl shadow-lg shadow-cyan-500/20 transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-4 h-4" />}
                </button>
              </div>
            </div>
          </div>

          {/* ─── Right Sidebar ─── 4/12 columns ──────────────────── */}
          <div className="lg:col-span-4 space-y-5">

            {/* Panel 1: Transport Mode Selector */}
            <div className="border border-white/10 rounded-3xl p-5 bg-white/[0.03] backdrop-blur-xl shadow-xl">
              <h3 className="font-bold text-xs uppercase tracking-widest text-slate-300 mb-4 flex items-center gap-2 pb-2 border-b border-white/5">
                <Globe className="w-4 h-4 text-cyan-400" />
                Travel Mode
              </h3>
              <div className="flex gap-2">
                <TransportModeCard
                  icon={Plane}
                  label="Flight"
                  value="flight"
                  selected={tripContext.transport_mode === 'flight'}
                  onClick={() => handleTransportModeSelect('flight')}
                  color="border-sky-400/60 bg-sky-500/15 shadow-sky-500/10"
                />
                <TransportModeCard
                  icon={TrainFront}
                  label="Train"
                  value="train"
                  selected={tripContext.transport_mode === 'train'}
                  onClick={() => handleTransportModeSelect('train')}
                  color="border-amber-400/60 bg-amber-500/15 shadow-amber-500/10"
                />
                <TransportModeCard
                  icon={Car}
                  label="Road Trip"
                  value="road_trip"
                  selected={tripContext.transport_mode === 'road_trip'}
                  onClick={() => handleTransportModeSelect('road_trip')}
                  color="border-emerald-400/60 bg-emerald-500/15 shadow-emerald-500/10"
                />
              </div>
            </div>

            {/* Panel 2: Editable Trip Context */}
            <div className="border border-white/10 rounded-3xl p-5 bg-white/[0.03] backdrop-blur-xl shadow-xl">
              <h3 className="font-bold text-xs uppercase tracking-widest text-slate-300 mb-4 flex items-center gap-2 pb-2 border-b border-white/5">
                <MapPin className="w-4 h-4 text-cyan-400" />
                Trip Details
              </h3>
              <div className="space-y-3">
                {renderContextField("Destination", "destination", <Compass className="w-3.5 h-3.5 text-indigo-400" />, "e.g. Shimla")}
                {renderContextField("Origin", "origin", <MapPin className="w-3.5 h-3.5 text-cyan-400" />, "e.g. Delhi")}
                {renderContextField("Duration (Days)", "num_days", <Calendar className="w-3.5 h-3.5 text-violet-400" />, "e.g. 5")}
                {renderContextField("Travelers", "travelers", <User className="w-3.5 h-3.5 text-emerald-400" />, "e.g. 2")}
                {renderContextField("Budget Tier", "budget_type", <DollarSign className="w-3.5 h-3.5 text-yellow-400" />, "e.g. Mid-range")}
                {renderContextField("Start Date", "start_date", <Calendar className="w-3.5 h-3.5 text-rose-400" />, "e.g. YYYY-MM-DD")}
              </div>
            </div>

            {/* Panel 3: Pipeline Timeline */}
            <div className="border border-white/10 rounded-3xl p-5 bg-white/[0.03] backdrop-blur-xl shadow-xl">
              <h3 className="font-bold text-xs uppercase tracking-widest text-slate-300 mb-4 flex items-center gap-2 pb-2 border-b border-white/5">
                <Compass className="w-4 h-4 text-indigo-400" />
                Pipeline Timeline
              </h3>
              <div className="flex flex-col pl-1">
                {toolTimelineItems.map(renderTimelineItem)}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
