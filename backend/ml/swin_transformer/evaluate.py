"""Evaluate a trained Swin Transformer acoustic classifier on a test set."""

import argparse
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay,
)
from torch.utils.data import DataLoader
from tqdm import tqdm

from .dataset import SeismicAnomalyDataset as AcousticDataset, CLASS_NAMES
from .model import AcousticSwinTransformer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate Swin-T acoustic classifier")
    parser.add_argument("--model-path", type=str, required=True, help="Path to .pth checkpoint")
    parser.add_argument("--data-dir", type=str, required=True, help="Root data directory")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--num-workers", type=int, default=4)
    parser.add_argument("--output-dir", type=str, default="eval_results")
    parser.add_argument("--device", type=str, default=None)
    return parser.parse_args()


@torch.no_grad()
def run_evaluation(
    model: AcousticSwinTransformer,
    loader: DataLoader,
    device: torch.device,
) -> tuple[np.ndarray, np.ndarray, float]:
    """Run inference on the full dataset and return true labels, predictions, and avg latency."""
    model.eval()
    all_preds: list[int] = []
    all_labels: list[int] = []
    total_time = 0.0
    total_samples = 0

    for spectrograms, labels in tqdm(loader, desc="Evaluating"):
        spectrograms = spectrograms.to(device, non_blocking=True)

        start = time.perf_counter()
        logits = model(spectrograms)
        if device.type == "cuda":
            torch.cuda.synchronize()
        elapsed = time.perf_counter() - start

        preds = logits.argmax(dim=1).cpu().numpy()
        all_preds.extend(preds.tolist())
        all_labels.extend(labels.numpy().tolist())

        total_time += elapsed
        total_samples += spectrograms.size(0)

    avg_latency_ms = (total_time / total_samples) * 1000 if total_samples else 0.0
    return np.array(all_labels), np.array(all_preds), avg_latency_ms


def save_confusion_matrix(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    output_path: Path,
) -> None:
    cm = confusion_matrix(y_true, y_pred, labels=list(range(len(CLASS_NAMES))))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=CLASS_NAMES)
    fig, ax = plt.subplots(figsize=(8, 8))
    disp.plot(ax=ax, cmap="Blues", colorbar=True)
    ax.set_title("Acoustic Swin-T Confusion Matrix")
    plt.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    print(f"Confusion matrix saved to {output_path}")


def main() -> None:
    args = parse_args()

    if args.device:
        device = torch.device(args.device)
    else:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # ---- Load model -----------------------------------------------------
    model = AcousticSwinTransformer(pretrained=False)
    ckpt = torch.load(args.model_path, map_location=device, weights_only=False)
    model.load_state_dict(ckpt["model_state_dict"])
    model = model.to(device)
    print(f"Loaded checkpoint from {args.model_path} (epoch {ckpt.get('epoch', '?')})")

    # ---- Data -----------------------------------------------------------
    test_dataset = AcousticDataset(args.data_dir, split="test")
    test_loader = DataLoader(
        test_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=True,
    )
    print(f"Test set: {len(test_dataset)} samples")

    # ---- Evaluate -------------------------------------------------------
    y_true, y_pred, avg_latency_ms = run_evaluation(model, test_loader, device)

    # ---- Metrics --------------------------------------------------------
    overall_acc = accuracy_score(y_true, y_pred)
    report = classification_report(y_true, y_pred, target_names=CLASS_NAMES, digits=4)

    print("\n" + "=" * 60)
    print("CLASSIFICATION REPORT")
    print("=" * 60)
    print(report)
    print(f"Overall accuracy: {overall_acc:.4f}")
    print(f"Avg inference latency: {avg_latency_ms:.2f} ms/sample")
    latency_status = "PASS" if avg_latency_ms < 200 else "FAIL"
    print(f"Latency target (<200ms): {latency_status}")

    # ---- Save outputs ---------------------------------------------------
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    save_confusion_matrix(y_true, y_pred, out_dir / "confusion_matrix.png")

    # Save metrics to text file
    metrics_path = out_dir / "metrics.txt"
    with open(metrics_path, "w") as f:
        f.write(report)
        f.write(f"\nOverall accuracy: {overall_acc:.4f}\n")
        f.write(f"Avg inference latency: {avg_latency_ms:.2f} ms/sample\n")
    print(f"Metrics saved to {metrics_path}")


if __name__ == "__main__":
    main()
