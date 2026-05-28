# ==============================================================================
# Paint Mixer Pro v6.5 Final
# Copyright (C) 2024-2026 Giuseppe Luongo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# ==============================================================================
import sys
import os
import json
import math
import re
import traceback
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QListWidget,
    QListWidgetItem, QSlider, QHBoxLayout, QFileDialog, QMessageBox, QScrollArea,
    QProgressDialog, QComboBox, QGroupBox
)
from PyQt5.QtGui import QColor, QPixmap, QIcon, QImage
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal

from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000

PIL_AVAILABLE = False
try:
    from PIL import Image, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    print("Avviso: Pillow non trovato.")

SCIPY_AVAILABLE = False
try:
    from scipy.optimize import minimize
    SCIPY_AVAILABLE = True
except ImportError:
    print("Avviso: scipy non trovato.")

CONFIG_FILE = "config.json"
DEFAULT_WHEEL = "cwheel06.gif"

MODEL_EMPIRICO = "Empirico (sottrattivo ponderato)"
MODEL_KUBELKA_MUNK = "Kubelka-Munk (scientifico)"

KS_MAX = 30.0


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def setup_exception_hook():
    def excepthook(exc_type, exc_value, exc_tb):
        tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        print(f"ERRORE CRITICO:\n{tb_text}")
        try:
            with open("error_log.txt", "w", encoding="utf-8") as f:
                f.write(tb_text)
        except Exception:
            pass
        sys.exit(1)
    sys.excepthook = excepthook


def _calc_support_info(hex_color):
    c = QColor(hex_color)
    r_n = c.red() / 255.0
    g_n = c.green() / 255.0
    b_n = c.blue() / 255.0
    try:
        rgb_obj = sRGBColor(r_n, g_n, b_n)
        lab = convert_color(rgb_obj, LabColor)
    except Exception:
        lab = None
    R_avg = (r_n + g_n + b_n) / 3.0
    return {"hex": hex_color, "lab": lab, "R": R_avg, "rgb": (r_n, g_n, b_n)}


# ==============================================================================
# DATABASE SUPPORTI
# ==============================================================================
SUPPORTI_HEX = {
    "Arches Cold Press 300gsm": "#F2EBDD", "Arches Hot Press 300gsm": "#F5EEE2",
    "Arches Rough 300gsm": "#EFE7DB", "Fabriano Artistico Traditional White": "#F3ECE0",
    "Canson Heritage 100% cotone": "#F2EBDD", "Hahnemuhle Leonardo": "#F0E9DC",
    "Hahnemuhle William Turner": "#EDE5D8", "Hahnemuhle Cezanne": "#F2EBDD",
    "Saunders Waterford": "#F3ECE1", "Fabriano Artistico Extra White": "#FAF7F0",
    "Canson Montval": "#F8F5EE", "Hahnemuhle Britannia": "#F7F2EA",
    "Winsor & Newton Professional": "#F7F2EA", "Strathmore 400 Series": "#F9F6F0",
    "Fabriano Acquerello": "#F4EEE2", "Clairefontaine PaintON": "#F5F0E5",
    "Canson Mi-Teintes White": "#F8F8F8", "Canson Mi-Teintes Ivory": "#F2E2C0",
    "Canson Mi-Teintes Light Gray": "#D0D0D0", "Canson Mi-Teintes Dark Gray": "#585858",
    "Canson Mi-Teintes Black": "#1C1C1C", "Canson Mi-Teintes Sky Blue": "#A8BCC8",
    "Canson Mi-Teintes Beige": "#D8C090", "Canson Mi-Teintes Touch": "#E8DCC0",
    "Sennelier Pastel Card Cream": "#F0E0B8", "Sennelier Pastel Card Neutral Gray": "#787878",
    "Hahnemuhle Velour White": "#F8F8F8", "Hahnemuhle Velour Black": "#181818",
    "UART 800 grit": "#E0D0B0", "Art Spectrum Colourfix": "#D8C8A8",
    "Claessens Belgium Linen #13": "#E0CD9F", "Claessens Portrait Linen #66": "#E5D3A8",
    "Claessens Type 66 Fine": "#E4D2A6", "Masterpiece Mona Lisa": "#DCC898",
    "Artefix Lino Fine": "#E2D0A2", "Telero Lino Extra Fine": "#E5D3A8",
    "Raimundo Garcia Lino": "#DFCB9C", "Da Vinci Pro Linen": "#DEC99A",
    "Fredrix Cotton Duck": "#F2E8D0", "Centurion Deluxe": "#EBE0C0",
    "Masterpiece Raphael": "#EBE0B8", "Arteza Canvas cotone": "#EFE5C8",
    "Claessens Acrylic Universal #64": "#F5F2E8", "Universal Canvas": "#F8F8F8",
    "Blick Studio Cotton Canvas": "#F4F0E5", "Ampersand Gessobord": "#F4F0E5",
    "Ampersand Claybord": "#ECE0C0", "Ampersand Encausticbord": "#E0D0B0",
    "RayMar Linen Panel": "#E0CCB0", "Jackson's Black Gesso Panel": "#181818",
    "Fredrix Canvas Board": "#EBE0B8", "Masterpiece Canvas Panel": "#E5D3A8",
    "Arteza Canvas Board": "#EDE0C0", "Carta Bianca Standard": "#FFFFFF",
    "Fondo Grigio Medio": "#808080", "Fondo Grigio Scuro": "#404040",
    "Carta Nera": "#181818", "Tavolozza Vetro": "#F5F5F5", "Tavolozza Legno": "#806038"
}

SUPPORTI = {nome: _calc_support_info(hex_c) for nome, hex_c in SUPPORTI_HEX.items()}


