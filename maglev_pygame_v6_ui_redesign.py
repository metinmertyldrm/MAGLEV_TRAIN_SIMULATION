# -*- coding: utf-8 -*-
"""
MAGLEV TRAIN VISUAL SIMULATION - V6 UI REDESIGN
------------------------------------------------
Bu sürümün amacı: sadece çalışan bir demo değil, yeni başlayan birinin de
hangi ayarın neyi değiştirdiğini rahat okuyabildiği kullanıcı dostu bir
simülasyon ekranı sunmak.

Çalıştırma:
    py maglev_pygame_v6_ui_redesign.py

Gerekli paket:
    pip install pygame-ce
    veya
    pip install pygame

Kısayollar:
    SPACE : duraklat / devam et
    R     : reset
    D     : darbe uygula
    S     : fren uygula
    A     : kuvvet vektörlerini aç/kapat
    G     : grafikleri aç/kapat
    H     : yardım kartını aç/kapat
    ESC   : çıkış
"""

import csv
import math
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Tuple

import pygame

# ============================================================
# GENEL AYARLAR
# ============================================================

APP_TITLE = "Maglev Train Visual Simulation"
VERSION = "v6.0"
FPS = 60

START_W, START_H = 1280, 720
MIN_W, MIN_H = 1050, 640

# Fizik alanı
TRACK_LEN_M = 2.0
TRAIN_LEN_M = 0.36
TRAIN_BODY_W = 230
TRAIN_BODY_H = 62
MIN_GAP_MM = 3.0
MAX_GAP_MM = 30.0

# ============================================================
# RENKLER
# ============================================================

BG = (6, 11, 19)
BG_SOFT = (9, 16, 27)
PANEL = (14, 22, 35)
PANEL_2 = (18, 29, 46)
PANEL_3 = (24, 38, 60)
CARD = (20, 32, 50)
CARD_HOVER = (27, 43, 68)
BORDER = (48, 69, 99)
GRID = (35, 52, 76)
TEXT = (229, 238, 249)
MUTED = (145, 158, 178)
FAINT = (92, 108, 132)
WHITE = (255, 255, 255)
BLUE = (58, 137, 255)
BLUE_2 = (24, 90, 190)
CYAN = (72, 218, 255)
GREEN = (74, 224, 139)
PURPLE = (171, 117, 255)
ORANGE = (255, 161, 67)
YELLOW = (255, 221, 94)
RED = (245, 84, 84)
RAIL = (158, 171, 190)
RAIL_DARK = (75, 89, 110)
COIL_OFF = (54, 68, 88)
COIL_ON = (100, 190, 255)
COPPER = (224, 113, 47)
HOT = (255, 84, 55)
TRAIN_WHITE = (230, 238, 250)
TRAIN_DARK = (21, 35, 58)
WINDOW = (8, 21, 38)

# ============================================================
# YARDIMCI FONKSİYONLAR
# ============================================================


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def lerp(a, b, t):
    return a + (b - a) * t


def color_lerp(a, b, t):
    t = clamp(t, 0.0, 1.0)
    return tuple(int(lerp(a[i], b[i], t)) for i in range(3))


def fmt(v: float, digits=2):
    if abs(v) >= 100:
        return f"{v:.0f}"
    if abs(v) >= 10:
        return f"{v:.1f}"
    return f"{v:.{digits}f}"


def rounded(surface, color, rect, radius=12, width=0):
    pygame.draw.rect(surface, color, rect, width=width, border_radius=radius)


def text(surface, font, msg, x, y, color=TEXT):
    surface.blit(font.render(str(msg), True, color), (x, y))


def text_center(surface, font, msg, rect, color=TEXT):
    img = font.render(str(msg), True, color)
    x = rect[0] + rect[2] // 2 - img.get_width() // 2
    y = rect[1] + rect[3] // 2 - img.get_height() // 2
    surface.blit(img, (x, y))


def wrap_lines(msg: str, font, width: int) -> List[str]:
    lines: List[str] = []
    for para in str(msg).split("\n"):
        words = para.split()
        if not words:
            lines.append("")
            continue
        cur = words[0]
        for w in words[1:]:
            test = cur + " " + w
            if font.size(test)[0] <= width:
                cur = test
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def glow(surface, center, radius, color, strength=0.45):
    if radius <= 0:
        return
    s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for r in range(radius, 0, -6):
        alpha = int(255 * strength * (r / radius) ** 2 * 0.08)
        pygame.draw.circle(s, (*color, alpha), (radius, radius), r)
    surface.blit(s, (center[0] - radius, center[1] - radius), special_flags=pygame.BLEND_PREMULTIPLIED)

# ============================================================
# AÇIKLAMALAR
# ============================================================

