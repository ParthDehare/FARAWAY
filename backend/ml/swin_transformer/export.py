"""Export trained Swin Transformer to TorchScript and ONNX for production."""

import argparse
from pathlib import Path

import numpy as np
import torch

from .model import AcousticSwinTransformer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export Swin-T acoustic model")
    parser.add_argument("--model-path", type=str, required=True, help="Path to .pth checkpoint")
    parser.add_argument("--output-dir", type=str, default="exported_models")
    parser.add_argument("--device", type=str, default="cpu")
    return parser.parse_args()


def verify_outputs(
    original: torch.nn.Module,
    loaded: torch.nn.Module | None,
    dummy: torch.Tensor,
    name: str,
    onnx_path: Path | None = None,
) -> bool:
    """Compare outputs between original and exported model."""
    original.eval()
    with torch.no_grad():
        ref = original(dummy).numpy()

    if loaded is not None:
        with torch.no_grad():
            out = loaded(dummy).numpy()
    elif onnx_path is not None:
        import onnxruntime as ort

        sess = ort.InferenceSession(str(onnx_path))
        input_name = sess.get_inputs()[0].name
        out = sess.run(None, {input_name: dummy.numpy()})[0]
    else:
        return False

    max_diff = float(np.max(np.abs(ref - out)))
    match = max_diff < 1e-4
    status = "PASS" if match else "FAIL"
    print(f"  {name} verification: {status} (max diff={max_diff:.2e})")
    return match


def export_torchscript(
    model: AcousticSwinTransformer,
    dummy: torch.Tensor,
    output_path: Path,
) -> Path:
    """Export to TorchScript via tracing."""
    model.eval()
    traced = torch.jit.trace(model, dummy)
    traced.save(str(output_path))
    print(f"TorchScript saved to {output_path}")
    return output_path


def export_onnx(
    model: AcousticSwinTransformer,
    dummy: torch.Tensor,
    output_path: Path,
) -> Path:
    """Export to ONNX format."""
    model.eval()
    torch.onnx.export(
        model,
        dummy,
        str(output_path),
        input_names=["mel_spectrogram"],
        output_names=["logits"],
        dynamic_axes={
            "mel_spectrogram": {0: "batch_size"},
            "logits": {0: "batch_size"},
        },
        opset_version=17,
    )
    print(f"ONNX saved to {output_path}")
    return output_path


def main() -> None:
    args = parse_args()
    device = torch.device(args.device)

    # ---- Load model -----------------------------------------------------
    model = AcousticSwinTransformer(pretrained=False)
    ckpt = torch.load(args.model_path, map_location=device, weights_only=False)
    model.load_state_dict(ckpt["model_state_dict"])
    model = model.to(device).eval()
    print(f"Loaded checkpoint from {args.model_path}")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Dummy input matching expected inference shape
    dummy = torch.randn(1, 1, 128, 128, device=device)

    # ---- TorchScript ----------------------------------------------------
    ts_path = export_torchscript(model, dummy, out_dir / "swin_acoustic.pt")
    ts_model = torch.jit.load(str(ts_path), map_location=device)
    verify_outputs(model, ts_model, dummy.cpu(), "TorchScript")

    # ---- ONNX -----------------------------------------------------------
    onnx_path = export_onnx(model, dummy, out_dir / "swin_acoustic.onnx")
    try:
        verify_outputs(model, None, dummy.cpu(), "ONNX", onnx_path=onnx_path)
    except ImportError:
        print("  ONNX verification skipped (onnxruntime not installed)")

    print("\nExport complete.")


if __name__ == "__main__":
    main()