# ==============================================================================
# PROCESSORE RUOTA COLORI
# ==============================================================================
class WheelImageProcessor:
    CACHE_DIR = "wheel_cache"
    
    @classmethod
    def ensure_cache_dir(cls):
        if not os.path.exists(cls.CACHE_DIR):
            try: os.makedirs(cls.CACHE_DIR)
            except Exception: pass
            
    @classmethod
    def get_cache_path(cls, original_path):
        cls.ensure_cache_dir()
        basename = os.path.basename(original_path)
        name, _ = os.path.splitext(basename)
        path_hash = abs(hash(original_path)) % (10 ** 8)
        return os.path.join(cls.CACHE_DIR, f"{name}_optimized_{path_hash}.png")
    
    @classmethod
    def needs_processing(cls, image_path):
        ext = os.path.splitext(image_path)[1].lower()
        if ext in ['.gif']: return True, "GIF (256 colori, posterizzato)"
        if ext in ['.jpg', '.jpeg']: return True, "JPG (artefatti compressione)"
        if ext in ['.png']:
            try:
                if PIL_AVAILABLE:
                    with Image.open(image_path) as img:
                        if img.mode == 'P': return True, "PNG-8 (palette limitata)"
            except Exception: pass
        return False, "OK (alta qualità)"
    
    @classmethod
    def process(cls, image_path):
        if not PIL_AVAILABLE: return image_path
        needs_proc, reason = cls.needs_processing(image_path)
        if not needs_proc: return image_path
        cache_path = cls.get_cache_path(image_path)
        if os.path.exists(cache_path):
            try:
                if os.path.getmtime(cache_path) > os.path.getmtime(image_path):
                    return cache_path
            except Exception: pass
        try:
            with Image.open(image_path) as img:
                if img.mode != 'RGB': img = img.convert('RGB')
                original_size = img.size
                if max(original_size) < 1000:
                    # FIX: Compatibilità Pillow >= 10.0
                    try: resample = Image.Resampling.BICUBIC
                    except AttributeError: resample = Image.BICUBIC
                    img = img.resize((original_size[0] * 2, original_size[1] * 2), resample)
                img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
                img.save(cache_path, 'PNG', optimize=False)
                return cache_path
        except Exception as e:
            print(f"[WheelProcessor] Errore: {e}")
            return image_path


# ==============================================================================
# DATA MANAGER
# ==============================================================================
class DataManager:
    def __init__(self):
        self.pigments = []
        self.config = {
            "color_wheel_image": DEFAULT_WHEEL,
            "selected_support": "Carta Bianca Standard",
            "mixing_model": MODEL_EMPIRICO
        }
        self.load_config()
        self.load_pigments()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.config.update(data)
                    if not os.path.exists(self.config.get("color_wheel_image", "")):
                        self.config["color_wheel_image"] = resource_path(DEFAULT_WHEEL)
            except Exception:
                self.config["color_wheel_image"] = resource_path(DEFAULT_WHEEL)
        else:
            self.config["color_wheel_image"] = resource_path(DEFAULT_WHEEL)

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
        except Exception: pass

    def load_pigments(self):
        path = resource_path("pigments.json")
        if not os.path.exists(path): raise FileNotFoundError(f"File mancante: {path}")
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)
                self.pigments = []
                seen_colors = set()
                for p in raw:
                    color_hex = p.get("colore", "#000000").strip().upper()
                    if color_hex in seen_colors:
                        print(f"[DataManager] Skip duplicato (colore): {p.get('nome')}")
                        continue
                    seen_colors.add(color_hex)
                    
                    nome = p.get("nome", "").strip()
                    family = re.sub(
                        r'\s*(PY|PR|PB|PG|PO|PV|PBk|PBr|PW)\d+[:.]?\d*\s*$',
                        '', nome, flags=re.IGNORECASE
                    ).strip().lower()
                    
                    self.pigments.append({
                        "nome": nome,
                        "codice": p.get("codice", "").strip(),
                        "colore": color_hex,
                        "tipo": p.get("tipo", "non specificato").strip(),
                        "opacita": float(p.get("opacita", 0.80)),
                        "k_factor": float(p.get("k_factor", 1.0)),
                        "s_factor": float(p.get("s_factor", 1.0)),
                        "resistenza_luce": p.get("resistenza_luce", "non nota").strip(),
                        "compatibilità": [c.strip() for c in p.get("compatibilità", [])],
                        "indice_tintoriale": p.get("indice_tintoriale", 5),
                        "famiglia": family
                    })
        except Exception as e:
            raise RuntimeError(f"Errore caricamento pigmenti: {e}")


