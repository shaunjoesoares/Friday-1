import React, { useState, useEffect, useRef } from 'react';
import { Send, Mic, Paperclip, Calendar, HardDrive, Mail, Clock, Shield, Activity, FileText } from 'lucide-react';

function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I am Friday. How can I help you with your Google Workspace today?' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [dashboardData, setDashboardData] = useState({ recent_files: [], upcoming_events: [] });
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Fetch dashboard data on load
  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const response = await fetch('http://localhost:8000/dashboard');
        if (response.ok) {
          const data = await response.json();
          setDashboardData(data);
        }
      } catch (error) {
        console.error("Failed to fetch dashboard data:", error);
      }
    };
    fetchDashboard();
    // Refresh every minute
    const interval = setInterval(fetchDashboard, 60000);
    return () => clearInterval(interval);
  }, []);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input }),
      });

      const data = await response.json();
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.response,
        type: data.type,
        data: data.data
      }]);
    } catch (error) {
      setMessages(prev => [...prev, { role: 'assistant', content: "Sorry, I encountered an error connecting to the server." }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-midnight-900 via-midnight-800 to-midnight-900 text-white font-sans overflow-hidden">

      {/* Sidebar */}
      <div className="w-20 bg-black/30 backdrop-blur-xl border-r border-white/10 flex flex-col items-center py-8 space-y-8 z-10">
        <div className="p-3 bg-neon-cyan/20 rounded-xl border border-neon-cyan/50 shadow-[0_0_15px_rgba(0,255,255,0.3)]">
          <Activity className="w-6 h-6 text-neon-cyan" />
        </div>
        <nav className="flex flex-col space-y-6 w-full items-center">
          <SidebarIcon icon={<Mail />} active />
          <SidebarIcon icon={<Calendar />} />
          <SidebarIcon icon={<HardDrive />} />
          <SidebarIcon icon={<Shield />} />
        </nav>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col relative">
        {/* Header */}
        <header className="h-16 border-b border-white/10 bg-black/20 backdrop-blur-md flex items-center justify-between px-8">
          <div className="flex items-center space-x-4">
            <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-neon-cyan to-neon-pink">
              FRIDAY <span className="text-xs font-normal text-white/50 tracking-widest">V1.0</span>
            </h1>
          </div>
          <div className="flex items-center space-x-4 text-sm text-neon-blue/80">
            <div className="flex items-center space-x-2 px-3 py-1 rounded-full bg-neon-blue/10 border border-neon-blue/30">
              <span className="w-2 h-2 rounded-full bg-neon-blue animate-pulse"></span>
              <span>SYSTEM ONLINE</span>
            </div>
          </div>
        </header>

        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto p-8 space-y-6 scrollbar-hide">
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-2xl p-4 rounded-2xl backdrop-blur-md border ${msg.role === 'user'
                  ? 'bg-neon-purple/10 border-neon-purple/30 text-white rounded-tr-none'
                  : 'bg-white/5 border-white/10 text-gray-200 rounded-tl-none'
                }`}>
                <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>

                {/* Rich Content Rendering */}
                {msg.type === 'calendar' && (
                  <div className="mt-4 p-4 bg-black/40 rounded-xl border-l-4 border-neon-pink">
                    <div className="flex items-center space-x-3 mb-2">
                      <Calendar className="w-5 h-5 text-neon-pink" />
                      <span className="font-semibold text-neon-pink">Calendar Event</span>
                    </div>
                    <div className="text-sm opacity-80">
                      {msg.content.split('\n').slice(1).map((line, i) => (
                        <div key={i}>{line}</div>
                      ))}
                    </div>
                  </div>
                )}

                {msg.type === 'drive' && (
                  <div className="mt-4 p-4 bg-black/40 rounded-xl border-l-4 border-neon-cyan">
                    <div className="flex items-center space-x-3 mb-2">
                      <HardDrive className="w-5 h-5 text-neon-cyan" />
                      <span className="font-semibold text-neon-cyan">Drive File</span>
                    </div>
                    <div className="text-sm opacity-80">
                      {msg.content.split('\n').slice(1).map((line, i) => (
                        <div key={i}>{line}</div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white/5 border border-white/10 p-4 rounded-2xl rounded-tl-none flex items-center space-x-2">
                <div className="w-2 h-2 bg-neon-cyan rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-2 h-2 bg-neon-pink rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-2 h-2 bg-neon-purple rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-6 bg-black/20 backdrop-blur-xl border-t border-white/10">
          <div className="max-w-4xl mx-auto relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
              placeholder="Command Friday..."
              className="w-full bg-black/40 text-white placeholder-white/30 rounded-xl py-4 pl-6 pr-32 focus:outline-none focus:ring-2 focus:ring-neon-cyan/50 border border-white/10 transition-all"
            />
            <div className="absolute right-2 top-2 flex items-center space-x-2">
              <button className="p-2 hover:bg-white/10 rounded-lg transition-colors text-neon-cyan">
                <Mic className="w-5 h-5" />
              </button>
              <button
                onClick={sendMessage}
                className="p-2 bg-neon-cyan/20 hover:bg-neon-cyan/30 text-neon-cyan rounded-lg transition-all border border-neon-cyan/30 shadow-[0_0_10px_rgba(0,255,255,0.2)]"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Right Status Panel */}
      <div className="w-80 bg-black/30 backdrop-blur-xl border-l border-white/10 p-6 hidden xl:block overflow-y-auto">
        <h2 className="text-xs font-bold text-white/40 tracking-widest mb-6 uppercase">System Status</h2>

        <div className="space-y-6">
          {/* Upcoming Events */}
          <div className="p-4 rounded-2xl bg-white/5 border border-white/10 hover:border-neon-pink/30 transition-all group">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-neon-pink/10 rounded-lg group-hover:bg-neon-pink/20 transition-colors">
                  <Calendar className="w-5 h-5 text-neon-pink" />
                </div>
                <span className="font-medium text-gray-200">Upcoming</span>
              </div>
              <span className="text-xs text-neon-pink bg-neon-pink/10 px-2 py-1 rounded border border-neon-pink/20">
                {dashboardData.upcoming_events.length}
              </span>
            </div>
            <div className="space-y-3">
              {dashboardData.upcoming_events.length === 0 ? (
                <div className="text-sm text-white/30 italic">No upcoming events</div>
              ) : (
                dashboardData.upcoming_events.map((event, i) => (
                  <div key={i} className="text-sm border-l-2 border-white/10 pl-3 py-1">
                    <div className="text-white/90 font-medium truncate">{event.summary}</div>
                    <div className="text-white/50 text-xs">
                      {new Date(event.start.dateTime || event.start.date).toLocaleString()}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Recent Files */}
          <div className="p-4 rounded-2xl bg-white/5 border border-white/10 hover:border-neon-cyan/30 transition-all group">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-neon-cyan/10 rounded-lg group-hover:bg-neon-cyan/20 transition-colors">
                  <HardDrive className="w-5 h-5 text-neon-cyan" />
                </div>
                <span className="font-medium text-gray-200">Drive</span>
              </div>
              <span className="text-xs text-neon-cyan bg-neon-cyan/10 px-2 py-1 rounded border border-neon-cyan/20">
                {dashboardData.recent_files.length}
              </span>
            </div>
            <div className="space-y-3">
              {dashboardData.recent_files.length === 0 ? (
                <div className="text-sm text-white/30 italic">No recent files</div>
              ) : (
                dashboardData.recent_files.map((file, i) => (
                  <a key={i} href={file.webViewLink} target="_blank" rel="noreferrer" className="block group/file">
                    <div className="flex items-center justify-between text-sm p-2 rounded hover:bg-white/5 transition-colors">
                      <div className="flex items-center space-x-2 truncate">
                        <FileText className="w-3 h-3 text-white/40 group-hover/file:text-neon-cyan transition-colors" />
                        <span className="text-white/70 group-hover/file:text-white truncate max-w-[120px]">{file.name}</span>
                      </div>
                    </div>
                  </a>
                ))
              )}
            </div>
          </div>

          {/* System Metrics (Mock) */}
          <div className="p-4 rounded-2xl bg-white/5 border border-white/10">
            <div className="flex items-center space-x-3 mb-4">
              <Activity className="w-5 h-5 text-neon-purple" />
              <span className="font-medium text-gray-200">Metrics</span>
            </div>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-white/50">CPU</span>
                  <span className="text-neon-purple">12%</span>
                </div>
                <div className="h-1 bg-white/10 rounded-full overflow-hidden">
                  <div className="h-full w-[12%] bg-neon-purple shadow-[0_0_10px_#bc13fe]"></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-white/50">Memory</span>
                  <span className="text-neon-blue">45%</span>
                </div>
                <div className="h-1 bg-white/10 rounded-full overflow-hidden">
                  <div className="h-full w-[45%] bg-neon-blue shadow-[0_0_10px_#00ccff]"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

const SidebarIcon = ({ icon, active }) => (
  <div className={`p-3 rounded-xl transition-all cursor-pointer ${active
      ? 'bg-neon-pink/20 text-neon-pink shadow-[0_0_15px_rgba(255,0,255,0.3)]'
      : 'text-white/40 hover:text-white hover:bg-white/10'
    }`}>
    {React.cloneElement(icon, { className: "w-6 h-6" })}
  </div>
);

export default App;
