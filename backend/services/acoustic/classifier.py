import time
import threading
import logging
import numpy as np
from dataclasses import dataclass, field

from .preprocessor import AcousticPreprocessor
from .model import AcousticModel, CLASS_NAMES

logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    event_class: str
    confidence: float
    all_probabilities: dict[str, float]
    spectrogram_data: np.ndarray | None  # (128, 128) mel-spec for visualization
    inference_time_ms: float


class AcousticClassifier:
    """High-level classifier combining preprocessor + model. Thread-safe singleton."""

    _instance = None
    _lock = threading.Lock()

    def __init__(self, model_path: str | None = None):
        self.preprocessor = AcousticPreprocessor()
        self.model = AcousticModel(model_path)

    @classmethod
    def get_instance(cls, model_path: str | None = None) -> "AcousticClassifier":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(model_path)
        return cls._instance

    def classify_audio(self, audio_bytes: bytes) -> ClassificationResult:
        """Classify raw audio bytes end-to-end."""
        with self._lock:
            start = time.perf_counter()

            mel_tensor = self.preprocessor.preprocess_audio(audio_bytes)
            spectrogram_data = mel_tensor.squeeze().numpy() if mel_tensor is not None else None

            result = self.model.predict(mel_tensor)

            elapsed_ms = (time.perf_counter() - start) * 1000

        return ClassificationResult(
            event_class=result["class"],
            confidence=result["confidence"],
            all_probabilities=result["all_probs"],
            spectrogram_data=spectrogram_data,
            inference_time_ms=elapsed_ms,
        )

    def classify_waveform(self, waveform: np.ndarray, sr: int) -> ClassificationResult:
        """Classify a numpy waveform array."""
        with self._lock:
            start = time.perf_counter()

            mel_tensor = self.preprocessor.preprocess_waveform(waveform, sr)
            spectrogram_data = mel_tensor.squeeze().numpy() if mel_tensor is not None else None

            result = self.model.predict(mel_tensor)

            elapsed_ms = (time.perf_counter() - start) * 1000

        return ClassificationResult(
            event_class=result["class"],
            confidence=result["confidence"],
            all_probabilities=result["all_probs"],
            spectrogram_data=spectrogram_data,
            inference_time_ms=elapsed_ms,
        )