# ==============================================================================
# MOTORE COLORI (UPGRADE K/S + LINEARIZZAZIONE GAMMA)
# ==============================================================================
class ColorEngine:
    @staticmethod
    def srgb_to_linear(c):
        c = max(0.0, min(1.0, c))
        if c <= 0.04045: return c / 12.92
        return math.pow((c + 0.055) / 1.055, 2.4)

    @staticmethod
    def linear_to_srgb(c):
        c = max(0.0, min(1.0, c))
        if c <= 0.0031308: return c * 12.92
        return 1.055 * math.pow(c, 1.0 / 2.4) - 0.055

    @staticmethod
    def get_opacity(tipo, opacita_reale=None):
        if opacita_reale is not None: return max(0.05, min(1.0, float(opacita_reale)))
        t = tipo.lower()
        if "opaco" in t: return 0.95
        if "semicoprente" in t: return 0.75
        if "semitrasparente" in t: return 0.55
        if "trasparente" in t: return 0.35
        return 0.80

    @staticmethod
    def rgb_to_lab(r, g, b):
        rgb_obj = sRGBColor(r / 255.0, g / 255.0, b / 255.0)
        return convert_color(rgb_obj, LabColor)

    @staticmethod
    def delta_e(lab1, lab2):
        return delta_e_cie2000(lab1, lab2)

    @staticmethod
    def get_hue(lab):
        hue = math.degrees(math.atan2(lab.lab_b, lab.lab_a))
        if hue < 0: hue += 360
        return hue

    @staticmethod
    def get_chroma(lab):
        return math.sqrt(lab.lab_a**2 + lab.lab_b**2)

    @staticmethod
    def mix_subtractive(weights, colors_rgb):
        total = sum(weights)
        if total == 0: return [1.0, 1.0, 1.0]
        brightness = sum(max(c) for c in colors_rgb) / len(colors_rgb) if colors_rgb else 1.0
        r_geo = g_geo = b_geo = 1.0
        for w, (r, g, b) in zip(weights, colors_rgb):
            if w <= 0: continue
            q = w / total
            r_geo *= max(r, 0.005) ** q
            g_geo *= max(g, 0.005) ** q
            b_geo *= max(b, 0.005) ** q
        r_lin = sum(w * c[0] for w, c in zip(weights, colors_rgb)) / total
        g_lin = sum(w * c[1] for w, c in zip(weights, colors_rgb)) / total
        b_lin = sum(w * c[2] for w, c in zip(weights, colors_rgb)) / total
        blend = min(1.0, max(0.0, (brightness - 0.5) * 2))
        r = r_geo * (1 - blend) + r_lin * blend
        g = g_geo * (1 - blend) + g_lin * blend
        b = b_geo * (1 - blend) + b_lin * blend
        return [r, g, b]

    @staticmethod
    def _effective_coverage(film_rgb_tuple, base_opacity):
        r, g, b = film_rgb_tuple
        if max(r, g, b) <= 1.0 and r <= 1.0: r, g, b = r*255, g*255, b*255
        film_brightness = (r + g + b) / 3.0
        op = base_opacity
        if film_brightness < 20: op = max(op, 0.98)
        elif film_brightness < 50 and op > 0.5: op = min(1.0, op + 0.25)
        elif film_brightness < 80 and op > 0.7: op = min(1.0, op + 0.15)
        if film_brightness > 220 and op > 0.8: op = min(1.0, op + 0.05)
        return max(0.0, min(1.0, op))

    @staticmethod
    def apply_support(rgb_tuple, support_hex, opacity):
        sup = QColor(support_hex)
        eff_op = ColorEngine._effective_coverage(rgb_tuple, opacity)
        r = int(rgb_tuple[0] * eff_op + sup.red() * (1 - eff_op))
        g = int(rgb_tuple[1] * eff_op + sup.green() * (1 - eff_op))
        b = int(rgb_tuple[2] * eff_op + sup.blue() * (1 - eff_op))
        return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))

    @staticmethod
    def _ks_to_reflectance(ks):
        ks = max(0.0, min(ks, KS_MAX))
        return 1.0 + ks - math.sqrt(ks * ks + 2.0 * ks)

    @staticmethod
    def mix_kubelka_munk(weights, colors_rgb, opacities, tint_strengths=None, k_factors=None, s_factors=None):
        if tint_strengths is None: tint_strengths = [1.0] * len(weights)
        if k_factors is None: k_factors = [1.0] * len(weights)
        if s_factors is None: s_factors = [1.0] * len(weights)
            
        total_w = sum(weights)
        if total_w == 0: return [1.0, 1.0, 1.0]
            
        k_mix = [0.0, 0.0, 0.0]
        s_mix = [0.0, 0.0, 0.0]
            
        for w, (r, g, b), op, tint, kf, sf in zip(weights, colors_rgb, opacities, tint_strengths, k_factors, s_factors):
            if w <= 0: continue
            c = w / total_w
            w_s = c * (0.25 + 0.75 * op) * sf
            w_k = c * (0.5 + 0.5 * tint) * kf * (0.4 + 0.6 * op)
                
            r_lin = ColorEngine.srgb_to_linear(r)
            g_lin = ColorEngine.srgb_to_linear(g)
            b_lin = ColorEngine.srgb_to_linear(b)
                
            ks_r = ((1.0 - r_lin) ** 2) / (2.0 * r_lin + 0.001)
            ks_g = ((1.0 - g_lin) ** 2) / (2.0 * g_lin + 0.001)
            ks_b = ((1.0 - b_lin) ** 2) / (2.0 * b_lin + 0.001)
                
            k_mix[0] += w_k * ks_r * sf
            k_mix[1] += w_k * ks_g * sf
            k_mix[2] += w_k * ks_b * sf
            s_mix[0] += w_s
            s_mix[1] += w_s
            s_mix[2] += w_s
            
        ks_ratio = [
            k_mix[0] / max(s_mix[0], 0.01),
            k_mix[1] / max(s_mix[1], 0.01),
            k_mix[2] / max(s_mix[2], 0.01)
        ]
        
        res_linear = [ColorEngine._ks_to_reflectance(ks) for ks in ks_ratio]
        return [
            ColorEngine.linear_to_srgb(res_linear[0]),
            ColorEngine.linear_to_srgb(res_linear[1]),
            ColorEngine.linear_to_srgb(res_linear[2])
        ]

    @staticmethod
    def apply_support_km(film_rgb, support_info, avg_opacity):
        sup_r, sup_g, sup_b = support_info["rgb"]
        film_rgb_255 = (film_rgb[0]*255, film_rgb[1]*255, film_rgb[2]*255)
        eff_op = ColorEngine._effective_coverage(film_rgb_255, avg_opacity)
        r = film_rgb[0] * eff_op + sup_r * (1 - eff_op)
        g = film_rgb[1] * eff_op + sup_g * (1 - eff_op)
        b = film_rgb[2] * eff_op + sup_b * (1 - eff_op)
        return (
            int(max(0, min(255, r * 255))),
            int(max(0, min(255, g * 255))),
            int(max(0, min(255, b * 255)))
        )