INFO: Dict[str, Dict[str, str]] = {
    "target_gap": {
        "title": "Hedef Boşluk",
        "what": "Trenin raydan kaç mm yukarıda tutulmak istendiğini belirler.",
        "up": "Artarsa elektromıknatıs treni daha uzak mesafeden tutmaya çalışır; sistem daha çok zorlanır.",
        "down": "Azalırsa kaldırmak kolaylaşır ama tren raya fazla yaklaşabilir.",
        "watch": "Gerçek boşluk kartı ve Boşluk grafiği hedefe oturuyor mu?",
    },
    "guide": {
        "title": "Kılavuz / Stabilizör",
        "what": "Gerçek prototipteki yan kılavuz, mekanik sınırlama ve gövde dengelemesini temsil eder.",
        "up": "Artarsa tren daha az eğilir, daha güvenli ve kontrollü görünür.",
        "down": "Azalırsa pitch/eğim hareketi artar; mekanik kılavuzun önemi daha net görülür.",
        "watch": "Pitch kartı ve trenin burun eğimine bak.",
    },
    "friction": {
        "title": "Sürtünme Katsayısı",
        "what": "Ray üzerindeki kayıplar, hava direnci ve hareketi yavaşlatan etkileri temsil eder.",
        "up": "Artarsa tren daha yavaş ve okunabilir hareket eder.",
        "down": "Azalırsa tren daha hızlı hızlanır; değerleri takip etmek zorlaşabilir.",
        "watch": "Hız ve pozisyon değerlerinin ne kadar hızlı değiştiğini izle.",
    },
    "mass": {
        "title": "Kütle",
        "what": "Trenin toplam ağırlığıdır. Daha ağır tren daha fazla kaldırma kuvveti ister.",
        "up": "Artarsa bobin akımı ve sıcaklık artar; tren hedef boşluğu korumakta zorlanabilir.",
        "down": "Azalırsa tren daha kolay havada kalır ama fazla agresif PID ile zıplayabilir.",
        "watch": "Akım, sıcaklık ve gerçek boşluk değerlerine bak.",
    },
    "kp": {
        "title": "Kp - Oransal Kazanç",
        "what": "Hata oluşunca sistemin ne kadar sert tepki vereceğini belirler.",
        "up": "Artarsa hedefe dönüş hızlanır; fazla olursa zıplama ve salınım artar.",
        "down": "Azalırsa hareket sakinleşir ama tren hedefe geç döner veya düşebilir.",
        "watch": "Boşluk ve Pitch grafiklerindeki dalgalanmayı izle.",
    },
    "ki": {
        "title": "Ki - İntegral Kazanç",
        "what": "Uzun süre kalan küçük hataları zamanla düzeltmeye çalışır.",
        "up": "Artarsa kalıcı hata azalabilir; fazla olursa sistem aşırı düzeltme yapabilir.",
        "down": "Azalırsa sistem daha güvenli olur ama küçük sabit hata kalabilir.",
        "watch": "Başlangıçta 0 bırak; sonra çok küçük artır.",
    },
    "kd": {
        "title": "Kd - Türev Kazanç",
        "what": "Zıplamayı ve salınımı azaltan fren etkisi gibi çalışır.",
        "up": "Artarsa titreşim azalabilir; çok artarsa sistem geç veya gürültülü tepki verebilir.",
        "down": "Azalırsa tren daha canlı tepki verir ama salınım artabilir.",
        "watch": "Pitch ve boşluk dalgalanması azaldı mı?",
    },
    "voltage": {
        "title": "Voltaj",
        "what": "Güç kaynağının bobinlere verebildiği gerilimi temsil eder.",
        "up": "Artarsa akım kapasitesi ve kaldırma gücü artar; ısınma riski yükselir.",
        "down": "Azalırsa sistem zayıflar; ağır tren düşebilir.",
        "watch": "Akım limiti ve sıcaklık değerlerini izle.",
    },
    "resistance": {
        "title": "Bobin Direnci",
        "what": "Bobinin elektriksel direncidir. Direnç arttıkça aynı voltajda alınan akım azalır.",
        "up": "Artarsa akım limiti düşer, manyetik kuvvet zayıflar.",
        "down": "Azalırsa daha çok akım geçebilir; ısınma riski yükselir.",
        "watch": "Akım limiti ve sıcaklık değerlerine bak.",
    },
    "current_limit": {
        "title": "Maksimum Akım Limiti",
        "what": "Güç elektroniğinin veya güvenlik sisteminin izin verdiği üst akımı temsil eder.",
        "up": "Artarsa bobin daha güçlü olabilir ama ısınma ve MOSFET riski artar.",
        "down": "Azalırsa sistem daha güvenli ama zayıf olur.",
        "watch": "Ortalama akım sürekli limite yaklaşıyor mu?",
    },
    "noise": {
        "title": "Sensör Gürültüsü",
        "what": "Hall sensörünün ölçümde yaptığı rastgele hatayı temsil eder.",
        "up": "Artarsa kontrolcü yanlış veriyle çalışır; tren ve akım daha titrek olur.",
        "down": "Azalırsa ölçüm temizleşir ve kontrol kararlı görünür.",
        "watch": "Boşluk ve Akım grafiklerindeki hızlı küçük dalgalanmaları izle.",
    },
    "propulsion": {
        "title": "İtki Kuvveti",
        "what": "Ray boyunca sıralı bobinlerin treni ileri çekme gücüdür.",
        "up": "Artarsa tren hızlanır; değerleri okumak zorlaşabilir ve eğim artabilir.",
        "down": "Azalırsa tren daha yavaş gider, eğitim/demo için daha anlaşılır olur.",
        "watch": "Hız, pozisyon ve aktif bobin değerlerini izle.",
    },
    "max_speed": {
        "title": "Maksimum Hız",
        "what": "Trenin ray boyunca çıkabileceği üst hızı sınırlar.",
        "up": "Artarsa demo hızlanır; öğrenme için biraz zorlaşır.",
        "down": "Azalırsa yavaş çekim gibi daha okunabilir olur.",
        "watch": "Telemetriyi rahat okuyabildiğin hızı seç.",
    },
    "sim_speed": {
        "title": "Simülasyon Hızı",
        "what": "Fiziğin gerçek zamana göre ne kadar hızlı aktığını belirler.",
        "up": "Artarsa olaylar daha hızlı akar.",
        "down": "Azalırsa ağır çekim gibi olur; öğrenmek için idealdir.",
        "watch": "Sağdaki değerleri okuyabildiğin seviyeyi seç.",
    },
}

# ============================================================
# UI ELEMANLARI
# ============================================================


class Button:
    def __init__(self, label: str, action: Callable, color=BLUE_2):
        self.label = label
        self.action = action
        self.color = color
        self.rect = pygame.Rect(0, 0, 1, 1)
        self.enabled = True

    def draw(self, surf, font, rect, active=False):
        self.rect = pygame.Rect(rect)
        mx, my = pygame.mouse.get_pos()
        hover = self.rect.collidepoint(mx, my)
        c = self.color if not active else BLUE
        if hover:
            c = color_lerp(c, WHITE, 0.10)
        rounded(surf, c, self.rect, 9)
        rounded(surf, color_lerp(c, WHITE, 0.22), self.rect, 9, 1)
        text_center(surf, font, self.label, self.rect, WHITE)

    def event(self, ev):
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and self.rect.collidepoint(ev.pos):
            self.action()
            return True
        return False


