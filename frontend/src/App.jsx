import { useRef, useState } from "react";

function App() {
  const wsRef = useRef(null);
  const audioContextRef = useRef(null);
  const processorRef = useRef(null);

  const [status, setStatus] = useState("Idle");

  const start = async () => {
    setStatus("Connecting...");

    const ws = new WebSocket("ws://127.0.0.1:8000/ws");
    ws.binaryType = "arraybuffer";
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus("🎤 Listening...");
    };

    ws.onmessage = async (event) => {
      if (typeof event.data === "string") {
        const msg = JSON.parse(event.data);
        console.log("AI:", msg.text);
      } else {
        const audioBlob = new Blob([event.data]);
        const audio = new Audio(URL.createObjectURL(audioBlob));
        audio.play();
      }
    };

    // Mic access
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    const audioContext = new AudioContext({ sampleRate: 16000 });
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
        int16[i] = input[i] * 32767;
      }

      if (ws.readyState === 1) {
        ws.send(int16.buffer);
      }
    };
  };

  const stop = () => {
    processorRef.current?.disconnect();
    audioContextRef.current?.close();
    wsRef.current?.close();
    setStatus("Stopped");
  };

  return (
    <div style={{ padding: 20 }}>
      <h1>🎤 AI Interview Agent</h1>

      <button onClick={start}>Start</button>
      <button onClick={stop}>Stop</button>

      <p>Status: {status}</p>
    </div>
  );
}

export default App;