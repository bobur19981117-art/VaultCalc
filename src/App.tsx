import React, { useState, useEffect, useRef } from "react";
import {
  Volume2,
  Sparkles,
  Download,
  Play,
  Pause,
  RefreshCw,
  Clock,
  Trash2,
  FileText,
  Sliders,
  Type,
  Disc,
  Info,
  Check,
  AlertCircle,
  Key,
  Settings,
} from "lucide-react";
import {
  synthesizeSpeech,
  enhanceText,
  saveAudioFile,
  getApiKey,
  setApiKey,
  resetApiKey,
  isUsingCustomKey,
} from "./services/geminiService";

interface HistoryTrack {
  id: string;
  text: string;
  voiceName: string;
  style: string;
  speed: number;
  timestamp: string;
  audioBase64: string;
}

const PRESET_CHIPS = [
  {
    id: "salom",
    label: "💬 Salomlashish",
    text: "Assalomu alaykum! O'zbek ovoz sun'iy intellekt xizmatiga xush kelibsiz. Ushbu tizim eng so'nggi neyron tarmoqlar yordamida o'zbekcha matnlarni tabiiy va ravon ovozga aylantiradi.",
  },
  {
    id: "yangilik",
    label: "📰 Yangiliklar",
    text: "Xayrli kun, hurmatli tinglovchilar! Bugun poytaxtimizda eng so'nggi texnologiyalar haftaligi boshlandi. Mazkur tadbirda sun'iy intellekt va ovozli yordamchilar sohasi bo'yicha ko'plab yangi innovatsiyalar namoyish etilmoqda.",
  },
  {
    id: "sher",
    label: "✨ She'riyat",
    text: "O'zbekiston, ey ona vatan, sening tuprog'ing muqaddas, sening havong va suving hayotbaxshdir. Sening har bir go'shang, har bir qarich yering biz uchun aziz va mo'tabardir.",
  },
  {
    id: "ilm",
    label: "🔬 Ilmiy ma'ruzalar",
    text: "Inson miyasi neyronlari faoliyati va ularning matematik modellari bugungi kunda chuqur o'rganilmoqda. Neyrotarmoqlar yordamida nutq sintezini yanada takomillashtirish yangi ufqlarni ochib beradi.",
  },
];

const VOICE_CHARACTERS = [
  {
    id: "dilnoza",
    name: "Dilnoza (Ayol)",
    desc: "Mayin va ifodali ovoz (Tavsiya etiladi!)",
    systemVoice: "Zephyr",
  },
  {
    id: "madina",
    name: "Madina (Ayol)",
    desc: "Aniq va ravon ma'ruzachi ovozi.",
    systemVoice: "Kore",
  },
  {
    id: "sardor",
    name: "Sardor (Erkak)",
    desc: "Yoqimli, samimiy va do'stona ovoz.",
    systemVoice: "Puck",
  },
  {
    id: "jasur",
    name: "Jasur (Erkak)",
    desc: "Shiddatli, chuqur va vazmin ovoz.",
    systemVoice: "Charon",
  },
  {
    id: "farrux",
    name: "Farrux (Erkak)",
    desc: "Muloyim va iliq nutq ohangi.",
    systemVoice: "Fenrir",
  },
];

const STYLES = [
  { id: "natural", label: "Tabiiy / Oddiy" },
  { id: "cheerful", label: "Xushchaqchaq" },
  { id: "calm", label: "Sokin va muloyim" },
  { id: "serious", label: "Jiddiy / Rasmiy" },
  { id: "dramatic", label: "Hayajonli / Dramatik" },
];