class Slider:
    def __init__(self, key, label, lo, hi, value, step, unit="", category=""):
        self.key = key
        self.label = label
        self.lo = lo
        self.hi = hi
        self.value = value
        self.default = value
        self.step = step
        self.unit = unit
        self.category = category
        self.track = pygame.Rect(0, 0, 1, 1)
        self.row_rect = pygame.Rect(0, 0, 1, 1)
        self.drag = False

    def set(self, v):
        if self.step:
            v = round(v / self.step) * self.step
        self.value = clamp(v, self.lo, self.hi)

    def percent(self):
        return clamp((self.value - self.lo) / max(1e-9, self.hi - self.lo), 0, 1)

    def set_from_mouse(self, mx):
        p = clamp((mx - self.track.x) / max(1, self.track.w), 0, 1)
        self.set(self.lo + p * (self.hi - self.lo))

    def event(self, ev):
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.row_rect.collidepoint(ev.pos) or self.track.collidepoint(ev.pos):
                self.drag = True
                self.set_from_mouse(ev.pos[0])
                return True
        if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
            if self.drag:
                self.drag = False
                return True
        if ev.type == pygame.MOUSEMOTION and self.drag:
            self.set_from_mouse(ev.pos[0])
            return True
        return False

    def value_str(self):
        if self.step >= 1:
            val = f"{self.value:.0f}"
        elif self.step >= 0.1:
            val = f"{self.value:.1f}"
        elif self.step >= 0.01:
            val = f"{self.value:.2f}"
        else:
            val = f"{self.value:.3f}"
        return f"{val} {self.unit}".strip()

    def draw(self, surf, fonts, x, y, w, active=False):
        font = fonts["small"]
        tiny = fonts["tiny"]
        row_h = 46
        self.row_rect = pygame.Rect(x, y, w, row_h)
        if active:
            rounded(surf, (25, 44, 70), self.row_rect, 10)
            rounded(surf, BLUE, self.row_rect, 10, 1)

        text(surf, font, self.label, x + 10, y + 5, WHITE if active else TEXT)
        # Value chip - user can always read current value here.
        chip_w = 70
        chip = pygame.Rect(x + w - chip_w - 8, y + 7, chip_w, 26)
        rounded(surf, (12, 22, 36), chip, 7)
        rounded(surf, BORDER if not active else YELLOW, chip, 7, 1)
        text_center(surf, tiny, self.value_str(), chip, YELLOW if active else TEXT)

        tx = x + 10
        tw = max(80, w - chip_w - 34)
        ty = y + 32
        self.track = pygame.Rect(tx, ty - 7, tw, 14)
        pygame.draw.line(surf, (49, 64, 87), (tx, ty), (tx + tw, ty), 5)
        kx = int(tx + self.percent() * tw)
        pygame.draw.line(surf, BLUE, (tx, ty), (kx, ty), 5)
        pygame.draw.circle(surf, WHITE, (kx, ty), 8)
        pygame.draw.circle(surf, YELLOW if active else BLUE, (kx, ty), 10, 1)

# ============================================================
# PARAMETRE VE SİMÜLASYON
# ============================================================


@dataclass
class Params:
    mass: float = 150.0
    target_gap: float = 8.0
    guide: float = 1.0
    friction: float = 0.90
    kp: float = 210.0
    ki: float = 0.0
    kd: float = 3.2
    voltage: float = 12.0
    resistance: float = 2.0
    current_limit: float = 6.0
    noise: float = 0.04
    propulsion: float = 0.16
    max_speed: float = 0.45
    sim_speed: float = 0.35


class MaglevSim:
    def __init__(self):
        self.reset()

    def reset(self):
        self.t = 0.0
        self.x = 0.10
        self.vx = 0.0
        self.gap = 8.0  # mm
        self.vgap = 0.0
        self.pitch = 0.0  # degree
        self.vpitch = 0.0
        self.current = 2.0
        self.temp = 25.0
        self.integral = 0.0
        self.prev_err = 0.0
        self.active_coil = 0
        self.status = "KARARLI"
        self.disturb = 0.0
        self.brake = 0.0
        self.history: Dict[str, List[float]] = {k: [] for k in ["gap", "pitch", "speed", "current", "temp"]}
        self.export_rows: List[Dict[str, float]] = []

    def hit(self):
        self.disturb = 0.18

    def brake_pulse(self):
        self.brake = 0.45

    def coils(self, count=12):
        return [0.08 + i * (TRACK_LEN_M - 0.16) / (count - 1) for i in range(count)]

    def step(self, dt, p: Params):
        dt *= clamp(p.sim_speed, 0.05, 1.0)
        self.t += dt

        mass = max(p.mass / 1000.0, 0.05)
        target = p.target_gap
        measured = self.gap + random.gauss(0, p.noise)
        err = measured - target  # + means too high/far -> need more pull downward? For visual we use corrective model.

        # Simple stable PID-like levitation model. It intentionally stays readable rather than physically perfect.
        # If gap is larger than target, magnetic force should pull it back down visually; if smaller, it relaxes upward.
        self.integral = clamp(self.integral + err * dt, -3.0, 3.0)
        derivative = (err - self.prev_err) / max(dt, 1e-5)
        derivative = clamp(derivative, -80, 80)
        self.prev_err = err

        control = p.kp * err * 0.00075 + p.ki * self.integral * 0.00035 + p.kd * derivative * 0.00008
        base_strength = (p.voltage / max(p.resistance, 0.1)) / max(p.current_limit, 0.2)
        mass_load = mass / 0.15

        # Vertical acceleration in mm/s^2, with damping.
        desired_acc = -control * 1200.0 / max(mass_load, 0.3)
        gravity_bias = 0.55 * (mass_load - 1.0)
        damping = (8.0 + 4.0 * p.guide) * self.vgap
        if self.disturb > 0:
            desired_acc += 50.0
            self.disturb -= dt
        self.vgap += (desired_acc + gravity_bias - damping) * dt
        self.vgap = clamp(self.vgap, -32, 32)
        self.gap += self.vgap * dt

        # Gap limits.
        if self.gap < MIN_GAP_MM:
            self.gap = MIN_GAP_MM
            self.vgap = max(0, self.vgap) * 0.25
        if self.gap > MAX_GAP_MM:
            self.gap = MAX_GAP_MM
            self.vgap = min(0, self.vgap) * 0.25

        # Pitch follows imperfect control + stabilizer.
        noise_pitch = random.gauss(0, p.noise * 0.05)
        self.vpitch += (err * 0.12 + noise_pitch - (1.6 + 2.3 * p.guide) * self.pitch - (0.9 + 0.7 * p.guide) * self.vpitch) * dt
        if self.disturb > 0:
            self.vpitch += 12.0 * dt
        self.pitch += self.vpitch * dt
        self.pitch = clamp(self.pitch, -8.5, 8.5)

        # Current and heating.
        wanted_current = 2.0 + abs(err) * 0.24 + abs(self.vgap) * 0.012 + (mass_load - 1.0) * 0.55
        power_limit = min(p.current_limit, p.voltage / max(p.resistance, 0.1))
        self.current += (clamp(wanted_current, 0, power_limit) - self.current) * min(1.0, dt * 6.0)
        heating = (self.current ** 2) * p.resistance * 0.022
        cooling = (self.temp - 25.0) * 0.018
        self.temp += (heating - cooling) * dt

        # Propulsion.
        coils = self.coils(12)
        self.active_coil = 0
        for i, c in enumerate(coils):
            if c >= self.x:
                self.active_coil = i
                break
        target_c = coils[self.active_coil]
        d = target_c - self.x
        shape = math.exp(-((d - 0.045) ** 2) / (2 * 0.10 ** 2))
        force = p.propulsion * shape
        if self.brake > 0:
            force -= 1.5 * self.vx + 0.2
            self.brake -= dt
        if self.x > TRACK_LEN_M - 0.25:
            force -= 1.8 * self.vx + 1.4 * (self.x - (TRACK_LEN_M - 0.25))
        drag = p.friction * self.vx * abs(self.vx)
        ax = (force - drag) / mass
        self.vx += ax * dt
        self.vx = clamp(self.vx, -0.10, p.max_speed)
        self.x += self.vx * dt
        if self.x > TRACK_LEN_M:
            self.x = 0.06
            self.vx = 0
        if self.x < 0.04:
            self.x = 0.04
            self.vx = 0

        # Status.
        if self.gap <= MIN_GAP_MM + 0.3:
            self.status = "RAYA YAKIN"
        elif self.gap >= MAX_GAP_MM - 0.3:
            self.status = "KONTROL DIŞI"
        elif abs(self.pitch) > 6.2:
            self.status = "EĞİM UYARISI"
        elif self.current > power_limit * 0.92:
            self.status = "AKIM LİMİTİ"
        elif self.temp > 70:
            self.status = "SICAKLIK"
        elif abs(self.gap - target) > 2.6:
            self.status = "BOŞLUK UYARISI"
        else:
            self.status = "KARARLI"

        for k, val in {
            "gap": self.gap,
            "pitch": self.pitch,
            "speed": self.vx,
            "current": self.current,
            "temp": self.temp,
        }.items():
            self.history[k].append(val)
            if len(self.history[k]) > 260:
                self.history[k].pop(0)

        if len(self.export_rows) < 5000:
            self.export_rows.append({
                "time_s": round(self.t, 4),
                "gap_mm": round(self.gap, 4),
                "pitch_deg": round(self.pitch, 4),
                "speed_mps": round(self.vx, 4),
                "current_A": round(self.current, 4),
                "temperature_C": round(self.temp, 4),
                "position_m": round(self.x, 4),
            })