# ==============================================================================
# WORKER (FIX: Supporto passato via costruttore, thread-safe)
# ==============================================================================
class MixWorker(QThread):
    finished = pyqtSignal(list, float, list)

    def __init__(self, pigments, target_lab, top_pigments, model=MODEL_EMPIRICO, support_name=None, parent=None):
        super().__init__(parent)
        self.pigments = pigments
        self.target_lab = target_lab
        self.top_pigments = top_pigments
        self.model = model
        self.support_name = support_name  # FIX

    def _compute_mix_lab(self, weights, colors_rgb, opacities, tints, k_factors, s_factors, support_info):
        if self.model == MODEL_KUBELKA_MUNK:
            mixed = ColorEngine.mix_kubelka_munk(weights, colors_rgb, opacities, tints, k_factors, s_factors)
            if support_info:
                total_w = sum(weights)
                avg_op = sum(opacities[i] * (weights[i]/total_w) for i in range(len(weights))) if total_w > 0 else 0.8
                final = ColorEngine.apply_support_km(mixed, support_info, avg_op)
            else:
                final = (int(mixed[0]*255), int(mixed[1]*255), int(mixed[2]*255))
        else:
            mixed = ColorEngine.mix_subtractive(weights, colors_rgb)
            if support_info and opacities:
                total_w = sum(weights)
                avg_op = sum(opacities[i] * (weights[i]/total_w) for i in range(len(weights))) if total_w > 0 else 0.8
                final = ColorEngine.apply_support(
                    (mixed[0]*255, mixed[1]*255, mixed[2]*255),
                    support_info["hex"], avg_op
                )
            else:
                final = (int(mixed[0]*255), int(mixed[1]*255), int(mixed[2]*255))
        return ColorEngine.rgb_to_lab(final[0], final[1], final[2])

    def objective(self, x, colors_rgb, opacities, tints, k_factors, s_factors, support_info):
        w1, w2 = x
        w3 = 1.0 - w1 - w2
        if w1 < 0 or w2 < 0 or w3 < 0: return 1e6
        weights = [w1, w2, w3]
        try:
            calc_lab = self._compute_mix_lab(weights, colors_rgb, opacities, tints, k_factors, s_factors, support_info)
            return ColorEngine.delta_e(self.target_lab, calc_lab)
        except Exception: return 1e6

    def exhaustive_search(self, colors_rgb, opacities, tints, k_factors, s_factors, support_info):
        best_mix = [100, 0, 0]
        min_de = float("inf")
        for a in range(0, 101, 5):
            for b in range(0, 101 - a, 5):
                c = 100 - a - b
                weights = [a/100.0, b/100.0, c/100.0]
                try:
                    calc_lab = self._compute_mix_lab(weights, colors_rgb, opacities, tints, k_factors, s_factors, support_info)
                    de = ColorEngine.delta_e(self.target_lab, calc_lab)
                    if de < min_de: min_de, best_mix = de, [a, b, c]
                except Exception: continue
        best_a, best_b, best_c = best_mix
        for a in range(max(0, best_a - 7), min(101, best_a + 8)):
            for b in range(max(0, best_b - 7), min(101 - a, best_b + 8)):
                c = 100 - a - b
                if c < 0 or c > 100: continue
                weights = [a/100.0, b/100.0, c/100.0]
                try:
                    calc_lab = self._compute_mix_lab(weights, colors_rgb, opacities, tints, k_factors, s_factors, support_info)
                    de = ColorEngine.delta_e(self.target_lab, calc_lab)
                    if de < min_de: min_de, best_mix = de, [a, b, c]
                except Exception: continue
        return best_mix, min_de

    def run(self):
        colors_rgb, opacities, tints, k_factors, s_factors = [], [], [], [], []
        for p in self.top_pigments:
            c = QColor(p["colore"])
            colors_rgb.append([c.red()/255.0, c.green()/255.0, c.blue()/255.0])
            opacities.append(ColorEngine.get_opacity(p["tipo"], p.get("opacita")))
            tints.append(float(p.get("indice_tintoriale", 5)) / 10.0)
            k_factors.append(float(p.get("k_factor", 1.0)))
            s_factors.append(float(p.get("s_factor", 1.0)))
            
        # FIX: Lookup sicuro, senza mutare dict o accedere a indici errati
        support_info = SUPPORTI.get(self.support_name) if self.support_name and self.support_name in SUPPORTI else None

        if SCIPY_AVAILABLE:
            try:
                result = minimize(
                    self.objective, x0=[0.33, 0.33],
                    args=(colors_rgb, opacities, tints, k_factors, s_factors, support_info),
                    bounds=[(0, 1), (0, 1)],
                    constraints={'type': 'eq', 'fun': lambda x: 1 - x[0] - x[1]},
                    method='SLSQP'
                )
                if result.success:
                    w1, w2 = result.x
                    w3 = 1.0 - w1 - w2
                    self.finished.emit([w1*100, w2*100, w3*100], result.fun, self.top_pigments)
                    return
            except Exception: pass
            
        best_weights, min_de = self.exhaustive_search(colors_rgb, opacities, tints, k_factors, s_factors, support_info)
        self.finished.emit(best_weights, min_de, self.top_pigments)


