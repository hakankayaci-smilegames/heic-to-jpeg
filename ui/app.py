import os
import sys
import threading
from pathlib import Path
from typing import List, Optional
import customtkinter as ctk
from tkinter import filedialog, messagebox

from core.converter import (
    ConversionOptions,
    ConversionResult,
    batch_convert,
)
from core.optimizer import (
    OptimizeOptions,
    OptimizeResult,
    batch_optimize,
)

# Text Localization Map (TR / EN)
LOCALIZATION = {
    "tr": {
        "app_title": "HEIC & Medya Araçları Pro",
        "tab_converter": "🔄 Format Dönüştürücü",
        "tab_optimizer": "🗜️ Boyut Optimize Edici",
        
        # Converter Tab
        "conv_subtitle": "Apple Display P3, EXIF ve 4:4:4 Chroma Subsampling desteği",
        "select_files": "📁 Dosya(lar) Seç",
        "select_folder": "📂 Klasör Seç",
        "no_files_selected": "Henüz dosya seçilmedi",
        "files_selected": "{} adet dosya seçildi",
        "output_format": "Çıktı Formatı",
        "quality_format_label": "{} Kalitesi: %{}",
        "subsampling_label": "Ultra Renk Kalitesi (4:4:4 Chroma Subsampling)",
        "subsampling_tip": "Renk kenarlarındaki sıkıştırma bulanıklığını önler.",
        "icc_exif_label": "ICC Renk Profili (Display P3) & EXIF Koru",
        "same_as_source": "Kaynak dosya ile aynı klasöre kaydet",
        "custom_folder": "Özel Klasör Seç",
        "start_conversion": "🚀 Dönüştürmeyi Başlat",
        "converting": "Dönüştürülüyor... ({}/{})",
        "completed": "Tamamlandı! ({} başarılı, {} hatalı)",
        "open_folder": "📂 Klasörü Aç",
        "error_no_files": "Lütfen önce en az bir dosya seçin!",
        "png_info": "PNG kayıpsız (lossless) formattır. Kalite kaybı yaşanmaz.",
        "status_ready": "İşleme hazır",

        # Optimizer Tab
        "opt_subtitle": "HEIC, JPG, PNG ve WEBP görsellerinin boyutunu küçültür",
        "compression_level": "Sıkıştırma Seviyesi (Kalite: %{})",
        "tradeoff_light": "🟢 Hafif Sıkıştırma: Görsel fark yok, %100 keskinlik. (~%20-%35 boyut tasarrufu)",
        "tradeoff_balanced": "🟡 Dengeli: Web ve paylaşım için ideal. Fark gözle algılanmaz. (~%40-%60 boyut tasarrufu)",
        "tradeoff_aggressive": "🔴 Agresif: Maksimum küçültme. Çok ince detaylarda hafif sıkıştırma izi olabilir. (~%70-%80 boyut tasarrufu)",
        "opt_save_suffix": "Kaynak klasöre '_optimized' takısıyla kaydet",
        "start_optimization": "⚡ Boyutları Optimize Et",
        "optimizing": "Optimize ediliyor... ({}/{})",
        "opt_completed": "Tamamlandı! {} -> {} (%{:.1f} tasarruf)",
    },
    "en": {
        "app_title": "HEIC & Media Tools Pro",
        "tab_converter": "🔄 Format Converter",
        "tab_optimizer": "🗜️ Size Optimizer",
        
        # Converter Tab
        "conv_subtitle": "Apple Display P3, EXIF, and 4:4:4 Chroma Subsampling support",
        "select_files": "📁 Select File(s)",
        "select_folder": "📂 Select Folder",
        "no_files_selected": "No files selected yet",
        "files_selected": "{} file(s) selected",
        "output_format": "Output Format",
        "quality_format_label": "{} Quality: {}%",
        "subsampling_label": "Ultra Color Quality (4:4:4 Chroma Subsampling)",
        "subsampling_tip": "Eliminates compression blur on fine color edges.",
        "icc_exif_label": "Preserve ICC Profile (Display P3) & EXIF",
        "same_as_source": "Save in the same folder as source",
        "custom_folder": "Choose Custom Folder",
        "start_conversion": "🚀 Start Conversion",
        "converting": "Converting... ({}/{})",
        "completed": "Completed! ({} succeeded, {} failed)",
        "open_folder": "📂 Open Output Folder",
        "error_no_files": "Please select at least one file first!",
        "png_info": "PNG is inherently lossless. Zero quality loss.",
        "status_ready": "Ready to process",

        # Optimizer Tab
        "opt_subtitle": "Reduces file size of HEIC, JPG, PNG, and WEBP images",
        "compression_level": "Compression Level (Quality: {}%)",
        "tradeoff_light": "🟢 Light Compression: Visually lossless, 100% sharpness. (~20%-35% size reduction)",
        "tradeoff_balanced": "🟡 Balanced: Ideal for web & sharing. Imperceptible difference. (~40%-60% size reduction)",
        "tradeoff_aggressive": "🔴 Aggressive: Maximum space saving. Slight compression artifacts on fine details. (~70%-80% size reduction)",
        "opt_save_suffix": "Save in source folder with '_optimized' suffix",
        "start_optimization": "⚡ Optimize File Sizes",
        "optimizing": "Optimizing... ({}/{})",
        "opt_completed": "Completed! {} -> {} ({:.1f}% saved)",
    }
}


