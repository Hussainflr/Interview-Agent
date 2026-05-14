"use client";

import { useEffect, useRef, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export default function Home() {
  const wsRef = useRef(null);
  const audioContextRef = useRef(null);
  const processorRef = useRef(null);

  const [config, setConfig] = useState({ roles: [], difficulties: [], types: [] });
  const [provider, setProvider] = useState("ollama");
  const [model, setModel] = useState("qwen3:4b");
  const [health, setHealth] = useState(null);
  const [status, setStatus] = useState("Ready");
  const [session, setSession] = useState(null);
  const [profile, setProfile] = useState({
    role: "Software Engineer",
    difficulty: "intermediate",
    interview_type: "technical",
    cv_text: "",
    job_description: "",
  });
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const [voiceActive, setVoiceActive] = useState(false);

  useEffect(() => {
    loadConfig();
  }, []);

  async function loadConfig() {
    try {
      const res = await fetch(`${API}/api/config`);
      const data = await res.json();
      setConfig(data);
      setProvider(data.provider || "ollama");
      setModel(data.model || "qwen3:4b");
      setProfile((prev) => ({
        ...prev,
        role: data.roles?.[0] || prev.role,
        difficulty: data.difficulties?.[1] || prev.difficulty,
        interview_type: data.types?.[0] || prev.interview_type,
      }));
    } catch {
      setStatus("Backend is not reachable. Start FastAPI on port 8000.");
    }
  }

  async function saveProvider() {
    setBusy(true);
    try {
      await fetch(`${API}/api/provider`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider, model }),
      });
      await checkHealth();
    } finally {
      setBusy(false);
    }
  }

  async function checkHealth() {
    setBusy(true);
    try {
      const res = await fetch(`${API}/api/health/model`);
      const data = await res.json();
      setHealth(data);
      setStatus(data.ok ? data.message : data.message);
    } catch {
      setStatus("Could not check the local model server.");
    } finally {
      setBusy(false);
    }
  }

  async function startInterview() {
    setBusy(true);
    setStatus("Starting interview...");
    try {
      await saveProvider();
      const res = await fetch(`${API}/api/session/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(profile),
      });
      const data = await res.json();
      setSession(data);
      setStatus("Interview started. Answer the first question when ready.");
    } catch (err) {
      setStatus(`Could not start interview: ${err.message}`);
    } finally {
      setBusy(false);
    }
  }

  async function sendAnswer() {
    if (!session || !answer.trim()) return;
    setBusy(true);
    setStatus("Scoring your answer...");
    try {
      const res = await fetch(`${API}/api/session/${session.id}/message`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: answer }),
      });
      const data = await res.json();
      setSession(data.session);
      setAnswer("");
      setStatus(data.route?.intent === "interview_answer" ? "Feedback ready." : data.route?.response || "Ready");
    } catch (err) {
      setStatus(`Could not send answer: ${err.message}`);
    } finally {
      setBusy(false);
    }
  }

  async function uploadText(kind, file) {
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${API}/api/upload/text`, { method: "POST", body: formData });
    const data = await res.json();
    setProfile((prev) => ({ ...prev, [kind]: data.text }));
  }

  async function startVoice() {
    try {
      setStatus("Connecting voice...");
      const ws = new WebSocket("ws://127.0.0.1:8000/ws");
      ws.binaryType = "arraybuffer";
      wsRef.current = ws;
      ws.onopen = () => {
        setVoiceActive(true);
        setStatus("Voice recording is active.");
      };
      ws.onmessage = async (event) => {
        if (typeof event.data === "string") {
          const msg = JSON.parse(event.data);
          if (msg.session_id) {
            const res = await fetch(`${API}/api/session/${msg.session_id}`);
            setSession(await res.json());
          }
        }
      };

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
      });
      const audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
      audioContextRef.current = audioContext;
      const source = audioContext.createMediaStreamSource(stream);
      const processor = audioContext.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;
      source.connect(processor);
      processor.connect(audioContext.destination);
      processor.onaudioprocess = (e) => {
        const input = e.inputBuffer.getChannelData(0);
        const int16 = new Int16Array(input.length);
        for (let i = 0; i < input.length; i++) int16[i] = Math.max(-1, Math.min(1, input[i])) * 0x7fff;
        if (ws.readyState === 1) ws.send(int16.buffer);
      };
    } catch (err) {
      setStatus(`Voice unavailable: ${err.message}. Use text input instead.`);
      setVoiceActive(false);
    }
  }

  function stopVoice() {
    processorRef.current?.disconnect();
    audioContextRef.current?.close();
    wsRef.current?.close();
    setVoiceActive(false);
    setStatus("Voice stopped. Text input is available.");
  }

  const messages = session?.messages || [];
  const latestEvaluation = [...messages].reverse().find((m) => m.kind === "feedback")?.metadata;

  return (
    <main className="shell">
      <section className="topbar">
        <div>
          <h1>Local Interview Agent</h1>
          <p>Practice with Ollama or LM Studio. Your sessions stay on this machine.</p>
        </div>
        <div className={`health ${health?.ok ? "ok" : "warn"}`}>{health?.ok ? "Model ready" : "Local model check needed"}</div>
      </section>

      <section className="grid">
        <aside className="panel controls">
          <h2>Setup</h2>
          <label>
            Provider
            <select value={provider} onChange={(e) => setProvider(e.target.value)}>
              <option value="ollama">Ollama</option>
              <option value="lmstudio">LM Studio</option>
            </select>
          </label>
          <label>
            Model
            <input value={model} onChange={(e) => setModel(e.target.value)} placeholder="qwen3:4b" />
          </label>
          <button onClick={checkHealth} disabled={busy}>Check model</button>

          <h2>Interview</h2>
          <label>
            Role
            <select value={profile.role} onChange={(e) => setProfile({ ...profile, role: e.target.value })}>
              {config.roles.map((role) => <option key={role}>{role}</option>)}
            </select>
          </label>
          <label>
            Difficulty
            <select value={profile.difficulty} onChange={(e) => setProfile({ ...profile, difficulty: e.target.value })}>
              {config.difficulties.map((item) => <option key={item}>{item}</option>)}
            </select>
          </label>
          <label>
            Type
            <select value={profile.interview_type} onChange={(e) => setProfile({ ...profile, interview_type: e.target.value })}>
              {config.types.map((item) => <option key={item}>{item}</option>)}
            </select>
          </label>

          <label>
            CV or resume
            <input type="file" accept=".txt,.md,.csv" onChange={(e) => uploadText("cv_text", e.target.files?.[0])} />
          </label>
          <textarea
            value={profile.cv_text}
            onChange={(e) => setProfile({ ...profile, cv_text: e.target.value })}
            placeholder="Paste CV highlights here"
          />
          <label>
            Job description
            <textarea
              value={profile.job_description}
              onChange={(e) => setProfile({ ...profile, job_description: e.target.value })}
              placeholder="Paste the job description here"
            />
          </label>
          <button className="primary" onClick={startInterview} disabled={busy}>Start new interview</button>
        </aside>

        <section className="workspace">
          <div className="dashboard">
            <Metric label="Current score" value={session?.latest_score ?? "-"} />
            <Metric label="Average" value={session?.average_score ?? "-"} />
            <Metric label="Turns" value={messages.filter((m) => m.kind === "answer").length} />
            <div className="areas">
              <span>Improvement areas</span>
              <strong>{session?.improvement_areas?.slice(0, 3).join(", ") || "None yet"}</strong>
            </div>
          </div>

          <div className="status">{status}</div>

          <div className="conversation">
            {!session && <div className="empty">Pick a role and start a new interview. A greeting like hello will not trigger scoring.</div>}
            {messages.map((msg, index) => (
              <article className={`message ${msg.role}`} key={`${msg.kind}-${index}`}>
                <small>{msg.role === "assistant" ? `AI ${msg.kind}` : `You ${msg.kind}`}</small>
                <p>{msg.content}</p>
              </article>
            ))}
          </div>

          <div className="composer">
            <textarea
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              placeholder={session ? "Type your answer here" : "Start an interview first"}
              disabled={!session || busy}
            />
            <div className="actions">
              <button className="primary" onClick={sendAnswer} disabled={!session || busy || !answer.trim()}>Send answer</button>
              <button onClick={voiceActive ? stopVoice : startVoice}>{voiceActive ? "Stop voice" : "Use microphone"}</button>
              {session && (
                <>
                  <a href={`${API}/api/session/${session.id}/export?format=markdown`}>Markdown report</a>
                  <a href={`${API}/api/session/${session.id}/export?format=pdf`}>PDF report</a>
                </>
              )}
            </div>
          </div>

          {latestEvaluation && (
            <div className="rubric">
              {Object.entries(latestEvaluation.rubric || {}).map(([key, value]) => (
                <Metric key={key} label={key.replace("_", " ")} value={`${value}/20`} />
              ))}
            </div>
          )}
        </section>
      </section>

      <style jsx>{`
        .shell { min-height: 100vh; background: #f6f7f9; color: #1f2933; padding: 24px; font-family: Arial, sans-serif; }
        .topbar { display: flex; justify-content: space-between; align-items: end; gap: 16px; margin-bottom: 18px; }
        h1 { margin: 0 0 6px; font-size: 32px; letter-spacing: 0; }
        h2 { margin: 20px 0 12px; font-size: 16px; }
        p { margin: 0; line-height: 1.45; }
        .health { border-radius: 6px; padding: 8px 12px; font-weight: 700; background: #fff3cd; color: #5f4b00; }
        .health.ok { background: #dff3e4; color: #14532d; }
        .grid { display: grid; grid-template-columns: 320px 1fr; gap: 18px; align-items: start; }
        .panel, .workspace { background: #ffffff; border: 1px solid #dde3ea; border-radius: 8px; }
        .controls { padding: 18px; }
        label { display: grid; gap: 6px; margin-bottom: 12px; font-size: 13px; font-weight: 700; color: #44515f; }
        input, select, textarea { width: 100%; box-sizing: border-box; border: 1px solid #cbd5df; border-radius: 6px; padding: 10px; font: inherit; background: white; color: #17202a; }
        textarea { min-height: 84px; resize: vertical; }
        button, a { border: 1px solid #aeb9c5; background: #ffffff; color: #17202a; border-radius: 6px; padding: 10px 12px; font-weight: 700; cursor: pointer; text-decoration: none; display: inline-flex; align-items: center; justify-content: center; min-height: 38px; }
        button:disabled { opacity: 0.55; cursor: not-allowed; }
        .primary { background: #176b87; border-color: #176b87; color: white; width: 100%; }
        .workspace { padding: 18px; min-width: 0; }
        .dashboard, .rubric { display: grid; grid-template-columns: repeat(4, minmax(120px, 1fr)); gap: 10px; margin-bottom: 12px; }
        .metric, .areas { border: 1px solid #dde3ea; border-radius: 8px; padding: 12px; background: #fbfcfd; min-height: 58px; }
        .metric span, .areas span { display: block; color: #667789; font-size: 12px; text-transform: capitalize; }
        .metric strong, .areas strong { display: block; margin-top: 6px; font-size: 20px; }
        .areas { grid-column: span 1; }
        .areas strong { font-size: 14px; line-height: 1.35; }
        .status { background: #e8f1f2; color: #184e5d; border-radius: 6px; padding: 10px 12px; margin-bottom: 12px; }
        .conversation { height: 460px; overflow-y: auto; border: 1px solid #dde3ea; border-radius: 8px; padding: 14px; background: #fbfcfd; }
        .empty { color: #697786; text-align: center; padding: 80px 16px; }
        .message { max-width: 86%; margin-bottom: 12px; padding: 12px; border-radius: 8px; background: white; border: 1px solid #dde3ea; white-space: pre-wrap; }
        .message.user { margin-left: auto; background: #eef5ff; border-color: #bfd7ff; }
        .message small { display: block; color: #687789; font-weight: 700; margin-bottom: 6px; text-transform: capitalize; }
        .composer { display: grid; gap: 10px; margin-top: 12px; }
        .composer textarea { min-height: 110px; }
        .actions { display: flex; gap: 8px; flex-wrap: wrap; }
        .actions .primary { width: auto; }
        @media (max-width: 900px) {
          .shell { padding: 14px; }
          .topbar { align-items: start; flex-direction: column; }
          .grid { grid-template-columns: 1fr; }
          .dashboard, .rubric { grid-template-columns: repeat(2, minmax(0, 1fr)); }
          .conversation { height: 360px; }
          .message { max-width: 100%; }
        }
      `}</style>
    </main>
  );
}

function Metric({ label, value }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
