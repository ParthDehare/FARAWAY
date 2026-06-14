"""Swin Transformer Tiny acoustic classifier for rail defect detection."""

import torch
import torch.nn as nn
import torch.nn.functional as F
import timm


CLASS_NAMES = ["NORMAL", "FLAT_WHEEL", "MICRO_CRACK", "OBSTRUCTION"]
NUM_CLASSES = len(CLASS_NAMES)


class AcousticSwinTransformer(nn.Module):
    """Swin Transformer Tiny adapted for single-channel mel-spectrogram classification.

    Input:  (B, 1, 128, 128) mel-spectrograms
    Output: (B, NUM_CLASSES) logits

    The model internally resizes inputs to 224x224 and converts the single
    channel to the 3-channel input expected by the pretrained backbone.
    """

    TARGET_SIZE = (224, 224)

    def __init__(self, pretrained: bool = True, num_classes: int = NUM_CLASSES):
        super().__init__()
        self.num_classes = num_classes

        # Load pretrained Swin-T and replace the classifier head
        self.backbone = timm.create_model(
            "swin_tiny_patch4_window7_224",
            pretrained=pretrained,
            num_classes=num_classes,
        )

        # Replace the first conv layer to accept 1-channel input.
        # Original patch embedding conv: (3, 96, kernel=4, stride=4)
        orig_proj = self.backbone.patch_embed.proj
        self.backbone.patch_embed.proj = nn.Conv2d(
            in_channels=1,
            out_channels=orig_proj.out_channels,
            kernel_size=orig_proj.kernel_size,
            stride=orig_proj.stride,
            padding=orig_proj.padding,
            bias=orig_proj.bias is not None,
        )

        # Initialise new conv by averaging the pretrained RGB weights
        if pretrained:
            with torch.no_grad():
                self.backbone.patch_embed.proj.weight.copy_(
                    orig_proj.weight.mean(dim=1, keepdim=True)
                )
                if orig_proj.bias is not None:
                    self.backbone.patch_embed.proj.bias.copy_(orig_proj.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Args:
            x: (B, 1, H, W) mel-spectrogram tensor. H, W are typically 128.

        Returns:
            (B, num_classes) logits.
        """
        # Resize to 224x224 if needed
        if x.shape[-2:] != self.TARGET_SIZE:
            x = F.interpolate(x, size=self.TARGET_SIZE, mode="bilinear", align_corners=False)

        return self.backbone(x)

    @torch.no_grad()
    def predict(self, mel_spectrogram: torch.Tensor) -> tuple[int, float]:
        """Run inference on a single mel-spectrogram.

        Args:
            mel_spectrogram: (1, 128, 128) or (1, 1, 128, 128) tensor.

        Returns:
            Tuple of (class_index, confidence) where confidence is the
            softmax probability of the predicted class.
        """
        self.eval()
        if mel_spectrogram.dim() == 3:
            mel_spectrogram = mel_spectrogram.unsqueeze(0)

        logits = self.forward(mel_spectrogram)
        probs = F.softmax(logits, dim=1)
        confidence, class_idx = probs.max(dim=1)
        return class_idx.item(), confidence.item()
