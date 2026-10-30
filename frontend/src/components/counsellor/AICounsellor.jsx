import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import {
  GraduationCap,
  Sparkles,
  Send,
  User,
  Bot,
  RefreshCw,
  Sliders,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  CheckCircle2,
  HelpCircle,
  TrendingUp,
  BookOpen,
  ArrowRight,
  ShieldCheck,
  Flame,
  KeyRound
} from 'lucide-react';
import { api, CATEGORIES, BRANCHES } from '../../services/api';
import { useAppStore } from '../../store/useAppStore';
import { Button } from '../common/Button';

export const AICounsellor = () => {
  const storeProfile = useAppStore((state) => state.profile);
  const updateStoreProfile = useAppStore((state) => state.updateProfile);

  // Local student profile for the counsellor session
  const [profile, setProfile] = useState({
    percentile: storeProfile?.percentile || '95.50',
    category: storeProfile?.category || 'GOPEN',
    branch_family: 'CS_FAMILY',
    district: storeProfile?.home_university || 'Pune'
  });

  const [showProfileDrawer, setShowProfileDrawer] = useState(false);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [aiStatus, setAiStatus] = useState({ configured: false, model: 'gemini-2.5-flash', message: 'Checking...' });
  const [suggestions, setSuggestions] = useState([
    "Which colleges can I get with my percentile?",
    "Why is a college classified as Safe, Target or Ambitious?",
    "Compare two engineering colleges based on cutoff trends",
    "What is the difference between Freeze, Float and Slide in CAP?",
    "Which engineering branches should I consider?"
  ]);

  const [messages, setMessages] = useState([
    {
      id: 'welcome-1',
      role: 'assistant',
      content: `### 🎓 Welcome to GradMap AI Counselling!
I'm your **Generative AI Admission Assistant**, powered by the **Google Gemini API Free Tier** and strictly grounded in GradMap's **Scikit-learn prediction model** and **230k+ historical MHT-CET cutoff records**.

Here is what I can do for you:
- 📊 **Explain your ML predictions** (Why a choice is *Safe*, *Target*, or *Ambitious*)
- 🏛️ **Recommend colleges** tailored to your actual score and reservation category
- 📈 **Compare institutes & branches** with multi-year cutoff trends (2022–2025)
- 📝 **Guide your CAP Round Strategy** (Freeze, Float, Slide rules & Option Form order)

*Click any suggested question below or type your query to begin!*`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      modelUsed: 'gemini-2.5-flash',
      grounded: true
    }
  ]);

  const chatEndRef = useRef(null);
  const inputRef = useRef(null);

  // Check backend status on mount
  useEffect(() => {
    checkStatus();
  }, []);

  // Auto-scroll on new messages
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const checkStatus = async () => {
    try {
      const statusRes = await api.getAIStatus();
      setAiStatus(statusRes);
    } catch (e) {
      setAiStatus({
        configured: false,
        model: 'gemini-2.5-flash',
        message: 'Could not connect to FastAPI backend. Ensure backend is running.'
      });
    }
  };

  const handleReloadEnv = async () => {
    try {
      const res = await api.reloadAIEnv();
      setAiStatus({
        configured: res.configured,
        model: res.model,
        message: res.message
      });
    } catch (e) {
      console.error('Failed to reload .env', e);
    }
  };

  const handleSendMessage = async (textToSend) => {
    const text = (textToSend || inputMessage).trim();
    if (!text || isLoading) return;

    const userMsgId = `user-${Date.now()}`;
    const userMsg = {
      id: userMsgId,
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputMessage('');
    setIsLoading(true);

    try {
      // Build conversation history (excluding the very first welcome message)
      const history = messages
        .filter((m) => m.id !== 'welcome-1')
        .map((m) => ({ role: m.role, content: m.content }));

      const response = await api.aiChat({
        message: text,
        history,
        profile: {
          percentile: parseFloat(profile.percentile) || 0.0,
          category: profile.category,
          branch_family: profile.branch_family,
          district: profile.district
        }
      });

      const aiMsg = {
        id: `ai-${Date.now()}`,
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        modelUsed: response.model_used,
        grounded: response.grounded,
        status: response.status
      };

      setMessages((prev) => [...prev, aiMsg]);
      if (response.suggestions && response.suggestions.length > 0) {
        setSuggestions(response.suggestions);
      }
    } catch (error) {
      console.error('Chat error:', error);
      const errorMsg = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: `⚠️ **Unable to fetch response:** ${error.message || 'Server error'}.\n\nPlease ensure your FastAPI backend is running and that your \`GEMINI_API_KEY\` is configured in \`backend/.env\`.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        status: 'error'
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };

  const handleProfileChange = (field, val) => {
    const updated = { ...profile, [field]: val };
    setProfile(updated);
    if (field === 'percentile' || field === 'category') {
      updateStoreProfile({ [field]: val });
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const clearChat = () => {
    setMessages([
      {
        id: `welcome-${Date.now()}`,
        role: 'assistant',
        content: `### 🔄 Session Reset
Ask me anything about your admission path with your current profile (**${profile.percentile}%**, **${profile.category}**)!`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        modelUsed: aiStatus.model,
        grounded: true
      }
    ]);
  };

  return (
    <div className="min-h-screen bg-background bg-mesh flex flex-col font-sans selection:bg-emerald-500/30">
      
      {/* ── TOP NAVIGATION BAR ── */}
      <motion.nav
        initial={{ y: -40, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="sticky top-0 z-40 border-b border-white/5 bg-background/60 backdrop-blur-2xl px-4 md:px-8 py-3.5"
      >
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link to="/" className="flex items-center gap-2.5 group">
              <div className="w-9 h-9 bg-gradient-to-br from-emerald-600 via-teal-600 to-emerald-500 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-500/20 group-hover:scale-105 transition-transform">
                <GraduationCap className="text-white w-5 h-5" />
              </div>
              <span className="font-black text-xl text-gradient">GradMap</span>
            </Link>
            <span className="hidden sm:inline-block text-muted-foreground/40 font-light">|</span>
            <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-bold">
              <Sparkles className="w-3.5 h-3.5 text-amber-400 animate-pulse" />
              <span>AI Counsellor</span>
              <span className="text-[10px] px-1.5 py-0.2 bg-emerald-500/20 rounded text-emerald-300 font-mono">Gemini Free</span>
            </div>
          </div>

          <div className="flex items-center gap-2 sm:gap-3">
            {/* API Status Badge */}
            <button
              onClick={checkStatus}
              title={aiStatus.message}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border transition-all ${
                aiStatus.configured
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20'
                  : 'bg-amber-500/10 border-amber-500/30 text-amber-300 hover:bg-amber-500/20'
              }`}
            >
              {aiStatus.configured ? (
                <>
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="hidden md:inline">Gemini Online</span>
                </>
              ) : (
                <>
                  <KeyRound className="w-3.5 h-3.5 text-amber-400" />
                  <span className="hidden md:inline">Configure Key</span>
                </>
              )}
            </button>

            {/* Quick Navigation Links */}
            <Link to="/predictor">
              <Button variant="ghost" size="sm" className="hidden lg:flex text-xs">
                Predictor
              </Button>
            </Link>
            <Link to="/simulator">
              <Button variant="ghost" size="sm" className="hidden lg:flex text-xs">
                Simulator
              </Button>
            </Link>
            <Link to="/colleges">
              <Button variant="ghost" size="sm" className="hidden lg:flex text-xs">
                Colleges
              </Button>
            </Link>

            <Button
              variant="outline"
              size="sm"
              onClick={clearChat}
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              <RefreshCw className="w-3.5 h-3.5 sm:mr-1.5" />
              <span className="hidden sm:inline">New Session</span>
            </Button>
          </div>
        </div>
      </motion.nav>

      {/* ── PROFILE CONTEXT BAR ── */}
      <div className="border-b border-white/5 bg-emerald-950/20 backdrop-blur-md px-4 md:px-8 py-2.5">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex flex-wrap items-center gap-2 text-muted-foreground">
            <span className="font-semibold text-foreground flex items-center gap-1.5 text-amber-200">
              <Sliders className="w-3.5 h-3.5 text-emerald-400" />
              Counselling Context:
            </span>
            <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 font-bold">
              <span>Percentile:</span>
              <span className="text-foreground font-mono">{profile.percentile || '0'}%</span>
            </div>
            <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md bg-amber-500/10 border border-amber-500/20 text-amber-300 font-bold">
              <span>Category:</span>
              <span className="text-foreground">{profile.category}</span>
            </div>
            <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md bg-teal-500/10 border border-teal-500/20 text-teal-300 font-bold hidden sm:inline-flex">
              <span>Branch:</span>
              <span className="text-foreground">{profile.branch_family}</span>
            </div>
          </div>

          <button
            onClick={() => setShowProfileDrawer(!showProfileDrawer)}
            className="text-emerald-400 hover:text-emerald-300 font-semibold flex items-center gap-1 ml-auto text-xs transition-colors"
          >
            <span>{showProfileDrawer ? 'Hide Profile Settings' : 'Edit Profile Context'}</span>
            {showProfileDrawer ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>

        {/* Collapsible Profile Customization */}
        <AnimatePresence>
          {showProfileDrawer && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden pt-3 pb-1"
            >
              <div className="p-4 rounded-2xl glass border-white/10 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                  <label className="text-[10px] font-black uppercase text-muted-foreground tracking-wider block mb-1.5">
                    MHT-CET Percentile
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="100"
                    value={profile.percentile}
                    onChange={(e) => handleProfileChange('percentile', e.target.value)}
                    className="w-full bg-background/70 border border-white/10 rounded-xl px-3 py-1.5 text-xs text-foreground focus:outline-none focus:border-emerald-500 font-mono font-bold"
                  />
                </div>

                <div>
                  <label className="text-[10px] font-black uppercase text-muted-foreground tracking-wider block mb-1.5">
                    Category (Seat Matrix)
                  </label>
                  <select
                    value={profile.category}
                    onChange={(e) => handleProfileChange('category', e.target.value)}
                    className="w-full bg-background/70 border border-white/10 rounded-xl px-3 py-1.5 text-xs text-foreground focus:outline-none focus:border-emerald-500"
                  >
                    {CATEGORIES.map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-[10px] font-black uppercase text-muted-foreground tracking-wider block mb-1.5">
                    Target Branch Family
                  </label>
                  <select
                    value={profile.branch_family}
                    onChange={(e) => handleProfileChange('branch_family', e.target.value)}
                    className="w-full bg-background/70 border border-white/10 rounded-xl px-3 py-1.5 text-xs text-foreground focus:outline-none focus:border-emerald-500"
                  >
                    <option value="CS_FAMILY">Computer & IT Family</option>
                    <option value="CIRCUITS_FAMILY">Electronics & Circuits</option>
                    <option value="CORE_MECHANICAL">Mechanical & Robotics</option>
                    <option value="CIVIL_FAMILY">Civil Engineering</option>
                    <option value="CHEMICAL_FAMILY">Chemical & Allied</option>
                    <option value="ALL">All Branches</option>
                  </select>
                </div>

                <div>
                  <label className="text-[10px] font-black uppercase text-muted-foreground tracking-wider block mb-1.5">
                    Preferred Location / District
                  </label>
                  <input
                    type="text"
                    value={profile.district}
                    onChange={(e) => handleProfileChange('district', e.target.value)}
                    placeholder="e.g. Pune, Mumbai"
                    className="w-full bg-background/70 border border-white/10 rounded-xl px-3 py-1.5 text-xs text-foreground focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* ── API KEY CONFIG BANNER (Visible if key not configured) ── */}
      {!aiStatus.configured && (
        <div className="bg-gradient-to-r from-amber-500/15 via-orange-500/10 to-amber-500/15 border-b border-amber-500/20 px-4 md:px-8 py-2.5">
          <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-3 text-xs">
            <div className="flex items-center gap-2 text-amber-200">
              <KeyRound className="w-4 h-4 text-amber-400 shrink-0" />
              <span>
                <strong>Gemini API Key Required:</strong> Add your free key to <code className="bg-black/30 px-1.5 py-0.5 rounded text-amber-300">backend/.env</code> to unlock real-time Gemini generation.
              </span>
            </div>
            <div className="flex items-center gap-2">
              <a
                href="https://aistudio.google.com/app/apikey"
                target="_blank"
                rel="noreferrer"
                className="underline text-amber-400 hover:text-amber-300 font-semibold"
              >
                Get Free Key ↗
              </a>
              <button
                onClick={handleReloadEnv}
                className="px-2.5 py-1 rounded bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/30 text-[11px] font-bold transition-all"
              >
                Reload .env
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── MAIN CHAT AREA ── */}
      <main className="flex-1 max-w-5xl w-full mx-auto p-4 md:p-6 flex flex-col">
        {/* Messages Container */}
        <div className="flex-1 space-y-6 pb-6 overflow-y-auto min-h-[400px]">
          {messages.map((msg) => {
            const isUser = msg.role === 'user';
            return (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className={`flex gap-3 md:gap-4 ${isUser ? 'justify-end' : 'justify-start'}`}
              >
                {!isUser && (
                  <div className="w-9 h-9 rounded-2xl bg-gradient-to-br from-emerald-600 via-teal-600 to-emerald-500 flex items-center justify-center text-white shrink-0 shadow-md shadow-emerald-500/20 mt-1">
                    <Bot className="w-5 h-5" />
                  </div>
                )}

                <div
                  className={`max-w-[85%] md:max-w-[78%] rounded-3xl p-5 shadow-lg ${
                    isUser
                      ? 'bg-gradient-to-br from-emerald-600 to-teal-700 text-white rounded-tr-sm'
                      : 'glass-morphism border-white/10 rounded-tl-sm text-foreground bg-card/75'
                  }`}
                >
                  {/* Message Meta Info */}
                  <div className="flex items-center justify-between gap-3 mb-2 pb-1.5 border-b border-white/10 text-[11px]">
                    <span className="font-bold tracking-wide flex items-center gap-1.5">
                      {isUser ? (
                        <>
                          <User className="w-3.5 h-3.5" /> You
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-3.5 h-3.5 text-amber-400" /> GradMap Counsellor
                        </>
                      )}
                    </span>
                    <div className="flex items-center gap-2 text-muted-foreground text-[10px]">
                      {msg.grounded && !isUser && (
                        <span className="flex items-center gap-1 text-emerald-400 font-bold bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                          <ShieldCheck className="w-3 h-3" /> Data Grounded
                        </span>
                      )}
                      <span>{msg.timestamp}</span>
                    </div>
                  </div>

                  {/* Message Content */}
                  <div className="prose prose-invert prose-emerald max-w-none text-sm leading-relaxed space-y-2.5">
                    <ReactMarkdown
                      components={{
                        h1: ({ node, ...props }) => <h1 className="text-xl font-bold text-foreground mt-2 mb-1" {...props} />,
                        h2: ({ node, ...props }) => <h2 className="text-lg font-bold text-foreground mt-2 mb-1" {...props} />,
                        h3: ({ node, ...props }) => <h3 className="text-base font-bold text-emerald-400 mt-2 mb-1" {...props} />,
                        h4: ({ node, ...props }) => <h4 className="text-sm font-bold text-amber-300 mt-1.5 mb-1" {...props} />,
                        p: ({ node, ...props }) => <p className="mb-2 leading-relaxed" {...props} />,
                        ul: ({ node, ...props }) => <ul className="list-disc pl-5 my-2 space-y-1" {...props} />,
                        ol: ({ node, ...props }) => <ol className="list-decimal pl-5 my-2 space-y-1" {...props} />,
                        li: ({ node, ...props }) => <li className="pl-1" {...props} />,
                        strong: ({ node, ...props }) => <strong className="font-bold text-emerald-300" {...props} />,
                        code: ({ node, inline, ...props }) =>
                          inline ? (
                            <code className="bg-black/30 text-amber-300 px-1.5 py-0.5 rounded font-mono text-xs" {...props} />
                          ) : (
                            <code className="block bg-black/40 text-emerald-300 p-3 rounded-xl font-mono text-xs my-2 overflow-x-auto" {...props} />
                          ),
                        blockquote: ({ node, ...props }) => (
                          <blockquote className="border-l-4 border-emerald-500 pl-3 italic text-muted-foreground my-2" {...props} />
                        )
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                </div>

                {isUser && (
                  <div className="w-9 h-9 rounded-2xl bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center text-white shrink-0 shadow-md shadow-orange-500/20 mt-1">
                    <User className="w-5 h-5" />
                  </div>
                )}
              </motion.div>
            );
          })}

          {/* Loading Indicator */}
          {isLoading && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex gap-3 md:gap-4 items-start"
            >
              <div className="w-9 h-9 rounded-2xl bg-gradient-to-br from-emerald-600 to-teal-600 flex items-center justify-center text-white shrink-0 shadow-md shadow-emerald-500/20 animate-pulse">
                <Bot className="w-5 h-5" />
              </div>
              <div className="glass-morphism rounded-3xl rounded-tl-sm p-4 px-6 border-white/10 flex items-center gap-3 shadow-lg">
                <div className="flex gap-1.5">
                  <span className="w-2.5 h-2.5 bg-emerald-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
                  <span className="w-2.5 h-2.5 bg-teal-400 rounded-full animate-bounce [animation-delay:-0.15s]" />
                  <span className="w-2.5 h-2.5 bg-amber-400 rounded-full animate-bounce" />
                </div>
                <span className="text-xs text-muted-foreground font-medium">
                  GradMap AI is analyzing ML predictions & historical cutoffs...
                </span>
              </div>
            </motion.div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* ── SUGGESTED QUESTIONS CHIPS ── */}
        <div className="py-2.5">
          <div className="text-[11px] font-black uppercase text-muted-foreground tracking-wider mb-2 flex items-center gap-1.5">
            <Flame className="w-3.5 h-3.5 text-amber-400" /> Suggested for your score:
          </div>
          <div className="flex flex-wrap gap-2">
            {suggestions.slice(0, 4).map((sugg, idx) => (
              <button
                key={idx}
                disabled={isLoading}
                onClick={() => handleSendMessage(sugg)}
                className="text-xs bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/20 hover:border-emerald-500/40 text-emerald-200 hover:text-white px-3.5 py-1.5 rounded-full transition-all text-left flex items-center gap-1.5 shadow-sm active:scale-95 disabled:opacity-50"
              >
                <span>{sugg}</span>
                <ArrowRight className="w-3 h-3 text-emerald-400 shrink-0" />
              </button>
            ))}
          </div>
        </div>

        {/* ── INPUT BOX & CONTROLS ── */}
        <div className="pt-2 sticky bottom-4 z-20">
          <div className="glass-morphism border-white/10 rounded-2xl p-2 shadow-2xl flex items-center gap-2 bg-card/90">
            <textarea
              ref={inputRef}
              rows={1}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about colleges, Safe/Target chances, branch comparisons, or CAP Round rules..."
              className="flex-1 bg-transparent px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground/60 focus:outline-none resize-none max-h-32 min-h-[44px]"
            />

            <Button
              variant="premium"
              size="md"
              disabled={isLoading || !inputMessage.trim()}
              onClick={() => handleSendMessage()}
              className="rounded-xl px-4 shrink-0 shadow-lg"
            >
              <Send className="w-4 h-4 mr-1" />
              <span className="hidden sm:inline">Ask AI</span>
            </Button>
          </div>
          <div className="text-[11px] text-muted-foreground/60 text-center mt-2 flex items-center justify-center gap-2">
            <span>Powered by Google Gemini Free Tier</span>
            <span>•</span>
            <span>ML Model Grounded</span>
            <span>•</span>
            <span>Official MHT-CET Historical Records</span>
          </div>
        </div>
      </main>
    </div>
  );
};
