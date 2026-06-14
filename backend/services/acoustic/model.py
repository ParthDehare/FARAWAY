import os
import logging
import numpy as np
from fastapi import HTTPException

logger = logging.getLogger(__name__)

CLASS_NAMES = ["NORMAL", "FLAT_WHEEL", "CRACK", "JOINT_BAR"]

try:
    import torch
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class AcousticModel:
    """Production model loader with Hackathon Demo fallback."""

    def __init__(self, model_path: str | None = None):
        self.model_path = os.getenv(
            "ACOUSTIC_MODEL_PATH", "../../ml/models/acoustic_demo.pth"
        )
        self._model = None
        self._device = None

    def _train_demo_model(self):
        """Generates synthetic data and trains the Swin Transformer as a demo fallback."""
        logger.warning("Demo mode triggered: Missing .pth file. Training synthetic Swin Transformer...")
        from torch.utils.data import Dataset, DataLoader
        import torch.nn as nn
        from ml.swin_transformer.model import AcousticSwinTransformer

        # Fix import bug mapping: generate SeismicAnomalyDataset internally
        class SeismicAnomalyDataset(Dataset):
            def __init__(self):
                self.samples = []
                self.labels = []
                # 50 samples per class (4 classes = 200 total)
                for class_idx in range(4):
                    for _ in range(50):
                        # 128-dim mel spectrogram simulation (1 channel, 128, 128)
                        data = np.random.randn(1, 128, 128).astype(np.float32) * 0.1
                        if class_idx == 0:  # NORMAL
                            data += 0.5
                        elif class_idx == 1:  # FLAT_WHEEL
                            data[:, 20:30, :] += 2.0
                        elif class_idx == 2:  # CRACK
                            data[:, :, 40:50] += 2.0
                        elif class_idx == 3:  # JOINT_BAR
                            data[:, 60:80, 60:80] += 1.5
                        
                        self.samples.append(torch.from_numpy(data))
                        self.labels.append(class_idx)

            def __len__(self):
                return len(self.samples)
                
            def __getitem__(self, idx):
                return self.samples[idx], self.labels[idx]

        dataset = SeismicAnomalyDataset()
        dataloader = DataLoader(dataset, batch_size=16, shuffle=True)
        
        model = AcousticSwinTransformer(num_classes=4)
        model.to(self._device)
        
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        criterion = nn.CrossEntropyLoss()
        
        model.train()
        for epoch in range(10):
            for inputs, labels in dataloader:
                inputs = inputs.to(self._device)
                labels = labels.to(self._device)
                
                optimizer.zero_grad()
                
                # Resize to 224x224 for Swin Transformer
                inputs_resized = F.interpolate(inputs, size=(224, 224), mode="bilinear", align_corners=False)
                
                outputs = model(inputs_resized)
                loss = criterion(outputs, labels)
                
                loss.backward()
                optimizer.step()
            logger.info(f"Demo Training Epoch {epoch+1}/10 completed. Loss: {loss.item():.4f}")
            
        os.makedirs(os.path.dirname(self.model_path) or ".", exist_ok=True)
        torch.save({"model_state_dict": model.state_dict()}, self.model_path)
        logger.info(f"Synthetic demo model saved to {self.model_path}")

    def _load_model(self):
        if not TORCH_AVAILABLE:
            logger.error("CRITICAL: PyTorch is not available. Cannot load acoustic model.")
            raise HTTPException(status_code=503, detail="Acoustic inference engine is unavailable due to missing PyTorch dependency.")

        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        if not os.path.exists(self.model_path):
            # Hackathon Fallback: Train synthetic model instead of crashing 503
            self._train_demo_model()

        try:
            # Try TorchScript first
            self._model = torch.jit.load(self.model_path, map_location=self._device)
            logger.info(f"Loaded TorchScript model from {self.model_path}")
        except Exception:
            try:
                # Load PyTorch state dict checkpoint
                checkpoint = torch.load(self.model_path, map_location=self._device, weights_only=False)
                if "model_state_dict" in checkpoint:
                    from ml.swin_transformer.model import AcousticSwinTransformer
                    self._model = AcousticSwinTransformer(num_classes=4)
                    self._model.load_state_dict(checkpoint["model_state_dict"])
                else:
                    self._model = checkpoint
                self._model.to(self._device)
                logger.info(f"Loaded PyTorch checkpoint from {self.model_path}")
            except Exception as e:
                logger.error(f"CRITICAL: Failed to load PyTorch model weights: {str(e)}")
                raise HTTPException(status_code=503, detail=f"Failed to load acoustic model weights: {str(e)}")

        self._model.eval()

    def predict(self, mel_tensor) -> dict:
        """Run inference on a mel-spectrogram tensor. Returns class, confidence, all_probs."""
        if self._model is None:
            self._load_model()

        try:
            with torch.no_grad():
                if not isinstance(mel_tensor, torch.Tensor):
                    mel_tensor = torch.from_numpy(mel_tensor).float()

                mel_tensor = mel_tensor.to(self._device)
                if mel_tensor.dim() == 3:
                    mel_tensor = mel_tensor.unsqueeze(0)

                # Resize to 224x224 for Swin Transformer
                if mel_tensor.shape[-2:] != (224, 224):
                    mel_tensor = F.interpolate(mel_tensor, size=(224, 224), mode="bilinear", align_corners=False)

                logits = self._model(mel_tensor)
                probs = F.softmax(logits, dim=-1).squeeze(0).cpu().numpy()

            idx = int(np.argmax(probs))
            return {
                "class": CLASS_NAMES[idx],
                "confidence": float(probs[idx]),
                "all_probs": {name: float(p) for name, p in zip(CLASS_NAMES, probs)},
            }
        except Exception as e:
            logger.error(f"CRITICAL: Inference failed on acoustic model: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Acoustic model inference failed: {str(e)}")
