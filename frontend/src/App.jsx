import { useEffect, useRef, useState } from "react";
import { BookOpen, Bot, Send, LogOut, Plus, Trash2, Sparkles, Menu, X, GraduationCap } from "lucide-react";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";
const starters = ["Giải thích khái niệm Machine Learning đơn giản", "Tạo kế hoạch ôn thi trong 7 ngày", "Tóm tắt kiến thức Python cơ bản", "Hướng dẫn giải một bài toán từng bước"];

export default function App() {
  const [token, setToken] = useState(localStorage.getItem("sm_token") || "");
  const [user, setUser] = useState(null);
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [sidebar, setSidebar] = useState(true);
  const endRef = useRef(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, busy]);
  useEffect(() => {
    if (!token) return;
    fetch(API + "/api/auth/me", { headers: { Authorization: "Bearer " + token } })
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then(async u => { setUser(u); const h = await fetch(API + "/api/chat/history", { headers: { Authorization: "Bearer " + token } }); if (h.ok) setMessages(await h.json()); })
      .catch(() => logout());
  }, [token]);

  function logout() { localStorage.removeItem("sm_token"); setToken(""); setUser(null); setMessages([]); }
  async function auth(e) {
    e.preventDefault(); setError(""); setBusy(true);
    try {
      const r = await fetch(API + "/api/auth/" + mode, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(form) });
      const d = await r.json(); if (!r.ok) throw new Error(d.detail || "Không thể đăng nhập");
      localStorage.setItem("sm_token", d.access_token); setToken(d.access_token); setUser(d.user);
    } catch (e) { setError(e.message); } finally { setBusy(false); }
  }
  async function send(text = input) {
    const value = text.trim(); if (!value || busy) return;
    setInput(""); setError(""); setMessages(m => [...m, { role: "user", content: value }]); setBusy(true);
    try {
      const r = await fetch(API + "/api/chat", { method: "POST", headers: { "Content-Type": "application/json", Authorization: "Bearer " + token }, body: JSON.stringify({ message: value }) });
      const d = await r.json(); if (!r.ok) throw new Error(d.detail || "Có lỗi xảy ra");
      setMessages(m => [...m, { role: "assistant", content: d.reply }]);
    } catch (e) { setMessages(m => [...m, { role: "assistant", content: "Không thể kết nối: " + e.message }]); }
    finally { setBusy(false); }
  }
  async function clearChat() {
    if (!confirm("Bạn muốn xóa toàn bộ lịch sử trò chuyện?")) return;
    await fetch(API + "/api/chat/history", { method: "DELETE", headers: { Authorization: "Bearer " + token } });
    setMessages([]);
  }

  if (!token || !user) return <main className="auth-page"><div className="auth-glow glow-one"/><div className="auth-glow glow-two"/>
    <section className="auth-card"><div className="brand-mark"><GraduationCap size={27}/></div><div className="eyebrow">YOUR PERSONAL AI STUDY PARTNER</div>
      <h1>StudyMate <span>AI</span></h1><p className="muted">Học tập thông minh hơn, từng ngày.</p>
      <div className="auth-tabs"><button className={mode==="login"?"active":""} onClick={()=>{setMode("login");setError("");}}>Đăng nhập</button><button className={mode==="register"?"active":""} onClick={()=>{setMode("register");setError("");}}>Tạo tài khoản</button></div>
      <form onSubmit={auth}>{mode==="register"&&<label>Họ và tên<input required minLength="2" placeholder="Nguyễn Văn A" value={form.name} onChange={e=>setForm({...form,name:e.target.value})}/></label>}
        <label>Email<input required type="email" placeholder="ban@email.com" value={form.email} onChange={e=>setForm({...form,email:e.target.value})}/></label>
        <label>Mật khẩu<input required minLength="8" type="password" placeholder="Ít nhất 8 ký tự" value={form.password} onChange={e=>setForm({...form,password:e.target.value})}/></label>
        {error&&<div className="error">{error}</div>}<button className="primary full" disabled={busy}>{busy?"Đang xử lý...":mode==="login"?"Đăng nhập":"Tạo tài khoản"}</button></form>
      <div className="auth-foot">StudyMate AI · Không gian học tập của bạn</div>
    </section></main>;

  return <div className="app-shell">
    <aside className={"sidebar "+(sidebar?"":"closed")}><div className="side-top"><div className="brand"><div className="brand-mark small"><GraduationCap size={20}/></div><div><b>StudyMate <span>AI</span></b><small>STUDY WORKSPACE</small></div></div><button className="icon-btn mobile-only" onClick={()=>setSidebar(false)}><X/></button></div>
      <button className="new-chat" onClick={()=>setMessages([])}><Plus size={17}/> Cuộc trò chuyện mới</button>
      <div className="side-label">TRỢ LÝ HỌC TẬP</div><div className="side-feature"><Bot size={18}/><span>AI Study Assistant</span><span className="online-dot"/></div>
      <div className="side-bottom"><div className="user-chip"><div className="avatar">{user.name?.[0]?.toUpperCase()}</div><div className="user-meta"><b>{user.name}</b><small>{user.email}</small></div><button className="icon-btn" title="Đăng xuất" onClick={logout}><LogOut size={17}/></button></div></div>
    </aside>
    <main className="main-area"><header className="topbar"><button className="icon-btn" onClick={()=>setSidebar(!sidebar)}><Menu size={19}/></button><div className="crumb"><span>Workspace</span><b>/</b> Trợ lý AI</div><div className="top-status"><span className="online-dot"/> AI Assistant</div></header>
      <section className="chat-area">{messages.length===0?<div className="welcome"><div className="welcome-icon"><Sparkles size={25}/></div><div className="eyebrow">LEARN WITHOUT LIMITS</div><h2>Xin chào, {user.name?.split(" ").slice(-1)[0]}!</h2><h3>Hôm nay bạn muốn học gì?</h3><p>Tôi có thể giúp bạn giải thích kiến thức, tóm tắt tài liệu và xây dựng kế hoạch học tập.</p>
        <div className="starter-grid">{starters.map((s,i)=><button key={i} className="starter" onClick={()=>send(s)}><span>{["✦","◈","⌘","↗"][i]}</span>{s}</button>)}</div></div>:
        <div className="messages">{messages.map((m,i)=><article className={"message "+m.role} key={i}><div className="message-avatar">{m.role==="assistant"?<Bot size={18}/>:user.name?.[0]?.toUpperCase()}</div><div className="message-body"><div className="message-name">{m.role==="assistant"?"StudyMate AI":"Bạn"}</div><div className="message-content">{m.content}</div></div></article>)}{busy&&<article className="message assistant"><div className="message-avatar"><Bot size={18}/></div><div className="message-body"><div className="message-name">StudyMate AI</div><div className="typing"><i/><i/><i/></div></div></article>}<div ref={endRef}/></div>}</section>
      <div className="composer-wrap"><div className="composer"><textarea rows="1" value={input} onChange={e=>setInput(e.target.value)} onKeyDown={e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();send();}}} placeholder="Nhập câu hỏi hoặc nội dung bạn muốn tìm hiểu..."/><button className="send-btn" disabled={!input.trim()||busy} onClick={()=>send()}><Send size={18}/></button></div><div className="composer-note">StudyMate AI có thể mắc lỗi. Hãy kiểm tra lại thông tin quan trọng.</div></div>
    </main>
  </div>;
}