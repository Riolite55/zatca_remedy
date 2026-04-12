"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { Send, BarChart2, MessageSquare, Database, Sparkles, Loader2, Trash2, Pin, LayoutDashboard, RefreshCcw, Plus, Wand2, LogOut, Pencil, Check, X, FileDown } from "lucide-react";
import * as htmlToImage from "html-to-image";
import { jsPDF } from "jspdf";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts';
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from "@/components/ui/resizable";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";

interface ChartDef {
  id?: string;
  title: string;
  type: "metric" | "table" | "bar" | "pie" | "line";
  sql_query: string;
  x_col?: string;
  y_col?: string;
  data: any[];
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  charts?: ChartDef[];
  follow_ups?: string[];
}

interface KPI {
  label: string;
  value: string | number;
  type: "text" | "number" | "percentage";
}

interface Dashboard {
  id: string;
  name: string;
}

interface Session {
  id: string;
  title: string;
  updated_at: string;
}

// ZATCA Colors: Royal Blue, Teal, Green, Light Blue, Dark Blue, Orange
const COLORS = ['#2053a4', '#4fbbbd', '#62b34f', '#0996d4', '#1d3761', '#f59e0b'];


const AnimatedChatPlaceholder = ({ kpis, suggestions, onSuggestionClick }: { kpis: KPI[], suggestions: string[], onSuggestionClick: (q: string) => void }) => (
  <div className="flex flex-col items-center justify-center w-full space-y-8 animate-in fade-in zoom-in duration-500 py-8">
    {/* KPI Banner */}
    {kpis.length > 0 && (
      <div className="w-full max-w-5xl">
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
          {kpis.map((kpi, i) => (
            <div key={i} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow">
              <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">{kpi.label}</p>
              <p className={`font-bold truncate ${
                kpi.type === 'number' ? 'text-2xl text-[#2053a4]' :
                kpi.type === 'percentage' ? 'text-2xl text-[#62b34f]' :
                'text-sm text-[#1d3761] dark:text-slate-200'
              }`}>{kpi.value}</p>
            </div>
          ))}
        </div>
      </div>
    )}

    {/* Icon + Title */}
    <div className="flex flex-col items-center space-y-4">
      <div className="relative w-24 h-24 flex items-center justify-center">
        <div className="absolute w-12 h-12 bg-blue-100 dark:bg-slate-800 rounded-2xl rounded-tr-sm right-1 top-1 animate-[bounce_3s_infinite]" />
        <div className="absolute w-14 h-14 bg-[#2053a4] rounded-2xl rounded-tl-sm left-1 bottom-1 animate-[bounce_3s_infinite_200ms] flex items-center justify-center shadow-lg">
          <Sparkles className="text-white w-7 h-7 animate-pulse" />
        </div>
      </div>
      <div className="space-y-2 text-center">
        <h3 className="text-xl font-semibold text-[#1d3761] dark:text-slate-200 tracking-tight">AI Analytical Chat</h3>
        <p className="text-slate-500 text-sm max-w-sm mx-auto leading-relaxed">
          Ask a question or pick a suggestion below to get started.
        </p>
      </div>
    </div>

    {/* Suggested Questions */}
    {suggestions.length > 0 && (
      <div className="w-full max-w-3xl">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {suggestions.map((q, i) => (
            <button
              key={i}
              onClick={() => onSuggestionClick(q)}
              className="text-left px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 hover:border-[#2053a4] hover:bg-blue-50 dark:hover:bg-slate-800 transition-all text-sm text-slate-700 dark:text-slate-300 shadow-sm hover:shadow-md group"
            >
              <span className="text-[#2053a4] mr-2 group-hover:mr-3 transition-all">&#8594;</span>
              {q}
            </button>
          ))}
        </div>
      </div>
    )}
  </div>
);

const AnimatedDashboardPlaceholder = () => (
  <div className="flex flex-col items-center justify-center min-h-[60vh] w-full space-y-6 animate-in fade-in zoom-in duration-500">
    <div className="relative w-40 h-32 flex items-end justify-center gap-3 pb-2">
      <div className="w-6 bg-[#2053a4] rounded-t-sm animate-[pulse_1.5s_infinite_100ms] h-12 shadow-sm" />
      <div className="w-6 bg-[#4fbbbd] rounded-t-sm animate-[pulse_1.5s_infinite_300ms] h-20 shadow-sm" />
      <div className="w-6 bg-[#62b34f] rounded-t-sm animate-[pulse_1.5s_infinite_500ms] h-16 shadow-sm" />
      <div className="w-6 bg-[#0996d4] rounded-t-sm animate-[pulse_1.5s_infinite_700ms] h-24 shadow-sm" />
      
      <div className="absolute -top-4 right-0 w-16 h-12 bg-white dark:bg-slate-800 shadow-xl border border-slate-100 dark:border-slate-700 rounded-md animate-[bounce_4s_infinite] flex flex-col p-2 gap-1">
        <div className="w-full h-2 bg-slate-100 dark:bg-slate-700 rounded-full" />
        <div className="w-2/3 h-2 bg-slate-100 dark:bg-slate-700 rounded-full" />
      </div>
    </div>
    <div className="space-y-3 text-center">
      <h3 className="text-2xl font-semibold text-[#1d3761] dark:text-slate-200 tracking-tight">Interactive Dashboards</h3>
      <p className="text-slate-500 text-sm max-w-sm mx-auto leading-relaxed">
        Select a dashboard to view your pinned metrics, or go to the Chats tab to start building a new one.
      </p>
    </div>
  </div>
);

