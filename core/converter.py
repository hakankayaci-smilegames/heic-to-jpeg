import os
from pathlib import Path
from typing import Callable, List, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image
import pillow_heif

# Register HEIF opener with Pillow so Image.open supports .heic / .heif seamlessly
pillow_heif.register_heif_opener()


@dataclass
class ConversionOptions:
    target_format: str = "JPG"  # "JPG", "JPEG", "PNG"
    quality: int = 98           # 1-100 (for JPEG/JPG)
    subsampling_444: bool = True # False = 4:2:0, True = 4:4:4
    keep_icc_profile: bool = True
    keep_exif: bool = True
    output_dir: Optional[Path] = None


@dataclass
class ConversionResult:
    source_file: Path
    output_file: Optional[Path]
    success: bool
    error: Optional[str] = None


def convert_single_image(source_path: Path, options: ConversionOptions) -> ConversionResult:
    """
    Converts a single HEIC/HEIF image to JPEG or PNG with maximum visual quality.
    Preserves ICC Color Profile and EXIF metadata whenever possible.
    """
    try:
        source_path = Path(source_path)
        if not source_path.exists():
            return ConversionResult(source_path, None, False, "File does not exist")

        ext = options.target_format.lower()
        if ext == "jpg":
            file_ext = ".jpg"
            save_format = "JPEG"
        elif ext == "jpeg":
            file_ext = ".jpeg"
            save_format = "JPEG"
        elif ext == "png":
            file_ext = ".png"
            save_format = "PNG"
        else:
            file_ext = f".{ext}"
            save_format = options.target_format.upper()

        # Determine output location
        if options.output_dir:
            out_dir = Path(options.output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            output_path = out_dir / f"{source_path.stem}{file_ext}"
        else:
            output_path = source_path.parent / f"{source_path.stem}{file_ext}"

        with Image.open(source_path) as img:
            save_kwargs = {}

            # Handle ICC Color Profile (Critical for Apple Display P3 gamut)
            if options.keep_icc_profile:
                icc_profile = img.info.get("icc_profile")
                if icc_profile:
                    save_kwargs["icc_profile"] = icc_profile

            # Handle EXIF metadata & orientation
            if options.keep_exif:
                exif_data = img.info.get("exif")
                if exif_data:
                    save_kwargs["exif"] = exif_data

            if save_format == "JPEG":
                # JPEG does not support RGBA or palette transparency
                if img.mode in ("RGBA", "LA", "P"):
                    # Create white background for alpha channel
                    rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    rgb_img.paste(img, mask=img.split()[-1])
                    img = rgb_img
                elif img.mode != "RGB":
                    img = img.convert("RGB")

                # Quality and chroma subsampling settings
                save_kwargs["quality"] = max(1, min(100, options.quality))
                save_kwargs["optimize"] = True
                
                # 0 = 4:4:4 (no subsampling, pristine color edges)
                # 2 = 4:2:0 (standard JPEG subsampling)
                save_kwargs["subsampling"] = 0 if options.subsampling_444 else 2

                img.save(output_path, format="JPEG", **save_kwargs)

            elif save_format == "PNG":
                # PNG is lossless, preserves alpha if present
                save_kwargs["optimize"] = True
                save_kwargs["compress_level"] = 6
                img.save(output_path, format="PNG", **save_kwargs)

            else:
                img.save(output_path, format=save_format, **save_kwargs)

        return ConversionResult(source_path, output_path, True, None)

    except Exception as e:
        return ConversionResult(source_path, None, False, str(e))


def batch_convert(
    files: List[Path],
    options: ConversionOptions,
    progress_callback: Optional[Callable[[int, int, ConversionResult], None]] = None,
    max_workers: Optional[int] = None
) -> List[ConversionResult]:
    """
    Converts a batch of HEIC files concurrently using thread/worker pool.
    Calls progress_callback(completed_count, total_count, result) after each file.
    """
    total = len(files)
    results: List[ConversionResult] = []
    completed = 0

    if total == 0:
        return results

    if max_workers is None:
        max_workers = min(32, (os.cpu_count() or 1) + 4)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(convert_single_image, f, options): f for f in files
        }

        for future in as_completed(future_to_file):
            completed += 1
            try:
                res = future.result()
            except Exception as e:
                res = ConversionResult(future_to_file[future], None, False, str(e))

            results.append(res)
            if progress_callback:
                progress_callback(completed, total, res)

    return results
