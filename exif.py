import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import piexif
from PIL import Image, ImageTk
import os
import json
import tkintermapview
import sys

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


from datetime import datetime
from tkcalendar import DateEntry  # Library DatePicker Modern

class ExifEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("EXIF Editor By Gobel")
        self.root.geometry("1000x720")
        self.root.minsize(950, 650)

        self.file_path = None
        self.exif_dict = None

        # Set Window Icon
        try:
            icon_path = resource_path("logo.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
            else:
                png_path = resource_path("logo.png")
                if os.path.exists(png_path):
                    img_icon = ImageTk.PhotoImage(file=png_path)
                    self.root.iconphoto(True, img_icon)
        except Exception:
            pass

        self.entries = {}
        
        # Tema GUI Modern agar serasi dengan DatePicker
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('.', font=('Segoe UI', 10))
        self.style.configure('TNotebook.Tab', font=('Segoe UI', 10, 'bold'), padding=[10, 4])
        self.style.configure('TLabelframe.Label', font=('Segoe UI', 10, 'bold'), foreground='#0078D4')

        self._create_widgets()


    def load_templates(self):
        self.templates = {}
        try:
            # If device_templates.json does not exist in CWD, look for it in resource_path
            path = "device_templates.json"
            if not os.path.exists(path):
                alt_path = resource_path("device_templates.json")
                if os.path.exists(alt_path):
                    path = alt_path
            with open(path, "r", encoding="utf-8") as f:
                self.templates = json.load(f)
            self.cb_template["values"] = list(self.templates.keys())
        except Exception:
            pass

    def apply_template(self, event=None):
        tpl_name = self.template_var.get()
        if tpl_name not in self.templates:
            return
        tpl = self.templates[tpl_name]
        
        def _set_val(key, val):
            if key in self.entries:
                self.entries[key].delete(0, tk.END)
                self.entries[key].insert(0, str(val))
                
        for k, v in tpl.items():
            _set_val(k, v)

    def save_template(self):
        # Minta nama template dari user
        tpl_name = simpledialog.askstring("Simpan Template", "Masukkan nama template baru:", parent=self.root)
        if not tpl_name:
            return
            
        tpl_name = tpl_name.strip()
        if not tpl_name:
            return
            
        if tpl_name in self.templates:
            if not messagebox.askyesno("Konfirmasi", f"Template '{tpl_name}' sudah ada. Timpa?"):
                return
                
        # Kumpulkan nilai dari seluruh entri saat ini
        new_tpl = {}
        for key, ent in self.entries.items():
            val = ent.get().strip()
            if val:
                new_tpl[key] = val
                
        if not new_tpl:
            messagebox.showwarning("Peringatan", "Tidak ada data untuk disimpan!")
            return
            
        self.templates[tpl_name] = new_tpl
        
        # Simpan ke device_templates.json
        try:
            with open("device_templates.json", "w", encoding="utf-8") as f:
                json.dump(self.templates, f, indent=4)
            self.load_templates()
            self.template_var.set(tpl_name)
            messagebox.showinfo("Sukses", f"Template '{tpl_name}' berhasil disimpan!")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal menyimpan template: {e}")

    # ------------------------------------------------------------------ UI
    def _create_widgets(self):
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill=tk.X)

        # Row 1: File Actions (Responsive/Flexible packing)
        row1 = ttk.Frame(top)
        row1.pack(fill=tk.X, pady=(0, 5))

        self.btn_open = ttk.Button(row1, text="Buka Foto (JPEG)", command=self.open_image)
        self.btn_open.pack(side=tk.LEFT, padx=5)

        self.lbl_file = ttk.Label(row1, text="Tidak ada file yang dipilih",
                                  font=("Segoe UI", 10, "italic"))
        self.lbl_file.pack(side=tk.LEFT, padx=10)

        self.btn_save = ttk.Button(row1, text="Simpan Perubahan EXIF",
                                   command=self.save_exif, state=tk.DISABLED)
        self.btn_save.pack(side=tk.RIGHT, padx=5)

        self.btn_save_as = ttk.Button(row1, text="Simpan Sebagai...",
                                      command=self.save_exif_as, state=tk.DISABLED)
        self.btn_save_as.pack(side=tk.RIGHT, padx=5)

        # Row 2: Template Controls
        row2 = ttk.Frame(top)
        row2.pack(fill=tk.X, pady=(5, 0))

        self.lbl_template = ttk.Label(row2, text="Template Perangkat:")
        self.lbl_template.pack(side=tk.LEFT, padx=(5, 5))

        self.template_var = tk.StringVar()
        self.cb_template = ttk.Combobox(row2, textvariable=self.template_var, state="readonly", width=25)
        self.cb_template.pack(side=tk.LEFT, padx=5)
        self.cb_template.bind("<<ComboboxSelected>>", self.apply_template)

        self.btn_save_template = ttk.Button(row2, text="Simpan ke Template", command=self.save_template)
        self.btn_save_template.pack(side=tk.LEFT, padx=5)

        self.load_templates()

        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        # Left - preview
        self.left_panel = ttk.LabelFrame(main, text=" Preview Foto ", padding=10, width=260)
        self.left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))
        self.left_panel.pack_propagate(False)

        self.lbl_image = ttk.Label(self.left_panel, text="Belum ada gambar", anchor="center")
        self.lbl_image.pack(fill=tk.BOTH, expand=True)

        # Right - tabs
        self.notebook = ttk.Notebook(main)
        self.notebook.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.tab_general = self._make_tab("Perangkat & Sistem")
        self.tab_time = self._make_tab("Waktu & Zona")
        self.tab_camera = self._make_tab("Pengaturan Kamera")
        self.tab_lens = self._make_tab("Lensa & Sensor")
        self.tab_gps = self._make_tab("Geolokasi (GPS)")

        self._setup_general_tab()
        self._setup_time_tab()
        self._setup_camera_tab()
        self._setup_lens_tab()
        self._setup_gps_tab()

    def _make_tab(self, title):
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text=title)
        return frame

    @staticmethod
    def _add_fields(parent, fields, entries):
        for row, (label_text, key) in enumerate(fields):
            ttk.Label(parent, text=label_text).grid(row=row, column=0,
                                                     sticky=tk.W, pady=4, padx=5)
            ent = ttk.Entry(parent, width=45)
            ent.grid(row=row, column=1, sticky="ew", pady=4, padx=5)
            entries[key] = ent
        parent.columnconfigure(1, weight=1)

    # -- Tab definitions ------------------------------------------------
    def _setup_general_tab(self):
        fields = [
            ("Make (Produsen)", "make"),
            ("Model Perangkat", "model"),
            ("Software", "software"),
            ("Host Computer", "host"),
            ("Orientation (1-8)", "orientation"),
            ("XResolution", "xresolution"),
            ("YResolution", "yresolution"),
            ("Resolution Unit (2=inches,3=cm)", "resolution_unit"),
            ("Pixel X Dimension", "pixel_x"),
            ("Pixel Y Dimension", "pixel_y"),
        ]
        self._add_fields(self.tab_general, fields, self.entries)

    def _setup_time_tab(self):
        """Tab Waktu yang didesain ulang dengan DatePicker Kalender + Time Spinner"""
        self.tab_time.columnconfigure(1, weight=1)
        
        time_fields = ["datetime", "datetime_orig", "datetime_digitized"]
        labels = ["DateTime (Sistem)", "DateTimeOriginal (Foto Diambil)", "DateTimeDigitized (Digitalisasi)"]
        
        self.time_widgets = {}
        
        for idx, (key, label_text) in enumerate(zip(time_fields, labels)):
            frame_row = ttk.LabelFrame(self.tab_time, text=f" {label_text} ", padding=10)
            frame_row.grid(row=idx, column=0, columnspan=2, sticky="ew", pady=8, padx=5)
            frame_row.columnconfigure(1, weight=1)
            
            # Kalender Picker Widget (DateEntry)
            ttk.Label(frame_row, text="Tanggal:").grid(row=0, column=0, sticky=tk.W, padx=5)
            date_picker = DateEntry(frame_row, width=15, background='darkblue', foreground='white', 
                                    borderwidth=2, date_pattern='yyyy-mm-dd')
            date_picker.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
            
            # Waktu Kontrol (Jam, Menit, Detik) menggunakan Spinbox
            time_subframe = ttk.Frame(frame_row)
            time_subframe.grid(row=0, column=2, sticky=tk.E, padx=5)
            
            ttk.Label(time_subframe, text="Jam:").pack(side=tk.LEFT, padx=2)
            spin_h = ttk.Spinbox(time_subframe, from_=0, to=23, width=3, format="%02.0f")
            spin_h.pack(side=tk.LEFT, padx=2)
            
            ttk.Label(time_subframe, text=":").pack(side=tk.LEFT)
            spin_m = ttk.Spinbox(time_subframe, from_=0, to=59, width=3, format="%02.0f")
            spin_m.pack(side=tk.LEFT, padx=2)
            
            ttk.Label(time_subframe, text=":").pack(side=tk.LEFT)
            spin_s = ttk.Spinbox(time_subframe, from_=0, to=59, width=3, format="%02.0f")
            spin_s.pack(side=tk.LEFT, padx=2)
            
            # Simpan referensi objek kontrol
            self.time_widgets[key] = {
                "date": date_picker,
                "hour": spin_h,
                "minute": spin_m,
                "second": spin_s
            }

        # Kolom Offset Sisa Waktu & Sub-detik (Tetap menggunakan Form Entry Biasa)
        extra_fields_frame = ttk.Frame(self.tab_time)
        extra_fields_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)
        
        extra_fields = [
            ("OffsetTime (e.g. +07:00)", "offset_time"),
            ("OffsetTimeOriginal", "offset_time_orig"),
            ("OffsetTimeDigitized", "offset_time_dig"),
            ("SubSecTimeOriginal", "subsec_orig"),
            ("SubSecTimeDigitized", "subsec_dig"),
        ]
        self._add_fields(extra_fields_frame, extra_fields, self.entries)

    def _setup_camera_tab(self):
        fields = [
            ("ExposureTime (e.g. 1/132)", "exposure_time"),
            ("FNumber (e.g. 1.5)", "fnumber"),
            ("ExposureProgram (0-8)", "exposure_program"),
            ("ISO Speed", "iso"),
            ("ShutterSpeedValue (APEX)", "shutter_speed"),
            ("ApertureValue (APEX)", "aperture_value"),
            ("BrightnessValue", "brightness"),
            ("ExposureBiasValue", "exposure_bias"),
            ("MeteringMode (0-6,255)", "metering_mode"),
            ("Flash (0-95)", "flash"),
            ("FocalLength (mm)", "focal_length"),
            ("FocalLengthIn35mmFilm", "focal_35mm"),
        ]
        self._add_fields(self.tab_camera, fields, self.entries)

    def _setup_lens_tab(self):
        fields = [
            ("Lens Make", "lens_make"),
            ("Lens Model", "lens_model"),
            ("LensSpecification (min_f,max_f,min_fn,max_fn)", "lens_spec"),
            ("SensingMethod (1-8)", "sensing_method"),
            ("SceneType (1=direct)", "scene_type"),
            ("ExposureMode (0=Auto,1=Manual,2=Bracket)", "exposure_mode"),
            ("WhiteBalance (0=Auto,1=Manual)", "white_balance"),
            ("SceneCaptureType (0-3)", "scene_capture"),
        ]
        self._add_fields(self.tab_lens, fields, self.entries)

    def _setup_gps_tab(self):
        left_frame = ttk.Frame(self.tab_gps)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, expand=False, padx=5, pady=5)
        
        right_frame = ttk.Frame(self.tab_gps)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        fields = [
            ("GPS Latitude Ref (N/S)", "gps_lat_ref"),
            ("GPS Latitude (Desimal)", "gps_lat"),
            ("GPS Longitude Ref (E/W)", "gps_lon_ref"),
            ("GPS Longitude (Desimal)", "gps_lon"),
            ("GPS Altitude Ref (0=sea,1=below)", "gps_alt_ref"),
            ("GPS Altitude (Meter)", "gps_alt"),
            ("GPS TimeStamp (HH:MM:SS)", "gps_time"),
            ("GPS DateStamp (YYYY:MM:DD)", "gps_date"),
            ("GPS Speed Ref (K/M/N)", "gps_speed_ref"),
            ("GPS Speed", "gps_speed"),
            ("GPS Img Direction Ref (T/M)", "gps_imgdir_ref"),
            ("GPS Img Direction", "gps_imgdir"),
            ("GPS H Positioning Error", "gps_hpe"),
        ]
        self._add_fields(left_frame, fields, self.entries)
        
        # Add maps
        self.map_widget = tkintermapview.TkinterMapView(right_frame, width=400, height=300, corner_radius=0)
        self.map_widget.pack(fill=tk.BOTH, expand=True)
        self.map_widget.set_position(-7.250445, 112.768845) # Default: Surabaya
        self.map_widget.set_zoom(12)
        
        # Click event to select location
        self.map_widget.add_left_click_map_command(self.map_click_event)
        
        # Marker storage
        self.current_marker = None

    def map_click_event(self, coords):
        lat, lon = coords
        
        # Clear existing marker
        if self.current_marker:
            self.current_marker.delete()
            
        self.current_marker = self.map_widget.set_marker(lat, lon, text="Selected Location")
        
        # Update Lat/Lon fields
        if "gps_lat" in self.entries:
            self.entries["gps_lat"].delete(0, tk.END)
            self.entries["gps_lat"].insert(0, f"{abs(lat):.7f}")
        
        if "gps_lat_ref" in self.entries:
            self.entries["gps_lat_ref"].delete(0, tk.END)
            self.entries["gps_lat_ref"].insert(0, "N" if lat >= 0 else "S")
            
        if "gps_lon" in self.entries:
            self.entries["gps_lon"].delete(0, tk.END)
            self.entries["gps_lon"].insert(0, f"{abs(lon):.7f}")
            
        if "gps_lon_ref" in self.entries:
            self.entries["gps_lon_ref"].delete(0, tk.END)
            self.entries["gps_lon_ref"].insert(0, "E" if lon >= 0 else "W")

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _rational_to_float(val):
        if isinstance(val, tuple) and len(val) == 2:
            return val[0] / val[1] if val[1] != 0 else float(val[0])
        return float(val)

    @staticmethod
    def _srational_to_float(val):
        if isinstance(val, tuple) and len(val) == 2:
            num, den = val
            if isinstance(num, int) and num > 0x7FFFFFFF:
                num = num - 0x100000000
            if isinstance(den, int) and den > 0x7FFFFFFF:
                den = den - 0x100000000
            return num / den if den != 0 else float(num)
        return float(val)

    @staticmethod
    def _parse_gps_coord(data):
        try:
            deg = data[0][0] / data[0][1]
            minute = data[1][0] / data[1][1]
            sec = data[2][0] / data[2][1]
            return deg + (minute / 60.0) + (sec / 3600.0)
        except Exception:
            return 0.0

    @staticmethod
    def _float_to_rational(value, precision=1000000):
        return (int(round(abs(value) * precision)), precision)

    @staticmethod
    def _float_to_srational(value, precision=1000000):
        return (int(round(value * precision)), precision)

    @staticmethod
    def _decimal_to_dms(decimal_value):
        decimal_value = abs(decimal_value)
        deg = int(decimal_value)
        md = (decimal_value - deg) * 60
        minute = int(md)
        sec = int(round((md - minute) * 60 * 10000))
        return ((deg, 1), (minute, 1), (sec, 10000))

    # ------------------------------------------------------------------ open
    def open_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg")])
        if not path:
            return

        self.file_path = path
        self.lbl_file.config(text=os.path.basename(path))
        self.btn_save.config(state=tk.NORMAL)
        self.btn_save_as.config(state=tk.NORMAL)

        img = Image.open(path)
        img.thumbnail((240, 320))
        img_tk = ImageTk.PhotoImage(img)
        self.lbl_image.config(image=img_tk, text="")
        self.lbl_image.image = img_tk

        try:
            self.exif_dict = piexif.load(path)
            self._populate()
        except Exception as exc:
            messagebox.showerror("Error", f"Gagal membaca EXIF:\n{exc}")

    # ------------------------------------------------------------------ populate
    def _populate(self):
        # Reset form entry teks
        for ent in self.entries.values():
            ent.delete(0, tk.END)

        if not self.exif_dict:
            return

        zeroth = self.exif_dict.get("0th", {})
        exif = self.exif_dict.get("Exif", {})
        gps = self.exif_dict.get("GPS", {})

        def _str(ifd, tag):
            val = ifd.get(tag)
            if val is None:
                return None
            if isinstance(val, bytes):
                return val.decode("utf-8", "ignore").strip("\x00")
            return str(val)

        def _ins(key, value):
            if value is not None and key in self.entries:
                self.entries[key].insert(0, str(value))

        def _parse_and_fill_date_widget(key, date_str):
            """Fungsi pembantu untuk mem-parsing 'YYYY:MM:DD HH:MM:SS' ke widget Kalender & Spinner"""
            if not date_str:
                return
            try:
                # Mengubah pemisah koordinat waktu EXIF ':' menjadi format standar datetime
                dt = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                self.time_widgets[key]["date"].set_date(dt.date())
                
                self.time_widgets[key]["hour"].set(f"{dt.hour:02d}")
                self.time_widgets[key]["minute"].set(f"{dt.minute:02d}")
                self.time_widgets[key]["second"].set(f"{dt.second:02d}")
            except Exception:
                pass

        # -- Perangkat & Sistem (0th) --
        _ins("make", _str(zeroth, piexif.ImageIFD.Make))
        _ins("model", _str(zeroth, piexif.ImageIFD.Model))
        _ins("software", _str(zeroth, piexif.ImageIFD.Software))
        if piexif.ImageIFD.HostComputer in zeroth:
            _ins("host", _str(zeroth, piexif.ImageIFD.HostComputer))
        if piexif.ImageIFD.Orientation in zeroth:
            _ins("orientation", zeroth[piexif.ImageIFD.Orientation])
        if piexif.ImageIFD.XResolution in zeroth:
            _ins("xresolution", self._rational_to_float(zeroth[piexif.ImageIFD.XResolution]))
        if piexif.ImageIFD.YResolution in zeroth:
            _ins("yresolution", self._rational_to_float(zeroth[piexif.ImageIFD.YResolution]))
        if piexif.ImageIFD.ResolutionUnit in zeroth:
            _ins("resolution_unit", zeroth[piexif.ImageIFD.ResolutionUnit])
        if piexif.ExifIFD.PixelXDimension in exif:
            _ins("pixel_x", exif[piexif.ExifIFD.PixelXDimension])
        if piexif.ExifIFD.PixelYDimension in exif:
            _ins("pixel_y", exif[piexif.ExifIFD.PixelYDimension])

        # -- Populasikan data Kalender Waktu & Zona --
        _parse_and_fill_date_widget("datetime", _str(zeroth, piexif.ImageIFD.DateTime))
        _parse_and_fill_date_widget("datetime_orig", _str(exif, piexif.ExifIFD.DateTimeOriginal))
        _parse_and_fill_date_widget("datetime_digitized", _str(exif, piexif.ExifIFD.DateTimeDigitized))
        
        _ins("offset_time", _str(exif, piexif.ExifIFD.OffsetTime))
        _ins("offset_time_orig", _str(exif, piexif.ExifIFD.OffsetTimeOriginal))
        _ins("offset_time_dig", _str(exif, piexif.ExifIFD.OffsetTimeDigitized))
        _ins("subsec_orig", _str(exif, piexif.ExifIFD.SubSecTimeOriginal))
        _ins("subsec_dig", _str(exif, piexif.ExifIFD.SubSecTimeDigitized))

        # -- Pengaturan Kamera --
        if piexif.ExifIFD.ExposureTime in exif:
            val = exif[piexif.ExifIFD.ExposureTime]
            _ins("exposure_time", f"{val[0]}/{val[1]}" if val[1] != 0 else str(val[0]))
        if piexif.ExifIFD.FNumber in exif:
            _ins("fnumber", self._rational_to_float(exif[piexif.ExifIFD.FNumber]))
        if piexif.ExifIFD.ExposureProgram in exif:
            _ins("exposure_program", exif[piexif.ExifIFD.ExposureProgram])
        if piexif.ExifIFD.ISOSpeedRatings in exif:
            _ins("iso", exif[piexif.ExifIFD.ISOSpeedRatings])
        if piexif.ExifIFD.ShutterSpeedValue in exif:
            _ins("shutter_speed", self._srational_to_float(exif[piexif.ExifIFD.ShutterSpeedValue]))
        if piexif.ExifIFD.ApertureValue in exif:
            _ins("aperture_value", self._rational_to_float(exif[piexif.ExifIFD.ApertureValue]))
        if piexif.ExifIFD.BrightnessValue in exif:
            _ins("brightness", self._srational_to_float(exif[piexif.ExifIFD.BrightnessValue]))
        if piexif.ExifIFD.ExposureBiasValue in exif:
            _ins("exposure_bias", self._srational_to_float(exif[piexif.ExifIFD.ExposureBiasValue]))
        if piexif.ExifIFD.MeteringMode in exif:
            _ins("metering_mode", exif[piexif.ExifIFD.MeteringMode])
        if piexif.ExifIFD.Flash in exif:
            _ins("flash", exif[piexif.ExifIFD.Flash])
        if piexif.ExifIFD.FocalLength in exif:
            _ins("focal_length", self._rational_to_float(exif[piexif.ExifIFD.FocalLength]))
        if piexif.ExifIFD.FocalLengthIn35mmFilm in exif:
            _ins("focal_35mm", exif[piexif.ExifIFD.FocalLengthIn35mmFilm])

        # -- Lensa & Sensor --
        _ins("lens_make", _str(exif, piexif.ExifIFD.LensMake))
        _ins("lens_model", _str(exif, piexif.ExifIFD.LensModel))
        if piexif.ExifIFD.LensSpecification in exif:
            spec = exif[piexif.ExifIFD.LensSpecification]
            parts = [str(self._rational_to_float(r)) for r in spec]
            _ins("lens_spec", ",".join(parts))
        if piexif.ExifIFD.SensingMethod in exif:
            _ins("sensing_method", exif[piexif.ExifIFD.SensingMethod])
        if piexif.ExifIFD.SceneType in exif:
            val = exif[piexif.ExifIFD.SceneType]
            if isinstance(val, bytes) and len(val) == 1:
                _ins("scene_type", val[0])
            else:
                _ins("scene_type", val)
        if piexif.ExifIFD.ExposureMode in exif:
            _ins("exposure_mode", exif[piexif.ExifIFD.ExposureMode])
        if piexif.ExifIFD.WhiteBalance in exif:
            _ins("white_balance", exif[piexif.ExifIFD.WhiteBalance])
        if piexif.ExifIFD.SceneCaptureType in exif:
            _ins("scene_capture", exif[piexif.ExifIFD.SceneCaptureType])

        # -- GPS --
        if piexif.GPSIFD.GPSLatitudeRef in gps:
            _ins("gps_lat_ref", gps[piexif.GPSIFD.GPSLatitudeRef].decode("utf-8", "ignore"))
        if piexif.GPSIFD.GPSLatitude in gps:
            _ins("gps_lat", f"{self._parse_gps_coord(gps[piexif.GPSIFD.GPSLatitude]):.7f}")
        if piexif.GPSIFD.GPSLongitudeRef in gps:
            _ins("gps_lon_ref", gps[piexif.GPSIFD.GPSLongitudeRef].decode("utf-8", "ignore"))
        if piexif.GPSIFD.GPSLongitude in gps:
            _ins("gps_lon", f"{self._parse_gps_coord(gps[piexif.GPSIFD.GPSLongitude]):.7f}")
        if piexif.GPSIFD.GPSAltitudeRef in gps:
            _ins("gps_alt_ref", gps[piexif.GPSIFD.GPSAltitudeRef])
        if piexif.GPSIFD.GPSAltitude in gps:
            _ins("gps_alt", self._rational_to_float(gps[piexif.GPSIFD.GPSAltitude]))
        if piexif.GPSIFD.GPSTimeStamp in gps:
            ts = gps[piexif.GPSIFD.GPSTimeStamp]
            hh = int(self._rational_to_float(ts[0]))
            mm = int(self._rational_to_float(ts[1]))
            ss = int(self._rational_to_float(ts[2]))
            _ins("gps_time", f"{hh:02d}:{mm:02d}:{ss:02d}")
        if piexif.GPSIFD.GPSDateStamp in gps:
            _ins("gps_date", gps[piexif.GPSIFD.GPSDateStamp].decode("utf-8", "ignore"))
        if piexif.GPSIFD.GPSSpeedRef in gps:
            _ins("gps_speed_ref", gps[piexif.GPSIFD.GPSSpeedRef].decode("utf-8", "ignore"))
        if piexif.GPSIFD.GPSSpeed in gps:
            _ins("gps_speed", self._rational_to_float(gps[piexif.GPSIFD.GPSSpeed]))
        if piexif.GPSIFD.GPSImgDirectionRef in gps:
            _ins("gps_imgdir_ref", gps[piexif.GPSIFD.GPSImgDirectionRef].decode("utf-8", "ignore"))
        if piexif.GPSIFD.GPSImgDirection in gps:
            _ins("gps_imgdir", self._rational_to_float(gps[piexif.GPSIFD.GPSImgDirection]))
        if piexif.GPSIFD.GPSHPositioningError in gps:
            _ins("gps_hpe", self._rational_to_float(gps[piexif.GPSIFD.GPSHPositioningError]))
            
        # Update map pin
        try:
            if "gps_lat" in self.entries and "gps_lon" in self.entries:
                lat_str = self.entries["gps_lat"].get()
                lon_str = self.entries["gps_lon"].get()
                if lat_str and lon_str:
                    lat_val = float(lat_str)
                    lon_val = float(lon_str)
                    
                    if self.entries.get("gps_lat_ref") and self.entries["gps_lat_ref"].get().upper() == "S":
                        lat_val = -lat_val
                    if self.entries.get("gps_lon_ref") and self.entries["gps_lon_ref"].get().upper() == "W":
                        lon_val = -lon_val
                        
                    if getattr(self, "current_marker", None):
                        self.current_marker.delete()
                    
                    self.current_marker = self.map_widget.set_marker(lat_val, lon_val, text="Photo Location")
                    self.map_widget.set_position(lat_val, lon_val)
                    self.map_widget.set_zoom(15)
        except Exception:
            pass

    # ------------------------------------------------------------------ save
    def _collect_exif(self):
        if not self.exif_dict:
            return

        zeroth = self.exif_dict.setdefault("0th", {})
        exif = self.exif_dict.setdefault("Exif", {})
        gps = self.exif_dict.setdefault("GPS", {})

        def _get(key):
            if key in self.entries:
                return self.entries[key].get().strip()
            return ""

        def _get_compiled_date(key):
            """Menggabungkan nilai dari DateEntry dan Jam Spinbox ke format EXIF 'YYYY:MM:DD HH:MM:SS'"""
            try:
                date_part = self.time_widgets[key]["date"].get_date().strftime("%Y:%m:%d")
                h = int(self.time_widgets[key]["hour"].get())
                m = int(self.time_widgets[key]["minute"].get())
                s = int(self.time_widgets[key]["second"].get())
                return f"{date_part} {h:02d}:{m:02d}:{s:02d}"
            except Exception:
                return ""

        # -- Perangkat & Sistem --
        zeroth[piexif.ImageIFD.Make] = _get("make").encode("utf-8")
        zeroth[piexif.ImageIFD.Model] = _get("model").encode("utf-8")
        zeroth[piexif.ImageIFD.Software] = _get("software").encode("utf-8")
        zeroth[piexif.ImageIFD.HostComputer] = _get("host").encode("utf-8")

        val = _get("orientation")
        if val.isdigit() and 1 <= int(val) <= 8:
            zeroth[piexif.ImageIFD.Orientation] = int(val)

        for field_key, tag in [("xresolution", piexif.ImageIFD.XResolution),
                                ("yresolution", piexif.ImageIFD.YResolution)]:
            try:
                v = float(_get(field_key))
                zeroth[tag] = self._float_to_rational(v)
            except ValueError:
                pass

        val = _get("resolution_unit")
        if val.isdigit() and int(val) in (2, 3):
            zeroth[piexif.ImageIFD.ResolutionUnit] = int(val)

        for field_key, tag in [("pixel_x", piexif.ExifIFD.PixelXDimension),
                                ("pixel_y", piexif.ExifIFD.PixelYDimension)]:
            val = _get(field_key)
            if val.isdigit():
                exif[tag] = int(val)

        # -- Mengemas data dari DatePicker & Spinner ke EXIF --
        zeroth[piexif.ImageIFD.DateTime] = _get_compiled_date("datetime").encode("utf-8")
        exif[piexif.ExifIFD.DateTimeOriginal] = _get_compiled_date("datetime_orig").encode("utf-8")
        exif[piexif.ExifIFD.DateTimeDigitized] = _get_compiled_date("datetime_digitized").encode("utf-8")
        
        exif[piexif.ExifIFD.OffsetTime] = _get("offset_time").encode("utf-8")
        exif[piexif.ExifIFD.OffsetTimeOriginal] = _get("offset_time_orig").encode("utf-8")
        exif[piexif.ExifIFD.OffsetTimeDigitized] = _get("offset_time_dig").encode("utf-8")
        exif[piexif.ExifIFD.SubSecTimeOriginal] = _get("subsec_orig").encode("utf-8")
        exif[piexif.ExifIFD.SubSecTimeDigitized] = _get("subsec_dig").encode("utf-8")

        # -- Pengaturan Kamera --
        val = _get("exposure_time")
        if "/" in val:
            parts = val.split("/")
            try:
                exif[piexif.ExifIFD.ExposureTime] = (int(parts[0]), int(parts[1]))
            except ValueError:
                pass
        elif val:
            try:
                exif[piexif.ExifIFD.ExposureTime] = self._float_to_rational(float(val))
            except ValueError:
                pass

        try:
            exif[piexif.ExifIFD.FNumber] = self._float_to_rational(float(_get("fnumber")))
        except ValueError:
            pass

        val = _get("exposure_program")
        if val.isdigit():
            exif[piexif.ExifIFD.ExposureProgram] = int(val)

        val = _get("iso")
        if val.isdigit():
            exif[piexif.ExifIFD.ISOSpeedRatings] = int(val)

        try:
            exif[piexif.ExifIFD.ShutterSpeedValue] = self._float_to_srational(float(_get("shutter_speed")))
        except ValueError:
            pass

        try:
            exif[piexif.ExifIFD.ApertureValue] = self._float_to_rational(float(_get("aperture_value")))
        except ValueError:
            pass

        try:
            exif[piexif.ExifIFD.BrightnessValue] = self._float_to_srational(float(_get("brightness")))
        except ValueError:
            pass

        try:
            exif[piexif.ExifIFD.ExposureBiasValue] = self._float_to_srational(float(_get("exposure_bias")))
        except ValueError:
            pass

        val = _get("metering_mode")
        if val.isdigit():
            exif[piexif.ExifIFD.MeteringMode] = int(val)

        val = _get("flash")
        if val.isdigit():
            exif[piexif.ExifIFD.Flash] = int(val)

        try:
            exif[piexif.ExifIFD.FocalLength] = self._float_to_rational(float(_get("focal_length")))
        except ValueError:
            pass

        val = _get("focal_35mm")
        if val.isdigit():
            exif[piexif.ExifIFD.FocalLengthIn35mmFilm] = int(val)

        # -- Lensa & Sensor --
        exif[piexif.ExifIFD.LensMake] = _get("lens_make").encode("utf-8")
        exif[piexif.ExifIFD.LensModel] = _get("lens_model").encode("utf-8")

        val = _get("lens_spec")
        if val:
            parts = val.split(",")
            if len(parts) == 4:
                try:
                    spec = tuple(self._float_to_rational(float(p.strip())) for p in parts)
                    exif[piexif.ExifIFD.LensSpecification] = spec
                except ValueError:
                    pass

        val = _get("sensing_method")
        if val.isdigit():
            exif[piexif.ExifIFD.SensingMethod] = int(val)

        val = _get("scene_type")
        if val.isdigit():
            exif[piexif.ExifIFD.SceneType] = bytes([int(val)])

        val = _get("exposure_mode")
        if val.isdigit():
            exif[piexif.ExifIFD.ExposureMode] = int(val)

        val = _get("white_balance")
        if val.isdigit():
            exif[piexif.ExifIFD.WhiteBalance] = int(val)

        val = _get("scene_capture")
        if val.isdigit():
            exif[piexif.ExifIFD.SceneCaptureType] = int(val)

        # -- GPS --
        val = _get("gps_lat_ref")
        if val.upper() in ("N", "S"):
            gps[piexif.GPSIFD.GPSLatitudeRef] = val.upper().encode("utf-8")

        try:
            gps[piexif.GPSIFD.GPSLatitude] = self._decimal_to_dms(float(_get("gps_lat")))
        except ValueError:
            pass

        val = _get("gps_lon_ref")
        if val.upper() in ("E", "W"):
            gps[piexif.GPSIFD.GPSLongitudeRef] = val.upper().encode("utf-8")

        try:
            gps[piexif.GPSIFD.GPSLongitude] = self._decimal_to_dms(float(_get("gps_lon")))
        except ValueError:
            pass

        val = _get("gps_alt_ref")
        if val.isdigit() and int(val) in (0, 1):
            gps[piexif.GPSIFD.GPSAltitudeRef] = int(val)

        try:
            alt = float(_get("gps_alt"))
            gps[piexif.GPSIFD.GPSAltitude] = (int(round(alt * 100)), 100)
        except ValueError:
            pass

        val = _get("gps_time")
        if ":" in val:
            parts = val.split(":")
            if len(parts) == 3:
                try:
                    gps[piexif.GPSIFD.GPSTimeStamp] = (
                        (int(parts[0]), 1),
                        (int(parts[1]), 1),
                        (int(parts[2]), 1),
                    )
                except ValueError:
                    pass

        val = _get("gps_date")
        if val:
            gps[piexif.GPSIFD.GPSDateStamp] = val.encode("utf-8")

        val = _get("gps_speed_ref")
        if val.upper() in ("K", "M", "N"):
            gps[piexif.GPSIFD.GPSSpeedRef] = val.upper().encode("utf-8")

        try:
            gps[piexif.GPSIFD.GPSSpeed] = self._float_to_rational(float(_get("gps_speed")))
        except ValueError:
            pass

        val = _get("gps_imgdir_ref")
        if val.upper() in ("T", "M"):
            gps[piexif.GPSIFD.GPSImgDirectionRef] = val.upper().encode("utf-8")

        try:
            gps[piexif.GPSIFD.GPSImgDirection] = self._float_to_rational(float(_get("gps_imgdir")))
        except ValueError:
            pass

        try:
            gps[piexif.GPSIFD.GPSHPositioningError] = self._float_to_rational(float(_get("gps_hpe")))
        except ValueError:
            pass

    def _write_exif(self, target_path):
        self._collect_exif()
        exif_bytes = piexif.dump(self.exif_dict)
        piexif.insert(exif_bytes, target_path)

    def save_exif(self):
        if not self.file_path or not self.exif_dict:
            return
        try:
            self._write_exif(self.file_path)
            messagebox.showinfo("Sukses", "Data EXIF berhasil diperbarui!")
        except Exception as exc:
            messagebox.showerror("Error", f"Gagal menyimpan data EXIF:\n{exc}")

    def save_exif_as(self):
        if not self.file_path or not self.exif_dict:
            return
        target = filedialog.asksaveasfilename(
            defaultextension=".jpg",
            filetypes=[("JPEG files", "*.jpg *.jpeg")],
            initialfile=os.path.basename(self.file_path),
        )
        if not target:
            return
        try:
            img = Image.open(self.file_path)
            img.save(target, "JPEG", quality=95)
            self._write_exif(target)
            messagebox.showinfo("Sukses", f"File disimpan ke:\n{target}")
        except Exception as exc:
            messagebox.showerror("Error", f"Gagal menyimpan file:\n{exc}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ExifEditorApp(root)
    root.mainloop()