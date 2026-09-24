import sys
import argparse
from pathlib import Path
from core.converter import ConversionOptions, batch_convert, convert_single_image


def run_cli(args):
    files = []
    for target in args.inputs:
        p = Path(target)
        if p.is_dir():
            files.extend([f for f in p.iterdir() if f.is_file() and f.suffix.lower() in (".heic", ".heif")])
        elif p.is_file() and p.suffix.lower() in (".heic", ".heif"):
            files.append(p)

    if not files:
        print("[!] No HEIC/HEIF files found in the provided arguments.")
        sys.exit(1)

    out_dir = Path(args.output) if args.output else None
    options = ConversionOptions(
        target_format=args.format.upper(),
        quality=args.quality,
        subsampling_444=not args.no_444,
        keep_icc_profile=not args.no_icc,
        keep_exif=not args.no_exif,
        output_dir=out_dir
    )

    print(f"[*] Converting {len(files)} file(s) to {options.target_format}...")
    print(f"[*] Settings: Quality={options.quality}, Subsampling444={options.subsampling_444}, ICC={options.keep_icc_profile}")

    def on_progress(done, total, res):
        status = "OK" if res.success else f"FAIL ({res.error})"
        print(f"[{done}/{total}] {res.source_file.name} -> {status}")

    results = batch_convert(files, options, progress_callback=on_progress)
    success_count = sum(1 for r in results if r.success)
    print(f"\n[✓] Done! {success_count}/{len(files)} converted successfully.")


def main():
    parser = argparse.ArgumentParser(
        description="Lossless HEIC to JPG/JPEG/PNG Converter with Display P3 & 4:4:4 Chroma Subsampling support."
    )
    parser.add_argument("inputs", nargs="*", help="HEIC files or directories to convert (Leave empty to open GUI)")
    parser.add_argument("-f", "--format", choices=["jpg", "jpeg", "png", "JPG", "JPEG", "PNG"], default="jpg", help="Target format (default: jpg)")
    parser.add_argument("-q", "--quality", type=int, default=98, help="JPEG quality 1-100 (default: 98)")
    parser.add_argument("-o", "--output", help="Output directory")
    parser.add_argument("--no-444", action="store_true", help="Disable 4:4:4 chroma subsampling (uses standard 4:2:0)")
    parser.add_argument("--no-icc", action="store_true", help="Do not preserve ICC color profile")
    parser.add_argument("--no-exif", action="store_true", help="Do not preserve EXIF metadata")

    args = parser.parse_args()

    if args.inputs:
        run_cli(args)
    else:
        try:
            from ui.app import main as run_gui
            run_gui()
        except ModuleNotFoundError as e:
            if "tkinter" in str(e):
                print("\n[!] Hata: Tkinter kütüphanesi eksik.")
                print("[!] Linux için çözüm:")
                print("    sudo apt install python3-tk  (veya python3.14-tk)\n")
            raise


if __name__ == "__main__":
    main()
