"""
SCEDC/IRIS Seismic Dataset Pipeline for Railway Acoustic Anomaly Detection.

Maps seismic waveform signals to railway anomaly classes using mel-spectrogram
representations suitable for Swin Transformer input.

Classes:
    0 - NORMAL:     Ambient noise / no anomaly
    1 - FLAT_WHEEL: Periodic impact patterns (mapped from small quakes)
    2 - MICRO_CRACK: Transient high-frequency bursts (mapped from surface events)
    3 - OBSTRUCTION: Sustained broadband signal (mapped from large events)
"""

from __future__ import annotations

import logging
import os
import warnings
from enum import IntEnum
from pathlib import Path
from typing import Optional, Tuple

import librosa
import numpy as np
import torch
import torchaudio
from scipy import signal as scipy_signal
from sklearn.model_selection import train_test_split
from torch.utils.data import Dataset

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SAMPLE_RATE = 16_000
N_FFT = 1024
HOP_LENGTH = 512
N_MELS = 128
SPEC_TIME_FRAMES = 128  # target time-axis length for (1, 128, 128) output
DURATION_SEC = SPEC_TIME_FRAMES * HOP_LENGTH / SAMPLE_RATE  # ~4.1 s

DEFAULT_DATA_DIR = Path(__file__).resolve().parent / "data"


class AnomalyClass(IntEnum):
    NORMAL = 0
    FLAT_WHEEL = 1
    MICRO_CRACK = 2
    OBSTRUCTION = 3


CLASS_NAMES = {
    AnomalyClass.NORMAL: "normal",
    AnomalyClass.FLAT_WHEEL: "flat_wheel",
    AnomalyClass.MICRO_CRACK: "micro_crack",
    AnomalyClass.OBSTRUCTION: "obstruction",
}

# SCEDC / IRIS seismic-type to railway-anomaly mapping
SEISMIC_TO_ANOMALY = {
    "noise": AnomalyClass.NORMAL,
    "qb": AnomalyClass.NORMAL,       # quarry blast background
    "le": AnomalyClass.FLAT_WHEEL,    # local event (small quake)
    "lf": AnomalyClass.FLAT_WHEEL,    # low-frequency event
    "se": AnomalyClass.MICRO_CRACK,   # surface event
    "st": AnomalyClass.MICRO_CRACK,   # shallow tremor
    "eq": AnomalyClass.OBSTRUCTION,   # earthquake (large event)
    "re": AnomalyClass.OBSTRUCTION,   # regional event
}


# ---------------------------------------------------------------------------
# Augmentation helpers
# ---------------------------------------------------------------------------

