import os
from pathlib import Path
from typing import Callable, List, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image
import pillow_heif

pillow_heif.register_heif_opener()


@dataclass
class OptimizeOptions:
    quality: int = 80             # 50 - 95
    keep_exif: bool = True
    keep_icc: bool = True
    output_dir: Optional[Path] = None
    output_suffix: str = "_optimized"  # If same directory, append suffix to avoid overwrite


@dataclass
class OptimizeResult:
    source_file: Path
    output_file: Optional[Path]
    original_bytes: int
    optimized_bytes: int
    success: bool
    error: Optional[str] = None

    @property
    def savings_bytes(self) -> int:
        if not self.success or self.optimized_bytes == 0:
            return 0
        return max(0, self.original_bytes - self.optimized_bytes)

    @property
    def savings_percent(self) -> float:
        if self.original_bytes == 0 or not self.success:
            return 0.0
        return max(0.0, (self.original_bytes - self.optimized_bytes) / self.original_bytes * 100)


def optimize_single_image(source_path: Path, options: OptimizeOptions) -> OptimizeResult:
    """
    Optimizes/compresses an image file (JPEG, PNG, HEIC, WEBP) to reduce file size
    while preserving visual fidelity based on selected quality.
    """
    source_path = Path(source_path)
    if not source_path.exists():
        return OptimizeResult(source_path, None, 0, 0, False, "File does not exist")

    original_size = source_path.stat().st_size
    ext = source_path.suffix.lower()

    # Determine target filename and output format
    if ext in (".heic", ".heif"):
        # HEIC cannot be saved back lossy reliably across all platforms, convert to optimized JPEG
        out_ext = ".jpg"
        save_format = "JPEG"
    elif ext in (".jpg", ".jpeg"):
        out_ext = ext
        save_format = "JPEG"
    elif ext == ".png":
        out_ext = ".png"
        save_format = "PNG"
    elif ext == ".webp":
        out_ext = ".webp"
        save_format = "WEBP"
    else:
        out_ext = ext
        save_format = "JPEG"

    if options.output_dir:
        out_dir = Path(options.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        output_path = out_dir / f"{source_path.stem}{out_ext}"
    else:
        # Same folder: add suffix to avoid overwriting original file
        suffix = options.output_suffix if options.output_suffix else "_optimized"
        output_path = source_path.parent / f"{source_path.stem}{suffix}{out_ext}"

    try:
        with Image.open(source_path) as img:
            save_kwargs = {}

            if options.keep_icc:
                icc = img.info.get("icc_profile")
                if icc:
                    save_kwargs["icc_profile"] = icc

            if options.keep_exif:
                exif = img.info.get("exif")
                if exif:
                    save_kwargs["exif"] = exif

            if save_format == "JPEG":
                if img.mode in ("RGBA", "LA", "P"):
                    rgb = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    rgb.paste(img, mask=img.split()[-1])
                    img = rgb
                elif img.mode != "RGB":
                    img = img.convert("RGB")

                save_kwargs["quality"] = max(30, min(95, options.quality))
                save_kwargs["optimize"] = True
                save_kwargs["progressive"] = True
                # Use 4:2:0 subsampling for aggressive compression, 4:4:4 for high quality
                save_kwargs["subsampling"] = 0 if options.quality >= 88 else 2
                img.save(output_path, format="JPEG", **save_kwargs)

            elif save_format == "PNG":
                # PNG is lossless; use maximum compression level and optimize
                save_kwargs["optimize"] = True
                save_kwargs["compress_level"] = 9
                img.save(output_path, format="PNG", **save_kwargs)

            elif save_format == "WEBP":
                save_kwargs["quality"] = options.quality
                save_kwargs["method"] = 6
                img.save(output_path, format="WEBP", **save_kwargs)

            else:
                img.save(output_path, format=save_format, **save_kwargs)

        new_size = output_path.stat().st_size
        return OptimizeResult(source_path, output_path, original_size, new_size, True, None)

    except Exception as e:
        return OptimizeResult(source_path, None, original_size, 0, False, str(e))


def batch_optimize(
    files: List[Path],
    options: OptimizeOptions,
    progress_callback: Optional[Callable[[int, int, OptimizeResult], None]] = None,
    max_workers: Optional[int] = None
) -> List[OptimizeResult]:
    """
    Optimizes a batch of images concurrently.
    """
    total = len(files)
    results: List[OptimizeResult] = []
    completed = 0

    if total == 0:
        return results

    if max_workers is None:
        max_workers = min(32, (os.cpu_count() or 1) + 4)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(optimize_single_image, f, options): f for f in files
        }

        for future in as_completed(future_to_file):
            completed += 1
            try:
                res = future.result()
            except Exception as e:
                res = OptimizeResult(future_to_file[future], None, 0, 0, False, str(e))

            results.append(res)
            if progress_callback:
                progress_callback(completed, total, res)

    return results