export default function Home() {

  const router = useRouter();
  
  // Auth State
  const [token, setToken] = useState<string | null>(null);
  const [username, setUsername] = useState<string | null>(null);
  const [role, setRole] = useState<string | null>(null);
  const [department, setDepartment] = useState<string | null>(null);
  const [authChecked, setAuthChecked] = useState(false);

  // Persona State
  const [kpis, setKpis] = useState<KPI[]>([]);
  const [suggestions, setSuggestions] = useState<string[]>([]);

  // Chat State
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState<"chat" | "dashboard">("chat");
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);

  // Dashboards State
  const [dashboards, setDashboards] = useState<Dashboard[]>([]);
  const [selectedDashboard, setSelectedDashboard] = useState<string | null>(null);
  const [dashboardWidgets, setDashboardWidgets] = useState<ChartDef[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [editingWidgetId, setEditingWidgetId] = useState<string | null>(null);
  const [editingWidgetTitle, setEditingWidgetTitle] = useState("");
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingSessionTitle, setEditingSessionTitle] = useState("");
  const [editingDashboardId, setEditingDashboardId] = useState<string | null>(null);
  const [editingDashboardName, setEditingDashboardName] = useState("");
  
  // Pinning Dialog State
  const [pinDialogOpen, setPinDialogOpen] = useState(false);
  const [chartToPin, setChartToPin] = useState<ChartDef | null>(null);
  const [newDashboardName, setNewDashboardName] = useState("");
  const [pinTargetId, setPinTargetId] = useState<string>("");

  // PDF Export
  const dashboardRef = useRef<HTMLDivElement>(null);
  const [exportingPDF, setExportingPDF] = useState(false);

  // Auto Scroll
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  useEffect(() => {
    const t = localStorage.getItem("token");
    const u = localStorage.getItem("username");
    if (!t) {
      router.push("/login");
    } else {
      setToken(t);
      setUsername(u);
      setRole(localStorage.getItem("role"));
      setDepartment(localStorage.getItem("department") || null);
      setAuthChecked(true);
    }
  }, [router]);

  useEffect(() => {
    if (authChecked && token) {
      fetchSessions();
      fetchDashboards();
      fetchPersonaData();
    }
  }, [authChecked, token]);

  useEffect(() => {
    if (selectedDashboard && token) {
      refreshDashboard(selectedDashboard);
    }
  }, [selectedDashboard, token]);

  // --- API Wrappers with Auth ---
  const authFetch = async (url: string, options: any = {}) => {
    if (!token) return null;
    const headers = {
      ...options.headers,
      "Authorization": `Bearer ${token}`
    };
    const res = await fetch(url, { ...options, headers });
    if (res.status === 401) {
      handleLogout();
      throw new Error("Unauthorized");
    }
    return res;
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    localStorage.removeItem("role");
    localStorage.removeItem("department");
    router.push("/login");
  };

  const fetchPersonaData = async () => {
    try {
      const [kpiRes, sugRes] = await Promise.all([
        authFetch("http://localhost:8000/api/persona/kpis"),
        authFetch("http://localhost:8000/api/persona/suggestions"),
      ]);
      if (kpiRes) {
        const data = await kpiRes.json();
        setKpis(data.kpis);
      }
      if (sugRes) {
        const data = await sugRes.json();
        setSuggestions(data.suggestions);
      }
    } catch (e) {}
  };

  const fetchSessions = async () => {
    try {
      const res = await authFetch("http://localhost:8000/api/sessions");
      if (res) setSessions(await res.json());
    } catch (e) {}
  };

  const loadSession = async (id: string) => {
    try {
      const res = await authFetch(`http://localhost:8000/api/sessions/${id}`);
      if (res) {
        const data = await res.json();
        setMessages(data.history);
        setActiveSessionId(id);
        setViewMode("chat");
      }
    } catch (e) {}
  };

  const handleTabChange = (val: string) => {
    const newMode = val === "chats" ? "chat" : "dashboard";
    setViewMode(newMode);
    if (newMode === "chat") {
      setActiveSessionId(null);
      setMessages([]);
    } else {
      setSelectedDashboard(null);
      setDashboardWidgets([]);
    }
  };

  const handleNewChat = () => {
    setActiveSessionId(null);
    setMessages([]);
    setViewMode("chat");
  };

  const fetchDashboards = async () => {
    try {
      const res = await authFetch("http://localhost:8000/api/dashboards");
      if (res) {
        const data = await res.json();
        setDashboards(data);
        if (data.length > 0 && !selectedDashboard) {
          setSelectedDashboard(data[0].id);
          setPinTargetId(data[0].id);
        }
      }
    } catch (e) {}
  };

  const refreshDashboard = async (id: string) => {
    setRefreshing(true);
    try {
      const res = await authFetch(`http://localhost:8000/api/dashboards/${id}/refresh`);
      if (res) setDashboardWidgets(await res.json());
    } catch (e) {
      console.error(e);
    } finally {
      setRefreshing(false);
    }
  };

  const handleSimulate = async () => {
    setRefreshing(true);
    try {
      await authFetch("http://localhost:8000/api/simulate-activity", { method: "POST" });
      if (selectedDashboard) {
        await refreshDashboard(selectedDashboard);
      }
    } finally {
      setRefreshing(false);
    }
  };

  const handleRenameSession = async (id: string) => {
    if (!editingSessionTitle.trim()) {
      setEditingSessionId(null);
      return;
    }
    try {
      const res = await authFetch(`http://localhost:8000/api/sessions/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: editingSessionTitle }),
      });
      if (res && res.ok) {
        setSessions(prev => prev.map(s => s.id === id ? { ...s, title: editingSessionTitle } : s));
      }
    } catch (e) {
      console.error(e);
    } finally {
      setEditingSessionId(null);
    }
  };

  const handleRenameDashboard = async (id: string) => {
    if (!editingDashboardName.trim()) {
      setEditingDashboardId(null);
      return;
    }
    try {
      const res = await authFetch(`http://localhost:8000/api/dashboards/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: editingDashboardName }),
      });
      if (res && res.ok) {
        setDashboards(prev => prev.map(d => d.id === id ? { ...d, name: editingDashboardName } : d));
      }
    } catch (e) {
      console.error(e);
    } finally {
      setEditingDashboardId(null);
    }
  };

  const handleRenameWidget = async (widgetId: string) => {
    if (!selectedDashboard || !editingWidgetTitle.trim()) {
      setEditingWidgetId(null);
      return;
    }
    try {
      const res = await authFetch(`http://localhost:8000/api/dashboards/${selectedDashboard}/widgets/${widgetId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: editingWidgetTitle }),
      });
      
      if (res && res.ok) {
        setDashboardWidgets(prev => prev.map(w => w.id === widgetId ? { ...w, title: editingWidgetTitle } : w));
      }
    } catch (e) {
      console.error(e);
    } finally {
      setEditingWidgetId(null);
    }
  };

  const handlePin = async () => {
    if (!chartToPin) return;
    let targetId = pinTargetId;
    
    if (targetId === "new" && newDashboardName.trim()) {
      const res = await authFetch("http://localhost:8000/api/dashboards", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newDashboardName }),
      });
      if (res) {
        const data = await res.json();
        targetId = data.id;
        await fetchDashboards();
        setSelectedDashboard(targetId);
      }
    }

    if (!targetId || targetId === "new") return;

    await authFetch(`http://localhost:8000/api/dashboards/${targetId}/widgets`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: chartToPin.title,
        type: chartToPin.type,
        sql_query: chartToPin.sql_query,
        x_col: chartToPin.x_col,
        y_col: chartToPin.y_col
      }),
    });

    setPinDialogOpen(false);
    setChartToPin(null);
    setNewDashboardName("");
    if (selectedDashboard === targetId) {
      refreshDashboard(targetId);
    }
  };

  const handleExportPDF = async () => {
    if (!dashboardRef.current || !selectedDashboard) return;
    
    setExportingPDF(true);
    
    try {
      const dashboardObj = dashboards.find(d => d.id === selectedDashboard);
      const dashboardName = dashboardObj?.name || 'Dashboard';
      
      const imgData = await htmlToImage.toJpeg(dashboardRef.current, {
        quality: 1.0, 
        backgroundColor: '#ffffff',
        pixelRatio: 2,
      });

      // Get natural dimensions of the DOM node
      const imgWidth = dashboardRef.current.offsetWidth;
      const imgHeight = dashboardRef.current.offsetHeight;
      
      const pdf = new jsPDF({
        orientation: 'landscape',
        unit: 'mm',
        format: 'a4'
      });
      
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = pdf.internal.pageSize.getHeight();
      
      const ratio = Math.min((pdfWidth - 20) / imgWidth, (pdfHeight - 30) / imgHeight);
      
      const imgX = (pdfWidth - imgWidth * ratio) / 2;
      const imgY = 20; 
      
      // ZATCA Header
      pdf.setTextColor(29, 55, 97); // #1d3761
      pdf.setFontSize(22);
      pdf.text(`ZATCA Remedy BI`, 14, 15);
      
      pdf.setTextColor(100, 100, 100);
      pdf.setFontSize(12);
      pdf.text(`${dashboardName} | Generated: ${new Date().toLocaleString()}`, 14, 22);
      
      // Divider
      pdf.setDrawColor(200, 200, 200);
      pdf.line(14, 26, pdfWidth - 14, 26);
      
      pdf.addImage(imgData, 'JPEG', imgX, 30, imgWidth * ratio, imgHeight * ratio);
      
      pdf.save(`ZATCA_${dashboardName.replace(/\s+/g, '_')}.pdf`);
    } catch (err) {
      console.error('Error generating PDF:', err);
    } finally {
      setExportingPDF(false);
    }
  };

  const activeChatDashboard = messages.filter(m => m.role === "assistant").pop();

  const handleSuggestionClick = (question: string) => {
    setInput(question);
  };

  const handleFollowUpClick = (question: string) => {
    setInput(question);
  };

  const handleSend = async () => {
    if (!input.trim() || !token) return;

    const userMsg = { role: "user" as const, content: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await authFetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          prompt: userMsg.content,
          session_id: activeSessionId 
        }),
      });

      if (!res) throw new Error("API Error");
      const data = await res.json();
      
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.message, charts: data.charts, follow_ups: data.follow_ups },
      ]);
      
      if (!activeSessionId) {
        setActiveSessionId(data.session_id);
        fetchSessions(); // Refresh sidebar
      }
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, I encountered an error communicating with the API." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const renderChart = (chart: ChartDef) => {
    if (!chart.data || chart.data.length === 0) {
      return <div className="p-4 text-center text-muted-foreground">No data returned for this query.</div>;
    }

    if (chart.type === "metric") {
      const val = Object.values(chart.data[0])[0];
      return (
        <div className="flex flex-col items-center justify-center p-6 h-48">
          <span className="text-5xl font-bold text-primary">{val as string}</span>
        </div>
      );
    }

    if (chart.type === "table") {
      const headers = Object.keys(chart.data[0]);
      return (
        <ScrollArea className="h-64 rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                {headers.map(h => <TableHead key={h}>{h}</TableHead>)}
              </TableRow>
            </TableHeader>
            <TableBody>
              {chart.data.map((row, i) => (
                <TableRow key={i}>
                  {headers.map(h => <TableCell key={h}>{row[h]}</TableCell>)}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </ScrollArea>
      );
    }

    const xCol = chart.x_col || Object.keys(chart.data[0])[0];
    const yCol = chart.y_col || Object.keys(chart.data[0])[1];

    if (chart.type === "bar") {
      return (
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chart.data} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
              <XAxis dataKey={xCol} tick={{fontSize: 12}} interval={0} angle={-45} textAnchor="end" stroke="#64748b" />
              <YAxis stroke="#64748b" />
              <Tooltip cursor={{fill: 'transparent'}} contentStyle={{borderRadius: '8px'}} />
              <Bar dataKey={yCol} fill="var(--color-chart-1)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      );
    }

    if (chart.type === "pie") {
      return (
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={chart.data} dataKey={yCol} nameKey={xCol} cx="50%" cy="50%" innerRadius={60} outerRadius={80} paddingAngle={2}>
                {chart.data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{borderRadius: '8px'}} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      );
    }

    if (chart.type === "line") {
      return (
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chart.data} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
              <XAxis dataKey={xCol} tick={{fontSize: 12}} stroke="#64748b" />
              <YAxis stroke="#64748b" />
              <Tooltip contentStyle={{borderRadius: '8px'}} />
              <Line type="monotone" dataKey={yCol} stroke="var(--color-chart-2)" strokeWidth={3} dot={{r: 4}} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      );
    }
    return null;
  };

  // Prevent flash of content before auth is checked
  if (!authChecked) return <div className="h-screen w-full bg-slate-50 dark:bg-slate-950 flex items-center justify-center"><Loader2 className="animate-spin text-blue-500" size={32}/></div>;

  return (
    <div className="h-screen w-full bg-slate-50 dark:bg-slate-950 overflow-hidden flex">
      
      {/* Pin Dialog */}
      <Dialog open={pinDialogOpen} onOpenChange={setPinDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Pin to Dashboard</DialogTitle>
            <DialogDescription>
              Save "{chartToPin?.title}" to a persistent dashboard. It will automatically fetch fresh data.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Select Dashboard</Label>
              <Select value={pinTargetId} onValueChange={(val) => setPinTargetId(val || "")}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a dashboard" />
                </SelectTrigger>
                <SelectContent>
                  {dashboards.map(d => (
                    <SelectItem key={d.id} value={d.id}>{d.name}</SelectItem>
                  ))}
                  <SelectItem value="new" className="text-primary font-medium">+ Create New Dashboard</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {pinTargetId === "new" && (
              <div className="space-y-2">
                <Label>New Dashboard Name</Label>
                <Input value={newDashboardName} onChange={e => setNewDashboardName(e.target.value)} placeholder="e.g. Daily Ops Review" />
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setPinDialogOpen(false)}>Cancel</Button>
            <Button onClick={handlePin} disabled={pinTargetId === "new" && !newDashboardName.trim()}>Pin Widget</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <ResizablePanelGroup autoSaveId="dashboard-layout" direction="horizontal" className="flex-1 h-full w-full">

      {/* LEFT SIDEBAR: ChatGPT Style Session History & ZATCA Branding */}
      <ResizablePanel defaultSize={20} minSize={15} maxSize={30} className="hidden md:flex flex-col h-full bg-[#1d3761] text-white border-r border-[#152846] shadow-xl z-20">
        <div className="p-6 flex items-center justify-center border-b border-white/10 bg-white shrink-0">
          <img src="/zatca-logo-light.png" alt="ZATCA Logo" className="h-16 w-auto object-contain" />
        </div>
        
        <Tabs value={viewMode === "chat" ? "chats" : "dashboards"} onValueChange={handleTabChange} className="flex-1 flex flex-col overflow-hidden">
          <div className="px-4 pt-4 shrink-0">
            <TabsList className="w-full bg-white/10 border border-white/20 p-1 mb-4 h-auto">
              <TabsTrigger value="chats" className="flex-1 text-xs py-1.5 data-[state=active]:bg-white data-[state=active]:text-[#1d3761] text-white">Chats</TabsTrigger>
              <TabsTrigger value="dashboards" className="flex-1 text-xs py-1.5 data-[state=active]:bg-white data-[state=active]:text-[#1d3761] text-white">Dashboards</TabsTrigger>
            </TabsList>
          </div>
          
          {/* CHATS TAB */}
          <TabsContent value="chats" className="flex-1 flex flex-col m-0 outline-none overflow-hidden">
            <div className="px-4 pb-3 shrink-0">
              <Button variant="outline" className="w-full justify-start gap-2 bg-white/10 border-white/20 text-white hover:bg-white/20 hover:text-white transition-all shadow-none" onClick={handleNewChat}>
                <Plus size={16} /> New Analysis
              </Button>
            </div>
            <ScrollArea className="flex-1 px-3">
              <div className="space-y-1 pb-4">
                <h4 className="text-[10px] font-semibold text-white/50 uppercase tracking-wider mb-2 px-2 mt-1">Chat History</h4>
                {sessions.map(s => (
                  <button 
                    key={s.id} 
                    onClick={() => loadSession(s.id)}
                    className={`w-full text-left px-3 py-2.5 rounded-md text-sm flex items-center gap-2 transition-colors overflow-hidden ${
                      activeSessionId === s.id && viewMode === "chat" ? 'bg-white/20 text-white font-medium' : 'hover:bg-white/10 text-white/80'
                    }`}
                    title={s.title}
                  >
                    <MessageSquare size={14} className={`shrink-0 ${activeSessionId === s.id && viewMode === "chat" ? 'text-[#4fbbbd]' : 'opacity-70'}`}/>
                    <span className="truncate flex-1 min-w-0">{s.title}</span>
                  </button>
                ))}
                {sessions.length === 0 && (
                  <div className="p-4 text-xs text-white/50 text-center">No chat history yet.</div>
                )}
              </div>
            </ScrollArea>
          </TabsContent>

          {/* DASHBOARDS TAB */}
          <TabsContent value="dashboards" className="flex-1 flex flex-col m-0 outline-none overflow-hidden">
            <div className="px-4 pb-3 shrink-0 flex items-center justify-between">
              <span className="text-xs font-medium text-white/70 uppercase">My Dashboards</span>
            </div>
            <ScrollArea className="flex-1 px-3">
              <div className="space-y-1 pb-4">
                {dashboards.map(d => (
                  <button 
                    key={d.id} 
                    onClick={() => {
                      setSelectedDashboard(d.id);
                      setViewMode("dashboard");
                    }}
                    className={`w-full text-left px-3 py-2.5 rounded-md text-sm flex items-center gap-2 transition-colors overflow-hidden ${
                      selectedDashboard === d.id && viewMode === "dashboard" ? 'bg-white/20 text-white font-medium' : 'hover:bg-white/10 text-white/80'
                    }`}
                    title={d.name}
                  >
                    <LayoutDashboard size={14} className={`shrink-0 ${selectedDashboard === d.id && viewMode === "dashboard" ? 'text-[#4fbbbd]' : 'opacity-70'}`}/>
                    <span className="truncate flex-1 min-w-0">{d.name}</span>
                  </button>
                ))}
                {dashboards.length === 0 && (
                  <div className="p-4 text-xs text-white/50 text-center">No dashboards pinned yet.</div>
                )}
              </div>
            </ScrollArea>
          </TabsContent>
        </Tabs>

        <div className="p-4 border-t border-white/10 flex items-center justify-between bg-black/10 shrink-0">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-full bg-[#0996d4] flex items-center justify-center font-bold text-sm shadow-sm">
              {username?.substring(0,2).toUpperCase()}
            </div>
            <span className="text-sm font-medium text-white truncate w-24" title={username || ""}>{username}</span>
          </div>
          <Button variant="ghost" size="icon" onClick={handleLogout} className="text-white/60 hover:text-white hover:bg-white/10">
            <LogOut size={16} />
          </Button>
        </div>
      </ResizablePanel>

      <ResizableHandle className="w-1.5 bg-slate-100 dark:bg-slate-900 cursor-col-resize flex flex-col justify-center items-center group transition-colors hover:bg-slate-200">
        <div className="h-8 w-1 rounded-full bg-slate-300 group-hover:bg-[#2053a4] transition-colors" />
      </ResizableHandle>
        
      {/* MAIN CONTENT AREA */}
      <ResizablePanel defaultSize={80}>
        {viewMode === "chat" ? (
          <div className="h-full flex flex-col bg-white dark:bg-slate-950">
            <div className="p-4 border-b flex items-center justify-between bg-slate-50 dark:bg-slate-900 shrink-0">
              <div className="flex items-center w-full">
                {activeSessionId && editingSessionId === activeSessionId ? (
                  <div className="flex items-center gap-2 w-full max-w-md">
                    <Input 
                      value={editingSessionTitle} 
                      onChange={(e) => setEditingSessionTitle(e.target.value)} 
                      className="h-8 text-sm flex-1 font-medium text-[#1d3761]"
                      autoFocus
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') handleRenameSession(activeSessionId);
                        if (e.key === 'Escape') setEditingSessionId(null);
                      }}
                    />
                    <Button size="icon" variant="ghost" className="h-8 w-8 text-green-600 hover:bg-green-50 shrink-0" onClick={() => handleRenameSession(activeSessionId)}>
                      <Check size={14} />
                    </Button>
                    <Button size="icon" variant="ghost" className="h-8 w-8 text-red-600 hover:bg-red-50 shrink-0" onClick={() => setEditingSessionId(null)}>
                      <X size={14} />
                    </Button>
                  </div>
                ) : (
                  <div className="flex items-center group gap-2">
                    <h1 className="font-semibold text-sm text-[#1d3761] dark:text-slate-200">
                      {activeSessionId ? sessions.find(s => s.id === activeSessionId)?.title || "ZATCA Remedy AI" : "ZATCA Remedy AI"}
                    </h1>
                    {activeSessionId && (
                      <Button 
                        variant="ghost" 
                        size="icon" 
                        className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity shrink-0 text-[#2053a4] hover:bg-blue-50"
                        onClick={() => {
                          setEditingSessionId(activeSessionId);
                          const currentTitle = sessions.find(s => s.id === activeSessionId)?.title || "";
                          setEditingSessionTitle(currentTitle);
                        }}
                        title="Rename Chat Session"
                      >
                        <Pencil size={12} />
                      </Button>
                    )}
                  </div>
                )}
              </div>
            </div>

            <ScrollArea className="flex-1 p-4 bg-slate-50/50 dark:bg-transparent min-h-0">
              <div className="flex flex-col gap-4 pb-4">
                {messages.length === 0 && <AnimatedChatPlaceholder kpis={kpis} suggestions={suggestions} onSuggestionClick={handleSuggestionClick} />}
                
                {messages.map((msg, idx) => (
                  <div key={idx}>
                  <div className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 shadow-sm mt-1 ${msg.role === 'user' ? 'bg-[#1d3761] text-white' : 'bg-blue-50 text-[#2053a4]'}`}>
                      {msg.role === 'user' ? <MessageSquare size={14} /> : <BarChart2 size={14} />}
                    </div>
                    <div className={`rounded-xl text-sm shadow-sm leading-relaxed ${
                      msg.role === 'user' 
                        ? 'max-w-[85%] p-3.5 bg-[#1d3761] text-white rounded-tr-sm' 
                        : 'w-full max-w-[95%] bg-transparent text-slate-800 dark:text-slate-200'
                    }`}>
                      {msg.role === 'user' ? (
                        msg.content
                      ) : (
                        <div className="flex flex-col gap-3 w-full">
                          {msg.charts && msg.charts.length > 0 ? (
                            <Tabs defaultValue="answer" className="w-full border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden bg-white dark:bg-slate-950 shadow-sm">
                              <div className="bg-slate-50 dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 px-3 py-2 flex justify-between items-center">
                                <TabsList className="h-8 bg-transparent p-0 space-x-1">
                                  <TabsTrigger value="answer" className="text-xs h-7 px-4 data-[state=active]:bg-white data-[state=active]:text-[#2053a4] data-[state=active]:shadow-sm rounded-md transition-all">Answer</TabsTrigger>
                                  <TabsTrigger value="chart" className="text-xs h-7 px-4 data-[state=active]:bg-white data-[state=active]:text-[#2053a4] data-[state=active]:shadow-sm rounded-md transition-all">Chart</TabsTrigger>
                                  <TabsTrigger value="sql" className="text-xs h-7 px-4 data-[state=active]:bg-white data-[state=active]:text-[#2053a4] data-[state=active]:shadow-sm rounded-md transition-all font-mono">SQL</TabsTrigger>
                                </TabsList>
                              </div>
                              
                              <TabsContent value="answer" className="p-5 m-0 text-slate-700 dark:text-slate-300 text-sm">
                                <div className="mb-4 whitespace-pre-wrap">{msg.content}</div>
                                {msg.charts.filter(c => c.type === 'table').length > 0 && (
                                  <div className="mt-4 space-y-4">
                                    {msg.charts.filter(c => c.type === 'table').map((c, i) => (
                                       <div key={i} className="border border-slate-100 rounded-lg overflow-hidden">
                                         <div className="bg-slate-50 px-3 py-2 border-b border-slate-100 flex items-center justify-between">
                                           <div className="text-xs font-semibold text-[#1d3761] uppercase tracking-wider">{c.title}</div>
                                           <Button variant="ghost" size="icon" className="h-6 w-6 text-[#2053a4] hover:bg-blue-100 shrink-0" onClick={() => { setChartToPin(c); setPinDialogOpen(true); }} title="Pin to Dashboard">
                                             <Pin size={12} />
                                           </Button>
                                         </div>
                                         <div className="bg-white">{renderChart(c)}</div>
                                       </div>
                                    ))}
                                  </div>
                                )}
                              </TabsContent>
                              
                              <TabsContent value="chart" className="p-5 m-0 bg-slate-50/50 dark:bg-slate-900/50">
                                <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                                  {msg.charts.filter(c => c.type !== 'table').map((c, i) => (
                                    <Card key={i} className="shadow-sm border-slate-200 bg-white">
                                      <CardHeader className="pb-2 pt-4 px-4 flex flex-row items-center justify-between space-y-0">
                                        <CardTitle className="text-sm font-semibold text-[#1d3761]">{c.title}</CardTitle>
                                        <Button variant="ghost" size="icon" className="h-7 w-7 text-[#2053a4] hover:bg-blue-50" onClick={() => { setChartToPin(c); setPinDialogOpen(true); }} title="Pin to Dashboard">
                                          <Pin size={14} />
                                        </Button>
                                      </CardHeader>
                                      <CardContent className="px-4 pb-4 pt-2">
                                        {renderChart(c)}
                                      </CardContent>
                                    </Card>
                                  ))}
                                  {msg.charts.filter(c => c.type !== 'table').length === 0 && (
                                    <div className="text-center text-slate-500 text-xs py-8 col-span-full">No visual charts generated for this response. See Answer tab for table data.</div>
                                  )}
                                </div>
                              </TabsContent>
                              
                              <TabsContent value="sql" className="p-0 m-0">
                                <div className="bg-slate-900 text-green-400 p-5 text-xs font-mono overflow-x-auto leading-relaxed">
                                  {msg.charts.map((c, i) => (
                                    <div key={i} className="mb-6 last:mb-0">
                                      <span className="text-slate-500 block mb-2 select-none">-- {c.title}</span>
                                      <span className="text-blue-300">{c.sql_query}</span>
                                    </div>
                                  ))}
                                </div>
                              </TabsContent>
                            </Tabs>
                          ) : (
                            <div className="p-4 bg-white border border-slate-100 rounded-xl rounded-tl-sm text-sm text-slate-800 dark:bg-slate-900 dark:border-slate-800 dark:text-slate-200">
                              {msg.content}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                  {/* Follow-up question chips — show only on the last assistant message */}
                  {msg.role === 'assistant' && msg.follow_ups && msg.follow_ups.length > 0 && idx === messages.length - 1 && !loading && (
                    <div className="flex flex-wrap gap-2 mt-2 ml-11">
                      {msg.follow_ups.map((q, fi) => (
                        <button
                          key={fi}
                          onClick={() => handleFollowUpClick(q)}
                          className="text-xs px-3 py-1.5 rounded-full border border-[#2053a4]/30 bg-blue-50 dark:bg-slate-800 text-[#2053a4] dark:text-blue-300 hover:bg-[#2053a4] hover:text-white transition-all shadow-sm"
                        >
                          {q}
                        </button>
                      ))}
                    </div>
                  )}
                  </div>
                ))}

                {loading && (
                  <div className="flex gap-3">
                    <div className="w-8 h-8 rounded-full bg-blue-50 text-[#2053a4] flex items-center justify-center shrink-0 shadow-sm mt-1">
                      <Loader2 size={14} className="animate-spin" />
                    </div>
                    <div className="p-3.5 bg-white border border-slate-100 rounded-xl rounded-tl-sm text-sm text-slate-500 shadow-sm flex items-center gap-2">
                      Querying Remedy database...
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>

            <div className="p-4 md:p-6 bg-gradient-to-t from-white via-white to-transparent dark:from-slate-950 dark:via-slate-950 pt-8 shrink-0 relative z-10">
              <div className="max-w-4xl mx-auto relative rounded-2xl shadow-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 focus-within:ring-2 focus-within:ring-[#2053a4]/20 focus-within:border-[#2053a4] transition-all">
                <textarea 
                  value={input} 
                  onChange={e => {
                    setInput(e.target.value);
                    // Simple auto-resize logic
                    e.target.style.height = 'auto';
                    e.target.style.height = Math.min(e.target.scrollHeight, 200) + 'px';
                  }}
                  onKeyDown={e => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSend();
                    }
                  }}
                  placeholder="Ask an analytical question..." 
                  className="w-full min-h-[60px] max-h-[200px] resize-none bg-transparent py-4 pl-5 pr-14 text-[15px] placeholder:text-slate-400 focus:outline-none dark:text-slate-200"
                  disabled={loading}
                  rows={1}
                />
                <Button 
                  onClick={(e) => { e.preventDefault(); handleSend(); }}
                  size="icon" 
                  disabled={!input.trim() || loading}
                  className="absolute right-2.5 bottom-2.5 w-10 h-10 rounded-xl bg-[#2053a4] hover:bg-[#1d3761] text-white shadow-sm transition-all disabled:opacity-50 disabled:bg-slate-200 disabled:text-slate-400 dark:disabled:bg-slate-800"
                >
                  <Send size={16} className={input.trim() ? "translate-x-0.5 -translate-y-0.5" : ""} />
                </Button>
              </div>
              <p className="text-center text-xs text-slate-400 mt-3 font-medium">ZATCA Remedy AI can make mistakes. Check important info.</p>
            </div>
          </div>
        ) : (
          <div className="h-full flex flex-col bg-slate-50/50 dark:bg-slate-950 p-6 overflow-hidden">
            <div className="flex flex-col h-full">
              <div className="flex flex-wrap justify-between items-center gap-4 mb-6 shrink-0">
                {selectedDashboard && editingDashboardId === selectedDashboard ? (
                  <div className="flex items-center gap-2 w-full max-w-sm">
                    <LayoutDashboard size={24} className="text-[#2053a4] shrink-0"/>
                    <Input 
                      value={editingDashboardName} 
                      onChange={(e) => setEditingDashboardName(e.target.value)} 
                      className="h-9 text-lg flex-1 font-semibold text-[#2053a4]"
                      autoFocus
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') handleRenameDashboard(selectedDashboard);
                        if (e.key === 'Escape') setEditingDashboardId(null);
                      }}
                    />
                    <Button size="icon" variant="ghost" className="h-9 w-9 text-green-600 hover:bg-green-50 shrink-0" onClick={() => handleRenameDashboard(selectedDashboard)}>
                      <Check size={16} />
                    </Button>
                    <Button size="icon" variant="ghost" className="h-9 w-9 text-red-600 hover:bg-red-50 shrink-0" onClick={() => setEditingDashboardId(null)}>
                      <X size={16} />
                    </Button>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 text-[#2053a4] font-semibold text-xl group">
                    <LayoutDashboard size={24}/> 
                    <span className="truncate">{dashboards.find(d => d.id === selectedDashboard)?.name || "My Dashboard"}</span>
                    {selectedDashboard && (
                      <Button 
                        variant="ghost" 
                        size="icon" 
                        className="h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity shrink-0 text-[#2053a4] hover:bg-blue-50"
                        onClick={() => {
                          setEditingDashboardId(selectedDashboard);
                          const currentName = dashboards.find(d => d.id === selectedDashboard)?.name || "";
                          setEditingDashboardName(currentName);
                        }}
                        title="Rename Dashboard"
                      >
                        <Pencil size={14} />
                      </Button>
                    )}
                  </div>
                )}
                
                <div className="flex flex-wrap items-center gap-3">
                  <Button variant="outline" className="bg-white shadow-sm h-10 px-3 lg:px-4 font-medium" onClick={() => selectedDashboard && refreshDashboard(selectedDashboard)} disabled={!selectedDashboard || refreshing}>
                    <RefreshCcw size={16} className={`mr-1 lg:mr-2 ${refreshing ? 'animate-spin' : ''}`} /> <span className="hidden lg:inline">Refresh</span>
                  </Button>
                  <Button variant="secondary" className="shadow-sm bg-[#e8f5e9] hover:bg-[#dcf0dd] border-[#a5d6a7] border text-[#2e7d32] h-10 px-3 lg:px-4 font-medium transition-colors" onClick={handleSimulate} disabled={refreshing} title="Simulate real Remedy activity to see live chart updates">
                    <Wand2 size={16} className="mr-1 lg:mr-2" /> <span className="hidden lg:inline">Simulate Activity</span>
                  </Button>
                  <Button variant="outline" className="shadow-sm border-[#2053a4] text-[#2053a4] hover:bg-blue-50 h-10 px-3 lg:px-4 font-medium transition-colors" onClick={handleExportPDF} disabled={exportingPDF || !selectedDashboard || dashboardWidgets.length === 0} title="Export dashboard to PDF">
                    {exportingPDF ? <Loader2 size={16} className="mr-1 lg:mr-2 animate-spin" /> : <FileDown size={16} className="mr-1 lg:mr-2" />} 
                    <span className="hidden lg:inline">{exportingPDF ? 'Exporting...' : 'Export PDF'}</span>
                  </Button>
                </div>
              </div>

              {/* DASHBOARDS CONTENT */}
              <ScrollArea className="flex-1 -mx-6 px-6">
                {!selectedDashboard ? (
                  <AnimatedDashboardPlaceholder />
                ) : (
                  <div className="pb-20 pt-2">
                    <div ref={dashboardRef} className="grid grid-cols-1 xl:grid-cols-2 gap-6 bg-slate-50/50 dark:bg-slate-950">
                      {dashboardWidgets.map((widget, idx) => (
                        <Card key={idx} className={`shadow-sm border-slate-200 bg-white overflow-hidden ${widget.type === 'table' ? 'xl:col-span-2' : ''}`}>
                          <CardHeader className="pb-3 border-b border-slate-50 bg-slate-50/50 flex flex-row items-center justify-between min-h-[64px]">
                            {editingWidgetId === widget.id ? (
                              <div className="flex items-center gap-2 w-full">
                                <Input 
                                  value={editingWidgetTitle} 
                                  onChange={(e) => setEditingWidgetTitle(e.target.value)} 
                                  className="h-8 text-sm flex-1 font-medium text-[#1d3761]"
                                  autoFocus
                                  onKeyDown={(e) => {
                                    if (e.key === 'Enter') handleRenameWidget(widget.id!);
                                    if (e.key === 'Escape') setEditingWidgetId(null);
                                  }}
                                />
                                <Button size="icon" variant="ghost" className="h-8 w-8 text-green-600 hover:bg-green-50 shrink-0" onClick={() => handleRenameWidget(widget.id!)}>
                                  <Check size={14} />
                                </Button>
                                <Button size="icon" variant="ghost" className="h-8 w-8 text-red-600 hover:bg-red-50 shrink-0" onClick={() => setEditingWidgetId(null)}>
                                  <X size={14} />
                                </Button>
                              </div>
                            ) : (
                              <>
                                <CardTitle className="text-lg font-semibold text-[#1d3761] flex items-center group w-full">
                                  <span className="truncate flex-1" title={widget.title}>{widget.title}</span>
                                  <Button 
                                    variant="ghost" 
                                    size="icon" 
                                    className="h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity ml-2 shrink-0 text-[#2053a4] hover:bg-blue-50"
                                    onClick={() => {
                                      if (widget.id) {
                                        setEditingWidgetId(widget.id);
                                        setEditingWidgetTitle(widget.title);
                                      }
                                    }}
                                    title="Rename Widget"
                                  >
                                    <Pencil size={13} />
                                  </Button>
                                </CardTitle>
                              </>
                            )}
                          </CardHeader>
                          <CardContent className="pt-4">
                            {renderChart(widget)}
                          </CardContent>
                        </Card>
                      ))}
                      {dashboardWidgets.length === 0 && !refreshing && (
                        <div className="col-span-full p-12 text-center border-2 border-dashed border-slate-200 rounded-xl bg-white/50">
                          <p className="text-slate-500 font-medium">This dashboard has no widgets yet.</p>
                          <p className="text-sm text-slate-400 mt-1">Go to the Chat to pin some charts here.</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </ScrollArea>
            </div>
          </div>
        )}
      </ResizablePanel>
    </ResizablePanelGroup>
  </div>
  );
}