class WaveformAugmentor:
    """Stochastic waveform augmentations applied during training."""

    def __init__(
        self,
        p_time_shift: float = 0.5,
        p_freq_mask: float = 0.5,
        p_gaussian_noise: float = 0.5,
        p_time_stretch: float = 0.3,
        noise_std: float = 0.005,
        max_shift_frac: float = 0.1,
    ):
        self.p_time_shift = p_time_shift
        self.p_freq_mask = p_freq_mask
        self.p_gaussian_noise = p_gaussian_noise
        self.p_time_stretch = p_time_stretch
        self.noise_std = noise_std
        self.max_shift_frac = max_shift_frac

    # -- waveform-domain augmentations --

    def time_shift(self, wav: np.ndarray) -> np.ndarray:
        shift = int(len(wav) * self.max_shift_frac * (np.random.rand() * 2 - 1))
        return np.roll(wav, shift)

    def add_gaussian_noise(self, wav: np.ndarray) -> np.ndarray:
        return wav + np.random.randn(len(wav)).astype(np.float32) * self.noise_std

    def time_stretch(self, wav: np.ndarray) -> np.ndarray:
        rate = np.random.uniform(0.85, 1.15)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            stretched = librosa.effects.time_stretch(wav, rate=rate)
        # Pad or truncate to original length
        if len(stretched) > len(wav):
            stretched = stretched[: len(wav)]
        else:
            stretched = np.pad(stretched, (0, len(wav) - len(stretched)))
        return stretched

    # -- spectrogram-domain augmentations --

    @staticmethod
    def frequency_mask(spec: np.ndarray, max_width: int = 16) -> np.ndarray:
        """Zero-out a horizontal band of the mel spectrogram."""
        n_mels = spec.shape[0]
        width = np.random.randint(1, max_width + 1)
        start = np.random.randint(0, max(1, n_mels - width))
        spec = spec.copy()
        spec[start : start + width, :] = 0.0
        return spec

    def __call__(
        self, wav: np.ndarray, spec: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        if np.random.rand() < self.p_time_shift:
            wav = self.time_shift(wav)
        if np.random.rand() < self.p_gaussian_noise:
            wav = self.add_gaussian_noise(wav)
        if np.random.rand() < self.p_time_stretch:
            wav = self.time_stretch(wav)
        if np.random.rand() < self.p_freq_mask:
            spec = self.frequency_mask(spec)
        return wav, spec


# ---------------------------------------------------------------------------
# Mel-spectrogram conversion
# ---------------------------------------------------------------------------

def waveform_to_mel(
    wav: np.ndarray,
    sr: int = SAMPLE_RATE,
    n_fft: int = N_FFT,
    hop_length: int = HOP_LENGTH,
    n_mels: int = N_MELS,
    target_frames: int = SPEC_TIME_FRAMES,
) -> np.ndarray:
    """Convert a 1-D waveform to a log-mel spectrogram of shape (n_mels, target_frames)."""
    mel = librosa.feature.melspectrogram(
        y=wav.astype(np.float32),
        sr=sr,
        n_fft=n_fft,
        hop_length=hop_length,
        n_mels=n_mels,
    )
    mel_db = librosa.power_to_db(mel, ref=np.max)

    # Pad or truncate time axis to target_frames
    if mel_db.shape[1] < target_frames:
        mel_db = np.pad(mel_db, ((0, 0), (0, target_frames - mel_db.shape[1])))
    else:
        mel_db = mel_db[:, :target_frames]

    return mel_db


# ---------------------------------------------------------------------------
# Synthetic data generation
# ---------------------------------------------------------------------------

def _synth_normal(n_samples: int, sr: int = SAMPLE_RATE) -> np.ndarray:
    """Low-amplitude ambient noise."""
    return np.random.randn(n_samples).astype(np.float32) * 0.01


def _synth_flat_wheel(n_samples: int, sr: int = SAMPLE_RATE) -> np.ndarray:
    """Periodic impacts at 5-15 Hz simulating flat wheel strikes."""
    t = np.arange(n_samples, dtype=np.float32) / sr
    freq = np.random.uniform(5.0, 15.0)
    # Periodic impulse train convolved with a short decay
    impulse_period = int(sr / freq)
    impulse_train = np.zeros(n_samples, dtype=np.float32)
    impulse_train[::impulse_period] = 1.0
    # Exponential decay kernel
    decay_len = int(sr * 0.02)
    kernel = np.exp(-np.linspace(0, 5, decay_len)).astype(np.float32)
    sig = np.convolve(impulse_train, kernel, mode="same")
    # Add a bit of background noise
    sig += np.random.randn(n_samples).astype(np.float32) * 0.005
    sig = sig / (np.abs(sig).max() + 1e-8) * 0.5
    return sig


def _synth_micro_crack(n_samples: int, sr: int = SAMPLE_RATE) -> np.ndarray:
    """Brief transient high-frequency burst."""
    sig = np.random.randn(n_samples).astype(np.float32) * 0.005  # background
    # Insert 1-3 short bursts
    n_bursts = np.random.randint(1, 4)
    for _ in range(n_bursts):
        burst_len = int(sr * np.random.uniform(0.01, 0.05))
        start = np.random.randint(0, max(1, n_samples - burst_len))
        burst_freq = np.random.uniform(2000, 6000)
        t_burst = np.arange(burst_len, dtype=np.float32) / sr
        envelope = np.hanning(burst_len).astype(np.float32)
        burst = envelope * np.sin(2 * np.pi * burst_freq * t_burst).astype(np.float32)
        sig[start : start + burst_len] += burst * 0.8
    sig = sig / (np.abs(sig).max() + 1e-8) * 0.6
    return sig


def _synth_obstruction(n_samples: int, sr: int = SAMPLE_RATE) -> np.ndarray:
    """Sustained high-amplitude broadband signal."""
    # Broadband noise filtered with a gentle low-pass to sound natural
    sig = np.random.randn(n_samples).astype(np.float32)
    sos = scipy_signal.butter(4, 7000, btype="low", fs=sr, output="sos")
    sig = scipy_signal.sosfilt(sos, sig).astype(np.float32)
    # Apply a slow envelope so it ramps up and sustains
    envelope = np.ones(n_samples, dtype=np.float32)
    ramp = int(sr * 0.2)
    envelope[:ramp] = np.linspace(0, 1, ramp)
    envelope[-ramp:] = np.linspace(1, 0, ramp)
    sig = sig * envelope
    sig = sig / (np.abs(sig).max() + 1e-8) * 0.9
    return sig


_SYNTH_GENERATORS = {
    AnomalyClass.NORMAL: _synth_normal,
    AnomalyClass.FLAT_WHEEL: _synth_flat_wheel,
    AnomalyClass.MICRO_CRACK: _synth_micro_crack,
    AnomalyClass.OBSTRUCTION: _synth_obstruction,
}


def generate_synthetic_dataset(
    data_dir: str | Path = DEFAULT_DATA_DIR,
    samples_per_class: int = 200,
    sr: int = SAMPLE_RATE,
    duration: float = DURATION_SEC,
    seed: int = 42,
) -> Path:
    """Create synthetic waveform .npy files organised by class label.

    Directory layout::

        data_dir/
          synthetic/
            normal/0000.npy ...
            flat_wheel/0000.npy ...
            micro_crack/0000.npy ...
            obstruction/0000.npy ...

    Returns the path to ``data_dir/synthetic``.
    """
    rng_state = np.random.get_state()
    np.random.seed(seed)

    data_dir = Path(data_dir)
    root = data_dir / "synthetic"
    n_samples = int(sr * duration)

    for cls in AnomalyClass:
        cls_dir = root / CLASS_NAMES[cls]
        cls_dir.mkdir(parents=True, exist_ok=True)
        gen_fn = _SYNTH_GENERATORS[cls]
        for i in range(samples_per_class):
            wav = gen_fn(n_samples, sr)
            np.save(cls_dir / f"{i:04d}.npy", wav)

    np.random.set_state(rng_state)
    logger.info("Generated %d synthetic samples in %s", samples_per_class * 4, root)
    return root


# ---------------------------------------------------------------------------
# IRIS / FDSN download (best-effort, falls back to synthetic)
# ---------------------------------------------------------------------------

def download_scedc_data(
    data_dir: str | Path = DEFAULT_DATA_DIR,
    network: str = "CI",
    station: str = "RIO",
    channel: str = "HHZ",
    start: str = "2024-01-01T00:00:00",
    end: str = "2024-01-02T00:00:00",
    samples_per_class: int = 50,
    sr: int = SAMPLE_RATE,
    duration: float = DURATION_SEC,
) -> Path:
    """Download waveforms from IRIS FDSN web services and map to anomaly classes.

    Falls back to :func:`generate_synthetic_dataset` when the network is
    unreachable or the ``obspy`` package is unavailable.

    Returns the root data directory that was populated.
    """
    data_dir = Path(data_dir)
    iris_dir = data_dir / "iris"

    try:
        from obspy.clients.fdsn import Client  # type: ignore[import-untyped]
        from obspy import UTCDateTime  # type: ignore[import-untyped]

        client = Client("IRIS")
        t_start = UTCDateTime(start)
        t_end = UTCDateTime(end)

        # Fetch event catalogue to derive labels
        catalog = client.get_events(
            starttime=t_start,
            endtime=t_end,
            minmagnitude=0.5,
            maxmagnitude=6.0,
            limit=samples_per_class * 4,
        )

        n_samples = int(sr * duration)

        for cls in AnomalyClass:
            (iris_dir / CLASS_NAMES[cls]).mkdir(parents=True, exist_ok=True)

        counts = {cls: 0 for cls in AnomalyClass}

        for event in catalog:
            mag = event.preferred_magnitude().mag if event.preferred_magnitude() else 0
            etype = (event.event_type or "noise").lower().replace(" ", "")

            # Map magnitude ranges as a fallback when event_type is generic
            if etype in SEISMIC_TO_ANOMALY:
                label = SEISMIC_TO_ANOMALY[etype]
            elif mag < 1.5:
                label = AnomalyClass.FLAT_WHEEL
            elif mag < 3.0:
                label = AnomalyClass.MICRO_CRACK
            else:
                label = AnomalyClass.OBSTRUCTION

            if counts[label] >= samples_per_class:
                continue

            origin = event.preferred_origin()
            if origin is None:
                continue

            try:
                st = client.get_waveforms(
                    network, station, "*", channel,
                    origin.time, origin.time + duration,
                )
                wav = st[0].data.astype(np.float32)
                # Resample if needed
                if st[0].stats.sampling_rate != sr:
                    wav = librosa.resample(
                        wav, orig_sr=st[0].stats.sampling_rate, target_sr=sr
                    )
                # Normalise and fix length
                wav = wav / (np.abs(wav).max() + 1e-8)
                if len(wav) > n_samples:
                    wav = wav[:n_samples]
                else:
                    wav = np.pad(wav, (0, max(0, n_samples - len(wav))))

                idx = counts[label]
                cls_name = CLASS_NAMES[label]
                np.save(iris_dir / cls_name / f"{idx:04d}.npy", wav)
                counts[label] += 1
            except Exception:
                continue

        logger.info("Downloaded IRIS data: %s", counts)
        return iris_dir

    except Exception as exc:
        logger.warning(
            "IRIS download unavailable (%s). Falling back to synthetic data.", exc
        )
        return generate_synthetic_dataset(data_dir=data_dir, samples_per_class=200)


# ---------------------------------------------------------------------------
# PyTorch Dataset
# ---------------------------------------------------------------------------

class SeismicAnomalyDataset(Dataset):
    """PyTorch dataset that loads seismic/audio waveforms and returns
    ``(mel_spectrogram, label)`` pairs with shape ``(1, 128, 128)``.

    Parameters
    ----------
    data_dir : path to root containing class sub-directories of ``.npy`` files.
    split : one of ``"train"``, ``"val"``, ``"test"``.
    augment : whether to apply data augmentation (auto-enabled for train).
    train_ratio, val_ratio : proportions for splitting.
    seed : random seed for reproducible splits.
    """

    def __init__(
        self,
        data_dir: str | Path,
        split: str = "train",
        augment: Optional[bool] = None,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        seed: int = 42,
    ):
        assert split in ("train", "val", "test"), f"Invalid split: {split}"
        self.data_dir = Path(data_dir)
        self.split = split
        self.augment = augment if augment is not None else (split == "train")
        self.augmentor = WaveformAugmentor() if self.augment else None

        # Collect all (file_path, label) pairs
        all_files: list[Tuple[Path, int]] = []
        for cls in AnomalyClass:
            cls_dir = self.data_dir / CLASS_NAMES[cls]
            if not cls_dir.is_dir():
                continue
            for f in sorted(cls_dir.glob("*.npy")):
                all_files.append((f, int(cls)))

        if len(all_files) == 0:
            raise FileNotFoundError(
                f"No .npy files found in {self.data_dir}. "
                "Run generate_synthetic_dataset() or download_scedc_data() first."
            )

        paths, labels = zip(*all_files)
        paths, labels = list(paths), list(labels)

        # Stratified train / val / test split
        test_ratio = 1.0 - train_ratio - val_ratio
        train_paths, temp_paths, train_labels, temp_labels = train_test_split(
            paths, labels,
            test_size=(val_ratio + test_ratio),
            stratify=labels,
            random_state=seed,
        )
        relative_val = val_ratio / (val_ratio + test_ratio)
        val_paths, test_paths, val_labels, test_labels = train_test_split(
            temp_paths, temp_labels,
            test_size=(1.0 - relative_val),
            stratify=temp_labels,
            random_state=seed,
        )

        split_map = {
            "train": (train_paths, train_labels),
            "val": (val_paths, val_labels),
            "test": (test_paths, test_labels),
        }
        self.files, self.labels = split_map[split]
        logger.info(
            "SeismicAnomalyDataset[%s]: %d samples from %s",
            split, len(self.files), self.data_dir,
        )

    # ----- Dataset interface -----

    def __len__(self) -> int:
        return len(self.files)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        wav = np.load(self.files[idx]).astype(np.float32)
        label = self.labels[idx]

        # Compute mel spectrogram
        mel = waveform_to_mel(wav)

        # Augmentation (waveform-domain augments recompute the spectrogram)
        if self.augmentor is not None:
            wav, mel = self.augmentor(wav, mel)
            # Recompute spectrogram after waveform augments
            mel = waveform_to_mel(wav)
            # Apply frequency mask on the final spectrogram
            if np.random.rand() < self.augmentor.p_freq_mask:
                mel = WaveformAugmentor.frequency_mask(mel)

        # Normalise to [0, 1]
        mel_min, mel_max = mel.min(), mel.max()
        if mel_max - mel_min > 1e-6:
            mel = (mel - mel_min) / (mel_max - mel_min)
        else:
            mel = np.zeros_like(mel)

        # Shape: (1, 128, 128)
        tensor = torch.from_numpy(mel).unsqueeze(0).float()
        return tensor, label


# ---------------------------------------------------------------------------
# Convenience builders
# ---------------------------------------------------------------------------

def build_dataloaders(
    data_dir: str | Path = DEFAULT_DATA_DIR / "synthetic",
    batch_size: int = 32,
    num_workers: int = 2,
    seed: int = 42,
) -> dict:
    """Return a dict of ``{split_name: DataLoader}`` for train/val/test."""
    from torch.utils.data import DataLoader

    loaders = {}
    for split in ("train", "val", "test"):
        ds = SeismicAnomalyDataset(data_dir, split=split, seed=seed)
        loaders[split] = DataLoader(
            ds,
            batch_size=batch_size,
            shuffle=(split == "train"),
            num_workers=num_workers,
            pin_memory=True,
            drop_last=(split == "train"),
        )
    return loaders


# ---------------------------------------------------------------------------
# CLI quick-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("Generating synthetic dataset ...")
    root = generate_synthetic_dataset()

    print("Building data loaders ...")
    loaders = build_dataloaders(data_dir=root, batch_size=8, num_workers=0)

    for name, loader in loaders.items():
        batch = next(iter(loader))
        specs, labels = batch
        print(f"  {name:5s} -> spectrogram shape: {specs.shape}, labels: {labels.tolist()}")

    print("Done.")