def format_bytes(bytes_num: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_num < 1024.0:
            return f"{bytes_num:.1f} {unit}"
        bytes_num /= 1024.0
    return f"{bytes_num:.1f} TB"


class HEICConverterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.current_lang = "tr"
        
        # Converter State
        self.conv_files: List[Path] = []
        self.conv_custom_output_dir: Optional[Path] = None
        self.conv_last_output_dir: Optional[Path] = None
        self.is_converting = False

        # Optimizer State
        self.opt_files: List[Path] = []
        self.opt_custom_output_dir: Optional[Path] = None
        self.opt_last_output_dir: Optional[Path] = None
        self.is_optimizing = False

        # Window Configuration
        self.title("HEIC & Media Tools Pro")
        self.geometry("680x760")
        self.minsize(620, 720)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self._build_header()
        self._build_tabs()
        self._update_language(self.current_lang)

    def _t(self, key: str, *args) -> str:
        text = LOCALIZATION.get(self.current_lang, {}).get(key, key)
        if args:
            return text.format(*args)
        return text

    def _build_header(self):
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=20, pady=(15, 5))

        self.header_title = ctk.CTkLabel(
            top_bar, text="", font=ctk.CTkFont(size=20, weight="bold")
        )
        self.header_title.pack(side="left")

        # Language Selector
        self.lang_btn = ctk.CTkSegmentedButton(
            top_bar, values=["TR", "EN"], command=self._on_lang_changed, width=90
        )
        self.lang_btn.set("TR")
        self.lang_btn.pack(side="right")

    def _build_tabs(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=(5, 15))

        self.tab_conv = self.tabview.add("Converter")
        self.tab_opt = self.tabview.add("Optimizer")

        self._build_converter_ui(self.tab_conv)
        self._build_optimizer_ui(self.tab_opt)

    # =========================================================================
    # TAB 1: FORMAT CONVERTER
    # =========================================================================
    def _build_converter_ui(self, parent):
        self.lbl_conv_sub = ctk.CTkLabel(
            parent, text="", font=ctk.CTkFont(size=12), text_color="gray70"
        )
        self.lbl_conv_sub.pack(anchor="w", padx=10, pady=(5, 8))

        # File Select Box
        card_file = ctk.CTkFrame(parent)
        card_file.pack(fill="x", padx=10, pady=6)

        btn_box = ctk.CTkFrame(card_file, fg_color="transparent")
        btn_box.pack(fill="x", padx=12, pady=(12, 6))

        self.btn_conv_files = ctk.CTkButton(
            btn_box, text="", command=self._choose_conv_files, height=36
        )
        self.btn_conv_files.pack(side="left", expand=True, fill="x", padx=(0, 6))

        self.btn_conv_folder = ctk.CTkButton(
            btn_box, text="", command=self._choose_conv_folder, height=36, fg_color="#34495e", hover_color="#2c3e50"
        )
        self.btn_conv_folder.pack(side="right", expand=True, fill="x", padx=(6, 0))

        self.lbl_conv_summary = ctk.CTkLabel(
            card_file, text="", font=ctk.CTkFont(size=13, weight="bold")
        )
        self.lbl_conv_summary.pack(anchor="w", padx=12, pady=(0, 12))

        # Format & Quality Box
        card_settings = ctk.CTkFrame(parent)
        card_settings.pack(fill="x", padx=10, pady=6)

        # Format row
        fmt_row = ctk.CTkFrame(card_settings, fg_color="transparent")
        fmt_row.pack(fill="x", padx=12, pady=(12, 8))

        self.lbl_conv_format = ctk.CTkLabel(fmt_row, text="", font=ctk.CTkFont(weight="bold"))
        self.lbl_conv_format.pack(side="left")

        self.seg_conv_format = ctk.CTkSegmentedButton(
            fmt_row, values=["JPG", "JPEG", "PNG"], command=self._on_conv_format_changed
        )
        self.seg_conv_format.set("JPG")
        self.seg_conv_format.pack(side="right")

        # Quality slider frame
        self.frame_conv_quality = ctk.CTkFrame(card_settings, fg_color="transparent")
        self.frame_conv_quality.pack(fill="x", padx=12, pady=(0, 6))

        self.lbl_conv_quality = ctk.CTkLabel(self.frame_conv_quality, text="")
        self.lbl_conv_quality.pack(anchor="w")

        self.slider_conv_quality = ctk.CTkSlider(
            self.frame_conv_quality, from_=50, to=100, number_of_steps=50, command=self._on_conv_quality_changed
        )
        self.slider_conv_quality.set(98)
        self.slider_conv_quality.pack(fill="x", pady=(4, 0))

        # PNG info label
        self.lbl_conv_png_info = ctk.CTkLabel(
            card_settings, text="", text_color="#3498db", font=ctk.CTkFont(size=12)
        )

        # Subsampling toggle
        self.cb_conv_subsampling = ctk.CTkCheckBox(
            card_settings, text="", onvalue=True, offvalue=False
        )
        self.cb_conv_subsampling.select()
        self.cb_conv_subsampling.pack(anchor="w", padx=12, pady=6)

        # ICC & EXIF toggle
        self.cb_conv_icc_exif = ctk.CTkCheckBox(
            card_settings, text="", onvalue=True, offvalue=False
        )
        self.cb_conv_icc_exif.select()
        self.cb_conv_icc_exif.pack(anchor="w", padx=12, pady=(0, 12))

        # Output Box
        card_out = ctk.CTkFrame(parent)
        card_out.pack(fill="x", padx=10, pady=6)

        self.cb_conv_same_out = ctk.CTkCheckBox(
            card_out, text="", command=self._on_conv_same_out_toggled, onvalue=True, offvalue=False
        )
        self.cb_conv_same_out.select()
        self.cb_conv_same_out.pack(anchor="w", padx=12, pady=(12, 6))

        self.btn_conv_custom_out = ctk.CTkButton(
            card_out, text="", command=self._choose_conv_custom_out, height=30, fg_color="#4a5568", hover_color="#2d3748"
        )
        self.btn_conv_custom_out.pack(anchor="w", padx=12, pady=(0, 12))
        self.btn_conv_custom_out.configure(state="disabled")

        # Action & Progress
        card_action = ctk.CTkFrame(parent, fg_color="transparent")
        card_action.pack(fill="x", padx=10, pady=(10, 5))

        self.btn_conv_start = ctk.CTkButton(
            card_action, text="", command=self._start_conversion_thread, height=42, font=ctk.CTkFont(size=14, weight="bold")
        )
        self.btn_conv_start.pack(fill="x", pady=(0, 8))

        self.prog_conv = ctk.CTkProgressBar(card_action)
        self.prog_conv.set(0)
        self.prog_conv.pack(fill="x", pady=(0, 6))

        self.lbl_conv_status = ctk.CTkLabel(
            card_action, text="", text_color="gray70", font=ctk.CTkFont(size=12)
        )
        self.lbl_conv_status.pack()

        self.btn_conv_open_dir = ctk.CTkButton(
            card_action, text="", command=lambda: self._open_dir(self.conv_last_output_dir), height=32, fg_color="#27ae60", hover_color="#219653"
        )

    # =========================================================================
    # TAB 2: SIZE OPTIMIZER
    # =========================================================================
    def _build_optimizer_ui(self, parent):
        self.lbl_opt_sub = ctk.CTkLabel(
            parent, text="", font=ctk.CTkFont(size=12), text_color="gray70"
        )
        self.lbl_opt_sub.pack(anchor="w", padx=10, pady=(5, 8))

        # File Select Box
        card_file = ctk.CTkFrame(parent)
        card_file.pack(fill="x", padx=10, pady=6)

        btn_box = ctk.CTkFrame(card_file, fg_color="transparent")
        btn_box.pack(fill="x", padx=12, pady=(12, 6))

        self.btn_opt_files = ctk.CTkButton(
            btn_box, text="", command=self._choose_opt_files, height=36
        )
        self.btn_opt_files.pack(side="left", expand=True, fill="x", padx=(0, 6))

        self.btn_opt_folder = ctk.CTkButton(
            btn_box, text="", command=self._choose_opt_folder, height=36, fg_color="#34495e", hover_color="#2c3e50"
        )
        self.btn_opt_folder.pack(side="right", expand=True, fill="x", padx=(6, 0))

        self.lbl_opt_summary = ctk.CTkLabel(
            card_file, text="", font=ctk.CTkFont(size=13, weight="bold")
        )
        self.lbl_opt_summary.pack(anchor="w", padx=12, pady=(0, 12))

        # Slider & Tradeoff Box
        card_slider = ctk.CTkFrame(parent)
        card_slider.pack(fill="x", padx=10, pady=6)

        self.lbl_opt_slider_val = ctk.CTkLabel(
            card_slider, text="", font=ctk.CTkFont(weight="bold")
        )
        self.lbl_opt_slider_val.pack(anchor="w", padx=12, pady=(12, 4))

        self.slider_opt = ctk.CTkSlider(
            card_slider, from_=50, to=95, number_of_steps=45, command=self._on_opt_slider_changed
        )
        self.slider_opt.set(80)
        self.slider_opt.pack(fill="x", padx=12, pady=(0, 8))

        # Dynamic Tradeoff description badge
        self.lbl_opt_tradeoff = ctk.CTkLabel(
            card_slider, text="", font=ctk.CTkFont(size=12), justify="left", wraplength=560
        )
        self.lbl_opt_tradeoff.pack(anchor="w", padx=12, pady=(0, 12))

        # Output Box
        card_out = ctk.CTkFrame(parent)
        card_out.pack(fill="x", padx=10, pady=6)

        self.cb_opt_suffix = ctk.CTkCheckBox(
            card_out, text="", command=self._on_opt_same_out_toggled, onvalue=True, offvalue=False
        )
        self.cb_opt_suffix.select()
        self.cb_opt_suffix.pack(anchor="w", padx=12, pady=(12, 6))

        self.btn_opt_custom_out = ctk.CTkButton(
            card_out, text="", command=self._choose_opt_custom_out, height=30, fg_color="#4a5568", hover_color="#2d3748"
        )
        self.btn_opt_custom_out.pack(anchor="w", padx=12, pady=(0, 12))
        self.btn_opt_custom_out.configure(state="disabled")

        # Action & Progress
        card_action = ctk.CTkFrame(parent, fg_color="transparent")
        card_action.pack(fill="x", padx=10, pady=(10, 5))

        self.btn_opt_start = ctk.CTkButton(
            card_action, text="", command=self._start_optimization_thread, height=42, font=ctk.CTkFont(size=14, weight="bold"), fg_color="#8e44ad", hover_color="#732d91"
        )
        self.btn_opt_start.pack(fill="x", pady=(0, 8))

        self.prog_opt = ctk.CTkProgressBar(card_action)
        self.prog_opt.set(0)
        self.prog_opt.pack(fill="x", pady=(0, 6))

        self.lbl_opt_status = ctk.CTkLabel(
            card_action, text="", text_color="gray70", font=ctk.CTkFont(size=12)
        )
        self.lbl_opt_status.pack()

        self.btn_opt_open_dir = ctk.CTkButton(
            card_action, text="", command=lambda: self._open_dir(self.opt_last_output_dir), height=32, fg_color="#27ae60", hover_color="#219653"
        )

    # =========================================================================
    # LANGUAGE SYNC
    # =========================================================================
    def _update_language(self, lang: str):
        self.current_lang = lang.lower()
        self.header_title.configure(text=self._t("app_title"))
        self.tabview._segmented_button._buttons_dict["Converter"].configure(text=self._t("tab_converter"))
        self.tabview._segmented_button._buttons_dict["Optimizer"].configure(text=self._t("tab_optimizer"))

        # Converter Translations
        self.lbl_conv_sub.configure(text=self._t("conv_subtitle"))
        self.btn_conv_files.configure(text=self._t("select_files"))
        self.btn_conv_folder.configure(text=self._t("select_folder"))
        self.lbl_conv_format.configure(text=self._t("output_format"))
        self.cb_conv_subsampling.configure(text=self._t("subsampling_label"))
        self.cb_conv_icc_exif.configure(text=self._t("icc_exif_label"))
        self.cb_conv_same_out.configure(text=self._t("same_as_source"))
        self.btn_conv_start.configure(text=self._t("start_conversion"))
        self.btn_conv_open_dir.configure(text=self._t("open_folder"))
        self.lbl_conv_png_info.configure(text=self._t("png_info"))

        if not self.conv_custom_output_dir:
            self.btn_conv_custom_out.configure(text=self._t("custom_folder"))
        else:
            self.btn_conv_custom_out.configure(text=f"📂 {self.conv_custom_output_dir.name}")

        self._on_conv_quality_changed(self.slider_conv_quality.get())
        self._update_conv_file_summary()
        if not self.is_converting:
            self.lbl_conv_status.configure(text=self._t("status_ready"))

        # Optimizer Translations
        self.lbl_opt_sub.configure(text=self._t("opt_subtitle"))
        self.btn_opt_files.configure(text=self._t("select_files"))
        self.btn_opt_folder.configure(text=self._t("select_folder"))
        self.cb_opt_suffix.configure(text=self._t("opt_save_suffix"))
        self.btn_opt_start.configure(text=self._t("start_optimization"))
        self.btn_opt_open_dir.configure(text=self._t("open_folder"))

        if not self.opt_custom_output_dir:
            self.btn_opt_custom_out.configure(text=self._t("custom_folder"))
        else:
            self.btn_opt_custom_out.configure(text=f"📂 {self.opt_custom_output_dir.name}")

        self._on_opt_slider_changed(self.slider_opt.get())
        self._update_opt_file_summary()
        if not self.is_optimizing:
            self.lbl_opt_status.configure(text=self._t("status_ready"))

    def _on_lang_changed(self, val: str):
        self._update_language(val)

    # =========================================================================
    # CONVERTER LOGIC & EVENTS
    # =========================================================================
    def _on_conv_format_changed(self, fmt_val: str):
        if fmt_val == "PNG":
            self.frame_conv_quality.pack_forget()
            self.cb_conv_subsampling.pack_forget()
            self.lbl_conv_png_info.pack(padx=12, pady=(0, 10))
        else:
            self.lbl_conv_png_info.pack_forget()
            self.frame_conv_quality.pack(fill="x", padx=12, pady=(0, 6))
            self.cb_conv_subsampling.pack(anchor="w", padx=12, pady=6)
        self._on_conv_quality_changed(self.slider_conv_quality.get())

    def _on_conv_quality_changed(self, val):
        current_fmt = self.seg_conv_format.get()
        # Dynamically displays "JPG Quality" or "JPEG Quality"
        self.lbl_conv_quality.configure(text=self._t("quality_format_label", current_fmt, int(val)))

    def _on_conv_same_out_toggled(self):
        if self.cb_conv_same_out.get():
            self.btn_conv_custom_out.configure(state="disabled")
        else:
            self.btn_conv_custom_out.configure(state="normal")

    def _choose_conv_files(self):
        files = filedialog.askopenfilenames(
            title=self._t("select_files"),
            filetypes=[("HEIC / HEIF Images", "*.heic *.HEIC *.heif *.HEIF"), ("All Files", "*.*")]
        )
        if files:
            self.conv_files = [Path(f) for f in files]
            self._update_conv_file_summary()

    def _choose_conv_folder(self):
        folder = filedialog.askdirectory(title=self._t("select_folder"))
        if folder:
            p = Path(folder)
            heic_files = [
                f for f in p.iterdir()
                if f.is_file() and f.suffix.lower() in (".heic", ".heif")
            ]
            self.conv_files = sorted(heic_files)
            self._update_conv_file_summary()

    def _choose_conv_custom_out(self):
        folder = filedialog.askdirectory(title=self._t("custom_folder"))
        if folder:
            self.conv_custom_output_dir = Path(folder)
            self.btn_conv_custom_out.configure(text=f"📂 {self.conv_custom_output_dir.name}")

    def _update_conv_file_summary(self):
        count = len(self.conv_files)
        if count == 0:
            self.lbl_conv_summary.configure(text=self._t("no_files_selected"), text_color="gray70")
        else:
            self.lbl_conv_summary.configure(
                text=self._t("files_selected", count), text_color="#2ecc71"
            )

    def _start_conversion_thread(self):
        if not self.conv_files:
            messagebox.showwarning("Uyarı / Warning", self._t("error_no_files"))
            return

        if self.is_converting:
            return

        self.is_converting = True
        self.btn_conv_start.configure(state="disabled")
        self.btn_conv_files.configure(state="disabled")
        self.btn_conv_folder.configure(state="disabled")
        self.btn_conv_open_dir.pack_forget()
        self.prog_conv.set(0)

        out_dir = self.conv_custom_output_dir if not self.cb_conv_same_out.get() else None
        options = ConversionOptions(
            target_format=self.seg_conv_format.get(),
            quality=int(self.slider_conv_quality.get()),
            subsampling_444=bool(self.cb_conv_subsampling.get()),
            keep_icc_profile=bool(self.cb_conv_icc_exif.get()),
            keep_exif=bool(self.cb_conv_icc_exif.get()),
            output_dir=out_dir
        )

        threading.Thread(target=self._run_conversion, args=(options,), daemon=True).start()

    def _run_conversion(self, options: ConversionOptions):
        files = self.conv_files
        total = len(files)
        succeeded = 0
        failed = 0

        def on_prog(done, total_count, res: ConversionResult):
            nonlocal succeeded, failed
            if res.success:
                succeeded += 1
                if res.output_file:
                    self.conv_last_output_dir = res.output_file.parent
            else:
                failed += 1
            p = done / total_count
            self.after(0, lambda: self._update_conv_progress(done, total_count, p))

        batch_convert(files, options, progress_callback=on_prog)
        self.after(0, lambda: self._conv_finished(succeeded, failed))

    def _update_conv_progress(self, done, total, progress):
        self.prog_conv.set(progress)
        self.lbl_conv_status.configure(text=self._t("converting", done, total))

    def _conv_finished(self, succeeded: int, failed: int):
        self.is_converting = False
        self.btn_conv_start.configure(state="normal")
        self.btn_conv_files.configure(state="normal")
        self.btn_conv_folder.configure(state="normal")
        self.lbl_conv_status.configure(text=self._t("completed", succeeded, failed))
        if self.conv_last_output_dir and self.conv_last_output_dir.exists():
            self.btn_conv_open_dir.pack(fill="x", pady=(8, 0))

    # =========================================================================
    # OPTIMIZER LOGIC & EVENTS
    # =========================================================================
    def _on_opt_slider_changed(self, val):
        q = int(val)
        self.lbl_opt_slider_val.configure(text=self._t("compression_level", q))
        if q >= 85:
            self.lbl_opt_tradeoff.configure(text=self._t("tradeoff_light"), text_color="#2ecc71")
        elif q >= 70:
            self.lbl_opt_tradeoff.configure(text=self._t("tradeoff_balanced"), text_color="#f1c40f")
        else:
            self.lbl_opt_tradeoff.configure(text=self._t("tradeoff_aggressive"), text_color="#e74c3c")

    def _on_opt_same_out_toggled(self):
        if self.cb_opt_suffix.get():
            self.btn_opt_custom_out.configure(state="disabled")
        else:
            self.btn_opt_custom_out.configure(state="normal")

    def _choose_opt_files(self):
        files = filedialog.askopenfilenames(
            title=self._t("select_files"),
            filetypes=[
                ("Image Files", "*.heic *.HEIC *.heif *.HEIF *.jpg *.jpeg *.JPG *.JPEG *.png *.PNG *.webp *.WEBP"),
                ("All Files", "*.*")
            ]
        )
        if files:
            self.opt_files = [Path(f) for f in files]
            self._update_opt_file_summary()

    def _choose_opt_folder(self):
        folder = filedialog.askdirectory(title=self._t("select_folder"))
        if folder:
            p = Path(folder)
            valid_exts = {".heic", ".heif", ".jpg", ".jpeg", ".png", ".webp"}
            found = [f for f in p.iterdir() if f.is_file() and f.suffix.lower() in valid_exts]
            self.opt_files = sorted(found)
            self._update_opt_file_summary()

    def _choose_opt_custom_out(self):
        folder = filedialog.askdirectory(title=self._t("custom_folder"))
        if folder:
            self.opt_custom_output_dir = Path(folder)
            self.btn_opt_custom_out.configure(text=f"📂 {self.opt_custom_output_dir.name}")

    def _update_opt_file_summary(self):
        count = len(self.opt_files)
        if count == 0:
            self.lbl_opt_summary.configure(text=self._t("no_files_selected"), text_color="gray70")
        else:
            self.lbl_opt_summary.configure(
                text=self._t("files_selected", count), text_color="#9b59b6"
            )

    def _start_optimization_thread(self):
        if not self.opt_files:
            messagebox.showwarning("Uyarı / Warning", self._t("error_no_files"))
            return

        if self.is_optimizing:
            return

        self.is_optimizing = True
        self.btn_opt_start.configure(state="disabled")
        self.btn_opt_files.configure(state="disabled")
        self.btn_opt_folder.configure(state="disabled")
        self.btn_opt_open_dir.pack_forget()
        self.prog_opt.set(0)

        out_dir = self.opt_custom_output_dir if not self.cb_opt_suffix.get() else None
        options = OptimizeOptions(
            quality=int(self.slider_opt.get()),
            keep_exif=True,
            keep_icc=True,
            output_dir=out_dir,
            output_suffix="_optimized"
        )

        threading.Thread(target=self._run_optimization, args=(options,), daemon=True).start()

    def _run_optimization(self, options: OptimizeOptions):
        files = self.opt_files
        total = len(files)
        total_orig_bytes = 0
        total_opt_bytes = 0

        def on_prog(done, total_count, res: OptimizeResult):
            nonlocal total_orig_bytes, total_opt_bytes
            if res.success:
                total_orig_bytes += res.original_bytes
                total_opt_bytes += res.optimized_bytes
                if res.output_file:
                    self.opt_last_output_dir = res.output_file.parent
            p = done / total_count
            self.after(0, lambda: self._update_opt_progress(done, total_count, p))

        batch_optimize(files, options, progress_callback=on_prog)
        self.after(0, lambda: self._opt_finished(total_orig_bytes, total_opt_bytes))

    def _update_opt_progress(self, done, total, progress):
        self.prog_opt.set(progress)
        self.lbl_opt_status.configure(text=self._t("optimizing", done, total))

    def _opt_finished(self, orig_bytes: int, opt_bytes: int):
        self.is_optimizing = False
        self.btn_opt_start.configure(state="normal")
        self.btn_opt_files.configure(state="normal")
        self.btn_opt_folder.configure(state="normal")

        saved_pct = 0.0
        if orig_bytes > 0:
            saved_pct = max(0.0, (orig_bytes - opt_bytes) / orig_bytes * 100)

        self.lbl_opt_status.configure(
            text=self._t("opt_completed", format_bytes(orig_bytes), format_bytes(opt_bytes), saved_pct)
        )
        if self.opt_last_output_dir and self.opt_last_output_dir.exists():
            self.btn_opt_open_dir.pack(fill="x", pady=(8, 0))

    def _open_dir(self, directory: Optional[Path]):
        if not directory:
            return
        path = str(directory)
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            os.system(f'open "{path}"')
        else:
            os.system(f'xdg-open "{path}"')


def main():
    app = HEICConverterApp()
    app.mainloop()


if __name__ == "__main__":
    main()
