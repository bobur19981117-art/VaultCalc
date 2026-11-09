import express, { Request, Response } from "express";
import path from "path";
import dotenv from "dotenv";
import { GoogleGenAI } from "@google/genai";
import { createServer as createViteServer } from "vite";

dotenv.config();

const app = express();
const PORT = 3000;

app.use(express.json());

// Initialize Gemini SDK with User-Agent and key
const apiKey = process.env.GEMINI_API_KEY;
const ai = apiKey
  ? new GoogleGenAI({
      apiKey,
      httpOptions: {
        headers: {
          "User-Agent": "aistudio-build",
        },
      },
    })
  : null;

// API routes first
app.get("/api/health", (req: Request, res: Response) => {
  res.json({
    status: "ok",
    hasApiKey: !!apiKey,
    time: new Date().toISOString(),
  });
});

// A. Speech Synthesis API
app.post("/api/tts", async (req: Request, res: Response): Promise<any> => {
  if (!ai) {
    return res.status(500).json({
      error: "Sinfiy intellekt kaliti (GEMINI_API_KEY) o'rnatilmagan. Iltimos, Secrets panelidan sozlang.",
    });
  }

  const { text, voiceName, style } = req.body;

  if (!text || typeof text !== "string") {
    return res.status(400).json({ error: "Sintez qilish uchun matn kiritish majburiy." });
  }

  if (text.length > 1200) {
    return res.status(400).json({ error: "Matn uzunligi 1200 belgidan oshmasligi kerak." });
  }

  // Voice Mapping
  // Dilnoza -> Zephyr
  // Madina -> Kore
  // Sardor -> Puck
  // Jasur -> Charon
  // Farrux -> Fenrir
  let resolvedSystemVoice = "Zephyr";
  const normalizedVoice = (voiceName || "").toLowerCase();
  if (normalizedVoice.includes("madina") || normalizedVoice === "kore") {
    resolvedSystemVoice = "Kore";
  } else if (normalizedVoice.includes("sardor") || normalizedVoice === "puck") {
    resolvedSystemVoice = "Puck";
  } else if (normalizedVoice.includes("jasur") || normalizedVoice === "charon") {
    resolvedSystemVoice = "Charon";
  } else if (normalizedVoice.includes("farrux") || normalizedVoice === "fenrir") {
    resolvedSystemVoice = "Fenrir";
  } else {
    resolvedSystemVoice = "Zephyr";
  }

  // Style directive to embed in the text prompt
  // tabiy / oddiy (natural)
  // xushchaqchaq (cheerful)
  // sokin va muloyim (calm)
  // jiddiy / rasmiy (serious)
  // hayajonli / dramatik (dramatic)
  let styleDirective = "";
  const styleLower = (style || "").toLowerCase();
  if (styleLower.includes("cheerful") || styleLower.includes("xushchaqchaq")) {
    styleDirective = "Say cheerfully and with high energy: ";
  } else if (styleLower.includes("calm") || styleLower.includes("sokin")) {
    styleDirective = "Say calmly, softly and slowly: ";
  } else if (styleLower.includes("serious") || styleLower.includes("jiddiy")) {
    styleDirective = "Say seriously, formally and with professional tone: ";
  } else if (styleLower.includes("dramatic") || styleLower.includes("hayajonli") || styleLower.includes("dramatik")) {
    styleDirective = "Say dramatically, with high expression and emotion: ";
  } else {
    styleDirective = "Say naturally and clearly: ";
  }

  const userConfiguredPromptWithEmotion = `${styleDirective}${text}`;

  try {
    const response = await ai.models.generateContent({
      model: "gemini-3.1-flash-tts-preview",
      contents: [{ parts: [{ text: userConfiguredPromptWithEmotion }] }],
      config: {
        responseModalities: ["AUDIO"],
        speechConfig: {
          voiceConfig: {
            prebuiltVoiceConfig: { voiceName: resolvedSystemVoice },
          },
        },
      },
    });

    const inlinePart = response.candidates?.[0]?.content?.parts?.[0];
    const base64Audio = inlinePart?.inlineData?.data;

    if (!base64Audio) {
      return res.status(500).json({
        error: "Ovoz hosil qilishda xatolik yuz berdi. Model audio qaytarmadi.",
      });
    }

    res.json({
      audio: base64Audio,
      voiceName,
      resolvedSystemVoice,
      style,
      textLength: text.length,
    });
  } catch (error: any) {
    console.error("TTS API Error:", error);
    res.status(500).json({
      error: `Gemini TTS xatosi: ${error.message || error}`,
    });
  }
});

// B. Intelligent Text Orthography Enhancer API
app.post("/api/enhance-text", async (req: Request, res: Response): Promise<any> => {
  if (!ai) {
    return res.status(500).json({
      error: "Sinfiy intellekt kaliti (GEMINI_API_KEY) o'rnatilmagan. Iltimos, Secrets panelidan sozlang.",
    });
  }

  const { text } = req.body;

  if (!text || typeof text !== "string") {
    return res.status(400).json({ error: "Tahrirlash uchun matn kiritish majburiy." });
  }

  if (text.length > 1200) {
    return res.status(400).json({ error: "Matn uzunligi 1200 belgidan oshmasligi kerak." });
  }

  try {
    // Correct Uzbek orthography: correct apostrophes o' and g' (should use standard apostrophe/single quote formats if appropriate), spelling, endings, punctuation.
    const prompt = `Inspect, correct, and smooth the Uzbek spelling, punctuation, and grammar in the following text.
Specifically check and correct letters like "o'" (o with single quote/apostrophe) and "g'" (g with single quote/apostrophe) to be formatted correctly, correct typos, verify suffix alignments, and refine overall readability.

CRITICAL INSTRUCTION: Return ONLY the corrected Uzbek text. Do NOT include any explanations, introduction, markdown codeblocks, notes, or chat wrappers. Just output the corrected text itself.

TEXT TO CORRECT:
${text}`;

    const response = await ai.models.generateContent({
      model: "gemini-3.5-flash",
      contents: prompt,
    });

    let correctedText = response.text || "";
    correctedText = correctedText.trim();

    // Clean up any accidental markdown blocks that the model might have returned
    if (correctedText.startsWith("```")) {
      correctedText = correctedText.replace(/^```[a-zA-Z]*\n/, "").replace(/\n```$/, "");
    }
    correctedText = correctedText.trim();

    res.json({ correctedText });
  } catch (error: any) {
    console.error("Enhance Text Error:", error);
    res.status(500).json({
      error: `Matnni tahrirlashda xatolik yuz berdi: ${error.message || error}`,
    });
  }
});

// Vite middleware or serving build files
async function setupServer() {
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*all", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on http://0.0.0.0:${PORT}`);
  });
}

setupServer().catch((err) => {
  console.error("Failed to start server:", err);
});