# ============================================================
# UYGULAMA
# ============================================================


class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(f"{APP_TITLE} - {VERSION}")
        self.screen = pygame.display.set_mode((START_W, START_H), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.fonts = self.make_fonts()
        self.w, self.h = START_W, START_H
        self.left_w = 320
        self.right_w = 330
        self.top_h = 56
        self.paused = False
        self.show_vectors = True
        self.show_graphs = True
        self.show_help = True
        self.scroll = 0
        self.max_scroll = 0
        self.selected_key = "kp"
        self.preset_name = "Dengeli"
        self.message = "Hazır"
        self.message_timer = 0
        self.sim = MaglevSim()
        self.sliders: Dict[str, Slider] = {}
        self.buttons: List[Button] = []
        self.init_controls()
        self.make_buttons()

    def make_fonts(self):
        # Segoe UI Windows'ta iyi görünür, yoksa pygame varsayılanına düşer.
        return {
            "title": pygame.font.SysFont("segoeui", 22, bold=True),
            "h1": pygame.font.SysFont("segoeui", 18, bold=True),
            "font": pygame.font.SysFont("segoeui", 15),
            "small": pygame.font.SysFont("segoeui", 13),
            "tiny": pygame.font.SysFont("segoeui", 12),
            "metric": pygame.font.SysFont("segoeui", 20, bold=True),
        }

    def layout(self):
        self.w, self.h = self.screen.get_size()
        self.w = max(self.w, MIN_W)
        self.h = max(self.h, MIN_H)
        self.left_w = int(clamp(self.w * 0.24, 300, 355))
        self.right_w = int(clamp(self.w * 0.25, 300, 380))
        self.center_x = self.left_w + 12
        self.center_w = self.w - self.left_w - self.right_w - 24
        self.right_x = self.w - self.right_w
        self.sim_rect = pygame.Rect(self.center_x + 12, self.top_h + 70, self.center_w - 24, max(300, self.h - self.top_h - 245))
        self.track_y = self.sim_rect.bottom - 72
        self.px_per_mm = clamp((self.track_y - self.sim_rect.y - 30) / 32.0, 4.5, 8.0)

    def init_controls(self):
        def add(key, label, lo, hi, val, step, unit, category):
            self.sliders[key] = Slider(key, label, lo, hi, val, step, unit, category)
        add("target_gap", "Hedef boşluk", 4.0, 18.0, 8.0, 0.5, "mm", "Fizik")
        add("guide", "Kılavuz / Stabilizör", 0.0, 2.0, 1.0, 0.05, "", "Fizik")
        add("friction", "Sürtünme katsayısı", 0.05, 2.0, 0.90, 0.05, "", "Fizik")
        add("mass", "Kütle", 50, 500, 150, 10, "g", "Fizik")
        add("kp", "Kp", 0, 900, 210, 5, "", "PID Kontrol")
        add("ki", "Ki", 0, 80, 0, 1, "", "PID Kontrol")
        add("kd", "Kd", 0, 18, 3.2, 0.1, "", "PID Kontrol")
        add("voltage", "Voltaj", 6, 24, 12, 0.5, "V", "Güç ve Bobin")
        add("resistance", "Bobin direnci", 0.5, 5.0, 2.0, 0.1, "Ω", "Güç ve Bobin")
        add("current_limit", "Maks. akım limiti", 1.0, 12.0, 6.0, 0.5, "A", "Güç ve Bobin")
        add("noise", "Sensör gürültüsü", 0.0, 0.50, 0.04, 0.01, "mm", "Sensör")
        add("propulsion", "İtki kuvveti", 0.02, 0.70, 0.16, 0.01, "N", "Ray ve Hareket")
        add("max_speed", "Maksimum hız", 0.15, 1.20, 0.45, 0.05, "m/s", "Ray ve Hareket")
        add("sim_speed", "Simülasyon hızı", 0.10, 1.0, 0.35, 0.05, "x", "Ray ve Hareket")

    def make_buttons(self):
        self.buttons = [
            Button("Dengeli", lambda: self.apply_preset("Dengeli"), BLUE_2),
            Button("Yavaş", lambda: self.apply_preset("Yavaş"), (23, 110, 105)),
            Button("Ağır", lambda: self.apply_preset("Ağır"), (78, 56, 130)),
            Button("Kararsız", lambda: self.apply_preset("Kararsız"), (134, 55, 33)),
            Button("Sıfırla", self.reset_all, (44, 57, 76)),
        ]

    def params(self) -> Params:
        return Params(**{k: s.value for k, s in self.sliders.items()})

    def apply_preset(self, name):
        presets = {
            "Dengeli": dict(mass=150, target_gap=8, guide=1.0, friction=0.9, kp=210, ki=0, kd=3.2, voltage=12, resistance=2.0, current_limit=6, noise=0.04, propulsion=0.16, max_speed=0.45, sim_speed=0.35),
            "Yavaş": dict(mass=150, target_gap=8, guide=1.25, friction=1.25, kp=190, ki=0, kd=3.8, voltage=12, resistance=2.0, current_limit=6, noise=0.03, propulsion=0.08, max_speed=0.25, sim_speed=0.22),
            "Ağır": dict(mass=280, target_gap=7.5, guide=1.15, friction=1.1, kp=260, ki=0, kd=4.2, voltage=14, resistance=1.8, current_limit=7, noise=0.04, propulsion=0.11, max_speed=0.36, sim_speed=0.32),
            "Kararsız": dict(mass=150, target_gap=12, guide=0.25, friction=0.45, kp=650, ki=0, kd=0.6, voltage=12, resistance=2.0, current_limit=6, noise=0.20, propulsion=0.48, max_speed=0.70, sim_speed=0.35),
        }
        for k, v in presets[name].items():
            self.sliders[k].set(v)
        self.preset_name = name
        self.sim.reset()
        self.toast(f"{name} preseti yüklendi")

    def reset_all(self):
        self.sim.reset()
        self.toast("Simülasyon sıfırlandı")

    def toast(self, msg):
        self.message = msg
        self.message_timer = 2.0

    def export_csv(self):
        path = Path.cwd() / f"maglev_export_{int(time.time())}.csv"
        rows = self.sim.export_rows
        if not rows:
            self.toast("Dışa aktarılacak veri yok")
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        self.toast(f"CSV kaydedildi: {path.name}")

    def x_to_screen(self, x_m):
        return int(self.sim_rect.x + (x_m / TRACK_LEN_M) * self.sim_rect.w)

    def handle_event(self, ev):
        if ev.type == pygame.QUIT:
            return False
        if ev.type == pygame.VIDEORESIZE:
            self.screen = pygame.display.set_mode((max(ev.w, MIN_W), max(ev.h, MIN_H)), pygame.RESIZABLE)
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                return False
            if ev.key == pygame.K_SPACE:
                self.paused = not self.paused
            if ev.key == pygame.K_r:
                self.reset_all()
            if ev.key == pygame.K_d:
                self.sim.hit(); self.toast("Darbe uygulandı")
            if ev.key == pygame.K_s:
                self.sim.brake_pulse(); self.toast("Fren uygulandı")
            if ev.key == pygame.K_a:
                self.show_vectors = not self.show_vectors
            if ev.key == pygame.K_g:
                self.show_graphs = not self.show_graphs
            if ev.key == pygame.K_h:
                self.show_help = not self.show_help
        if ev.type == pygame.MOUSEWHEEL:
            mx, _ = pygame.mouse.get_pos()
            if mx < self.left_w:
                self.scroll = clamp(self.scroll - ev.y * 35, 0, self.max_scroll)
                return True
        for b in self.buttons:
            if b.event(ev):
                return True
        for k, s in self.sliders.items():
            old = s.value
            if s.event(ev):
                self.selected_key = k
                if abs(old - s.value) > 1e-9:
                    self.toast(f"{s.label}: {s.value_str()}")
                return True
        # top action buttons handled by position in draw_topbar with rects
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if getattr(self, "help_btn", pygame.Rect(0, 0, 0, 0)).collidepoint(ev.pos):
                self.show_help = not self.show_help
            if getattr(self, "export_btn", pygame.Rect(0, 0, 0, 0)).collidepoint(ev.pos):
                self.export_csv()
            if getattr(self, "theme_btn", pygame.Rect(0, 0, 0, 0)).collidepoint(ev.pos):
                self.toast("Tema butonu şimdilik görsel")
        return True

    # ========================================================
    # ÇİZİM
    # ========================================================

    def draw(self):
        self.layout()
        self.screen.fill(BG)
        self.draw_topbar()
        self.draw_left_panel()
        self.draw_center()
        self.draw_right_panel()
        if self.message_timer > 0:
            self.draw_toast()
        pygame.display.flip()

    def draw_topbar(self):
        rounded(self.screen, (7, 13, 22), (0, 0, self.w, self.top_h), 0)
        pygame.draw.line(self.screen, BORDER, (0, self.top_h - 1), (self.w, self.top_h - 1), 1)
        # logo
        pygame.draw.polygon(self.screen, CYAN, [(20, 19), (46, 13), (58, 26), (35, 34)])
        pygame.draw.line(self.screen, WHITE, (24, 30), (57, 30), 2)
        text(self.screen, self.fonts["title"], APP_TITLE, 70, 16, TEXT)
        text(self.screen, self.fonts["small"], VERSION, 340, 22, MUTED)
        # actions
        x = self.w - 520
        self.help_btn = self.draw_top_button(x, 12, 88, "?  Yardım")
        self.draw_top_button(x + 96, 12, 132, "▣  Senaryoyu Kaydet")
        self.export_btn = self.draw_top_button(x + 238, 12, 132, "↓  Veriyi Dışa Aktar")
        self.theme_btn = self.draw_top_button(x + 380, 12, 88, "◉  Tema")

    def draw_top_button(self, x, y, w, label):
        r = pygame.Rect(x, y, w, 32)
        rounded(self.screen, (10, 20, 34), r, 8)
        rounded(self.screen, BORDER, r, 8, 1)
        text_center(self.screen, self.fonts["tiny"], label, r, TEXT)
        return r

    def draw_left_panel(self):
        pygame.draw.rect(self.screen, PANEL, (0, self.top_h, self.left_w, self.h - self.top_h))
        pygame.draw.line(self.screen, BORDER, (self.left_w, self.top_h), (self.left_w, self.h), 1)
        x = 16
        y = self.top_h + 18
        text(self.screen, self.fonts["h1"], "KONTROL PANELİ", x, y, BLUE)
        y += 30
        # search box
        search = pygame.Rect(x, y, self.left_w - 32, 34)
        rounded(self.screen, (12, 22, 36), search, 8)
        rounded(self.screen, BORDER, search, 8, 1)
        text(self.screen, self.fonts["small"], "⌕  Kontrol veya ayar ara...", search.x + 12, search.y + 8, MUTED)
        text(self.screen, self.fonts["tiny"], "Ctrl + K", search.right - 62, search.y + 9, FAINT)
        y += 50

        text(self.screen, self.fonts["small"], "PRESETLER", x, y, BLUE)
        y += 24
        bw = (self.left_w - 44) // 2
        bh = 34
        for i, b in enumerate(self.buttons):
            bx = x + (i % 2) * (bw + 10)
            by = y + (i // 2) * (bh + 10)
            active = b.label == self.preset_name
            b.draw(self.screen, self.fonts["small"], (bx, by, bw, bh), active=active)
        y += math.ceil(len(self.buttons) / 2) * (bh + 10) + 8

        clip = pygame.Rect(0, y, self.left_w, self.h - y - 28)
        old_clip = self.screen.get_clip()
        self.screen.set_clip(clip)
        cy = y - self.scroll
        categories = ["Fizik", "PID Kontrol", "Güç ve Bobin", "Sensör", "Ray ve Hareket"]
        for cat in categories:
            if cy > y - 60 and cy < self.h:
                self.draw_section_header(cat, x, cy)
            cy += 34
            for s in [sl for sl in self.sliders.values() if sl.category == cat]:
                if cy > y - 60 and cy < self.h:
                    s.draw(self.screen, self.fonts, x, cy, self.left_w - 32, active=(s.key == self.selected_key))
                cy += 50
            cy += 8
        self.max_scroll = max(0, cy - (self.h - 28))
        self.screen.set_clip(old_clip)

        text(self.screen, self.fonts["tiny"], "SPACE pause | R reset | D darbe | S fren | A vektör | G grafik | H yardım", 14, self.h - 22, FAINT)

    def draw_section_header(self, title, x, y):
        rounded(self.screen, (12, 22, 36), (x - 2, y, self.left_w - 28, 28), 8)
        icon = {"Fizik": "◎", "PID Kontrol": "P", "Güç ve Bobin": "ϟ", "Sensör": "◉", "Ray ve Hareket": "↔"}.get(title, "▣")
        text(self.screen, self.fonts["small"], f"{icon}  {title.upper()}", x + 8, y + 6, CYAN)
        text(self.screen, self.fonts["small"], "⌃", self.left_w - 42, y + 5, MUTED)

    def draw_center(self):
        p = self.params()
        # center panel background
        rounded(self.screen, PANEL, (self.center_x, self.top_h + 8, self.center_w, self.h - self.top_h - 16), 12)
        rounded(self.screen, BORDER, (self.center_x, self.top_h + 8, self.center_w, self.h - self.top_h - 16), 12, 1)
        text(self.screen, self.fonts["h1"], "2D MAGLEV RAY SİMÜLASYONU", self.center_x + 18, self.top_h + 28, TEXT)
        text(self.screen, self.fonts["small"], "Kaydır: yakınlaş/uzaklaş  |  Sürükle: görünümü kaydır", self.center_x + 18, self.top_h + 54, MUTED)
        self.draw_canvas(p)
        self.draw_bottom_status(p)
        self.draw_metric_strip(p)

    def draw_canvas(self, p: Params):
        r = self.sim_rect
        rounded(self.screen, BG_SOFT, r, 10)
        rounded(self.screen, BORDER, r, 10, 1)
        # grid
        for i in range(7):
            x = r.x + int(i * r.w / 6)
            pygame.draw.line(self.screen, GRID, (x, r.y), (x, r.bottom), 1)
        for mm in [-10, 0, 10, 20, 30]:
            y = int(self.track_y - mm * self.px_per_mm)
            if r.y <= y <= r.bottom:
                pygame.draw.line(self.screen, GRID, (r.x, y), (r.right, y), 1)
                text(self.screen, self.fonts["tiny"], f"{mm}", r.x + 10, y - 8, FAINT)
        text(self.screen, self.fonts["tiny"], "Boşluk (mm)", r.x + 10, r.y + 14, MUTED)
        # target line
        ty = int(self.track_y - p.target_gap * self.px_per_mm)
        pygame.draw.line(self.screen, CYAN, (r.x + 1, ty), (r.right - 1, ty), 1)
        text(self.screen, self.fonts["tiny"], "- - Hedef boşluk", r.right - 145, r.y + 18, CYAN)

        self.draw_track()
        self.draw_coils()
        self.draw_train(p)

        # x-axis marks
        for m in [-1.0, -0.5, 0, 0.5, 1.0]:
            x = r.centerx + int(m * (r.w / 2.5))
            if r.x < x < r.right:
                pygame.draw.line(self.screen, FAINT, (x, self.track_y + 40), (x, self.track_y + 62), 1)
                text(self.screen, self.fonts["tiny"], f"{m:.1f} m" if m != 0 else "0 m", x - 18, self.track_y + 64, BLUE if m == 0 else FAINT)

    def draw_track(self):
        r = self.sim_rect
        pygame.draw.line(self.screen, RAIL_DARK, (r.x + 30, self.track_y + 32), (r.right - 30, self.track_y + 32), 12)
        pygame.draw.line(self.screen, RAIL, (r.x + 30, self.track_y + 12), (r.right - 30, self.track_y + 12), 5)
        pygame.draw.line(self.screen, RAIL, (r.x + 30, self.track_y + 36), (r.right - 30, self.track_y + 36), 5)
        for x in range(r.x + 40, r.right - 20, 54):
            pygame.draw.line(self.screen, (95, 108, 130), (x, self.track_y + 4), (x + 18, self.track_y + 44), 2)

    def draw_coils(self):
        p = self.params()
        coils = self.sim.coils(12)
        heat = clamp((self.sim.temp - 35) / 50, 0, 1)
        for i, c in enumerate(coils):
            x = self.x_to_screen(c)
            active = i == self.sim.active_coil
            near = math.exp(-((c - self.sim.x) ** 2) / (2 * 0.08 ** 2))
            col = color_lerp(COIL_OFF, COIL_ON, 0.30 * near + (0.75 if active else 0))
            col = color_lerp(col, HOT, heat)
            if active:
                glow(self.screen, (x, self.track_y + 24), 36, COIL_ON, 0.6)
            pygame.draw.circle(self.screen, (12, 18, 28), (x, self.track_y + 24), 25)
            pygame.draw.circle(self.screen, col, (x, self.track_y + 24), 20)
            pygame.draw.circle(self.screen, COPPER if active else color_lerp(COPPER, COIL_OFF, 0.45), (x, self.track_y + 24), 13, 3)
            pygame.draw.circle(self.screen, BG, (x, self.track_y + 24), 7)

    def draw_train(self, p: Params):
        r = self.sim_rect
        x = self.x_to_screen(self.sim.x)
        y = self.track_y - self.sim.gap * self.px_per_mm - TRAIN_BODY_H // 2
        # shadow
        shadow_w = int(TRAIN_BODY_W * 0.92)
        shadow = pygame.Surface((shadow_w, 24), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 95), (0, 0, shadow_w, 24))
        self.screen.blit(shadow, (x - shadow_w // 2, self.track_y + 2))

        body = pygame.Surface((TRAIN_BODY_W, TRAIN_BODY_H), pygame.SRCALPHA)
        # body shape
        pygame.draw.polygon(body, TRAIN_WHITE, [(18, 30), (58, 5), (182, 5), (222, 28), (206, 48), (32, 50)])
        pygame.draw.polygon(body, (188, 205, 226), [(18, 30), (32, 50), (206, 48), (222, 28), (215, 58), (20, 58)])
        pygame.draw.polygon(body, WINDOW, [(65, 14), (166, 14), (198, 28), (178, 38), (52, 38)])
        for wx in [95, 128, 164]:
            pygame.draw.rect(body, BLUE, (wx, 27, 10, 4), border_radius=2)
        pygame.draw.rect(body, BLUE, (50, 51, 42, 5), border_radius=3)
        pygame.draw.rect(body, BLUE, (145, 51, 52, 5), border_radius=3)
        pygame.draw.circle(body, status_col(self.sim.status), (207, 19), 5)
        angle = -self.sim.pitch
        rotated = pygame.transform.rotate(body, angle)
        rect = rotated.get_rect(center=(x, int(y)))
        glow(self.screen, (x - 45, int(y + TRAIN_BODY_H / 2)), 46, BLUE, 0.28)
        glow(self.screen, (x + 48, int(y + TRAIN_BODY_H / 2)), 46, BLUE, 0.28)
        self.screen.blit(rotated, rect)
        # gap measurement
        pygame.draw.line(self.screen, GREEN, (x, int(y + TRAIN_BODY_H / 2)), (x, self.track_y + 12), 2)
        lab = pygame.Rect(x - 42, int((y + TRAIN_BODY_H / 2 + self.track_y) / 2) - 15, 84, 28)
        rounded(self.screen, (10, 60, 32), lab, 10)
        rounded(self.screen, GREEN, lab, 10, 1)
        text_center(self.screen, self.fonts["small"], f"{self.sim.gap:.2f} mm", lab, GREEN)
        if self.show_vectors:
            # Lift and propulsion arrows.
            self.arrow((x - 50, int(y + 30)), (x - 50, int(y - 35)), GREEN, "F")
            self.arrow((x + 10, int(y + 30)), (x + 72, int(y + 30)), ORANGE, "itki")

    def arrow(self, start, end, col, label):
        pygame.draw.line(self.screen, col, start, end, 3)
        ex, ey = end
        sx, sy = start
        ang = math.atan2(ey - sy, ex - sx)
        pts = []
        for da in [0, 2.5, -2.5]:
            pts.append((ex - 10 * math.cos(ang + da), ey - 10 * math.sin(ang + da)))
        pygame.draw.polygon(self.screen, col, [(ex, ey), pts[1], pts[2]])
        text(self.screen, self.fonts["tiny"], label, ex + 5, ey - 12, col)

    def draw_bottom_status(self, p):
        y = self.sim_rect.bottom + 12
        r = pygame.Rect(self.center_x + 22, y, self.center_w - 44, 64)
        rounded(self.screen, CARD, r, 12)
        rounded(self.screen, BORDER, r, 12, 1)
        # pause button
        btn = pygame.Rect(r.x + 14, r.y + 13, 40, 40)
        rounded(self.screen, BLUE, btn, 20)
        icon = "▶" if self.paused else "Ⅱ"
        text_center(self.screen, self.fonts["h1"], icon, btn, WHITE)
        state = "DURAKLATILDI" if self.paused else "ÇALIŞIYOR"
        text(self.screen, self.fonts["small"], state, btn.right + 16, r.y + 13, YELLOW if self.paused else GREEN)
        text(self.screen, self.fonts["small"], f"Zaman: {self.sim.t:05.1f}s", btn.right + 16, r.y + 36, MUTED)
        # speed buttons visual
        tx = r.right - 290
        text(self.screen, self.fonts["small"], "Simülasyon hızı", tx, r.y + 22, MUTED)
        for i, (label, val) in enumerate([("0.5x", 0.5), ("1x", 1.0), ("2x", 2.0)]):
            bx = pygame.Rect(tx + 122 + i * 54, r.y + 17, 46, 30)
            active = abs(p.sim_speed - val) < 0.05
            rounded(self.screen, BLUE_2 if active else PANEL_3, bx, 8)
            rounded(self.screen, BORDER, bx, 8, 1)
            text_center(self.screen, self.fonts["tiny"], label, bx, TEXT)

    def draw_metric_strip(self, p):
        y = self.sim_rect.bottom + 90
        if y + 86 > self.h:
            return
        r = pygame.Rect(self.center_x + 22, y, self.center_w - 44, 78)
        rounded(self.screen, (12, 22, 36), r, 12)
        rounded(self.screen, BORDER, r, 12, 1)
        metrics = [
            ("Hedef Boşluk", f"{p.target_gap:.2f} mm", CYAN),
            ("Gerçek Boşluk", f"{self.sim.gap:.2f} mm", GREEN),
            ("Hız", f"{self.sim.vx:.2f} m/s", BLUE),
            ("Sıcaklık", f"{self.sim.temp:.1f} °C", ORANGE),
            ("Akım", f"{self.sim.current:.2f} A", PURPLE),
            ("Pozisyon", f"{self.sim.x:.2f} m", CYAN),
        ]
        gap = 10
        w = int((r.w - gap * (len(metrics) + 1)) / len(metrics))
        for i, (lab, val, col) in enumerate(metrics):
            cr = pygame.Rect(r.x + gap + i * (w + gap), r.y + 10, w, 58)
            rounded(self.screen, CARD, cr, 10)
            text_center(self.screen, self.fonts["tiny"], lab, (cr.x, cr.y + 8, cr.w, 18), MUTED)
            text_center(self.screen, self.fonts["metric"], val, (cr.x, cr.y + 28, cr.w, 24), col)

    def draw_right_panel(self):
        pygame.draw.rect(self.screen, PANEL, (self.right_x, self.top_h, self.right_w, self.h - self.top_h))
        pygame.draw.line(self.screen, BORDER, (self.right_x, self.top_h), (self.right_x, self.h), 1)
        x = self.right_x + 16
        y = self.top_h + 18
        text(self.screen, self.fonts["h1"], "TELEMETRİ", x, y, BLUE)
        y += 34
        self.draw_telemetry_grid(x, y)
        y += 228
        if self.show_graphs:
            self.draw_graphs(x, y)
            y += 270
        if self.show_help:
            self.draw_help_card(x, y)

    def draw_telemetry_grid(self, x, y):
        p = self.params()
        items = [
            ("Durum", self.sim.status, status_col(self.sim.status)),
            ("Boşluk", f"{self.sim.gap:.2f} mm", CYAN),
            ("Ön Gap", f"{self.sim.gap + self.sim.pitch*0.04:.2f} mm", TEXT),
            ("Arka Gap", f"{self.sim.gap - self.sim.pitch*0.04:.2f} mm", TEXT),
            ("Pitch", f"{self.sim.pitch:+.2f}°", TEXT),
            ("Hız", f"{self.sim.vx:.2f} m/s", TEXT),
            ("Pozisyon", f"{self.sim.x:.2f} m", TEXT),
            ("Akım", f"{self.sim.current:.2f} A", PURPLE),
            ("Sıcaklık", f"{self.sim.temp:.1f} °C", ORANGE),
            ("Bobin", f"Aktif #{self.sim.active_coil+1}", TEXT),
            ("Akım Limiti", f"{p.current_limit:.2f} A", TEXT),
            ("Voltaj", f"{p.voltage:.1f} V", TEXT),
        ]
        cols = 3
        gap = 8
        cw = int((self.right_w - 32 - gap * (cols - 1)) / cols)
        ch = 52
        for i, (lab, val, col) in enumerate(items):
            rx = x + (i % cols) * (cw + gap)
            ry = y + (i // cols) * (ch + gap)
            rounded(self.screen, CARD, (rx, ry, cw, ch), 8)
            rounded(self.screen, BORDER, (rx, ry, cw, ch), 8, 1)
            text(self.screen, self.fonts["tiny"], lab, rx + 10, ry + 8, MUTED)
            text_center(self.screen, self.fonts["small"], val, (rx, ry + 24, cw, 20), col)

    def draw_graphs(self, x, y):
        panel = pygame.Rect(x, y, self.right_w - 32, 250)
        rounded(self.screen, (12, 22, 36), panel, 10)
        rounded(self.screen, BORDER, panel, 10, 1)
        text(self.screen, self.fonts["small"], "GRAFİKLER  (Gerçek zamanlı)", panel.x + 12, panel.y + 10, BLUE)
        charts = [
            ("Boşluk (mm)", "gap", GREEN, 0, 30),
            ("Pitch (°)", "pitch", PURPLE, -8, 8),
            ("Akım (A)", "current", BLUE, 0, 8),
            ("Sıcaklık (°C)", "temp", ORANGE, 20, 90),
        ]
        cw = (panel.w - 34) // 2
        ch = 86
        for i, (title, key, col, lo, hi) in enumerate(charts):
            rx = panel.x + 12 + (i % 2) * (cw + 10)
            ry = panel.y + 38 + (i // 2) * (ch + 10)
            self.draw_chart((rx, ry, cw, ch), title, self.sim.history[key], col, lo, hi)

    def draw_chart(self, rect, title, data, col, lo, hi):
        rounded(self.screen, PANEL_2, rect, 8)
        text(self.screen, self.fonts["tiny"], title, rect[0] + 8, rect[1] + 6, TEXT)
        if data:
            text(self.screen, self.fonts["tiny"], fmt(data[-1], 2), rect[0] + rect[2] - 44, rect[1] + 6, col)
        plot = pygame.Rect(rect[0] + 8, rect[1] + 28, rect[2] - 16, rect[3] - 36)
        pygame.draw.line(self.screen, GRID, (plot.x, plot.centery), (plot.right, plot.centery), 1)
        if len(data) > 1:
            pts = []
            n = min(len(data), plot.w)
            subset = data[-n:]
            for i, v in enumerate(subset):
                x = plot.x + int(i * plot.w / max(1, n - 1))
                y = plot.bottom - int(clamp((v - lo) / max(1e-9, hi - lo), 0, 1) * plot.h)
                pts.append((x, y))
            if len(pts) >= 2:
                pygame.draw.lines(self.screen, col, False, pts, 2)

    def draw_help_card(self, x, y):
        # Keep visible; if screen short, anchor near bottom.
        h = min(190, max(140, self.h - y - 20))
        if h < 125:
            y = self.h - 205
            h = 185
        panel = pygame.Rect(x, y, self.right_w - 32, h)
        rounded(self.screen, (12, 22, 36), panel, 10)
        rounded(self.screen, BORDER, panel, 10, 1)
        info = INFO.get(self.selected_key, INFO["kp"])
        text(self.screen, self.fonts["small"], "BU KONTROL NE İŞE YARAR?", panel.x + 12, panel.y + 10, TEXT)
        text(self.screen, self.fonts["tiny"], f"Seçili: {info['title']}", panel.right - 120, panel.y + 12, BLUE)
        yy = panel.y + 38
        entries = [
            ("Ne işe yarar?", info["what"], CYAN),
            ("Artırırsan", info["up"], GREEN),
            ("Azaltırsan", info["down"], ORANGE),
            ("Ne izlemeli?", info["watch"], RED),
        ]
        for head, body, col in entries:
            if yy > panel.bottom - 32:
                break
            text(self.screen, self.fonts["tiny"], head + ":", panel.x + 14, yy, col)
            yy += 15
            for line in wrap_lines(body, self.fonts["tiny"], panel.w - 28):
                if yy > panel.bottom - 18:
                    break
                text(self.screen, self.fonts["tiny"], line, panel.x + 14, yy, MUTED)
                yy += 14
            yy += 4

    def draw_toast(self):
        self.message_timer -= 1 / FPS
        msg = self.message
        font = self.fonts["small"]
        w = font.size(msg)[0] + 36
        r = pygame.Rect(self.center_x + self.center_w // 2 - w // 2, self.h - 48, w, 34)
        rounded(self.screen, (16, 30, 50), r, 12)
        rounded(self.screen, BLUE, r, 12, 1)
        text_center(self.screen, font, msg, r, TEXT)

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            for ev in pygame.event.get():
                if self.handle_event(ev) is False:
                    running = False
            if not self.paused:
                # a few substeps for smoother values
                p = self.params()
                for _ in range(2):
                    self.sim.step(dt / 2, p)
            self.draw()
        pygame.quit()


def status_col(s: str):
    if s == "KARARLI":
        return GREEN
    if "UYARI" in s or "LİMİT" in s or "SICAK" in s or "YAKIN" in s:
        return ORANGE
    return RED


if __name__ == "__main__":
    App().run()
