import io
import logging
import numpy as np

logger = logging.getLogger(__name__)

try:
    import torch
    import torchaudio
    TORCHAUDIO_AVAILABLE = True
except ImportError:
    TORCHAUDIO_AVAILABLE = False

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False


class AcousticPreprocessor:
    """Converts raw audio to mel-spectrogram tensors for Swin Transformer inference."""

    SAMPLE_RATE = 16000
    N_MELS = 128
    N_FFT = 1024
    HOP_LENGTH = 512
    TARGET_SIZE = (128, 128)

    def __init__(self):
        if TORCHAUDIO_AVAILABLE:
            self.mel_transform = torchaudio.transforms.MelSpectrogram(
                sample_rate=self.SAMPLE_RATE,
                n_fft=self.N_FFT,
                hop_length=self.HOP_LENGTH,
                n_mels=self.N_MELS,
            )
            self.amplitude_to_db = torchaudio.transforms.AmplitudeToDB(top_db=80)
        else:
            self.mel_transform = None
            self.amplitude_to_db = None

    def preprocess_audio(self, audio_bytes: bytes) -> "torch.Tensor":
        """Decode audio bytes → 16kHz waveform → mel-spectrogram tensor (1,1,128,128)."""
        waveform, sr = self._decode_audio(audio_bytes)
        return self.preprocess_waveform(waveform, sr)

    def preprocess_waveform(self, waveform: np.ndarray, sr: int) -> "torch.Tensor":
        """Convert numpy waveform to mel-spectrogram tensor (1,1,128,128)."""
        import torch

        if not isinstance(waveform, np.ndarray):
            waveform = np.array(waveform, dtype=np.float32)

        if waveform.ndim > 1:
            waveform = waveform.mean(axis=0)

        waveform = waveform.astype(np.float32)

        # Resample if needed
        if sr != self.SAMPLE_RATE:
            if LIBROSA_AVAILABLE:
                waveform = librosa.resample(waveform, orig_sr=sr, target_sr=self.SAMPLE_RATE)
            elif TORCHAUDIO_AVAILABLE:
                t = torch.from_numpy(waveform).unsqueeze(0)
                resampler = torchaudio.transforms.Resample(sr, self.SAMPLE_RATE)
                waveform = resampler(t).squeeze(0).numpy()

        # Compute mel-spectrogram
        mel = self._compute_mel(waveform)

        # Resize to target
        mel_tensor = torch.from_numpy(mel).unsqueeze(0).unsqueeze(0)  # (1,1,H,W)
        mel_tensor = torch.nn.functional.interpolate(
            mel_tensor, size=self.TARGET_SIZE, mode="bilinear", align_corners=False
        )

        # Normalize to [0, 1]
        mel_min = mel_tensor.min()
        mel_max = mel_tensor.max()
        if mel_max - mel_min > 1e-6:
            mel_tensor = (mel_tensor - mel_min) / (mel_max - mel_min)

        return mel_tensor

    def _compute_mel(self, waveform: np.ndarray) -> np.ndarray:
        """Compute log-mel spectrogram from waveform."""
        if TORCHAUDIO_AVAILABLE and self.mel_transform is not None:
            import torch
            t = torch.from_numpy(waveform).unsqueeze(0)
            mel = self.mel_transform(t)
            mel_db = self.amplitude_to_db(mel)
            return mel_db.squeeze(0).numpy()

        if LIBROSA_AVAILABLE:
            mel = librosa.feature.melspectrogram(
                y=waveform, sr=self.SAMPLE_RATE,
                n_fft=self.N_FFT, hop_length=self.HOP_LENGTH, n_mels=self.N_MELS,
            )
            mel_db = librosa.power_to_db(mel, ref=np.max)
            return mel_db

        # Fallback: simple FFT-based approximation
        from scipy import signal
        _, _, Sxx = signal.spectrogram(waveform, fs=self.SAMPLE_RATE, nperseg=self.N_FFT, noverlap=self.N_FFT - self.HOP_LENGTH)
        mel_approx = 10 * np.log10(Sxx + 1e-10)
        return mel_approx[:self.N_MELS, :]

    def _decode_audio(self, audio_bytes: bytes) -> tuple:
        """Decode audio bytes to (waveform_numpy, sample_rate)."""
        buf = io.BytesIO(audio_bytes)

        if TORCHAUDIO_AVAILABLE:
            try:
                waveform, sr = torchaudio.load(buf)
                return waveform.mean(dim=0).numpy(), sr
            except Exception:
                pass

        if LIBROSA_AVAILABLE:
            try:
                buf.seek(0)
                waveform, sr = librosa.load(buf, sr=None, mono=True)
                return waveform, sr
            except Exception:
                pass

        # Fallback: treat as raw float32 PCM
        raw = np.frombuffer(audio_bytes, dtype=np.float32)
        return raw, self.SAMPLE_RATE
