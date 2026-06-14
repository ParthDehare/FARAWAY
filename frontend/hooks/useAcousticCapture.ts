import { useEffect, useRef, useState, useCallback } from "react";

interface AcousticData {
  frequencyData: Float32Array;
  timeData: Float32Array;
  rms: number;
}

export function useAcousticCapture() {
  const [isCapturing, setIsCapturing] = useState(false);
  const [data, setData] = useState<AcousticData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const rafRef = useRef<number>(0);

  const start = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const ctx = new AudioContext({ sampleRate: 16000 });
      audioContextRef.current = ctx;

      const source = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 2048;
      analyser.smoothingTimeConstant = 0.8;
      source.connect(analyser);
      analyserRef.current = analyser;

      const freqBuf = new Float32Array(analyser.frequencyBinCount);
      const timeBuf = new Float32Array(analyser.fftSize);

      const tick = () => {
        analyser.getFloatFrequencyData(freqBuf);
        analyser.getFloatTimeDomainData(timeBuf);

        let sum = 0;
        for (let i = 0; i < timeBuf.length; i++) sum += timeBuf[i] * timeBuf[i];
        const rms = Math.sqrt(sum / timeBuf.length);

        setData({
          frequencyData: new Float32Array(freqBuf),
          timeData: new Float32Array(timeBuf),
          rms,
        });
        rafRef.current = requestAnimationFrame(tick);
      };

      tick();
      setIsCapturing(true);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Microphone access denied");
    }
  }, []);

  const stop = useCallback(() => {
    cancelAnimationFrame(rafRef.current);
    streamRef.current?.getTracks().forEach((t) => t.stop());
    audioContextRef.current?.close();
    setIsCapturing(false);
    setData(null);
  }, []);

  useEffect(() => {
    return () => {
      cancelAnimationFrame(rafRef.current);
      streamRef.current?.getTracks().forEach((t) => t.stop());
      audioContextRef.current?.close();
    };
  }, []);

  return { isCapturing, data, error, start, stop };
}
