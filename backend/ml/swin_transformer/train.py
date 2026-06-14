"""Training script for the Swin Transformer acoustic classifier."""

import argparse
import os
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.amp import GradScaler, autocast
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter
from tqdm import tqdm

from .dataset import SeismicAnomalyDataset as AcousticDataset, CLASS_NAMES
from .model import AcousticSwinTransformer, NUM_CLASSES


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train Swin-T acoustic classifier")
    parser.add_argument("--data-dir", type=str, required=True, help="Root data directory")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--weight-decay", type=float, default=1e-5)
    parser.add_argument("--patience", type=int, default=5, help="Early stopping patience")
    parser.add_argument("--checkpoint-dir", type=str, default="checkpoints")
    parser.add_argument("--log-dir", type=str, default="runs/swin_acoustic")
    parser.add_argument("--num-workers", type=int, default=4)
    parser.add_argument("--no-pretrained", action="store_true")
    parser.add_argument("--resume", type=str, default=None, help="Resume from checkpoint")
    parser.add_argument("--class-weights", type=float, nargs="+", default=None,
                        help="Manual class weights for loss (length must equal num classes)")
    return parser.parse_args()


def compute_class_weights(dataset: AcousticDataset) -> torch.Tensor:
    """Compute inverse-frequency class weights from the dataset labels."""
    labels = np.array([dataset[i][1] for i in range(len(dataset))])
    counts = np.bincount(labels, minlength=NUM_CLASSES).astype(np.float64)
    counts = np.maximum(counts, 1.0)  # avoid division by zero
    weights = len(labels) / (NUM_CLASSES * counts)
    return torch.tensor(weights, dtype=torch.float32)


def train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    scaler: GradScaler,
    device: torch.device,
) -> tuple[float, float]:
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for spectrograms, labels in tqdm(loader, desc="  train", leave=False):
        spectrograms = spectrograms.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)

        optimizer.zero_grad(set_to_none=True)
        with autocast(device_type=device.type):
            logits = model(spectrograms)
            loss = criterion(logits, labels)

        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()

        running_loss += loss.item() * spectrograms.size(0)
        correct += (logits.argmax(dim=1) == labels).sum().item()
        total += labels.size(0)

    return running_loss / total, correct / total


@torch.no_grad()
def validate(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> tuple[float, float]:
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0

    for spectrograms, labels in tqdm(loader, desc="  val  ", leave=False):
        spectrograms = spectrograms.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)

        with autocast(device_type=device.type):
            logits = model(spectrograms)
            loss = criterion(logits, labels)

        running_loss += loss.item() * spectrograms.size(0)
        correct += (logits.argmax(dim=1) == labels).sum().item()
        total += labels.size(0)

    return running_loss / total, correct / total


def main() -> None:
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # ---- Data -----------------------------------------------------------
    train_dataset = AcousticDataset(args.data_dir, split="train")
    val_dataset = AcousticDataset(args.data_dir, split="val")

    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        pin_memory=True,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=True,
    )

    # ---- Model ----------------------------------------------------------
    model = AcousticSwinTransformer(pretrained=not args.no_pretrained).to(device)

    # ---- Loss with class weights ----------------------------------------
    if args.class_weights is not None:
        weights = torch.tensor(args.class_weights, dtype=torch.float32)
    else:
        weights = compute_class_weights(train_dataset)
    print(f"Class weights: {weights.tolist()}")
    criterion = nn.CrossEntropyLoss(weight=weights.to(device))

    # ---- Optimizer / scheduler ------------------------------------------
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = CosineAnnealingLR(optimizer, T_max=args.epochs)
    scaler = GradScaler()

    # ---- Resume ---------------------------------------------------------
    start_epoch = 0
    best_val_acc = 0.0
    if args.resume and os.path.isfile(args.resume):
        ckpt = torch.load(args.resume, map_location=device, weights_only=False)
        model.load_state_dict(ckpt["model_state_dict"])
        optimizer.load_state_dict(ckpt["optimizer_state_dict"])
        start_epoch = ckpt.get("epoch", 0) + 1
        best_val_acc = ckpt.get("val_acc", 0.0)
        print(f"Resumed from epoch {start_epoch}, best val acc {best_val_acc:.4f}")

    # ---- Logging --------------------------------------------------------
    writer = SummaryWriter(log_dir=args.log_dir)
    ckpt_dir = Path(args.checkpoint_dir)
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    best_path = ckpt_dir / "swin_acoustic_best.pth"

    # ---- Training loop --------------------------------------------------
    epochs_no_improve = 0

    for epoch in range(start_epoch, args.epochs):
        t0 = time.time()
        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, scaler, device)
        val_loss, val_acc = validate(model, val_loader, criterion, device)
        scheduler.step()

        elapsed = time.time() - t0
        lr = optimizer.param_groups[0]["lr"]

        print(
            f"Epoch {epoch + 1}/{args.epochs} ({elapsed:.1f}s) | "
            f"train loss={train_loss:.4f} acc={train_acc:.4f} | "
            f"val loss={val_loss:.4f} acc={val_acc:.4f} | lr={lr:.2e}"
        )

        writer.add_scalars("loss", {"train": train_loss, "val": val_loss}, epoch)
        writer.add_scalars("accuracy", {"train": train_acc, "val": val_acc}, epoch)
        writer.add_scalar("lr", lr, epoch)

        # Checkpoint best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            epochs_no_improve = 0
            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "val_acc": val_acc,
                    "val_loss": val_loss,
                    "class_names": CLASS_NAMES,
                },
                best_path,
            )
            print(f"  -> Saved best model (val_acc={val_acc:.4f})")
        else:
            epochs_no_improve += 1

        # Early stopping
        if epochs_no_improve >= args.patience:
            print(f"Early stopping triggered after {args.patience} epochs without improvement.")
            break

    writer.close()
    print(f"Training complete. Best val accuracy: {best_val_acc:.4f}")
    print(f"Best checkpoint: {best_path}")


if __name__ == "__main__":
    main()