# ==============================================================================
# APPLICAZIONE PRINCIPALE
# ==============================================================================
class PaintMixerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.data = DataManager()
        self.setWindowTitle("Paint Mixer Pro v6.5 Final - Giuseppe Luongo")
        self.setGeometry(100, 100, 1150, 820)

        self.sliders = {}
        self.zoom = 1.0
        self.current_hex = "#FFFFFF"
        self.worker = None
        self.progress = None
        self._last_de = None
        self.wheel_status_lbl = None

        self.init_ui()
        self.update_preview()

    def init_ui(self):
        main_layout = QHBoxLayout()
        self.list_widget = QListWidget()
        self.list_widget.setFixedWidth(300)
        self.list_widget.setSelectionMode(QListWidget.NoSelection)
        for p in self.data.pigments:
            item = QListWidgetItem(p["nome"])
            pix = QPixmap(20, 20)
            pix.fill(QColor(p["colore"]))
            item.setIcon(QIcon(pix))
            comp_str = ", ".join(p["compatibilità"]) if p["compatibilità"] else "nessuna"
            opacita_pct = int(p["opacita"] * 100)
            item.setToolTip(
                f"Codice: {p['codice']}\n"
                f"Tipo: {p['tipo']}\n"
                f"Opacità (W&N): {opacita_pct}%\n"
                f"K-Factor: {p['k_factor']:.2f}\n"
                f"S-Factor: {p['s_factor']:.2f}\n"
                f"Resistenza: {p['resistenza_luce']}\n"
                f"Compatibilità: {comp_str}\n"
                f"Indice Tintoriale: {p['indice_tintoriale']}/10"
            )
            self.list_widget.addItem(item)
        self.list_widget.itemClicked.connect(self.toggle_slider)

        center_layout = QVBoxLayout()
        self.scroll = QScrollArea()
        self.wheel_label = QLabel()
        self.wheel_label.mousePressEvent = self.pick_color
        self.scroll.setWidget(self.wheel_label)
        self.scroll.setWidgetResizable(True)
        center_layout.addWidget(self.scroll)
        
        zoom_box = QHBoxLayout()
        zoom_box.addWidget(QPushButton("Zoom +", clicked=self.zoom_in))
        zoom_box.addWidget(QPushButton("Zoom -", clicked=self.zoom_out))
        zoom_box.addWidget(QPushButton("Cambia Ruota", clicked=self.change_wheel))
        self.wheel_status_lbl = QLabel("")
        self.wheel_status_lbl.setStyleSheet("color: #666; font-size: 10px; font-style: italic;")
        zoom_box.addWidget(self.wheel_status_lbl)
        center_layout.addLayout(zoom_box)

        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignTop)
        sup_box = QHBoxLayout()
        sup_box.addWidget(QLabel("Supporto:"))
        self.support_combo = QComboBox()
        self.support_combo.addItems(SUPPORTI.keys())
        self.support_combo.setCurrentText(self.data.config.get("selected_support", "Carta Bianca Standard"))
        self.support_combo.currentTextChanged.connect(self.on_support_change)
        sup_box.addWidget(self.support_combo)
        
        model_box = QHBoxLayout()
        model_box.addWidget(QLabel("Modello:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems([MODEL_EMPIRICO, MODEL_KUBELKA_MUNK])
        current_model = self.data.config.get("mixing_model", MODEL_EMPIRICO)
        if current_model in [MODEL_EMPIRICO, MODEL_KUBELKA_MUNK]:
            self.model_combo.setCurrentText(current_model)
        self.model_combo.currentTextChanged.connect(self.on_model_change)
        model_box.addWidget(self.model_combo)

        sliders_group = QGroupBox("Ricetta Attiva (Max 7)")
        sliders_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        self.sliders_layout = QVBoxLayout() 
        self.sliders_layout.setSpacing(1)
        sliders_group.setLayout(self.sliders_layout)
        
        self.sliders_container = QWidget()
        self.sliders_container.setLayout(self.sliders_layout)
        self.sliders_container.setFixedHeight(180)
        
        prev_box = QHBoxLayout()
        self.preview = QLabel()
        self.preview.setFixedSize(130, 130)
        self.preview.setStyleSheet("background-color: white; border: 2px solid black;")
        self.info_lbl = QLabel("Codice: #FFFFFF\nLAB: -\nHVC: -")
        self.info_lbl.setStyleSheet("color: black; background: white; padding: 5px;")
        prev_box.addWidget(self.preview)
        prev_box.addWidget(self.info_lbl)

        self.recipe_lbl = QLabel("Ricetta: Seleziona pigmenti")
        self.recipe_lbl.setWordWrap(True)
        self.recipe_lbl.setStyleSheet("background:#F5F5F5; color: black; padding:8px; border:1px dashed gray; min-height: 60px;")
        
        btn_box = QHBoxLayout()
        btn_box.addWidget(QPushButton("Miscela", clicked=self.update_preview))
        btn_box.addWidget(QPushButton("Reset", clicked=self.reset))
        btn_box.addWidget(QPushButton("Salva", clicked=self.save_image))
        btn_box.addWidget(QPushButton("Licenza GPL", clicked=self.show_license))

        right_layout.addLayout(sup_box)
        right_layout.addLayout(model_box)
        right_layout.addWidget(self.sliders_container)
        right_layout.addLayout(prev_box)
        right_layout.addWidget(self.recipe_lbl)
        right_layout.addLayout(btn_box)

        main_layout.addWidget(self.list_widget)
        main_layout.addLayout(center_layout)
        main_layout.addLayout(right_layout)
        self.setLayout(main_layout)
        self.load_wheel_image()
        self._update_wheel_status()

    def show_license(self):
        QMessageBox.about(self, "Licenza GNU GPL v3", 
            "Paint Mixer Pro v6.5 Final\n"
            "Copyright (C) 2024-2026 Giuseppe Luongo\n\n"
            "This program is free software: you can redistribute it and/or modify\n"
            "it under the terms of the GNU General Public License as published by\n"
            "the Free Software Foundation, either version 3 of the License, or\n"
            "(at your option) any later version.\n\n"
            "See the LICENSE file for full details.")

    def _update_wheel_status(self):
        if self.wheel_status_lbl is None: return
        original_path = self.data.config.get("color_wheel_image", DEFAULT_WHEEL)
        if not os.path.exists(original_path):
            self.wheel_status_lbl.setText("❌ File mancante"); return
        cache_path = WheelImageProcessor.get_cache_path(original_path)
        if os.path.exists(cache_path):
            self.wheel_status_lbl.setText("✨ Ottimizzata (cache PNG-24)")
        else:
            needs, reason = WheelImageProcessor.needs_processing(original_path)
            self.wheel_status_lbl.setText(f"✅ {reason}" if not needs else " Processing...")

    def load_wheel_image(self):
        original_path = self.data.config.get("color_wheel_image", DEFAULT_WHEEL)
        if not os.path.exists(original_path):
            self.wheel_label.setText("Immagine non trovata")
            if self.wheel_status_lbl is not None: self.wheel_status_lbl.setText(" File mancante")
            return
        processed_path = WheelImageProcessor.process(original_path)
        if self.wheel_status_lbl is not None:
            is_original = (processed_path == original_path)
            if is_original:
                needs, reason = WheelImageProcessor.needs_processing(original_path)
                self.wheel_status_lbl.setText(f"✅ {reason}" if not needs else "️ Processing fallito")
            else:
                self.wheel_status_lbl.setText("✨ Ottimizzata (cache PNG-24)")
        pm = QPixmap(processed_path).scaled(
            QPixmap(processed_path).size() * self.zoom,
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.wheel_label.setPixmap(pm)

    def toggle_slider(self, item):
        name = item.text()
        if name in self.sliders:
            w = self.sliders.pop(name)
            w["container"].deleteLater() 
            item.setBackground(Qt.transparent)
        else:
            p = next((x for x in self.data.pigments if x["nome"] == name), None)
            if not p: return
            container = QWidget()
            hbox = QHBoxLayout()
            hbox.setContentsMargins(0, 0, 0, 0)
            lbl_text = f"<b>{name}</b><br>20%<br><small>{p.get('codice', 'N/D')}</small>"
            lbl = QLabel(lbl_text)
            c = QColor(p["colore"])
            text_color = "black" if c.red() + c.green() + c.blue() > 500 else "white"
            lbl.setStyleSheet(f"background:{p['colore']}; padding:4px; border:1px solid gray; font-size: 11px; color: {text_color};")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFixedWidth(230)
            lbl.setFixedHeight(45)
            sld = QSlider(Qt.Horizontal)
            sld.setRange(0, 100)
            sld.setValue(20)
            sld.setStyleSheet("height: 15px;") 
            sld.valueChanged.connect(lambda v, l=lbl, n=name: self.on_slider_change(l, n, v))
            hbox.addWidget(lbl)
            hbox.addWidget(sld)
            container.setLayout(hbox)
            self.sliders_layout.addWidget(container)
            self.sliders[name] = {"slider": sld, "label": lbl, "pigment": p, "container": container}
            item.setBackground(Qt.lightGray)
        self._last_de = None
        self.update_preview()

    def on_slider_change(self, label, name, value):
        code = self.sliders[name]["pigment"].get("codice", "N/D")
        label.setText(f"<b>{name}</b><br>{value}%<br><small>{code}</small>")
        self._last_de = None
        self.update_preview()

    def on_support_change(self, text):
        self.data.config["selected_support"] = text
        self.data.save_config()
        self.update_preview()

    def on_model_change(self, text):
        self.data.config["mixing_model"] = text
        self.data.save_config()
        self.update_preview()

    def update_preview(self):
        if not self.sliders:
            self.preview.setStyleSheet("background-color: white; border: 2px solid black;")
            self.info_lbl.setText("Codice: #FFFFFF\nLAB: -\nHVC: -")
            self.recipe_lbl.setText("Ricetta: Nessun pigmento")
            self.current_hex = "#FFFFFF"
            self._last_de = None
            return

        weights, colors, opacities, tints, recipe, total_val = [], [], [], [], [], 0
        for name, data in self.sliders.items():
            val = data["slider"].value()
            if val > 0:
                weights.append(val)
                c = QColor(data["pigment"]["colore"])
                colors.append([c.red()/255.0, c.green()/255.0, c.blue()/255.0])
                op = ColorEngine.get_opacity(data["pigment"]["tipo"], data["pigment"].get("opacita"))
                opacities.append(op)
                tints.append(float(data["pigment"].get("indice_tintoriale", 5)) / 10.0)
                total_val += val
                recipe.append(f"{name}: {val}%")

        if total_val == 0: return

        support_name = self.support_combo.currentText()
        support_info = SUPPORTI.get(support_name, SUPPORTI["Carta Bianca Standard"])
        avg_opacity = sum(opacities[i] * (weights[i]/total_val) for i in range(len(weights)))
        model = self.model_combo.currentText()

        if model == MODEL_KUBELKA_MUNK:
            k_factors = [float(data["pigment"].get("k_factor", 1.0)) for data in self.sliders.values()]
            s_factors = [float(data["pigment"].get("s_factor", 1.0)) for data in self.sliders.values()]
            mixed_rgb = ColorEngine.mix_kubelka_munk(weights, colors, opacities, tints, k_factors, s_factors)
            final_rgb = ColorEngine.apply_support_km(mixed_rgb, support_info, avg_opacity)
        else:
            mixed_rgb = ColorEngine.mix_subtractive(weights, colors)
            final_rgb = ColorEngine.apply_support(
                (mixed_rgb[0]*255, mixed_rgb[1]*255, mixed_rgb[2]*255),
                support_info["hex"], avg_opacity
            )

        hex_code = f"#{final_rgb[0]:02X}{final_rgb[1]:02X}{final_rgb[2]:02X}"
        self.current_hex = hex_code
        self.preview.setStyleSheet(f"background-color: {hex_code}; border: 2px solid black;")

        lab = ColorEngine.rgb_to_lab(final_rgb[0], final_rgb[1], final_rgb[2])
        max_c, min_c, delta = max(final_rgb), min(final_rgb), max(final_rgb) - min(final_rgb)
        h = 0
        if delta != 0:
            if max_c == final_rgb[0]: h = 60 * (((final_rgb[1] - final_rgb[2]) / delta) % 6)
            elif max_c == final_rgb[1]: h = 60 * (((final_rgb[2] - final_rgb[0]) / delta) + 2)
            else: h = 60 * (((final_rgb[0] - final_rgb[1]) / delta) + 4)
        v = max_c / 255 * 100
        c = delta / 255 * 100

        self.info_lbl.setText(
            f"Codice HEX: {hex_code}\n"
            f"CIELAB: L={lab.lab_l:.1f} a={lab.lab_a:.1f} b={lab.lab_b:.1f}\n"
            f"HVC: H={h:.0f}° V={v:.0f}% C={c:.0f}%"
        )

        de_text = ""
        if self._last_de is not None:
            quality = " ✅ PERFETTO" if self._last_de < 2 else \
                      " 👍 Buono" if self._last_de < 5 else \
                      " ️ Accettabile" if self._last_de < 10 else "  Fuori gamut"
            de_text = f"🎯 DeltaE = {self._last_de:.2f}{quality}\n(ΔE<2=impercettibile | ΔE<5=accettabile)\n\n"

        recipe_text = de_text + f"Modello: {model}\nRicetta Miscela:\n" + "\n".join(recipe) + \
                      f"\n\nSupporto: {support_name}\nRiflettanza supporto: {support_info['R']*100:.0f}%\nOpacità Media Film: {avg_opacity*100:.0f}%"
        self.recipe_lbl.setText(recipe_text)

    def reset(self):
        for name in list(self.sliders.keys()):
            items = self.list_widget.findItems(name, Qt.MatchExactly)
            if items: items[0].setBackground(Qt.transparent)
            w = self.sliders.pop(name)
            w["container"].deleteLater() 
        self._last_de = None
        self.update_preview()

    def zoom_in(self): self.zoom *= 1.2; self.load_wheel_image()
    def zoom_out(self): self.zoom /= 1.2; self.load_wheel_image()

    def change_wheel(self):
        path, _ = QFileDialog.getOpenFileName(self, "Scegli ruota colori", "", "Immagini (*.png *.jpg *.jpeg *.gif *.bmp *.tiff)")
        if path:
            self.data.config["color_wheel_image"] = path
            self.data.save_config()
            self.load_wheel_image()

    # FIX: Mappatura corretta coordinate su pixmap scalato/zoomato
    def pick_color(self, event):
        pm = self.wheel_label.pixmap()
        if not pm or pm.isNull(): return

        x_w, y_w = event.pos().x(), event.pos().y()
        ratio_x = pm.width() / self.wheel_label.width()
        ratio_y = pm.height() / self.wheel_label.height()
        x = max(0, min(pm.width() - 1, int(x_w * ratio_x)))
        y = max(0, min(pm.height() - 1, int(y_w * ratio_y)))

        img = pm.toImage()
        r = g = b = c = 0
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                px, py = x + dx, y + dy
                if 0 <= px < pm.width() and 0 <= py < pm.height():
                    col = QColor(img.pixel(px, py))
                    r += col.red()
                    g += col.green()
                    b += col.blue()
                    c += 1
        if c == 0: return
        target_hex = f"#{int(r/c):02X}{int(g/c):02X}{int(b/c):02X}"
        self.auto_mix(target_hex)

    def _find_pigment_by_code(self, code_fragment):
        for p in self.data.pigments:
            if code_fragment in p["codice"]: return p
        return None

    def _find_pigment_by_name(self, name_fragment):
        nm = name_fragment.lower()
        for p in self.data.pigments:
            if nm in p["nome"].lower(): return p
        return None

    def _get_family(self, pigment):
        return pigment.get("famiglia", pigment["nome"].lower())

    def _find_saturated_by_hue(self, target_lab, used_names, min_chroma=25):
        target_hue = ColorEngine.get_hue(target_lab)
        target_L = target_lab.lab_l
        if target_L < 15: L_max, L_min, L_weight = 30, 0, 0.8
        elif target_L < 25: L_max, L_min, L_weight = 40, 0, 0.6
        elif target_L > 85: L_max, L_min, L_weight = 100, 50, 0.8
        elif target_L > 60: L_max, L_min, L_weight = 85, 30, 0.5
        else: L_max, L_min, L_weight = 100, 0, 0.4
        
        used_families = {self._get_family(p) for p in self.data.pigments if p["nome"] in used_names}
        best_pigment, best_score = None, float('inf')
        
        for p in self.data.pigments:
            if p["nome"] in used_names or self._get_family(p) in used_families: continue
            c = QColor(p["colore"])
            p_lab = ColorEngine.rgb_to_lab(c.red(), c.green(), c.blue())
            if ColorEngine.get_chroma(p_lab) < min_chroma: continue
            if p_lab.lab_l < L_min or p_lab.lab_l > L_max: continue
            p_hue = ColorEngine.get_hue(p_lab)
            hue_diff = abs(target_hue - p_hue)
            if hue_diff > 180: hue_diff = 360 - hue_diff
            score = hue_diff + (abs(target_L - p_lab.lab_l) * L_weight)
            if score < best_score: best_score, best_pigment = score, p
        
        if best_pigment is None:
            for p in self.data.pigments:
                if p["nome"] in used_names or self._get_family(p) in used_families: continue
                c = QColor(p["colore"])
                p_lab = ColorEngine.rgb_to_lab(c.red(), c.green(), c.blue())
                if ColorEngine.get_chroma(p_lab) < min_chroma: continue
                p_hue = ColorEngine.get_hue(p_lab)
                hue_diff = abs(target_hue - p_hue)
                if hue_diff > 180: hue_diff = 360 - hue_diff
                if hue_diff < best_score: best_score, best_pigment = hue_diff, p
        return best_pigment

    def auto_mix(self, target_hex):
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()

        target_lab = ColorEngine.rgb_to_lab(
            int(target_hex[1:3], 16), int(target_hex[3:5], 16), int(target_hex[5:7], 16)
        )
        target_L, target_chroma, target_hue = target_lab.lab_l, ColorEngine.get_chroma(target_lab), ColorEngine.get_hue(target_lab)

        scores = []
        for p in self.data.pigments:
            c = QColor(p["colore"])
            scores.append((p, ColorEngine.delta_e(target_lab, ColorEngine.rgb_to_lab(c.red(), c.green(), c.blue()))))
        scores.sort(key=lambda x: x[1])

        if scores[0][1] < 2.5:
            self.reset()
            items = self.list_widget.findItems(scores[0][0]["nome"], Qt.MatchExactly)
            if items:
                self.toggle_slider(items[0])
                self.sliders[scores[0][0]["nome"]]["slider"].setValue(100)
            return

        if target_L > 95:
            white = self._find_pigment_by_code("PW6")
            if white:
                self.reset()
                items = self.list_widget.findItems(white["nome"], Qt.MatchExactly)
                if items:
                    self.toggle_slider(items[0])
                    self.sliders[white["nome"]]["slider"].setValue(100)
                return

        if target_L < 5 and target_chroma < 5:
            best_black, best_score = None, float('inf')
            for code in ["PBk11", "PBk9", "PBk6", "PBk31"]:
                b = self._find_pigment_by_code(code)
                if b:
                    c = QColor(b["colore"])
                    p_lab = ColorEngine.rgb_to_lab(c.red(), c.green(), c.blue())
                    score = abs(target_L - p_lab.lab_l) + abs(target_chroma - ColorEngine.get_chroma(p_lab))
                    if score < best_score: best_score, best_black = score, b
            if best_black:
                self.reset()
                items = self.list_widget.findItems(best_black["nome"], Qt.MatchExactly)
                if items:
                    self.toggle_slider(items[0])
                    self.sliders[best_black["nome"]]["slider"].setValue(100)
                return

        if 15 < target_L < 90 and target_chroma > 12:
            best_pure_pig, best_score = None, float('inf')
            for p in self.data.pigments:
                c = QColor(p["colore"])
                p_lab = ColorEngine.rgb_to_lab(c.red(), c.green(), c.blue())
                p_c = ColorEngine.get_chroma(p_lab)
                if p_c < 15: continue
                h_diff = abs(target_hue - ColorEngine.get_hue(p_lab))
                if h_diff > 180: h_diff = 360 - h_diff
                score = h_diff + (abs(target_chroma - p_c) * 0.2)
                if score < best_score: best_score, best_pure_pig = score, p
            if best_pure_pig and best_score < 40:
                self.reset()
                items = self.list_widget.findItems(best_pure_pig["nome"], Qt.MatchExactly)
                if items:
                    self.toggle_slider(items[0])
                    self.sliders[best_pure_pig["nome"]]["slider"].setValue(100)
                return

        if target_chroma < 25:
            for ename in ["Raw Umber", "Burnt Umber", "Raw Sienna", "Burnt Sienna", "Yellow Ochre", "Gold Ochre"]:
                earth = self._find_pigment_by_name(ename)
                if earth:
                    c = QColor(earth["colore"])
                    if ColorEngine.delta_e(target_lab, ColorEngine.rgb_to_lab(c.red(), c.green(), c.blue())) < 10:
                        self.reset()
                        items = self.list_widget.findItems(earth["nome"], Qt.MatchExactly)
                        if items:
                            self.toggle_slider(items[0])
                            self.sliders[earth["nome"]]["slider"].setValue(100)
                        return

        selected, selected_names, strategy = [], set(), ""
        white = self._find_pigment_by_code("PW6")
        black = self._find_pigment_by_code("PBk11") or self._find_pigment_by_code("PBk9")
        gray = self._find_pigment_by_name("Grigio Neutro Medio")
        lamp_black = self._find_pigment_by_code("PBk6")

        if target_L < 20 and target_chroma < 8:
            strategy = f"Nero/Grigio scuro (L*={target_L:.0f})"
            if target_L > 5:
                selected, selected_names = [black, white], {black["nome"], white["nome"]}
                strategy += " → Nero + Bianco"
                if lamp_black and lamp_black["nome"] not in selected_names: selected.append(lamp_black)
            else:
                for b in [black, self._find_pigment_by_code("PBk9"), lamp_black, self._find_pigment_by_code("PBk31")]:
                    if b and len(selected) < 3: selected.append(b)
        elif target_chroma < 8:
            if target_L < 40:
                selected, strategy = [gray, black, white], "Grigio medio-scuro → Grigio + Nero + Bianco"
            elif target_L < 70:
                selected, strategy = [white, gray], "Grigio medio → Bianco + Grigio Neutro"
                third = self._find_pigment_by_name("Grigio Cenere") if target_L < 55 else self._find_pigment_by_name("Grigio Titanio Chiaro")
                if third: selected.append(third)
            else:
                selected, strategy = [white], "Grigio chiaro → Bianco + Nero"
                fine_black = lamp_black or self._find_pigment_by_code("PBk9")
                if fine_black: selected.append(fine_black)
                if len(selected) < 3:
                    gv = self._find_pigment_by_name("Grigio Titanio Chiaro")
                    if gv and gv["nome"] not in {p["nome"] for p in selected}: selected.append(gv)
            selected_names = {p["nome"] for p in selected}
        elif target_L < 40:
            strategy = f"Scuro (L*={target_L:.0f})"
            sat = self._find_saturated_by_hue(target_lab, selected_names, 25)
            if sat: selected.append(sat); selected_names.add(sat["nome"]); strategy += f" → {sat['nome']}"
            if target_chroma < 20 and black and black["nome"] not in selected_names:
                selected.append(black); selected_names.add(black["nome"]); strategy += " + Nero"
            else:
                earth_pig = next((e for en in ["Raw Umber", "Burnt Umber", "Raw Sienna", "Burnt Sienna"] if (e:=self._find_pigment_by_name(en)) and e["nome"] not in selected_names), None)
                if earth_pig: selected.append(earth_pig); selected_names.add(earth_pig["nome"]); strategy += f" + {earth_pig['nome']}"
                elif lamp_black and lamp_black["nome"] not in selected_names: selected.append(lamp_black); selected_names.add(lamp_black["nome"])
        else:
            strategy = f"Medio/Chiaro (L*={target_L:.0f})"
            sat = self._find_saturated_by_hue(target_lab, selected_names, 20)
            if sat: selected.append(sat); selected_names.add(sat["nome"]); strategy += f" → {sat['nome']}"
            if target_chroma < 15 and gray and gray["nome"] not in selected_names:
                selected.append(gray); selected_names.add(gray["nome"]); strategy += " + Grigio Neutro"
            elif white and white["nome"] not in selected_names:
                selected.append(white); selected_names.add(white["nome"]); strategy += " + Bianco"

        while len(selected) < 3:
            added = False
            for p, de in scores:
                if p["nome"] not in selected_names: selected.append(p); selected_names.add(p["nome"]); added = True; break
            if not added: break

        top_pigments = selected[:3]

        self.progress = QProgressDialog("Calcolo miscela (K/S lineari)...", "Annulla", 0, 0, self)
        self.progress.setWindowModality(Qt.WindowModal)
        self.progress.show()

        # FIX: Passaggio esplicito del supporto, rimossa mutazione dict
        self.worker = MixWorker(
            self.data.pigments, target_lab, top_pigments,
            self.model_combo.currentText(),
            support_name=self.support_combo.currentText(),
            parent=self
        )
        self.worker.finished.connect(self.on_mix_finished)
        self.worker.start()

    def on_mix_finished(self, weights, min_de, top_pigments):
        if self.progress: self.progress.close(); self.progress = None
        self._last_de = min_de
        for name in list(self.sliders.keys()):
            items = self.list_widget.findItems(name, Qt.MatchExactly)
            if items: items[0].setBackground(Qt.transparent)
            self.sliders.pop(name)["container"].deleteLater()
        for p, w in zip(top_pigments, weights):
            if w > 0.5:
                items = self.list_widget.findItems(p["nome"], Qt.MatchExactly)
                if items:
                    c = QColor(p["colore"])
                    txt_color = "black" if c.red() + c.green() + c.blue() > 500 else "white"
                    lbl = QLabel(f"<b>{p['nome']}</b><br>{int(round(w))}%<br><small>{p.get('codice', 'N/D')}</small>")
                    lbl.setStyleSheet(f"background:{p['colore']}; padding:4px; border:1px solid gray; font-size: 11px; color: {txt_color};")
                    lbl.setAlignment(Qt.AlignCenter); lbl.setFixedSize(230, 45)
                    sld = QSlider(Qt.Horizontal); sld.setRange(0, 100); sld.setValue(int(round(w))); sld.setStyleSheet("height: 15px;")
                    sld.valueChanged.connect(lambda v, l=lbl, n=p['nome']: self.on_slider_change(l, n, v))
                    cont = QWidget()
                    hb = QHBoxLayout(); hb.setContentsMargins(0,0,0,0); hb.addWidget(lbl); hb.addWidget(sld); cont.setLayout(hb)
                    self.sliders_layout.addWidget(cont)
                    self.sliders[p['nome']] = {"slider": sld, "label": lbl, "pigment": p, "container": cont}
                    items[0].setBackground(Qt.lightGray)
        self.update_preview()

    def save_image(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salva Campione Colore", f"colore_{self.current_hex.replace('#', '')}.png", "Immagini PNG (*.png);;Immagini JPEG (*.jpg)")
        if path:
            img = QImage(300, 300, QImage.Format_RGB32)
            img.fill(QColor(self.current_hex))
            if img.save(path): QMessageBox.information(self, "Successo", f"Campione colore salvato:\n{path}")
            else: QMessageBox.warning(self, "Errore", "Impossibile salvare l'immagine campione.")


if __name__ == '__main__':
    setup_exception_hook()
    app = QApplication(sys.argv)
    try:
        window = PaintMixerApp()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        QMessageBox.critical(None, "Errore Avvio", f"Impossibile avviare l'applicazione.\nVerifica che 'pigments.json' sia presente e valido.\n\nDettagli: {e}")
        sys.exit(1)