export default function App() {
  // App state
  const [text, setText] = useState("");
  const [activeVoice, setActiveVoice] = useState(VOICE_CHARACTERS[0]);
  const [activeStyle, setActiveStyle] = useState(STYLES[0]);
  const [speed, setSpeed] = useState(1.0);

  // Audio state
  const [activeAudioBase64, setActiveAudioBase64] = useState<string | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [mp3Blob, setMp3Blob] = useState<Blob | null>(null);
  const [mp3Url, setMp3Url] = useState<string | null>(null);
  const [waveformAmplitudes, setWaveformAmplitudes] = useState<number[]>([]);

  // Playback state
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  // Loading states
  const [isEnhancing, setIsEnhancing] = useState(false);
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // History state
  const [history, setHistory] = useState<HistoryTrack[]>([]);

  // Settings Modal State
  const [showSettings, setShowSettings] = useState(false);
  const [inputApiKey, setInputApiKey] = useState("");
  const [hasCustomKey, setHasCustomKey] = useState(isUsingCustomKey());

  // Audio References
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const sourceRef = useRef<MediaElementAudioSourceNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  // Load History from LocalStorage
  useEffect(() => {
    const saved = localStorage.getItem("ozbekovoz_history");
    if (saved) {
      try {
        setHistory(JSON.parse(saved));
      } catch (e) {
        console.error("Failed to parse history", e);
      }
    }
  }, []);

  // Save History to LocalStorage
  const saveHistory = (newHistory: HistoryTrack[]) => {
    setHistory(newHistory);
    localStorage.setItem("ozbekovoz_history", JSON.stringify(newHistory));
  };

  // Setup / Clean Audio Element playbackRate speed bound
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.playbackRate = speed;
    }
  }, [speed, audioUrl]);

  // Handle playing state changes
  useEffect(() => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.play()
        .then(() => {
          setupAudioContext();
          drawVisualizer();
        })
        .catch((err) => {
          console.error("Playback failed", err);
          setIsPlaying(false);
        });
    } else {
      audioRef.current.pause();
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    }
  }, [isPlaying]);

  // Setup Web Audio Context for visualizer
  const setupAudioContext = () => {
    if (!audioRef.current) return;
    if (!audioContextRef.current) {
      try {
        const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
        const ctx = new AudioContextClass();
        const analyser = ctx.createAnalyser();
        analyser.fftSize = 128; // compact FFT size for sleek bar visualization

        const src = ctx.createMediaElementSource(audioRef.current);
        src.connect(analyser);
        analyser.connect(ctx.destination);

        audioContextRef.current = ctx;
        analyserRef.current = analyser;
        sourceRef.current = src;
      } catch (err) {
        console.error("Failed to initialize AudioContext", err);
      }
    }

    if (audioContextRef.current && audioContextRef.current.state === "suspended") {
      audioContextRef.current.resume();
    }
  };

  // Draw Audio Visualizer to Canvas
  const drawVisualizer = () => {
    if (!analyserRef.current || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const analyser = analyserRef.current;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const draw = () => {
      animationFrameRef.current = requestAnimationFrame(draw);
      analyser.getByteFrequencyData(dataArray);

      const width = canvas.width;
      const height = canvas.height;
      ctx.clearRect(0, 0, width, height);

      const barWidth = width / bufferLength;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        // scale frequency data to visualizer height
        const barHeight = (dataArray[i] / 255) * height;

        // Custom Gradient: Cyan to Teal
        const gradient = ctx.createLinearGradient(0, height, 0, 0);
        gradient.addColorStop(0, "#0f766e"); // teal-700
        gradient.addColorStop(0.5, "#06b6d4"); // cyan-500
        gradient.addColorStop(1, "#22d3ee"); // cyan-400

        ctx.fillStyle = gradient;
        // rounded top bar simulation
        ctx.fillRect(x, height - barHeight, barWidth - 3, barHeight);

        x += barWidth;
      }
    };

    draw();
  };

  // Process raw base64 PCM output to dynamic WAV Blob in-memory
  const buildWavBlob = (base64String: string): { blob: Blob; amplitudes: number[] } => {
    const rawBinary = atob(base64String);
    const pcmData = new Uint8Array(rawBinary.length);
    for (let i = 0; i < rawBinary.length; i++) {
      pcmData[i] = rawBinary.charCodeAt(i);
    }

    // Dynamic 44-byte WAV header setup for 24000Hz mono 16-bit
    const sampleRate = 24000;
    const numChannels = 1;
    const bitsPerSample = 16;
    const byteRate = sampleRate * numChannels * (bitsPerSample / 8);
    const blockAlign = numChannels * (bitsPerSample / 8);

    const headerBuffer = new ArrayBuffer(44);
    const view = new DataView(headerBuffer);

    // Write WAV header structure
    // "RIFF"
    view.setUint32(0, 0x52494646, false);
    // File size - 8
    view.setUint32(4, 36 + pcmData.length, true);
    // "WAVE"
    view.setUint32(8, 0x57415645, false);
    // "fmt "
    view.setUint32(12, 0x666d7420, false);
    // Subchunk1Size (16 for PCM)
    view.setUint32(16, 16, true);
    // AudioFormat (1 for PCM)
    view.setUint16(20, 1, true);
    // NumChannels
    view.setUint16(22, numChannels, true);
    // SampleRate
    view.setUint32(24, sampleRate, true);
    // ByteRate
    view.setUint32(28, byteRate, true);
    // BlockAlign
    view.setUint16(32, blockAlign, true);
    // BitsPerSample
    view.setUint16(34, bitsPerSample, true);
    // "data"
    view.setUint32(36, 0x64617461, false);
    // Subchunk2Size
    view.setUint32(40, pcmData.length, true);

    const wavBytes = new Uint8Array(44 + pcmData.length);
    wavBytes.set(new Uint8Array(headerBuffer), 0);
    wavBytes.set(pcmData, 44);

    const blob = new Blob([wavBytes], { type: "audio/wav" });

    // Generate SoundCloud Waveform Amplitudes (100 bars)
    const totalSamples = Math.floor(pcmData.length / 2);
    const dataView = new DataView(pcmData.buffer, pcmData.byteOffset, pcmData.byteLength);
    const barCount = 64;
    const chunkSize = Math.max(1, Math.floor(totalSamples / barCount));
    const amplitudes: number[] = [];

    let maxVal = 0;
    for (let i = 0; i < barCount; i++) {
      let sum = 0;
      const startSample = i * chunkSize;
      const endSample = Math.min(totalSamples, startSample + chunkSize);
      let count = 0;
      for (let s = startSample; s < endSample; s += 2) {
        // Read 16-bit Int
        if (s * 2 + 1 < pcmData.length) {
          const val = Math.abs(dataView.getInt16(s * 2, true));
          sum += val;
          count++;
        }
      }
      const avg = count > 0 ? sum / count : 0;
      if (avg > maxVal) maxVal = avg;
      amplitudes.push(avg);
    }

    // Normalize
    const normalizedAmplitudes = amplitudes.map((amp) => {
      if (maxVal === 0) return 10;
      return Math.max(5, Math.round((amp / maxVal) * 100));
    });

    return { blob, amplitudes: normalizedAmplitudes };
  };

  // Convert raw PCM bytes to 128kbps MP3 Blob using client lamejs
  const convertPcmToMp3 = (base64String: string): Blob | null => {
    try {
      const lamejs = (window as any).lamejs;
      if (!lamejs) {
        console.warn("LameJS library not found. Falling back to WAV download.");
        return null;
      }

      const rawBinary = atob(base64String);
      const pcmBytes = new Uint8Array(rawBinary.length);
      for (let i = 0; i < rawBinary.length; i++) {
        pcmBytes[i] = rawBinary.charCodeAt(i);
      }

      const sampleRate = 24000;
      const mp3encoder = new lamejs.Mp3Encoder(1, sampleRate, 128); // 1 channel, 24kHz, 128kbps

      const numSamples = Math.floor(pcmBytes.length / 2);
      const dataView = new DataView(pcmBytes.buffer, pcmBytes.byteOffset, pcmBytes.byteLength);
      const int16Samples = new Int16Array(numSamples);

      for (let i = 0; i < numSamples; i++) {
        int16Samples[i] = dataView.getInt16(i * 2, true);
      }

      const mp3Data: any[] = [];
      const sampleBlockSize = 1152;
      for (let i = 0; i < int16Samples.length; i += sampleBlockSize) {
        const chunk = int16Samples.subarray(i, i + sampleBlockSize);
        const mp3buf = mp3encoder.encodeBuffer(chunk);
        if (mp3buf.length > 0) {
          mp3Data.push(new Uint8Array(mp3buf));
        }
      }

      const flushBuf = mp3encoder.flush();
      if (flushBuf.length > 0) {
        mp3Data.push(new Uint8Array(flushBuf));
      }

      return new Blob(mp3Data, { type: "audio/mp3" });
    } catch (e) {
      console.error("Error during LameJS compression", e);
      return null;
    }
  };

  // Handle Text Correction / Orthography enhancement
  const handleEnhanceText = async () => {
    if (!text.trim()) {
      setErrorMessage("Iltimos, avval matn kiriting.");
      return;
    }
    setIsEnhancing(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const corrected = await enhanceText(text);
      if (corrected) {
        setText(corrected);
        setSuccessMessage("Matn imlosi muvaffaqiyatli to'g'rilandi va optimallashtirildi!");
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Tahrirlash jarayonida noma'lum xatolik.");
    } finally {
      setIsEnhancing(false);
    }
  };

  // Handle Speech Synthesis
  const handleSynthesize = async () => {
    if (!text.trim()) {
      setErrorMessage("Sintez qilish uchun matn kiritilmagan.");
      return;
    }

    if (text.length > 1200) {
      setErrorMessage("Matn juda uzun. Maksimal uzunlik: 1200 belgi.");
      return;
    }

    setIsSynthesizing(true);
    setErrorMessage(null);
    setSuccessMessage(null);
    setIsPlaying(false);

    try {
      const data = await synthesizeSpeech(text, activeVoice.id, activeStyle.id);
      const base64Audio = data.audio;
      loadAudioFromBase64(base64Audio, text, activeVoice, activeStyle);

      // Save to History
      const track: HistoryTrack = {
        id: Math.random().toString(36).substring(2, 9),
        text,
        voiceName: activeVoice.name,
        style: activeStyle.label,
        speed,
        timestamp: new Date().toLocaleTimeString("uz-UZ", {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        }),
        audioBase64: base64Audio,
      };

      const updatedHistory = [track, ...history.slice(0, 5)];
      saveHistory(updatedHistory);
      setSuccessMessage("Matn muvaffaqiyatli ovozga sintez qilindi!");
    } catch (err: any) {
      setErrorMessage(err.message || "Sintez jarayonida xatolik yuz berdi.");
    } finally {
      setIsSynthesizing(false);
    }
  };

  // Helper to load audio from Base64 string (either new synth or history select)
  const loadAudioFromBase64 = (
    base64Audio: string,
    associatedText: string,
    voiceObj: typeof VOICE_CHARACTERS[0] | any,
    styleObj: typeof STYLES[0] | any
  ) => {
    // Revoke old URLs to release memory
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    if (mp3Url) URL.revokeObjectURL(mp3Url);

    // Prepend dynamic WAV header
    const { blob: wavBlob, amplitudes } = buildWavBlob(base64Audio);
    const newWavUrl = URL.createObjectURL(wavBlob);

    // Generate client-side MP3 Blob
    const newMp3Blob = convertPcmToMp3(base64Audio);
    if (newMp3Blob) {
      setMp3Blob(newMp3Blob);
      setMp3Url(URL.createObjectURL(newMp3Blob));
    } else {
      // fallback to wav if MP3 fails
      setMp3Blob(wavBlob);
      setMp3Url(newWavUrl);
    }

    setActiveAudioBase64(base64Audio);
    setAudioUrl(newWavUrl);
    setWaveformAmplitudes(amplitudes);

    // Reset playback info
    setCurrentTime(0);
    setDuration(0);
    setIsPlaying(true); // Auto-play the synthesized speech
  };

  // Audio lifecycle / progress bindings
  const onAudioLoadedMetadata = () => {
    if (audioRef.current) {
      setDuration(audioRef.current.duration);
    }
  };

  const onAudioTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
    }
  };

  const onAudioEnded = () => {
    setIsPlaying(false);
    setCurrentTime(0);
  };

  // SoundCloud progressive seeking handler
  const handleSeekWaveform = (index: number) => {
    if (!audioRef.current || waveformAmplitudes.length === 0) return;
    const percentage = index / waveformAmplitudes.length;
    const targetTime = percentage * duration;
    audioRef.current.currentTime = targetTime;
    setCurrentTime(targetTime);
  };

  // Use Preset helper
  const handleUsePreset = (presetText: string) => {
    setText(presetText);
    setErrorMessage(null);
    setSuccessMessage(null);
  };

  // Load History Clip
  const handleLoadHistoryClip = (track: HistoryTrack) => {
    setText(track.text);
    setSpeed(track.speed);

    // Find original voice and style object if they exist to match settings UI
    const foundVoice = VOICE_CHARACTERS.find((v) => v.name === track.voiceName) || VOICE_CHARACTERS[0];
    const foundStyle = STYLES.find((s) => s.label === track.style) || STYLES[0];

    setActiveVoice(foundVoice);
    setActiveStyle(foundStyle);

    loadAudioFromBase64(track.audioBase64, track.text, foundVoice, foundStyle);
  };

  // Clear All History
  const handleClearHistory = () => {
    saveHistory([]);
  };

  // Delete Individual History Clip
  const handleDeleteHistoryClip = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    const filtered = history.filter((h) => h.id !== id);
    saveHistory(filtered);
  };

  // Time format helper
  const formatTime = (timeInSecs: number) => {
    if (isNaN(timeInSecs)) return "00:00";
    const mins = Math.floor(timeInSecs / 60);
    const secs = Math.floor(timeInSecs % 60);
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <div className="min-h-screen flex flex-col justify-between" id="app_root">
      {/* HEADER SECTION */}
      <header className="border-b border-slate-200 bg-white shadow-sm py-4 px-6" id="app_header">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-teal-500 to-cyan-500 flex items-center justify-center shadow-md shadow-teal-100 animate-pulse">
              <Volume2 className="h-5 w-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-extrabold tracking-tight text-slate-900">O'zbek Ovoz</h1>
                <span className="text-[10px] font-bold uppercase tracking-wider bg-teal-500 text-white px-2 py-0.5 rounded-full">
                  AI SPEECH
                </span>
              </div>
              <p className="text-xs text-slate-500">Eng ilg'or ovoz sintezlovchi platformasi</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                setInputApiKey(hasCustomKey ? getApiKey() : "");
                setShowSettings(true);
              }}
              className="text-xs font-semibold bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-700 rounded-lg px-3 py-1.5 flex items-center gap-1.5 shadow-sm transition-all cursor-pointer"
              title="Gemini API Kaliti"
            >
              <Key className="h-3.5 w-3.5 text-teal-600" />
              <span>API Kalit</span>
              <span className={`h-2 w-2 rounded-full ${hasCustomKey ? "bg-cyan-500" : "bg-emerald-500"}`}></span>
            </button>
            <span className="text-xs font-semibold bg-slate-100 border border-slate-200 text-slate-600 rounded-lg px-3 py-1.5 hidden sm:flex items-center gap-1.5 shadow-sm">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-ping"></span>
              Gemini Flash TTS
            </span>
          </div>
        </div>
      </header>

      {/* API KEY SETTINGS MODAL */}
      {showSettings && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-xs flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Settings className="h-5 w-5 text-teal-600" />
                Gemini API Sozlamalari
              </h3>
              <button
                onClick={() => setShowSettings(false)}
                className="text-slate-400 hover:text-slate-600 text-lg font-bold p-1 cursor-pointer"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-slate-500 mb-4 leading-relaxed">
              Dastur sukut bo'yicha integratsiya qilingan Gemini API kaliti orqali ishlaydi. Agar xohlasangiz, o'zingizning Google AI Studio kalitingizni kiritishingiz mumkin:
            </p>

            <div className="mb-4">
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Google Gemini API Kaliti
              </label>
              <input
                type="password"
                placeholder={hasCustomKey ? "O'z shaxsiy kalitingiz o'rnatilgan" : "AIzaSy..."}
                value={inputApiKey}
                onChange={(e) => setInputApiKey(e.target.value)}
                className="w-full text-xs font-mono p-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-hidden focus:ring-2 focus:ring-teal-500 text-slate-800"
              />
              <span className="text-[10px] text-slate-400 mt-1 block">
                Holat: {hasCustomKey ? "Shaxsiy kalit faol" : "Tizim kaliti faol (Avtomatik)"}
              </span>
            </div>

            <div className="flex items-center justify-between gap-2 pt-2 border-t border-slate-100">
              <button
                onClick={() => {
                  resetApiKey();
                  setHasCustomKey(false);
                  setInputApiKey("");
                  setShowSettings(false);
                  setSuccessMessage("Tizimning asosiy API kalitiga qaytarildi.");
                }}
                className="text-xs text-slate-500 hover:text-rose-600 py-2 px-3 font-semibold transition-colors cursor-pointer"
              >
                Asliga qaytarish
              </button>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowSettings(false)}
                  className="text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 py-2 px-3.5 rounded-xl font-bold transition-colors cursor-pointer"
                >
                  Bekor qilish
                </button>
                <button
                  onClick={() => {
                    if (inputApiKey.trim()) {
                      setApiKey(inputApiKey.trim());
                      setHasCustomKey(true);
                      setSuccessMessage("Yangi API kalit saqlandi!");
                    }
                    setShowSettings(false);
                  }}
                  className="text-xs bg-teal-500 hover:bg-teal-600 text-slate-950 py-2 px-4 rounded-xl font-bold transition-colors cursor-pointer shadow-sm"
                >
                  Saqlash
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* CORE CONTENT */}
      <main className="max-w-7xl mx-auto px-4 py-8 w-full flex-grow">
        {/* Error / Success Notifications */}
        {errorMessage && (
          <div className="mb-6 bg-rose-50 border border-rose-200 text-rose-800 p-4 rounded-xl flex items-start gap-3 shadow-sm animate-fade-in">
            <AlertCircle className="h-5 w-5 text-rose-600 shrink-0 mt-0.5" />
            <div>
              <h4 className="font-semibold text-sm">Xatolik yuz berdi</h4>
              <p className="text-xs mt-1 text-rose-700">{errorMessage}</p>
            </div>
          </div>
        )}

        {successMessage && (
          <div className="mb-6 bg-emerald-50 border border-emerald-200 text-emerald-800 p-4 rounded-xl flex items-start gap-3 shadow-sm animate-fade-in">
            <Check className="h-5 w-5 text-emerald-600 shrink-0 mt-0.5" />
            <div>
              <h4 className="font-semibold text-sm">Muvaffaqiyatli</h4>
              <p className="text-xs mt-1 text-emerald-700">{successMessage}</p>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* LEFT COLUMN: EDITOR & SETTINGS (width: 7 cols) */}
          <section className="lg:col-span-7 flex flex-col gap-6" id="editor_section">
            {/* Matn Kiritish Card */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6" id="input_card">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Type className="h-5 w-5 text-teal-600" />
                  <h3 className="font-bold text-slate-800 text-base">O'zbekcha matn kiritish</h3>
                </div>
                <span className="text-xs font-medium text-slate-400 bg-slate-50 px-2.5 py-1 rounded-md border border-slate-100">
                  {text.length} / 1200 belgi
                </span>
              </div>

              <textarea
                className="w-full h-44 p-4 border border-slate-200 rounded-xl focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 outline-none text-slate-700 text-sm placeholder-slate-400 resize-none transition-all duration-200"
                placeholder="Bu yerga o'zbek tilidagi matnni kiriting. Eng yaxshi ovoz sintezi uchun matnda harf xatolariga yo'l qo'ymaslik, 'o' va 'g' harflariga to'g'ri apostroflardan foydalanish hamda tinish belgilarini joy-joyiga qo'yish tavsiya etiladi."
                maxLength={1200}
                value={text}
                onChange={(e) => setText(e.target.value)}
              />

              {/* Preset Chips Layout */}
              <div className="mt-4">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-2">
                  Tayyor andozalar (Tezkor yuklash):
                </span>
                <div className="flex flex-wrap gap-2">
                  {PRESET_CHIPS.map((chip) => (
                    <button
                      key={chip.id}
                      onClick={() => handleUsePreset(chip.text)}
                      className="text-xs px-3.5 py-2 bg-slate-100 hover:bg-slate-200 border border-slate-200 text-slate-600 hover:text-slate-900 rounded-xl font-medium transition-colors cursor-pointer"
                    >
                      {chip.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Tahrirlash Button */}
              <div className="mt-6 pt-5 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-4">
                <p className="text-[11px] text-slate-400 italic">
                  Imlo to'g'rilash o' va g' harflarini, tinish belgilarini chiroyli tekshiradi.
                </p>
                <button
                  onClick={handleEnhanceText}
                  disabled={isEnhancing || !text.trim()}
                  className={`w-full sm:w-auto px-5 py-2.5 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 border shadow-sm transition-all cursor-pointer ${
                    isEnhancing
                      ? "bg-slate-50 text-slate-400 border-slate-200"
                      : "bg-teal-50 hover:bg-teal-100 text-teal-700 border-teal-200 hover:border-teal-300"
                  }`}
                >
                  {isEnhancing ? (
                    <RefreshCw className="h-3.5 w-3.5 animate-spin text-teal-600" />
                  ) : (
                    <Sparkles className="h-3.5 w-3.5 text-teal-600" />
                  )}
                  Tahrirlash va Imlo to'g'rilash (Gemini 3.5-Flash)
                </button>
              </div>
            </div>

            {/* Sozlamalar Card */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6" id="settings_card">
              <div className="flex items-center gap-2 mb-6">
                <Sliders className="h-5 w-5 text-teal-600" />
                <h3 className="font-bold text-slate-800 text-base">Ovoz sozlamalari va Uslublar</h3>
              </div>

              {/* Voice Selectors */}
              <div className="mb-6">
                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-3">
                  Suxandonni tanlang:
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {VOICE_CHARACTERS.map((char) => (
                    <button
                      key={char.id}
                      onClick={() => setActiveVoice(char)}
                      className={`p-3.5 rounded-xl border text-left transition-all cursor-pointer ${
                        activeVoice.id === char.id
                          ? "border-teal-500 bg-teal-50/50 ring-2 ring-teal-500/10"
                          : "border-slate-200 hover:border-slate-300 bg-white"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-800 text-xs">{char.name}</span>
                        {activeVoice.id === char.id && (
                          <span className="h-1.5 w-1.5 rounded-full bg-teal-500" />
                        )}
                      </div>
                      <p className="text-[11px] text-slate-400 mt-1">{char.desc}</p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Emotion / Style Selectors */}
              <div className="mb-6">
                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-3">
                  Nutq hissiyoti va ohangi:
                </label>
                <div className="flex flex-wrap gap-2">
                  {STYLES.map((style) => (
                    <button
                      key={style.id}
                      onClick={() => setActiveStyle(style)}
                      className={`px-3.5 py-2.5 rounded-xl text-xs font-medium border transition-all cursor-pointer ${
                        activeStyle.id === style.id
                          ? "bg-slate-900 border-slate-900 text-white shadow-sm"
                          : "bg-slate-50 hover:bg-slate-100 border-slate-200 text-slate-600"
                      }`}
                    >
                      {style.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Tempo Speed Slider */}
              <div className="mb-8">
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-wider block">
                    Nutq tezligi (Tempo):
                  </label>
                  <span className="text-xs font-bold text-teal-600 bg-teal-50 px-2 py-0.5 rounded-md">
                    {speed.toFixed(1)}x
                  </span>
                </div>
                <input
                  type="range"
                  min="0.5"
                  max="2.0"
                  step="0.1"
                  value={speed}
                  onChange={(e) => setSpeed(parseFloat(e.target.value))}
                  className="w-full accent-teal-600 h-1.5 bg-slate-100 rounded-lg cursor-pointer"
                />
                <div className="flex items-center justify-between text-[11px] text-slate-400 mt-1.5">
                  <span>Sekin (0.5x)</span>
                  <span className="font-medium text-slate-300">Tabiiy (1.0x)</span>
                  <span>Tez (2.0x)</span>
                </div>
              </div>

              {/* Main Synthesize Button */}
              <button
                onClick={handleSynthesize}
                disabled={isSynthesizing || !text.trim()}
                className={`w-full py-4 rounded-xl font-bold text-sm tracking-wide transition-all shadow-md flex items-center justify-center gap-2 cursor-pointer ${
                  isSynthesizing
                    ? "bg-slate-100 border border-slate-200 text-slate-400"
                    : "bg-gradient-to-r from-teal-500 to-cyan-500 text-white hover:from-teal-600 hover:to-cyan-600 active:scale-[0.99] shadow-teal-500/10 hover:shadow-lg hover:shadow-teal-500/20"
                }`}
              >
                {isSynthesizing ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin text-teal-600" />
                    <span>Matn ovozga sintez qilinmoqda, kuting...</span>
                  </>
                ) : (
                  <>
                    <Volume2 className="h-4 w-4" />
                    <span>Matnni Ovozga Sintez Qilish</span>
                  </>
                )}
              </button>
            </div>
          </section>

          {/* RIGHT COLUMN: PREVIEW & HISTORY (width: 5 cols) */}
          <section className="lg:col-span-5 flex flex-col gap-6" id="playback_section">
            {/* Active Track Player (Immersive Dark Theme) */}
            <div className="bg-slate-950 text-white rounded-2xl border border-slate-800 shadow-xl p-6 relative overflow-hidden" id="player_card">
              {/* Background gradient hint */}
              <div className="absolute top-0 right-0 h-44 w-44 bg-teal-500/10 blur-3xl rounded-full pointer-events-none" />

              <div className="flex items-center justify-between mb-5 border-b border-slate-800/80 pb-4">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-1.5">
                  <span className={`h-2 w-2 rounded-full ${audioUrl ? 'bg-teal-400 animate-pulse' : 'bg-slate-600'}`}></span>
                  {audioUrl ? "FAOL TRACK" : "KUTISH REJIMI"}
                </span>
                <span className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider bg-slate-900 border border-slate-800 px-2 py-1 rounded-md">
                  Mono 24kHz • MP3 128kbps
                </span>
              </div>

              {/* No Audio Generated Yet State */}
              {!audioUrl ? (
                <div className="py-12 px-4 text-center flex flex-col items-center justify-center min-h-[300px]">
                  <div className="h-16 w-16 bg-slate-900 border border-slate-800 rounded-full flex items-center justify-center mb-4">
                    <Disc className="h-8 w-8 text-slate-600 animate-spin" style={{ animationDuration: '6s' }} />
                  </div>
                  <h4 className="font-bold text-sm text-slate-300">Hozircha hech qanday ovoz sintez qilinmadi</h4>
                  <p className="text-xs text-slate-500 mt-2 max-w-sm leading-relaxed">
                    Sintez qilish tugmasini bosing yoki tayyor andozalardan birini tanlab ovoz hosil qiling.
                  </p>
                </div>
              ) : (
                /* Audio Generated & Loaded State */
                <div className="min-h-[300px] flex flex-col justify-between py-2">
                  <div>
                    {/* Meta Info */}
                    <div className="flex items-start justify-between gap-4 mb-6">
                      <div>
                        <h4 className="font-extrabold text-teal-400 text-sm tracking-wide">
                          {activeVoice.name.replace(/\s*\(.*\)/, "")} ovozi
                        </h4>
                        <p className="text-xs text-slate-400 mt-0.5 font-medium">
                          Ohang: {activeStyle.label} • Tezlik: {speed.toFixed(1)}x
                        </p>
                      </div>
                      <div className="h-12 w-12 bg-slate-900 border border-slate-800 rounded-full flex items-center justify-center shrink-0">
                        <Disc className={`h-6 w-6 text-teal-400 ${isPlaying ? 'animate-spin' : ''}`} style={{ animationDuration: '4s' }} />
                      </div>
                    </div>

                    {/* Interactive progressive wave bar layout (SoundCloud style) */}
                    <div className="bg-slate-900/50 border border-slate-800/80 rounded-xl p-4 mb-4">
                      <div className="flex items-end justify-between gap-1.5 h-16 px-1" id="waveform_container">
                        {waveformAmplitudes.map((amp, index) => {
                          const progressPercent = duration > 0 ? (currentTime / duration) * 100 : 0;
                          const barPercent = (index / waveformAmplitudes.length) * 100;
                          const isActive = barPercent <= progressPercent;

                          return (
                            <button
                              key={index}
                              onClick={() => handleSeekWaveform(index)}
                              className="flex-1 rounded-t-sm transition-all duration-150 cursor-pointer hover:scale-y-110"
                              style={{
                                height: `${amp}%`,
                                backgroundColor: isActive ? "#06b6d4" : "#334155",
                              }}
                              title={`Seek to ${formatTime((index / waveformAmplitudes.length) * duration)}`}
                            />
                          );
                        })}
                      </div>

                      {/* Timeline timers */}
                      <div className="flex items-center justify-between text-[11px] text-slate-400 font-medium mt-3">
                        <span>{formatTime(currentTime)}</span>
                        <span>{formatTime(duration)}</span>
                      </div>
                    </div>
                  </div>

                  {/* Main Player controls row */}
                  <div className="flex items-center justify-center gap-5 my-4">
                    <button
                      onClick={() => setIsPlaying(!isPlaying)}
                      className="h-16 w-16 bg-gradient-to-tr from-teal-500 to-cyan-500 hover:from-teal-600 hover:to-cyan-600 rounded-full flex items-center justify-center text-white shadow-lg shadow-teal-500/20 active:scale-95 transition-all cursor-pointer"
                    >
                      {isPlaying ? (
                        <Pause className="h-6 w-6 text-white fill-current" />
                      ) : (
                        <Play className="h-6 w-6 text-white fill-current translate-x-0.5" />
                      )}
                    </button>
                  </div>

                  {/* Canvas Spectrum Visualizer (Active rendering) */}
                  <div className="mb-4 bg-slate-900/30 border border-slate-900 rounded-lg p-2.5">
                    <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block mb-2">
                      Spektral vizualizator:
                    </span>
                    <canvas
                      ref={canvasRef}
                      width={380}
                      height={40}
                      className="w-full h-10 rounded bg-slate-950 border border-slate-800"
                    />
                  </div>

                  {/* MP3 Export Section */}
                  {mp3Url && (
                    <div className="mt-4 pt-4 border-t border-slate-800/80 bg-slate-900/40 rounded-xl p-4 border border-slate-800">
                      <div className="flex items-center gap-2 mb-3">
                        <Check className="h-4 w-4 text-teal-400 shrink-0" />
                        <span className="text-xs font-bold text-slate-200">
                          LameJS yordamida tezkor MP3 o'tkazish yakunlandi.
                        </span>
                      </div>
                      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
                        <div>
                          <p className="text-slate-400 font-semibold">MP3 Audio (HD 128kbps)</p>
                          <p className="text-slate-500 text-[10px] mt-0.5">Yuklab olish formati: .mp3</p>
                        </div>
                        <button
                          onClick={() => {
                            const filename = `ozbekovoz_speech_${Date.now()}.mp3`;
                            if (mp3Blob) {
                              saveAudioFile(mp3Blob, filename);
                            } else if (activeAudioBase64) {
                              saveAudioFile(activeAudioBase64, filename);
                            }
                          }}
                          className="w-full sm:w-auto px-4 py-2.5 bg-teal-500 hover:bg-teal-600 text-slate-950 font-bold rounded-xl text-center flex items-center justify-center gap-1.5 transition-colors cursor-pointer shadow-md"
                        >
                          <Download className="h-4 w-4 stroke-[3px]" />
                          TAYYOR MP3 YUKLASH
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Native audio tag hidden inside */}
              {audioUrl && (
                <audio
                  ref={audioRef}
                  src={audioUrl}
                  onLoadedMetadata={onAudioLoadedMetadata}
                  onTimeUpdate={onAudioTimeUpdate}
                  onEnded={onAudioEnded}
                  className="hidden"
                />
              )}
            </div>

            {/* Sintez Tarixi */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6" id="history_card">
              <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <Clock className="h-5 w-5 text-slate-500" />
                  <h3 className="font-bold text-slate-800 text-sm">Oxirgi sintez qilingan ovozlar</h3>
                </div>
                {history.length > 0 && (
                  <button
                    onClick={handleClearHistory}
                    className="text-xs font-semibold text-rose-600 hover:text-rose-800 transition-colors flex items-center gap-1 cursor-pointer"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                    Tarixni tozalash
                  </button>
                )}
              </div>

              {history.length === 0 ? (
                <div className="py-8 text-center text-slate-400 flex flex-col items-center justify-center">
                  <FileText className="h-8 w-8 text-slate-300 mb-2" />
                  <p className="text-xs font-semibold text-slate-500">Hali ovozlar sintez qilinmadi</p>
                  <p className="text-[11px] text-slate-400 mt-1">Siz yaratgan ovozlar shu yerda saqlanadi.</p>
                </div>
              ) : (
                <div className="flex flex-col gap-3 max-h-[300px] overflow-y-auto pr-1">
                  {history.map((track) => (
                    <div
                      key={track.id}
                      onClick={() => handleLoadHistoryClip(track)}
                      className="p-3 bg-slate-50 hover:bg-slate-100/80 border border-slate-200 hover:border-slate-300 rounded-xl transition-all cursor-pointer flex items-center justify-between gap-3 group"
                    >
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-xs text-slate-800">{track.voiceName}</span>
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-200 text-slate-600 font-semibold uppercase">
                            {track.style}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-400 mt-1 truncate max-w-xs">{track.text}</p>
                        <span className="text-[9px] text-slate-400 block mt-0.5 font-medium">{track.timestamp}</span>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <span className="opacity-0 group-hover:opacity-100 text-[10px] text-teal-600 font-bold transition-opacity">
                          Tinglash
                        </span>
                        <div className="h-8 w-8 rounded-full bg-white border border-slate-200 flex items-center justify-center text-slate-600 group-hover:bg-teal-50 group-hover:border-teal-200 group-hover:text-teal-600 transition-colors">
                          <Play className="h-3.5 w-3.5 fill-current translate-x-0.5" />
                        </div>
                        <button
                          onClick={(e) => handleDeleteHistoryClip(e, track.id)}
                          className="h-8 w-8 rounded-full bg-white hover:bg-rose-50 border border-slate-200 hover:border-rose-200 flex items-center justify-center text-slate-400 hover:text-rose-600 transition-colors cursor-pointer"
                          title="O'chirish"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>
        </div>
      </main>

      {/* FOOTER SECTION */}
      <footer className="border-t border-slate-200 bg-white py-6 px-6 text-center text-slate-400 text-xs" id="app_footer_nav">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <p className="font-medium text-slate-500">© 2026 O'zbek Ovoz AI. Barcha huquqlar himoyalangan.</p>
          <p className="text-slate-400 text-[11px]">
            Sintez va audio vizualizatsiya to'liq brauzerda va serverda xavfsiz boshqariladi.
          </p>
        </div>
      </footer>
    </div>
  );
}
