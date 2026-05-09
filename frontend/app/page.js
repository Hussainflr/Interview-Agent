"use client";

import { useRef, useState } from "react";

function Home() {
  const wsRef = useRef(null);
  const audioContextRef = useRef(null);
  const processorRef = useRef(null);

  const [status, setStatus] = useState("Idle");
  const [messages, setMessages] = useState([]);

  const addMessage = (role, text) => {
    setMessages(prev => [...prev, { role, text, timestamp: new Date() }]);
  };

  const start = async () => {
    try {
      setStatus("Connecting...");

      const ws = new WebSocket("ws://127.0.0.1:8000/ws");
      ws.binaryType = "arraybuffer";
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus("🎤 Listening...");
        addMessage("system", "Connected to interview agent");
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        setStatus("❌ Connection error");
        addMessage("system", `Error: ${error}`);
      };

      ws.onmessage = async (event) => {
        try {
          if (typeof event.data === "string") {
            const msg = JSON.parse(event.data);
            if (msg.user_text) {
              addMessage("user", msg.user_text);
            }
            console.log("AI:", msg.text);
            addMessage("ai", msg.text);
          } else {
            const audioBlob = new Blob([event.data]);
            const audioUrl = URL.createObjectURL(audioBlob);
            const audio = new Audio(audioUrl);
            audio.volume = 0.8;
            const playPromise = audio.play();
            if (playPromise !== undefined) {
              playPromise.catch(err => {
                console.warn("Audio play failed:", err);
              });
            }
          }
        } catch (err) {
          console.error("Message processing error:", err);
        }
      };

      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        }
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
        for (let i = 0; i < input.length; i++) {
          int16[i] = Math.max(-1, Math.min(1, input[i])) * 0x7FFF;
        }

        if (ws.readyState === 1) {
          ws.send(int16.buffer);
        }
      };

      setStatus("✅ Recording started");
    } catch (err) {
      console.error("Start error:", err);
      setStatus(`❌ Error: ${err.message}`);
      addMessage("system", `Error: ${err.message}`);
    }
  };

  const stop = () => {
    try {
      if (processorRef.current) {
        processorRef.current.disconnect();
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
      setStatus("🛑 Stopped");
    } catch (err) {
      console.error("Stop error:", err);
      setStatus("Stopped (with errors)");
    }
  };

  return (
    <div style={{ padding: 20, fontFamily: "Arial, sans-serif" }}>
      <h1>🎤 AI Interview Agent</h1>

      <div style={{ marginBottom: 20 }}>
        <button 
          onClick={start} 
          disabled={status !== "Idle"}
          style={{
            padding: "10px 20px",
            fontSize: "16px",
            backgroundColor: status === "Idle" ? "#28a745" : "#ccc",
            color: "white",
            border: "none",
            borderRadius: "5px",
            cursor: status === "Idle" ? "pointer" : "not-allowed"
          }}
        >
          {status === "Idle" ? "🎤 Start Interview" : "Starting..."}
        </button>
        <button 
          onClick={stop}
          disabled={status === "Idle"}
          style={{ 
            marginLeft: 10,
            padding: "10px 20px",
            fontSize: "16px",
            backgroundColor: status !== "Idle" ? "#dc3545" : "#ccc",
            color: "white",
            border: "none",
            borderRadius: "5px",
            cursor: status !== "Idle" ? "pointer" : "not-allowed"
          }}
        >
          🛑 Stop
        </button>
      </div>

      <p style={{
        fontSize: "18px",
        fontWeight: "bold",
        padding: "10px",
        borderRadius: "5px",
        backgroundColor: status.includes("❌") ? "#f8d7da" : status.includes("✅") ? "#d4edda" : "#e2e3e5",
        color: status.includes("❌") ? "#721c24" : status.includes("✅") ? "#155724" : "#383d41"
      }}>
        Status: {status}
      </p>

      <div style={{ border: "1px solid #ccc", height: 400, overflowY: "auto", padding: 10, marginTop: 20, borderRadius: "5px" }}>
        {messages.length === 0 && (
          <div style={{ textAlign: "center", color: "#999", paddingTop: "50px" }}>
            Click "Start Interview" to begin...
          </div>
        )}
        {messages.map((msg, index) => (
          <div key={index} style={{
            marginBottom: 10,
            textAlign: msg.role === "system" ? "center" : msg.role === "user" ? "right" : "left"
          }}>
            <div style={{
              display: "inline-block",
              padding: 10,
              borderRadius: 10,
              backgroundColor: 
                msg.role === "system" ? "#e7f3ff" : 
                msg.role === "user" ? "#007bff" : "#f1f1f1",
              color: 
                msg.role === "system" ? "#0066cc" :
                msg.role === "user" ? "white" : "black",
              maxWidth: "80%",
              fontSize: msg.role === "system" ? "12px" : "14px"
            }}>
              {msg.role === "system" && "ℹ️ "}
              <strong>{msg.role === "system" ? "" : msg.role === "user" ? "You: " : "AI: "}</strong> {msg.text}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default Home;