const API_KEY = process.env.NEXT_PUBLIC_ELEVENLABS_API_KEY || "";
const VOICE_ID = process.env.NEXT_PUBLIC_ELEVENLABS_VOICE_ID || "21m00Tcm4TlvDq8ikWAM";

export async function speakAlert(text: string): Promise<void> {
  if (!API_KEY) {
    console.warn("ElevenLabs API key not set — falling back to Web Speech API");
    return fallbackSpeak(text);
  }

  try {
    const res = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${VOICE_ID}`, {
      method: "POST",
      headers: {
        "xi-api-key": API_KEY,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        text,
        model_id: "eleven_monolingual_v1",
        voice_settings: { stability: 0.75, similarity_boost: 0.85 },
      }),
    });

    if (!res.ok) throw new Error(`ElevenLabs API error: ${res.status}`);

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    await audio.play();
    audio.onended = () => URL.revokeObjectURL(url);
  } catch (err) {
    console.error("ElevenLabs TTS failed, using fallback:", err);
    return fallbackSpeak(text);
  }
}

function fallbackSpeak(text: string): void {
  if (typeof window === "undefined" || !window.speechSynthesis) return;
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 0.95;
  utterance.pitch = 0.9;
  window.speechSynthesis.speak(utterance);
}
