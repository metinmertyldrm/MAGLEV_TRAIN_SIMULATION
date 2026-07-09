# -*- coding: utf-8 -*-
"""
MAGLEV TRAIN VISUAL SIMULATION - V12 FINAL DEMO PACKAGE
------------------------------------------------
Bu sürümün amacı: sadece çalışan bir demo değil, yeni başlayan birinin de
hangi ayarın neyi değiştirdiğini rahat okuyabildiği kullanıcı dostu bir
simülasyon ekranı sunmak.

V12 paketi; final demo, örnek veri, senaryo kayıtları, raporlama ve Unity/Unreal geçiş dokümanlarıyla birlikte gelir.

Çalıştırma:
    py maglev_pygame_v12_final_demo.py

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
    M     : başlangıç/gelişmiş mod değiştir
    ESC   : çıkış
"""

import csv
import json
import math
import os
import sys
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
VERSION = "v12.0-final-demo"
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



# Başlangıç modunda görünen temel kontroller. Amaç: kullanıcıyı ilk açılışta boğmamak.
BASIC_KEYS = [
    "target_gap", "mass", "kp", "kd", "noise", "propulsion", "max_speed", "sim_speed"
]

CHANGE_EFFECTS: Dict[str, Dict[str, str]] = {
    "target_gap": {
        "increase": "Hedef boşluk büyüdü. Tren raydan daha uzakta tutulmaya çalışılır; bobin daha çok zorlanabilir.",
        "decrease": "Hedef boşluk küçüldü. Havada tutmak kolaylaşır ama tren raya çok yaklaşabilir.",
        "watch": "Gerçek boşluk hedef çizgiye oturuyor mu ve akım limiti yükseliyor mu?",
    },
    "mass": {
        "increase": "Tren ağırlaştı. Daha fazla kaldırma kuvveti, daha fazla akım ve daha fazla ısı beklenir.",
        "decrease": "Tren hafifledi. Sistem daha kolay dengede kalır; fazla agresif PID varsa zıplama görülebilir.",
        "watch": "Akım, sıcaklık ve boşluk hatasına bak.",
    },
    "kp": {
        "increase": "Kp arttı. Sistem hataya daha sert tepki verir; hedefe hızlı döner ama salınım artabilir.",
        "decrease": "Kp azaldı. Sistem daha sakinleşir; hedefe dönüş yavaşlayabilir.",
        "watch": "Boşluk grafiğinde aşım ve titreşim var mı?",
    },
    "ki": {
        "increase": "Ki arttı. Kalıcı küçük hataları düzeltmeye çalışır; fazla artarsa sistem taşabilir.",
        "decrease": "Ki azaldı. Sistem daha güvenli olur ama küçük sabit hata kalabilir.",
        "watch": "Uzun sürede hedefe tam oturuyor mu, yoksa aşırı düzeltme mi yapıyor?",
    },
    "kd": {
        "increase": "Kd arttı. Salınımı frenler; titreşim azalabilir ama tepki yavaşlayabilir.",
        "decrease": "Kd azaldı. Sistem daha canlı tepki verir; zıplama ve pitch salınımı artabilir.",
        "watch": "Pitch ve boşluk dalgalanması azaldı mı?",
    },
    "voltage": {
        "increase": "Voltaj arttı. Bobin daha güçlü olabilir ama ısınma riski yükselir.",
        "decrease": "Voltaj azaldı. Sistem daha zayıf olur; ağır tren hedef boşluğu koruyamayabilir.",
        "watch": "Akım limiti, sıcaklık ve durum uyarılarına bak.",
    },
    "resistance": {
        "increase": "Direnç arttı. Aynı voltajda akım azalır; manyetik kuvvet zayıflayabilir.",
        "decrease": "Direnç azaldı. Daha fazla akım geçebilir; ısınma riski artar.",
        "watch": "Akım limiti ve sıcaklık hızlı yükseliyor mu?",
    },
    "current_limit": {
        "increase": "Akım limiti arttı. Sistem daha güçlü davranabilir ama güvenlik/ısınma riski artar.",
        "decrease": "Akım limiti azaldı. Sistem daha güvenli ama kaldırma gücü sınırlı olur.",
        "watch": "Ortalama akım sürekli limite dayanıyor mu?",
    },
    "noise": {
        "increase": "Sensör gürültüsü arttı. Kontrolcü daha kirli veri alır; akım ve gap daha titrek olabilir.",
        "decrease": "Sensör gürültüsü azaldı. Ölçüm temizleşir; kontrol daha kararlı görünür.",
        "watch": "Akım grafiğinde küçük hızlı zıplamalar var mı?",
    },
    "propulsion": {
        "increase": "İtki arttı. Tren daha hızlı gider; değerleri okumak zorlaşabilir ve eğim artabilir.",
        "decrease": "İtki azaldı. Tren daha yavaş gider; öğrenme ve sunum için daha okunabilir olur.",
        "watch": "Hız, aktif bobin ve pitch değişimine bak.",
    },
    "max_speed": {
        "increase": "Maksimum hız yükseldi. Tren daha hızlı akabilir; telemetriyi takip etmek zorlaşır.",
        "decrease": "Maksimum hız düştü. Simülasyon daha öğretici ve okunabilir olur.",
        "watch": "Hız kartı gözle takip edilebilir seviyede mi?",
    },
    "sim_speed": {
        "increase": "Simülasyon hızı arttı. Fizik daha hızlı akar; değişimlerin etkisini hızlı görürsün.",
        "decrease": "Simülasyon hızı düştü. Ağır çekim gibi olur; öğrenmek için daha iyidir.",
        "watch": "Sağdaki değerleri rahat okuyabiliyor musun?",
    },
    "guide": {
        "increase": "Kılavuz/stabilizer arttı. Tren eğimi daha çok bastırılır; daha kontrollü görünür.",
        "decrease": "Kılavuz/stabilizer azaldı. Pitch artar; mekanik kılavuzun önemi ortaya çıkar.",
        "watch": "Pitch değeri ve trenin burun hareketi nasıl değişiyor?",
    },
    "friction": {
        "increase": "Sürtünme arttı. Tren daha yavaşlar ve daha okunabilir hareket eder.",
        "decrease": "Sürtünme azaldı. Tren daha kolay hızlanır; kontrolü okumak zorlaşabilir.",
        "watch": "Hız ve pozisyon değişimi çok hızlı mı?",
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


# V11 yeni kontrollerin açıklamaları
INFO.update({
    "saturation_current": {"title": "Manyetik Doyum Akımı", "what": "Bobin/çekirdeğin manyetik olarak doyuma yaklaşmaya başladığı akımı temsil eder.", "up": "Artarsa sistem daha yüksek akımlarda bile verimli kalır.", "down": "Azalırsa akım artsa bile kaldırma kuvveti beklenen kadar artmaz.", "watch": "Doyum oranı, akım ve gap hatası yükseliyor mu?"},
    "voltage_sag": {"title": "Voltaj Düşümü", "what": "Kablo, güç kaynağı ve sürücü kayıplarından dolayı akım çekildikçe voltajın düşmesini temsil eder.", "up": "Artarsa yük altında bobin daha zayıf kalır.", "down": "Azalırsa güç sistemi daha ideal davranır.", "watch": "Bus voltajı ve akım limiti düşüyor mu?"},
    "sensor_fault_rate": {"title": "Sensör Arıza Olasılığı", "what": "Hall sensöründe anlık donma, outlier veya parazitli ölçüm oluşma ihtimalidir.", "up": "Artarsa kontrolcü yanlış veriyle çalışır ve tren kararsızlaşır.", "down": "Azalırsa ölçüm temizleşir.", "watch": "Durum sensör arızasına dönüyor mu ve gap sıçrıyor mu?"},
    "thermal_limit": {"title": "Termal Koruma Eşiği", "what": "Bobin sıcaklığı bu değeri geçince sistem akımı kısarak kendini korur.", "up": "Artarsa sistem daha geç korumaya girer ama bobin riski artar.", "down": "Azalırsa erken koruma başlar ve tren zayıflayabilir.", "watch": "Termal derate ve sıcaklık kartlarına bak."},
    "cooling_factor": {"title": "Bobin Soğutma Etkisi", "what": "Fan, heatsink veya hava akışının bobini ne kadar iyi soğuttuğunu temsil eder.", "up": "Artarsa sıcaklık daha yavaş yükselir.", "down": "Azalırsa termal koruma daha hızlı devreye girer.", "watch": "Sıcaklık grafiği ve termal koruma süresi."},
    "calibration_gain": {"title": "Kalibrasyon Kazancı", "what": "Gerçek Hall sensörü ölçümünü simülasyon birimine çevirmek için çarpan.", "up": "Ölçülen gap daha büyük yorumlanır.", "down": "Ölçülen gap daha küçük yorumlanır.", "watch": "Simülasyon-gerçek gap farkı azalıyor mu?"},
    "calibration_offset": {"title": "Kalibrasyon Ofseti", "what": "Gerçek sensör ölçümüne eklenen sabit mm düzeltmesi.", "up": "Tüm ölçüm yukarı kayar.", "down": "Tüm ölçüm aşağı kayar.", "watch": "Ortalama gap farkı sıfıra yaklaşıyor mu?"},
})
CHANGE_EFFECTS.update({
    "saturation_current": {"increase": "Doyum akımı arttı; bobin yüksek akımda daha verimli davranır.", "decrease": "Doyum akımı azaldı; akım artsa da kaldırma kuvveti sınırlanır.", "watch": "Akım yükselirken gap hâlâ bozuluyor mu?"},
    "voltage_sag": {"increase": "Voltaj düşümü arttı; yük altında bus voltajı ve kaldırma gücü düşer.", "decrease": "Voltaj düşümü azaldı; güç kaynağı daha ideal davranır.", "watch": "Bus voltajı ve akım limitine bak."},
    "sensor_fault_rate": {"increase": "Sensör arıza olasılığı arttı; kontrolcü yanlış/anlık donmuş veri alabilir.", "decrease": "Sensör arıza olasılığı azaldı; ölçüm güvenilirliği artar.", "watch": "Sensör arızası durumu ve gap sıçramalarını izle."},
    "thermal_limit": {"increase": "Termal koruma daha geç başlar; performans artabilir ama risk de artar.", "decrease": "Termal koruma daha erken başlar; güvenlik artar ama tren zayıflayabilir.", "watch": "Termal derate ve sıcaklığı izle."},
    "cooling_factor": {"increase": "Soğutma etkisi arttı; bobin daha geç ısınır.", "decrease": "Soğutma etkisi azaldı; termal koruma daha hızlı devreye girebilir.", "watch": "Sıcaklık eğrisinin eğimine bak."},
    "calibration_gain": {"increase": "Kalibrasyon kazancı arttı; gerçek ölçüm daha büyük yorumlanır.", "decrease": "Kalibrasyon kazancı azaldı; gerçek ölçüm daha küçük yorumlanır.", "watch": "Gerçek-simülasyon gap farkı azalıyor mu?"},
    "calibration_offset": {"increase": "Ofset arttı; tüm sensör ölçümü yukarı kayar.", "decrease": "Ofset azaldı; tüm sensör ölçümü aşağı kayar.", "watch": "Ortalama gap farkı sıfıra yaklaştı mı?"},
})

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
    # V11 gerçekçilik parametreleri
    saturation_current: float = 5.0      # A, bobin/çekirdek doyuma yaklaşma akımı
    voltage_sag: float = 0.25            # V/A, yük altında kaynak/kablo voltaj düşümü
    sensor_fault_rate: float = 0.0       # 0-1, sensör arızası/outlier olasılığı
    thermal_limit: float = 70.0          # °C, koruma eşiği
    cooling_factor: float = 1.0          # bobin soğutma çarpanı
    calibration_gain: float = 1.0        # gerçek veri kalibrasyonu için sensör kazancı
    calibration_offset: float = 0.0      # mm, gerçek veri kalibrasyonu için ofset


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
        self.derailed = False
        self.instability_index = 0.0
        self.warning_reason = ""
        # Senaryo verileri: simülasyon başladığı/resetlendiği andan kaydet butonuna kadar tutulur.
        self.export_rows: List[Dict[str, float]] = []
        # V11 gerçekçilik durumu
        self.sensor_fault_active = False
        self.sensor_fault_timer = 0.0
        self.sensor_fault_count = 0
        self.last_measured_gap = self.gap
        self.effective_current = self.current
        self.bus_voltage = 12.0
        self.thermal_derate = 1.0
        self.saturation_ratio = 0.0
        self.protection_active_time = 0.0

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
        # V11 sensör modeli: gürültü + arıza + kalibrasyon.
        raw_measured = self.gap + random.gauss(0, p.noise)
        if self.sensor_fault_timer > 0:
            self.sensor_fault_timer -= dt
            self.sensor_fault_active = True
        else:
            self.sensor_fault_active = False
            # fault_rate 0-1 arası; yüksek değerlerde kısa süreli takılma/outlier üretir.
            if random.random() < p.sensor_fault_rate * dt * 1.8:
                self.sensor_fault_active = True
                self.sensor_fault_timer = random.uniform(0.15, 0.65)
                self.sensor_fault_count += 1
        if self.sensor_fault_active:
            mode = self.sensor_fault_count % 3
            if mode == 0:
                raw_measured = self.last_measured_gap  # sensör dondu
            elif mode == 1:
                raw_measured += random.choice([-1, 1]) * random.uniform(1.5, 4.5)  # outlier
            else:
                raw_measured += 2.5 * math.sin(self.t * 9.0)  # parazitli veri
        measured = p.calibration_gain * raw_measured + p.calibration_offset
        measured = clamp(measured, 0.0, 40.0)
        self.last_measured_gap = measured
        err = measured - target

        # ----------------------------------------------------
        # Daha gerçekçi kararlılık modeli
        # ----------------------------------------------------
        # Önceki sürüm bilinçli olarak çok sakin tutulmuştu; bu yüzden kullanıcı bütün
        # değerleri uç değerlere çekse bile tren çoğunlukla kararlı kalıyordu. Burada
        # kötü PID, zayıf güç, yüksek sensör gürültüsü, düşük stabilizer ve hızlı itki
        # değerleri birlikte büyüyen bir "instability_index" oluşturur. Bu indeks hem
        # fizikte salınım üretir hem de skor/durum etiketlerini etkiler.
        self.integral = clamp(self.integral + err * dt, -6.0, 6.0)
        derivative = (err - self.prev_err) / max(dt, 1e-5)
        derivative = clamp(derivative, -160, 160)
        self.prev_err = err

        mass_load = mass / 0.15
        # V11 güç modeli: yük altında voltaj düşümü + termal koruma + akım limiti.
        self.bus_voltage = max(1.0, p.voltage - p.voltage_sag * max(0.0, self.current))
        raw_power_limit = min(p.current_limit, self.bus_voltage / max(p.resistance, 0.1))
        if self.temp <= p.thermal_limit:
            self.thermal_derate = 1.0
        else:
            # Eşik üstünde akımı kademeli kıs; limit +20°C civarında neredeyse kapat.
            self.thermal_derate = clamp(1.0 - (self.temp - p.thermal_limit) / 20.0, 0.05, 1.0)
            self.protection_active_time += dt
        power_limit = max(0.0, raw_power_limit * self.thermal_derate)
        # Hedef mesafe, kütle ve düşük stabilizer arttıkça yaklaşık gereken akım yükselir.
        required_current = 1.65 + 0.95 * (mass_load - 1.0) + 0.16 * max(0.0, target - 8.0) + 0.15 * max(0.0, 0.8 - p.guide)
        power_shortage = max(0.0, (required_current - power_limit) / max(required_current, 0.1))
        underdamped = max(0.0, (p.kp - 360.0) / 420.0) + max(0.0, (2.2 - p.kd) / 2.2)
        excessive_damping = max(0.0, (p.kd - 12.0) / 8.0)
        noise_factor = p.noise / 0.50
        guide_weak = max(0.0, (0.65 - p.guide) / 0.65)
        speed_risk = max(0.0, (p.propulsion - 0.34) / 0.36) + max(0.0, (p.max_speed - 0.65) / 0.55)
        target_risk = max(0.0, (target - 12.0) / 6.0)
        self.instability_index = clamp(
            0.95 * underdamped + 1.15 * power_shortage + 0.65 * noise_factor + 0.75 * guide_weak + 0.55 * speed_risk + 0.35 * target_risk + 0.25 * excessive_damping,
            0.0, 4.0
        )

        # PID kontrol etkisi. Kp hedefe döndürür, Kd salınımı frenler. Çok yüksek Kp/çok düşük Kd
        # olduğunda aşağıdaki unstable_drive treni bilerek titreştirir.
        control = p.kp * err * 0.00075 + p.ki * self.integral * 0.00028 + p.kd * derivative * 0.000085
        desired_acc = -control * 1200.0 / max(mass_load, 0.3)
        weak_lift_sag = -70.0 * power_shortage
        unstable_drive = math.sin(self.t * (5.0 + 3.0 * underdamped)) * (22.0 * max(0.0, self.instability_index - 0.55))
        random_kick = random.gauss(0.0, 10.0 * p.noise * (1.0 + self.instability_index))
        damping = (7.2 + 4.2 * p.guide + 0.65 * p.kd) * self.vgap
        if self.disturb > 0:
            unstable_drive += 85.0
            self.disturb -= dt
        self.vgap += (desired_acc + weak_lift_sag + unstable_drive + random_kick - damping) * dt
        # Kararlı sistemlerde hız küçük kalır; kötü sistemlerde sınır daha geniştir ki kullanıcı farkı görebilsin.
        max_vgap = 24.0 + 24.0 * self.instability_index
        self.vgap = clamp(self.vgap, -max_vgap, max_vgap)
        self.gap += self.vgap * dt

        # Gap limits.
        if self.gap < MIN_GAP_MM:
            self.gap = MIN_GAP_MM
            self.vgap = max(0, self.vgap) * 0.25
        if self.gap > MAX_GAP_MM:
            self.gap = MAX_GAP_MM
            self.vgap = min(0, self.vgap) * 0.25

        # Pitch/eğim: düşük stabilizer + yüksek hız + gürültü + kötü PID artık daha görünür eğim üretir.
        noise_pitch = random.gauss(0, p.noise * (0.22 + 0.12 * self.instability_index))
        pitch_drive = err * (0.10 + 0.10 * self.instability_index) + math.sin(self.t * 3.1) * max(0.0, self.instability_index - 0.65) * 0.95
        guide_damping = (1.25 + 2.8 * p.guide)
        angular_damping = (0.72 + 0.95 * p.guide + 0.10 * p.kd)
        self.vpitch += (pitch_drive + noise_pitch + p.propulsion * max(0.0, self.vx) * 0.75 - guide_damping * self.pitch - angular_damping * self.vpitch) * dt
        if self.disturb > 0:
            self.vpitch += 16.0 * dt
        self.pitch += self.vpitch * dt
        self.pitch = clamp(self.pitch, -12.0, 12.0)

        # Current and heating. Kötü durumda akım limite dayanır ve sıcaklık daha anlamlı yükselir.
        wanted_current = required_current + abs(err) * 0.26 + abs(self.vgap) * 0.010 + 0.38 * self.instability_index
        self.current += (clamp(wanted_current, 0, power_limit) - self.current) * min(1.0, dt * (5.5 + self.instability_index))
        # V11 manyetik doyum: akım artsa bile manyetik etki sınırsız artmaz.
        sat_i = max(0.2, p.saturation_current)
        self.saturation_ratio = clamp(self.current / sat_i, 0.0, 3.0)
        self.effective_current = self.current / math.sqrt(1.0 + (self.current / sat_i) ** 2)
        saturation_loss = max(0.0, self.current - self.effective_current)
        # Doyum varsa kaldırma zayıflar; gap ve pitch tarafında ek kararsızlık oluşsun.
        self.vgap += (saturation_loss * 1.6 + max(0.0, self.saturation_ratio - 0.85) * 9.0) * dt
        self.vpitch += max(0.0, self.saturation_ratio - 0.9) * 0.45 * dt
        heating = (self.current ** 2) * p.resistance * (0.030 + 0.006 * self.instability_index)
        # V11 soğutma: fan/ısı emici etkisini temsil eder.
        cooling = (self.temp - 25.0) * (0.012 + 0.010 * p.friction) * max(0.15, p.cooling_factor)
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
        # Çok agresif itki + düşük kılavuzda raydan çıkma riski oluşsun.
        speed_cap = p.max_speed * (1.0 + 0.30 * max(0.0, self.instability_index - 1.0))
        self.vx = clamp(self.vx, -0.10, speed_cap)
        self.x += self.vx * dt
        if self.x > TRACK_LEN_M:
            if self.instability_index > 1.35 or abs(self.pitch) > 7.5 or self.vx > 0.75:
                self.derailed = True
                self.x = TRACK_LEN_M
                self.vx = 0
            else:
                self.x = 0.06
                self.vx = 0
        if self.x < 0.04:
            self.x = 0.04
            self.vx = 0

        # Status. Artık sadece anlık gap değil, kararsızlık indeksi de dikkate alınır.
        if self.derailed:
            self.status = "RAYDAN ÇIKTI"
        elif self.gap <= MIN_GAP_MM + 0.3:
            self.status = "RAYA YAKIN"
        elif self.gap >= MAX_GAP_MM - 0.3:
            self.status = "KONTROL DIŞI"
        elif abs(self.pitch) > 8.5:
            self.status = "RAYDAN ÇIKTI"
            self.derailed = True
        elif abs(self.pitch) > 5.2:
            self.status = "EĞİM UYARISI"
        elif power_shortage > 0.22 or self.current > power_limit * 0.94:
            self.status = "AKIM LİMİTİ"
        elif self.temp > p.thermal_limit + 12:
            self.status = "TERMAL KAPANMA"
        elif self.temp > p.thermal_limit:
            self.status = "TERMAL KORUMA"
        elif self.sensor_fault_active:
            self.status = "SENSÖR ARIZASI"
        elif self.saturation_ratio > 1.0:
            self.status = "MANYETİK DOYUM"
        elif abs(self.gap - target) > 2.4:
            self.status = "BOŞLUK UYARISI"
        elif self.instability_index > 1.25:
            self.status = "KARARSIZ"
        elif self.instability_index > 0.75:
            self.status = "SALINIM"
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

        # Tam senaryo kaydı. Buraya anlık simülasyon değerleri + o andaki tüm slider/parametre değerleri yazılır.
        # Böylece “hangi ayarı değiştirdim, grafik nasıl değişti?” sorusu CSV ve raporda izlenebilir.
        if len(self.export_rows) < 60000:
            self.export_rows.append({
                "time_s": round(self.t, 4),
                "target_gap_mm": round(p.target_gap, 4),
                "gap_mm": round(self.gap, 4),
                "gap_error_mm": round(self.gap - p.target_gap, 4),
                "front_gap_mm": round(self.gap + self.pitch * 0.04, 4),
                "rear_gap_mm": round(self.gap - self.pitch * 0.04, 4),
                "pitch_deg": round(self.pitch, 4),
                "speed_mps": round(self.vx, 4),
                "current_A": round(self.current, 4),
                "temperature_C": round(self.temp, 4),
                "position_m": round(self.x, 4),
                "active_coil": int(self.active_coil + 1),
                "status": self.status,
                "instability_index": round(self.instability_index, 4),
                "effective_current_A": round(self.effective_current, 4),
                "bus_voltage_V": round(self.bus_voltage, 4),
                "thermal_derate": round(self.thermal_derate, 4),
                "saturation_ratio": round(self.saturation_ratio, 4),
                "sensor_fault_active": int(self.sensor_fault_active),
                "sensor_fault_count": int(self.sensor_fault_count),
                "thermal_protection_time_s": round(self.protection_active_time, 4),
                "mass_g": round(p.mass, 4),
                "kp": round(p.kp, 4),
                "ki": round(p.ki, 4),
                "kd": round(p.kd, 4),
                "voltage_V": round(p.voltage, 4),
                "resistance_ohm": round(p.resistance, 4),
                "current_limit_A": round(p.current_limit, 4),
                "sensor_noise_mm": round(p.noise, 4),
                "propulsion_N": round(p.propulsion, 4),
                "max_speed_mps": round(p.max_speed, 4),
                "sim_speed_x": round(p.sim_speed, 4),
                "guide": round(p.guide, 4),
                "friction": round(p.friction, 4),
                "saturation_current_A": round(p.saturation_current, 4),
                "voltage_sag_V_per_A": round(p.voltage_sag, 4),
                "sensor_fault_rate": round(p.sensor_fault_rate, 4),
                "thermal_limit_C": round(p.thermal_limit, 4),
                "cooling_factor": round(p.cooling_factor, 4),
                "calibration_gain": round(p.calibration_gain, 5),
                "calibration_offset_mm": round(p.calibration_offset, 5),
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
        self.beginner_mode = True
        self.scroll = 0
        self.max_scroll = 0
        self.selected_key = "kp"
        self.preset_name = "Dengeli"
        self.last_change_title = "Henüz değişiklik yapılmadı"
        self.last_change_body = "Bir slider seçip değeri değiştir. Burada yaptığın değişikliğin beklenen etkisi adım adım anlatılacak."
        self.last_change_watch = "Önce Başlangıç modunda Kütle, Hedef boşluk, Kp, Kd ve İtki kuvveti ile oyna."
        self.last_change_color = CYAN
        self.change_log: List[Dict[str, object]] = []
        self.last_saved_folder = ""
        # V10: Kullanıcının karşılaştıracağı senaryoları seçebilmesi için modal durumları
        self.compare_picker_open = False
        self.compare_scenarios: List[Path] = []
        self.compare_selected: List[Path] = []
        self.compare_row_rects: List[Tuple[pygame.Rect, Path]] = []
        self.compare_scroll = 0
        self.compare_max_scroll = 0
        self.compare_run_btn = pygame.Rect(0, 0, 1, 1)
        self.compare_cancel_btn = pygame.Rect(0, 0, 1, 1)
        self.compare_refresh_btn = pygame.Rect(0, 0, 1, 1)
        # V11 fiziksel prototip bağlantısı
        self.real_rows: List[Dict[str, object]] = []
        self.real_data_path: str = ""
        self.real_compare_folder: str = ""
        self.calibration_report: str = "Henüz gerçek veri içe aktarılmadı."
        self.mode_beginner_rect = pygame.Rect(0, 0, 1, 1)
        self.mode_advanced_rect = pygame.Rect(0, 0, 1, 1)
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
        # V11 gerçekçilik ve prototip bağlantısı
        add("saturation_current", "Manyetik doyum akımı", 1.0, 10.0, 5.0, 0.1, "A", "Gerçekçilik")
        add("voltage_sag", "Voltaj düşümü", 0.0, 1.5, 0.25, 0.05, "V/A", "Gerçekçilik")
        add("sensor_fault_rate", "Sensör arıza olasılığı", 0.0, 1.0, 0.0, 0.02, "", "Gerçekçilik")
        add("thermal_limit", "Termal koruma eşiği", 35.0, 95.0, 70.0, 1.0, "°C", "Gerçekçilik")
        add("cooling_factor", "Bobin soğutma etkisi", 0.2, 4.0, 1.0, 0.1, "x", "Gerçekçilik")
        add("calibration_gain", "Kalibrasyon kazancı", 0.80, 1.20, 1.0, 0.005, "", "Prototip")
        add("calibration_offset", "Kalibrasyon ofseti", -3.0, 3.0, 0.0, 0.05, "mm", "Prototip")

    def make_buttons(self):
        self.buttons = [
            Button("Dengeli", lambda: self.apply_preset("Dengeli"), BLUE_2),
            Button("Yavaş", lambda: self.apply_preset("Yavaş"), (23, 110, 105)),
            Button("Ağır", lambda: self.apply_preset("Ağır"), (78, 56, 130)),
            Button("Kararsız", lambda: self.apply_preset("Kararsız"), (134, 55, 33)),
            Button("Sıfırla", self.reset_all, (44, 57, 76)),
        ]

    def visible_slider_keys(self) -> List[str]:
        if self.beginner_mode:
            return BASIC_KEYS
        return list(self.sliders.keys())

    def visible_sliders_for_category(self, category: str) -> List[Slider]:
        keys = set(self.visible_slider_keys())
        return [s for s in self.sliders.values() if s.category == category and s.key in keys]

    def analyze_change(self, key: str, old: float, new: float):
        info = INFO.get(key, INFO["kp"])
        effects = CHANGE_EFFECTS.get(key, {})
        direction = "increase" if new > old else "decrease"
        direction_tr = "arttı" if new > old else "azaldı"
        effect = effects.get(direction, info["up"] if direction == "increase" else info["down"])
        watch = effects.get("watch", info["watch"])
        label = self.sliders[key].label
        old_s = self.format_value_for_key(key, old)
        new_s = self.sliders[key].value_str()
        self.last_change_title = f"{label}: {old_s} → {new_s} ({direction_tr})"
        self.last_change_body = effect
        self.last_change_watch = watch
        self.last_change_color = GREEN if direction == "increase" else ORANGE
        self.change_log.append({
            "time_s": round(self.sim.t, 3),
            "parameter": key,
            "label": label,
            "old_value": old,
            "new_value": new,
            "old_text": old_s,
            "new_text": new_s,
            "direction": direction_tr,
            "expected_effect": effect,
            "watch": watch,
        })

    def format_value_for_key(self, key: str, value: float) -> str:
        s = self.sliders[key]
        current = s.value
        s.value = value
        out = s.value_str()
        s.value = current
        return out

    def params(self) -> Params:
        return Params(**{k: s.value for k, s in self.sliders.items()})

    def apply_preset(self, name):
        presets = {
            "Dengeli": dict(mass=150, target_gap=8, guide=1.0, friction=0.9, kp=210, ki=0, kd=3.2, voltage=12, resistance=2.0, current_limit=6, noise=0.04, propulsion=0.16, max_speed=0.45, sim_speed=0.35, saturation_current=5.0, voltage_sag=0.25, sensor_fault_rate=0.0, thermal_limit=70, cooling_factor=1.0, calibration_gain=1.0, calibration_offset=0.0),
            "Yavaş": dict(mass=150, target_gap=8, guide=1.25, friction=1.25, kp=190, ki=0, kd=3.8, voltage=12, resistance=2.0, current_limit=6, noise=0.03, propulsion=0.08, max_speed=0.25, sim_speed=0.22, saturation_current=5.5, voltage_sag=0.18, sensor_fault_rate=0.0, thermal_limit=75, cooling_factor=1.8, calibration_gain=1.0, calibration_offset=0.0),
            "Ağır": dict(mass=280, target_gap=7.5, guide=1.15, friction=1.1, kp=260, ki=0, kd=4.2, voltage=14, resistance=1.8, current_limit=7, noise=0.04, propulsion=0.11, max_speed=0.36, sim_speed=0.32, saturation_current=5.0, voltage_sag=0.30, sensor_fault_rate=0.02, thermal_limit=70, cooling_factor=1.1, calibration_gain=1.0, calibration_offset=0.0),
            "Kararsız": dict(mass=420, target_gap=17, guide=0.08, friction=0.18, kp=860, ki=0, kd=0.2, voltage=9, resistance=3.2, current_limit=3.0, noise=0.42, propulsion=0.66, max_speed=1.05, sim_speed=0.35, saturation_current=2.4, voltage_sag=1.05, sensor_fault_rate=0.35, thermal_limit=45, cooling_factor=0.25, calibration_gain=1.0, calibration_offset=0.0),
        }
        for k, v in presets[name].items():
            self.sliders[k].set(v)
        self.preset_name = name
        self.sim.reset()
        self.change_log.clear()
        self.toast(f"{name} preseti yüklendi")

    def reset_all(self):
        self.sim.reset()
        self.change_log.clear()
        self.toast("Simülasyon sıfırlandı")

    def toast(self, msg):
        self.message = msg
        self.message_timer = 2.0

    def compute_metrics(self) -> Dict[str, float]:
        rows = self.sim.export_rows
        if not rows:
            return {
                "duration_s": 0.0, "avg_abs_error_mm": 0.0, "max_abs_error_mm": 0.0,
                "max_overshoot_mm": 0.0, "settling_time_s": 0.0, "max_current_A": 0.0,
                "max_temp_C": 0.0, "max_pitch_deg": 0.0, "energy_J_est": 0.0,
                "stability_score": 0.0, "sensor_fault_count": 0, "thermal_protection_time_s": 0.0, "max_saturation_ratio": 0.0,
            }
        errors = [abs(r.get("gap_error_mm", r["gap_mm"] - r.get("target_gap_mm", 8.0))) for r in rows]
        signed_errors = [r.get("gap_error_mm", r["gap_mm"] - r.get("target_gap_mm", 8.0)) for r in rows]
        times = [r["time_s"] for r in rows]
        duration = max(times) - min(times) if len(times) > 1 else (times[-1] if times else 0.0)
        avg_abs_error = sum(errors) / len(errors)
        max_abs_error = max(errors)
        max_overshoot = max(0.0, max(signed_errors))
        max_current = max(r["current_A"] for r in rows)
        max_temp = max(r["temperature_C"] for r in rows)
        max_pitch = max(abs(r["pitch_deg"]) for r in rows)
        max_instability = max(float(r.get("instability_index", 0.0)) for r in rows)
        max_saturation = max(float(r.get("saturation_ratio", 0.0)) for r in rows)
        sensor_fault_count = max(int(float(r.get("sensor_fault_count", 0))) for r in rows)
        thermal_protection_time = max(float(r.get("thermal_protection_time_s", 0.0)) for r in rows)
        bad_status_count = sum(1 for r in rows if r.get("status") not in ("KARARLI", "DÜZELİYOR"))
        bad_status_ratio = bad_status_count / max(1, len(rows))
        # Yerleşme süresi: sonrasında hata 0.5 mm bandında kalıyorsa ilk zamanı bul.
        settling_time = duration
        band = 0.5
        for i, e in enumerate(errors):
            if e <= band and all(x <= band for x in errors[i:]):
                settling_time = rows[i]["time_s"]
                break
        energy = 0.0
        for a, b in zip(rows, rows[1:]):
            dt = max(0.0, b["time_s"] - a["time_s"])
            r_ohm = max(0.1, a.get("resistance_ohm", self.params().resistance))
            energy += (a["current_A"] ** 2) * r_ohm * dt
        score = 100.0
        score -= avg_abs_error * 12.0
        score -= max_abs_error * 2.6
        score -= max_pitch * 2.2
        score -= max(0.0, max_temp - 45.0) * 1.4
        score -= max(0.0, max_current - self.params().current_limit * 0.85) * 3.0
        score -= max_instability * 16.0
        score -= max(0.0, max_saturation - 0.85) * 14.0
        score -= min(20.0, sensor_fault_count * 2.0)
        score -= min(18.0, thermal_protection_time * 2.0)
        score -= bad_status_ratio * 26.0
        score = clamp(score, 0.0, 100.0)
        return {
            "duration_s": round(duration, 3),
            "avg_abs_error_mm": round(avg_abs_error, 4),
            "max_abs_error_mm": round(max_abs_error, 4),
            "max_overshoot_mm": round(max_overshoot, 4),
            "settling_time_s": round(settling_time, 4),
            "max_current_A": round(max_current, 4),
            "max_temp_C": round(max_temp, 4),
            "max_pitch_deg": round(max_pitch, 4),
            "energy_J_est": round(energy, 4),
            "max_instability_index": round(max_instability, 4),
            "bad_status_ratio": round(bad_status_ratio, 4),
            "sensor_fault_count": sensor_fault_count,
            "thermal_protection_time_s": round(thermal_protection_time, 4),
            "max_saturation_ratio": round(max_saturation, 4),
            "stability_score": round(score, 2),
        }

    def write_excel_csv(self, path: Path, rows: List[Dict[str, object]], fieldnames=None):
        """Excel'de Türkçe karakter ve sütun ayrımı düzgün açılsın diye UTF-8 BOM + sep=; kullanır."""
        if fieldnames is None and rows:
            fieldnames = list(rows[0].keys())
        fieldnames = fieldnames or []
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            f.write("sep=;\n")
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";", quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)

    def read_excel_csv(self, path: Path) -> List[Dict[str, object]]:
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            first = f.readline()
            delimiter = ";" if first.lower().startswith("sep=") else (";" if first.count(";") >= first.count(",") else ",")
            if not first.lower().startswith("sep="):
                f.seek(0)
            reader = csv.DictReader(f, delimiter=delimiter)
            rows = []
            for row in reader:
                cleaned = {}
                for k, v in row.items():
                    if k is None:
                        continue
                    if v is None:
                        cleaned[k] = v
                        continue
                    try:
                        cleaned[k] = float(v.replace(",", ".")) if isinstance(v, str) and v.strip() != "" else v
                    except Exception:
                        cleaned[k] = v
                rows.append(cleaned)
            return rows

    # ========================================================
    # V11: FİZİKSEL PROTOTİP VERİSİ + KALİBRASYON
    # ========================================================

    def candidate_real_data_files(self) -> List[Path]:
        roots = [Path.cwd() / "prototype_data", Path.cwd()]
        files: List[Path] = []
        for root in roots:
            if root.exists():
                files.extend([p for p in root.glob("*.csv") if p.is_file() and not p.name.startswith("telemetri_")])
        files = sorted(set(files), key=lambda p: (p.name.lower() != "real_data.csv", -p.stat().st_mtime))
        return files

    def create_real_data_template(self) -> Path:
        root = Path.cwd() / "prototype_data"
        root.mkdir(parents=True, exist_ok=True)
        path = root / "real_data.csv"
        if not path.exists():
            rows = []
            for i in range(180):
                t = i / 30.0
                rows.append({
                    "time_s": round(t, 4),
                    "gap_mm": round(8.0 + 0.18 * math.sin(t * 2.1), 4),
                    "current_A": round(2.05 + 0.08 * math.sin(t * 1.4), 4),
                    "temperature_C": round(25.0 + t * 0.12, 4),
                    "speed_mps": round(0.25 + 0.03 * math.sin(t), 4),
                })
            self.write_excel_csv(path, rows, list(rows[0].keys()))
        return path

    def normalize_real_rows(self, rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
        aliases = {
            "time_s": ["time_s", "time", "t", "zaman", "zaman_s", "millis"],
            "gap_mm": ["gap_mm", "gap", "distance_mm", "mesafe_mm", "bosluk_mm", "hall_gap_mm"],
            "current_A": ["current_A", "current", "akim_A", "akim", "coil_current_A"],
            "temperature_C": ["temperature_C", "temp_C", "sicaklik_C", "sicaklik", "coil_temp_C"],
            "speed_mps": ["speed_mps", "speed", "hiz_mps", "hiz"],
        }
        out = []
        for i, r in enumerate(rows):
            nr = {}
            lower = {str(k).strip().lower(): v for k, v in r.items()}
            for target, names in aliases.items():
                val = None
                for name in names:
                    if name.lower() in lower:
                        val = lower[name.lower()]
                        break
                if val is None:
                    val = i / 30.0 if target == "time_s" else 0.0
                try:
                    if isinstance(val, str):
                        val = val.replace(",", ".")
                    nr[target] = float(val)
                    if target == "time_s" and "millis" in lower and nr[target] > 1000:
                        nr[target] /= 1000.0
                except Exception:
                    nr[target] = 0.0
            out.append(nr)
        return out

    def import_real_data(self):
        files = self.candidate_real_data_files()
        if not files:
            template = self.create_real_data_template()
            self.toast(f"Örnek gerçek veri şablonu oluşturuldu: {template.name}")
            files = [template]
        path = files[0]
        rows = self.read_excel_csv(path)
        self.real_rows = self.normalize_real_rows(rows)
        self.real_data_path = str(path)
        self.calibration_report = f"İçe aktarıldı: {path.name} | {len(self.real_rows)} satır"
        self.toast(self.calibration_report)
        if self.sim.export_rows and self.real_rows:
            self.save_real_vs_sim_report()

    def align_series_pair(self, sim_rows, real_rows, sim_key, real_key):
        n = min(len(sim_rows), len(real_rows), 2000)
        if n <= 1:
            return [], []
        a, b = [], []
        for i in range(n):
            si = int(i * (len(sim_rows) - 1) / max(1, n - 1))
            ri = int(i * (len(real_rows) - 1) / max(1, n - 1))
            try: a.append(float(sim_rows[si].get(sim_key, 0)))
            except Exception: a.append(0.0)
            try: b.append(float(real_rows[ri].get(real_key, 0)))
            except Exception: b.append(0.0)
        return a, b

    def calibrate_from_real_data(self):
        if not self.real_rows:
            self.import_real_data()
        if not self.real_rows or not self.sim.export_rows:
            self.toast("Kalibrasyon için önce simülasyon çalıştır ve gerçek CSV içe aktar")
            return
        sim_gap, real_gap = self.align_series_pair(self.sim.export_rows, self.real_rows, "gap_mm", "gap_mm")
        if len(sim_gap) < 5:
            self.toast("Kalibrasyon için yeterli veri yok")
            return
        mean_sim = sum(sim_gap) / len(sim_gap)
        mean_real = sum(real_gap) / len(real_gap)
        var_real = sum((x - mean_real) ** 2 for x in real_gap) / max(1, len(real_gap))
        cov = sum((r - mean_real) * (s - mean_sim) for r, s in zip(real_gap, sim_gap)) / max(1, len(real_gap))
        gain = cov / var_real if var_real > 1e-9 else 1.0
        offset = mean_sim - gain * mean_real
        gain = clamp(gain, 0.80, 1.20)
        offset = clamp(offset, -3.0, 3.0)
        self.sliders["calibration_gain"].set(gain)
        self.sliders["calibration_offset"].set(offset)
        calibrated = [gain * r + offset for r in real_gap]
        before = sum(abs(s - r) for s, r in zip(sim_gap, real_gap)) / len(sim_gap)
        after = sum(abs(s - r) for s, r in zip(sim_gap, calibrated)) / len(sim_gap)
        self.calibration_report = f"Kalibrasyon: gain={gain:.4f}, offset={offset:.3f} mm | hata {before:.3f}→{after:.3f} mm"
        self.toast(self.calibration_report)
        self.save_real_vs_sim_report()

    def save_real_vs_sim_report(self):
        if not self.real_rows or not self.sim.export_rows:
            return
        stamp = time.strftime("%Y%m%d_%H%M%S")
        out_dir = Path.cwd() / "maglev_scenarios" / f"prototype_compare_{stamp}"
        out_dir.mkdir(parents=True, exist_ok=True)
        png = out_dir / "simulasyon_vs_gercek_veri.png"
        self.save_real_vs_sim_png(png, self.sim.export_rows, self.real_rows)
        report = [
            "MAGLEV PROTOTİP VERİ KARŞILAŞTIRMA RAPORU",
            "========================================",
            f"Gerçek veri dosyası: {self.real_data_path}",
            self.calibration_report,
            "",
            "Beklenen CSV kolonları:",
            "time_s, gap_mm, current_A, temperature_C, speed_mps",
        ]
        (out_dir / "prototip_karsilastirma_raporu.txt").write_text("\n".join(report), encoding="utf-8")
        self.real_compare_folder = str(out_dir)
        try:
            if sys.platform.startswith("win"):
                os.startfile(png)
                os.startfile(out_dir)
        except Exception:
            pass

    def save_real_vs_sim_png(self, path: Path, sim_rows, real_rows):
        surf = pygame.Surface((1600, 980))
        surf.fill(BG)
        text(surf, self.fonts["title"], "Simülasyon vs Gerçek Prototip Verisi", 42, 28, TEXT)
        text(surf, self.fonts["small"], self.calibration_report, 42, 62, MUTED)
        charts = [
            ("Gap / Boşluk", "gap_mm", "gap_mm", "mm", GREEN, ORANGE, 42, 110),
            ("Akım", "current_A", "current_A", "A", BLUE, ORANGE, 820, 110),
            ("Sıcaklık", "temperature_C", "temperature_C", "°C", PURPLE, ORANGE, 42, 520),
            ("Hız", "speed_mps", "speed_mps", "m/s", CYAN, ORANGE, 820, 520),
        ]
        for title_, sk, rk, unit, ca, cb, x, y in charts:
            rows_a = sim_rows
            rows_b = [{"time_s": r.get("time_s", 0), sk: r.get(rk, 0)} for r in real_rows]
            self.draw_comparison_chart(surf, pygame.Rect(x, y, 730, 340), title_, rows_a, rows_b, sk, ca, cb, unit, "generic")
        pygame.image.save(surf, str(path))

    def export_csv(self):
        path = Path.cwd() / f"maglev_export_{int(time.time())}.csv"
        rows = self.sim.export_rows
        if not rows:
            self.toast("Dışa aktarılacak veri yok")
            return
        self.write_excel_csv(path, rows, list(rows[0].keys()))
        self.toast(f"Excel uyumlu CSV kaydedildi: {path.name}")

    def save_scenario(self):
        rows = self.sim.export_rows
        if not rows:
            self.toast("Kaydedilecek senaryo verisi yok")
            return
        stamp = time.strftime("%Y%m%d_%H%M%S")
        out_dir = Path.cwd() / "maglev_scenarios" / f"scenario_{stamp}"
        out_dir.mkdir(parents=True, exist_ok=True)
        metrics = self.compute_metrics()
        params = {k: s.value for k, s in self.sliders.items()}

        # 1) Tam zaman serisi CSV - Excel uyumlu: UTF-8 BOM + sep=; + noktalı virgül
        csv_path = out_dir / "telemetri_tam_kayit.csv"
        self.write_excel_csv(csv_path, rows, list(rows[0].keys()))

        # 2) Slider değişiklikleri CSV - Excel uyumlu
        changes_path = out_dir / "degisiklikler.csv"
        change_fields = ["time_s", "parameter", "label", "old_value", "new_value", "old_text", "new_text", "direction", "expected_effect", "watch"]
        self.write_excel_csv(changes_path, self.change_log, change_fields)

        # 3) Senaryo özeti JSON
        summary = {
            "app": APP_TITLE,
            "version": VERSION,
            "created_at": stamp,
            "preset": self.preset_name,
            "duration_s": metrics["duration_s"],
            "parameters": params,
            "metrics": metrics,
            "change_count": len(self.change_log),
            "files": {
                "telemetry_csv": csv_path.name,
                "changes_csv": changes_path.name,
                "overview_png": "grafikler_ozet.png",
                "report_txt": "senaryo_raporu.txt",
            }
        }
        (out_dir / "senaryo_ozeti.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

        # 4) Okunabilir TXT rapor
        report_lines = [
            "MAGLEV SENARYO RAPORU",
            "======================",
            f"Preset: {self.preset_name}",
            f"Süre: {metrics['duration_s']:.2f} s",
            "",
            "Performans:",
            f"- Ortalama mutlak hata: {metrics['avg_abs_error_mm']:.3f} mm",
            f"- Maksimum mutlak hata: {metrics['max_abs_error_mm']:.3f} mm",
            f"- Maksimum aşım: {metrics['max_overshoot_mm']:.3f} mm",
            f"- Yerleşme süresi: {metrics['settling_time_s']:.3f} s",
            f"- Maksimum akım: {metrics['max_current_A']:.3f} A",
            f"- Maksimum sıcaklık: {metrics['max_temp_C']:.2f} °C",
            f"- Maksimum pitch: {metrics['max_pitch_deg']:.3f}°",
            f"- Tahmini enerji: {metrics['energy_J_est']:.3f} J",
            f"- Maksimum kararsızlık indeksi: {metrics.get('max_instability_index', 0):.3f}",
            f"- Maksimum manyetik doyum oranı: {metrics.get('max_saturation_ratio', 0):.3f}",
            f"- Sensör arıza sayısı: {metrics.get('sensor_fault_count', 0)}",
            f"- Termal koruma süresi: {metrics.get('thermal_protection_time_s', 0):.2f} s",
            f"- Riskli durum oranı: {metrics.get('bad_status_ratio', 0)*100:.1f}%",
            f"- Kararlılık skoru: {metrics['stability_score']:.1f}/100",
            "",
            "Son parametreler:",
        ]
        for k, v in params.items():
            report_lines.append(f"- {k}: {v}")
        report_lines.append("")
        report_lines.append("Değişiklikler:")
        if self.change_log:
            for c in self.change_log[-30:]:
                report_lines.append(f"- t={c['time_s']}s | {c['label']}: {c['old_text']} -> {c['new_text']} | {c['direction']}")
        else:
            report_lines.append("- Değişiklik kaydı yok.")
        (out_dir / "senaryo_raporu.txt").write_text("\n".join(report_lines), encoding="utf-8")

        # 5) Büyük grafik görseli + ayrı grafikler
        self.save_overview_png(out_dir / "grafikler_ozet.png", rows, metrics)
        self.save_single_chart(out_dir / "gap_grafigi.png", rows, "gap_mm", "target_gap_mm", "Boşluk Grafiği", "mm", GREEN)
        self.save_single_chart(out_dir / "akim_grafigi.png", rows, "current_A", None, "Akım Grafiği", "A", BLUE)
        self.save_single_chart(out_dir / "sicaklik_grafigi.png", rows, "temperature_C", None, "Sıcaklık Grafiği", "°C", ORANGE)
        self.save_single_chart(out_dir / "hiz_grafigi.png", rows, "speed_mps", None, "Hız Grafiği", "m/s", CYAN)
        self.save_single_chart(out_dir / "pitch_grafigi.png", rows, "pitch_deg", None, "Pitch Grafiği", "°", PURPLE)

        self.last_saved_folder = str(out_dir)
        self.toast(f"Senaryo kaydedildi: {out_dir.name}")
        # Windows'ta grafik ve klasör önüne düşsün.
        try:
            if sys.platform.startswith("win"):
                os.startfile(out_dir / "grafikler_ozet.png")
                os.startfile(out_dir)
        except Exception:
            pass

    def saved_scenario_dirs(self) -> List[Path]:
        root = Path.cwd() / "maglev_scenarios"
        if not root.exists():
            return []
        dirs = [d for d in root.glob("scenario_*") if (d / "telemetri_tam_kayit.csv").exists()]
        return sorted(dirs, key=lambda d: d.stat().st_mtime, reverse=True)

    def scenario_summary(self, scenario_dir: Path) -> Dict[str, object]:
        """Kaydedilmiş senaryonun kısa bilgisini okur. JSON yoksa CSV'den hesaplar."""
        summary_path = scenario_dir / "senaryo_ozeti.json"
        info: Dict[str, object] = {
            "name": scenario_dir.name,
            "created_at": scenario_dir.name.replace("scenario_", ""),
            "preset": "Bilinmiyor",
            "metrics": {},
        }
        try:
            if summary_path.exists():
                data = json.loads(summary_path.read_text(encoding="utf-8"))
                info.update(data)
        except Exception:
            pass
        try:
            rows = self.read_excel_csv(scenario_dir / "telemetri_tam_kayit.csv")
            if rows and not info.get("metrics"):
                info["metrics"] = self.metrics_for_rows(rows)
        except Exception:
            pass
        return info

    def scenario_display_name(self, scenario_dir: Path) -> str:
        info = self.scenario_summary(scenario_dir)
        created = str(info.get("created_at", scenario_dir.name.replace("scenario_", "")))
        preset = str(info.get("preset", "Senaryo"))
        return f"{preset} | {created}"

    def open_compare_picker(self):
        self.compare_scenarios = self.saved_scenario_dirs()
        self.compare_selected = [p for p in self.compare_selected if p in self.compare_scenarios]
        self.compare_scroll = 0
        if len(self.compare_scenarios) < 2:
            self.toast("Karşılaştırma için en az 2 senaryo kaydet")
            return
        self.compare_picker_open = True
        self.paused = True
        self.toast("Karşılaştırma modu: iki senaryo seç")

    def toggle_compare_selection(self, scenario_dir: Path):
        if scenario_dir in self.compare_selected:
            self.compare_selected.remove(scenario_dir)
            return
        if len(self.compare_selected) < 2:
            self.compare_selected.append(scenario_dir)
        else:
            # Üçüncü seçimi yaparsa B senaryosunu değiştir. A sabit kalır.
            self.compare_selected[1] = scenario_dir

    def compare_selected_scenarios(self):
        if len(self.compare_selected) != 2:
            self.toast("Önce karşılaştırılacak 2 senaryo seç")
            return
        a_dir, b_dir = self.compare_selected[0], self.compare_selected[1]
        rows_a = self.read_excel_csv(a_dir / "telemetri_tam_kayit.csv")
        rows_b = self.read_excel_csv(b_dir / "telemetri_tam_kayit.csv")
        if not rows_a or not rows_b:
            self.toast("Seçilen senaryo CSV dosyası okunamadı")
            return
        stamp = time.strftime("%Y%m%d_%H%M%S")
        out_dir = Path.cwd() / "maglev_scenarios" / f"comparison_{stamp}"
        out_dir.mkdir(parents=True, exist_ok=True)
        png_path = out_dir / "karsilastirma_ozet.png"
        name_a = self.scenario_display_name(a_dir)
        name_b = self.scenario_display_name(b_dir)
        self.save_comparison_png(png_path, rows_a, rows_b, name_a, name_b)
        report = self.comparison_report_text(rows_a, rows_b, name_a, name_b)
        (out_dir / "karsilastirma_raporu.txt").write_text(report, encoding="utf-8")
        # Seçilen kaynakları da rapora izlenebilirlik için kaydet.
        source_info = {
            "created_at": stamp,
            "scenario_a_folder": str(a_dir),
            "scenario_b_folder": str(b_dir),
            "scenario_a_name": name_a,
            "scenario_b_name": name_b,
            "output_png": png_path.name,
        }
        (out_dir / "karsilastirma_kaynaklari.json").write_text(json.dumps(source_info, ensure_ascii=False, indent=2), encoding="utf-8")
        self.last_saved_folder = str(out_dir)
        self.compare_picker_open = False
        self.toast(f"Seçili senaryolar karşılaştırıldı: {out_dir.name}")
        try:
            if sys.platform.startswith("win"):
                os.startfile(png_path)
                os.startfile(out_dir)
        except Exception:
            pass

    # Eski davranış korunuyor ama üst bardaki buton artık bunu doğrudan çağırmıyor.
    def compare_last_two_scenarios(self):
        dirs = self.saved_scenario_dirs()
        if len(dirs) < 2:
            self.toast("Karşılaştırma için en az 2 senaryo kaydet")
            return
        self.compare_selected = [dirs[0], dirs[1]]
        self.compare_selected_scenarios()

    def metrics_for_rows(self, rows: List[Dict[str, object]]) -> Dict[str, float]:
        if not rows:
            return {"duration_s": 0, "avg_abs_error_mm": 0, "max_abs_error_mm": 0, "max_current_A": 0, "max_temp_C": 0, "max_pitch_deg": 0, "score": 0}
        errors = [abs(float(r.get("gap_error_mm", float(r.get("gap_mm", 0)) - float(r.get("target_gap_mm", 0))))) for r in rows]
        currents = [float(r.get("current_A", 0)) for r in rows]
        temps = [float(r.get("temperature_C", 0)) for r in rows]
        pitch = [abs(float(r.get("pitch_deg", 0))) for r in rows]
        times = [float(r.get("time_s", 0)) for r in rows]
        bad = sum(1 for r in rows if str(r.get("status", "")) not in ("KARARLI", "DÜZELİYOR")) / max(1, len(rows))
        avg_error = sum(errors) / max(1, len(errors))
        score = 100 - avg_error * 12 - max(errors) * 2.6 - max(pitch) * 2.2 - max(0, max(temps) - 45) * 1.4 - bad * 26
        return {
            "duration_s": round(max(times) - min(times), 3) if times else 0,
            "avg_abs_error_mm": round(avg_error, 4),
            "max_abs_error_mm": round(max(errors), 4),
            "max_current_A": round(max(currents), 4),
            "max_temp_C": round(max(temps), 4),
            "max_pitch_deg": round(max(pitch), 4),
            "score": round(clamp(score, 0, 100), 2),
        }

    def comparison_report_text(self, rows_a, rows_b, name_a, name_b):
        ma = self.metrics_for_rows(rows_a)
        mb = self.metrics_for_rows(rows_b)
        better = name_a if ma["score"] >= mb["score"] else name_b
        return "\n".join([
            "MAGLEV SENARYO KARŞILAŞTIRMA RAPORU",
            "====================================",
            f"Senaryo A: {name_a}",
            f"Senaryo B: {name_b}",
            "",
            "Özet:",
            f"- Daha iyi skor: {better}",
            f"- A skoru: {ma['score']}/100 | ort. hata {ma['avg_abs_error_mm']} mm | maks. akım {ma['max_current_A']} A | maks. sıcaklık {ma['max_temp_C']} °C",
            f"- B skoru: {mb['score']}/100 | ort. hata {mb['avg_abs_error_mm']} mm | maks. akım {mb['max_current_A']} A | maks. sıcaklık {mb['max_temp_C']} °C",
            "",
            "Grafiklerdeki referanslar:",
            "- Best/ideal çizgi: hedefe yakın, düşük salınımlı çalışmayı temsil eder.",
            "- Worst/limit çizgisi: sistemin artık riskli kabul edildiği sınırı gösterir.",
        ])

    def row_series(self, rows, key):
        vals = []
        for r in rows:
            try:
                vals.append(float(r.get(key, 0)))
            except Exception:
                vals.append(0.0)
        return vals

    def draw_dashed_line_png(self, surf, color, start, end, width=2, dash=12, gap=8):
        x1, y1 = start; x2, y2 = end
        length = math.hypot(x2 - x1, y2 - y1)
        if length <= 0:
            return
        dx = (x2 - x1) / length
        dy = (y2 - y1) / length
        pos = 0
        while pos < length:
            a = pos
            b = min(length, pos + dash)
            pygame.draw.line(surf, color, (x1 + dx * a, y1 + dy * a), (x1 + dx * b, y1 + dy * b), width)
            pos += dash + gap

    def draw_comparison_chart(self, surf, rect, title, rows_a, rows_b, key, color_a, color_b, ylabel, benchmark="generic"):
        rounded(surf, CARD, rect, 14)
        rounded(surf, BORDER, rect, 14, 1)
        text(surf, self.fonts["small"], title, rect.x + 14, rect.y + 10, TEXT)
        plot = pygame.Rect(rect.x + 54, rect.y + 48, rect.w - 86, rect.h - 88)
        pygame.draw.rect(surf, (8, 16, 30), plot)
        for i in range(5):
            yy = plot.y + i * plot.h // 4
            pygame.draw.line(surf, GRID, (plot.x, yy), (plot.right, yy), 1)
        for i in range(6):
            xx = plot.x + i * plot.w // 5
            pygame.draw.line(surf, GRID, (xx, plot.y), (xx, plot.bottom), 1)
        data_a = self.row_series(rows_a, key)
        data_b = self.row_series(rows_b, key)
        target_a = self.row_series(rows_a, "target_gap_mm") if key == "gap_mm" else []
        all_vals = data_a + data_b + target_a
        if benchmark in ("gap", "gap_error"):
            if key == "gap_mm":
                t0 = target_a[-1] if target_a else 8.0
                all_vals += [t0 - 3.0, t0 + 3.0]
            else:
                all_vals += [-3.0, 3.0, 0.0]
        elif benchmark == "pitch":
            all_vals += [-6.0, 6.0, 0.0]
        elif benchmark == "current":
            all_vals += [0.0, max(self.row_series(rows_a, "current_limit_A") + self.row_series(rows_b, "current_limit_A") + [6.0])]
        elif benchmark == "temperature":
            all_vals += [40.0, 70.0]
        lo = min(all_vals) if all_vals else 0.0
        hi = max(all_vals) if all_vals else 1.0
        pad = max(0.25, (hi - lo) * 0.12)
        lo -= pad; hi += pad
        def pts(data):
            if not data: return []
            out=[]; n=len(data)
            for i,v in enumerate(data):
                x = plot.x + int(i * plot.w / max(1, n-1))
                y = plot.bottom - int(clamp((v - lo) / max(1e-9, hi-lo), 0, 1) * plot.h)
                out.append((x,y))
            return out
        def y_of(v):
            return plot.bottom - int(clamp((v - lo) / max(1e-9, hi-lo), 0, 1) * plot.h)
        # Best / worst reference lines
        if benchmark == "gap":
            t0 = target_a[-1] if target_a else 8.0
            ybest = y_of(t0)
            self.draw_dashed_line_png(surf, GREEN, (plot.x, ybest), (plot.right, ybest), 2)
            for v in [t0 - 3.0, t0 + 3.0]:
                yy = y_of(v); self.draw_dashed_line_png(surf, RED, (plot.x, yy), (plot.right, yy), 1)
            text(surf, self.fonts["tiny"], "best: hedef", plot.right - 110, ybest - 16, GREEN)
        elif benchmark == "gap_error":
            self.draw_dashed_line_png(surf, GREEN, (plot.x, y_of(0.0)), (plot.right, y_of(0.0)), 2)
            for v in [-3.0, 3.0]: self.draw_dashed_line_png(surf, RED, (plot.x, y_of(v)), (plot.right, y_of(v)), 1)
        elif benchmark == "pitch":
            self.draw_dashed_line_png(surf, GREEN, (plot.x, y_of(0.0)), (plot.right, y_of(0.0)), 2)
            for v in [-6.0, 6.0]: self.draw_dashed_line_png(surf, RED, (plot.x, y_of(v)), (plot.right, y_of(v)), 1)
        elif benchmark == "current":
            limit = max(self.row_series(rows_a, "current_limit_A") + self.row_series(rows_b, "current_limit_A") + [6.0])
            self.draw_dashed_line_png(surf, RED, (plot.x, y_of(limit)), (plot.right, y_of(limit)), 1)
        elif benchmark == "temperature":
            self.draw_dashed_line_png(surf, GREEN, (plot.x, y_of(40.0)), (plot.right, y_of(40.0)), 1)
            self.draw_dashed_line_png(surf, RED, (plot.x, y_of(70.0)), (plot.right, y_of(70.0)), 1)
        pa, pb = pts(data_a), pts(data_b)
        if len(pa) > 1: pygame.draw.lines(surf, color_a, False, pa, 2)
        if len(pb) > 1: pygame.draw.lines(surf, color_b, False, pb, 2)
        text(surf, self.fonts["tiny"], "A", rect.x + 18, rect.bottom - 28, color_a)
        text(surf, self.fonts["tiny"], "B", rect.x + 50, rect.bottom - 28, color_b)
        text(surf, self.fonts["tiny"], "yeşil: best/ideal  |  kırmızı: worst/limit", rect.x + 90, rect.bottom - 28, MUTED)
        text(surf, self.fonts["tiny"], ylabel, plot.x - 42, plot.y + 2, MUTED)

    def save_comparison_png(self, path: Path, rows_a, rows_b, name_a, name_b):
        surf = pygame.Surface((1800, 1200))
        surf.fill(BG)
        text(surf, self.fonts["title"], "Maglev Senaryo Karşılaştırma Modu", 42, 28, TEXT)
        text(surf, self.fonts["small"], f"A: {name_a}   |   B: {name_b}", 42, 62, MUTED)
        ma, mb = self.metrics_for_rows(rows_a), self.metrics_for_rows(rows_b)
        cards = [
            ("A skor", f"{ma['score']:.1f}/100", GREEN if ma['score'] >= 75 else ORANGE),
            ("B skor", f"{mb['score']:.1f}/100", GREEN if mb['score'] >= 75 else ORANGE),
            ("A ort. hata", f"{ma['avg_abs_error_mm']:.3f} mm", CYAN),
            ("B ort. hata", f"{mb['avg_abs_error_mm']:.3f} mm", CYAN),
            ("A maks. akım", f"{ma['max_current_A']:.2f} A", PURPLE),
            ("B maks. akım", f"{mb['max_current_A']:.2f} A", PURPLE),
        ]
        x=42
        for lab,val,col in cards:
            rr=pygame.Rect(x,96,270,72); rounded(surf,PANEL_2,rr,14); rounded(surf,BORDER,rr,14,1)
            text(surf,self.fonts["tiny"],lab,rr.x+16,rr.y+12,MUTED); text(surf,self.fonts["metric"],val,rr.x+16,rr.y+34,col)
            x += 286
        self.draw_comparison_chart(surf, pygame.Rect(42, 196, 840, 290), "Boşluk karşılaştırması", rows_a, rows_b, "gap_mm", GREEN, ORANGE, "mm", "gap")
        self.draw_comparison_chart(surf, pygame.Rect(918, 196, 840, 290), "Gap hatası", rows_a, rows_b, "gap_error_mm", GREEN, ORANGE, "mm", "gap_error")
        self.draw_comparison_chart(surf, pygame.Rect(42, 520, 840, 290), "Pitch / eğim", rows_a, rows_b, "pitch_deg", GREEN, ORANGE, "°", "pitch")
        self.draw_comparison_chart(surf, pygame.Rect(918, 520, 840, 290), "Bobin akımı", rows_a, rows_b, "current_A", GREEN, ORANGE, "A", "current")
        self.draw_comparison_chart(surf, pygame.Rect(42, 844, 840, 290), "Bobin sıcaklığı", rows_a, rows_b, "temperature_C", GREEN, ORANGE, "°C", "temperature")
        self.draw_comparison_chart(surf, pygame.Rect(918, 844, 840, 290), "Hız", rows_a, rows_b, "speed_mps", GREEN, ORANGE, "m/s", "speed")
        pygame.image.save(surf, str(path))

    def graph_points(self, rect: pygame.Rect, rows, key: str, lo=None, hi=None):
        data = [float(r[key]) for r in rows]
        if not data:
            return []
        if lo is None:
            lo = min(data)
        if hi is None:
            hi = max(data)
        if abs(hi - lo) < 1e-9:
            lo -= 1.0
            hi += 1.0
        n = len(data)
        pts = []
        for i, v in enumerate(data):
            x = rect.x + int(i * rect.w / max(1, n - 1))
            y = rect.bottom - int(clamp((v - lo) / (hi - lo), 0, 1) * rect.h)
            pts.append((x, y))
        return pts

    def draw_png_chart(self, surf, rect, title, rows, y_key, target_key, color, unit):
        rounded(surf, CARD, rect, 14)
        rounded(surf, BORDER, rect, 14, 1)
        text(surf, self.fonts["small"], title, rect.x + 14, rect.y + 10, TEXT)
        plot = pygame.Rect(rect.x + 46, rect.y + 44, rect.w - 68, rect.h - 76)
        pygame.draw.rect(surf, (8, 16, 30), plot)
        for i in range(5):
            yy = plot.y + i * plot.h // 4
            pygame.draw.line(surf, GRID, (plot.x, yy), (plot.right, yy), 1)
        for i in range(6):
            xx = plot.x + i * plot.w // 5
            pygame.draw.line(surf, GRID, (xx, plot.y), (xx, plot.bottom), 1)
        vals = [float(r[y_key]) for r in rows]
        extra = [float(r[target_key]) for r in rows] if target_key else []
        lo = min(vals + extra) if extra else min(vals)
        hi = max(vals + extra) if extra else max(vals)
        pad = max(0.5, (hi - lo) * 0.12)
        lo -= pad
        hi += pad
        pts = self.graph_points(plot, rows, y_key, lo, hi)
        if len(pts) > 1:
            pygame.draw.lines(surf, color, False, pts, 2)
        if target_key:
            tpts = self.graph_points(plot, rows, target_key, lo, hi)
            if len(tpts) > 1:
                pygame.draw.lines(surf, CYAN, False, tpts, 2)
        text(surf, self.fonts["tiny"], f"max {max(vals):.2f} {unit}", plot.x, rect.bottom - 24, MUTED)
        text(surf, self.fonts["tiny"], f"min {min(vals):.2f} {unit}", plot.x + 120, rect.bottom - 24, MUTED)
        text(surf, self.fonts["tiny"], f"son {vals[-1]:.2f} {unit}", plot.right - 110, rect.bottom - 24, color)

    def save_overview_png(self, path: Path, rows, metrics):
        surf = pygame.Surface((1600, 1050))
        surf.fill(BG)
        text(surf, self.fonts["title"], "Maglev Train Visual Simulation - Senaryo Grafikleri", 40, 28, TEXT)
        text(surf, self.fonts["small"], f"Preset: {self.preset_name} | Süre: {metrics['duration_s']:.2f}s | Kayıt sayısı: {len(rows)}", 40, 62, MUTED)
        cards = [
            ("Kararlılık", f"{metrics['stability_score']:.1f}/100", GREEN if metrics['stability_score'] >= 75 else ORANGE),
            ("Ort. hata", f"{metrics['avg_abs_error_mm']:.3f} mm", CYAN),
            ("Maks. hata", f"{metrics['max_abs_error_mm']:.3f} mm", ORANGE),
            ("Yerleşme", f"{metrics['settling_time_s']:.2f} s", BLUE),
            ("Maks. akım", f"{metrics['max_current_A']:.2f} A", PURPLE),
            ("Enerji", f"{metrics['energy_J_est']:.1f} J", YELLOW),
        ]
        x = 40
        for lab, val, col in cards:
            r = pygame.Rect(x, 96, 240, 72)
            rounded(surf, PANEL_2, r, 14)
            rounded(surf, BORDER, r, 14, 1)
            text(surf, self.fonts["tiny"], lab, r.x + 16, r.y + 12, MUTED)
            text(surf, self.fonts["metric"], val, r.x + 16, r.y + 34, col)
            x += 255
        self.draw_png_chart(surf, pygame.Rect(40, 196, 740, 245), "Boşluk: gerçek vs hedef", rows, "gap_mm", "target_gap_mm", GREEN, "mm")
        self.draw_png_chart(surf, pygame.Rect(820, 196, 740, 245), "Pitch / eğim", rows, "pitch_deg", None, PURPLE, "°")
        self.draw_png_chart(surf, pygame.Rect(40, 470, 740, 245), "Bobin akımı", rows, "current_A", None, BLUE, "A")
        self.draw_png_chart(surf, pygame.Rect(820, 470, 740, 245), "Bobin sıcaklığı", rows, "temperature_C", None, ORANGE, "°C")
        self.draw_png_chart(surf, pygame.Rect(40, 744, 740, 245), "Hız", rows, "speed_mps", None, CYAN, "m/s")
        self.draw_png_chart(surf, pygame.Rect(820, 744, 740, 245), "Gap hatası", rows, "gap_error_mm", None, RED, "mm")
        pygame.image.save(surf, str(path))

    def save_single_chart(self, path: Path, rows, y_key, target_key, title, unit, color):
        surf = pygame.Surface((1200, 720))
        surf.fill(BG)
        text(surf, self.fonts["title"], title, 42, 28, TEXT)
        text(surf, self.fonts["small"], f"Senaryo: {self.preset_name} | Süre: {self.compute_metrics()['duration_s']:.2f}s", 42, 62, MUTED)
        self.draw_png_chart(surf, pygame.Rect(42, 96, 1116, 570), title, rows, y_key, target_key, color, unit)
        pygame.image.save(surf, str(path))

    def x_to_screen(self, x_m):
        return int(self.sim_rect.x + (x_m / TRACK_LEN_M) * self.sim_rect.w)

    def handle_event(self, ev):
        if ev.type == pygame.QUIT:
            return False
        if ev.type == pygame.VIDEORESIZE:
            self.screen = pygame.display.set_mode((max(ev.w, MIN_W), max(ev.h, MIN_H)), pygame.RESIZABLE)
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                if self.compare_picker_open:
                    self.compare_picker_open = False
                    self.toast("Karşılaştırma seçimi kapatıldı")
                    return True
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
            if ev.key == pygame.K_m:
                self.beginner_mode = not self.beginner_mode
                self.scroll = 0
                self.toast("Başlangıç modu" if self.beginner_mode else "Gelişmiş mod")
            if ev.key == pygame.K_i:
                self.import_real_data()
            if ev.key == pygame.K_c:
                self.calibrate_from_real_data()
        if self.compare_picker_open:
            return self.handle_compare_picker_event(ev)
        if ev.type == pygame.MOUSEWHEEL:
            mx, _ = pygame.mouse.get_pos()
            if mx < self.left_w:
                self.scroll = clamp(self.scroll - ev.y * 35, 0, self.max_scroll)
                return True
        for b in self.buttons:
            if b.event(ev):
                return True
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.mode_beginner_rect.collidepoint(ev.pos):
                self.beginner_mode = True
                self.scroll = 0
                self.toast("Başlangıç modu açıldı")
                return True
            if self.mode_advanced_rect.collidepoint(ev.pos):
                self.beginner_mode = False
                self.scroll = 0
                self.toast("Gelişmiş mod açıldı")
                return True
        for k in self.visible_slider_keys():
            s = self.sliders[k]
            old = s.value
            if s.event(ev):
                self.selected_key = k
                if abs(old - s.value) > 1e-9:
                    self.analyze_change(k, old, s.value)
                    self.toast(f"{s.label}: {s.value_str()}")
                return True
        # top action buttons handled by position in draw_topbar with rects
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if getattr(self, "help_btn", pygame.Rect(0, 0, 0, 0)).collidepoint(ev.pos):
                self.show_help = not self.show_help
            if getattr(self, "save_btn", pygame.Rect(0, 0, 0, 0)).collidepoint(ev.pos):
                self.save_scenario()
            if getattr(self, "compare_btn", pygame.Rect(0, 0, 0, 0)).collidepoint(ev.pos):
                self.open_compare_picker()
            if getattr(self, "import_btn", pygame.Rect(0, 0, 0, 0)).collidepoint(ev.pos):
                self.import_real_data()
            if getattr(self, "calibrate_btn", pygame.Rect(0, 0, 0, 0)).collidepoint(ev.pos):
                self.calibrate_from_real_data()
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
        if self.compare_picker_open:
            self.draw_compare_picker()
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
        x = max(360, self.w - 850)
        self.help_btn = self.draw_top_button(x, 12, 76, "? Yardım")
        self.save_btn = self.draw_top_button(x + 84, 12, 92, "▣ Kaydet")
        self.compare_btn = self.draw_top_button(x + 184, 12, 118, "⇄ Senaryo")
        self.import_btn = self.draw_top_button(x + 310, 12, 112, "↑ Gerçek Veri")
        self.calibrate_btn = self.draw_top_button(x + 430, 12, 90, "◎ Kalibre")
        self.export_btn = self.draw_top_button(x + 528, 12, 106, "↓ CSV")
        self.theme_btn = self.draw_top_button(x + 642, 12, 76, "◉ Tema")

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

        # Mod seçimi: yeni başlayanlar için sade kontrol listesi, gerektiğinde tam liste.
        text(self.screen, self.fonts["small"], "MOD", x, y, BLUE)
        y += 22
        self.mode_beginner_rect = pygame.Rect(x, y, bw, bh)
        self.mode_advanced_rect = pygame.Rect(x + bw + 10, y, bw, bh)
        rounded(self.screen, BLUE_2 if self.beginner_mode else CARD, self.mode_beginner_rect, 9)
        rounded(self.screen, GREEN if not self.beginner_mode else CARD, self.mode_advanced_rect, 9)
        rounded(self.screen, BLUE if self.beginner_mode else BORDER, self.mode_beginner_rect, 9, 1)
        rounded(self.screen, GREEN if not self.beginner_mode else BORDER, self.mode_advanced_rect, 9, 1)
        text_center(self.screen, self.fonts["small"], "Başlangıç", self.mode_beginner_rect, WHITE)
        text_center(self.screen, self.fonts["small"], "Gelişmiş", self.mode_advanced_rect, WHITE)
        y += bh + 14
        if self.beginner_mode:
            text(self.screen, self.fonts["tiny"], "Sadece en önemli ayarlar gösteriliyor. Tam liste için Gelişmiş.", x, y, MUTED)
            y += 22

        clip = pygame.Rect(0, y, self.left_w, self.h - y - 28)
        old_clip = self.screen.get_clip()
        self.screen.set_clip(clip)
        cy = y - self.scroll
        categories = ["Fizik", "PID Kontrol", "Güç ve Bobin", "Sensör", "Ray ve Hareket", "Gerçekçilik", "Prototip"]
        for cat in categories:
            sliders_in_cat = self.visible_sliders_for_category(cat)
            if not sliders_in_cat:
                continue
            if cy > y - 60 and cy < self.h:
                self.draw_section_header(cat, x, cy)
            cy += 34
            for s in sliders_in_cat:
                if cy > y - 60 and cy < self.h:
                    s.draw(self.screen, self.fonts, x, cy, self.left_w - 32, active=(s.key == self.selected_key))
                cy += 50
            cy += 8
        self.max_scroll = max(0, cy - (self.h - 28))
        self.screen.set_clip(old_clip)

        text(self.screen, self.fonts["tiny"], "SPACE pause | R reset | D darbe | S fren | A vektör | G grafik | H yardım | M mod | I gerçek veri | C kalibre", 14, self.h - 22, FAINT)

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

        # 2. adım: performans ölçümleri sürekli hesaplanır.
        self.draw_performance_panel(x, y)
        y += 118

        self.draw_prototype_panel(x, y)
        y += 92

        self.draw_change_analysis(x, y)
        y += 134 if not self.beginner_mode else 154

        # Grafikler artık sadece gelişmiş moda saklanmıyor; yer varsa her modda görünür.
        if self.show_graphs and y + 190 < self.h:
            self.draw_graphs_compact(x, y)
            y += 190

        if self.show_help and y + 120 < self.h:
            self.draw_help_card(x, y)

    def draw_prototype_panel(self, x, y):
        panel = pygame.Rect(x, y, self.right_w - 32, 80)
        rounded(self.screen, (12, 22, 36), panel, 10)
        rounded(self.screen, BORDER, panel, 10, 1)
        text(self.screen, self.fonts["small"], "PROTOTİP BAĞLANTISI", panel.x + 12, panel.y + 8, BLUE)
        status = "Veri yok" if not self.real_rows else f"{len(self.real_rows)} satır gerçek veri"
        col = MUTED if not self.real_rows else GREEN
        text(self.screen, self.fonts["tiny"], status, panel.x + 12, panel.y + 32, col)
        if self.real_rows:
            text(self.screen, self.fonts["tiny"], self.calibration_report[:70], panel.x + 12, panel.y + 52, MUTED)
        else:
            text(self.screen, self.fonts["tiny"], "I: içe aktar  |  C: kalibre et  |  prototype_data/real_data.csv", panel.x + 12, panel.y + 52, MUTED)

    def draw_performance_panel(self, x, y):
        panel = pygame.Rect(x, y, self.right_w - 32, 104)
        rounded(self.screen, (12, 22, 36), panel, 10)
        rounded(self.screen, BORDER, panel, 10, 1)
        m = self.compute_metrics()
        text(self.screen, self.fonts["small"], "PERFORMANS ÖLÇÜMLERİ", panel.x + 12, panel.y + 10, BLUE)
        score_col = GREEN if m["stability_score"] >= 75 else ORANGE if m["stability_score"] >= 45 else RED
        items = [
            ("Skor", f"{m['stability_score']:.0f}/100", score_col),
            ("Ort. hata", f"{m['avg_abs_error_mm']:.2f} mm", CYAN),
            ("Maks. akım", f"{m['max_current_A']:.2f} A", PURPLE),
            ("Enerji", f"{m['energy_J_est']:.1f} J", YELLOW),
        ]
        gap = 8
        cw = (panel.w - 24 - gap * 3) // 4
        for i, (lab, val, col) in enumerate(items):
            r = pygame.Rect(panel.x + 12 + i * (cw + gap), panel.y + 40, cw, 50)
            rounded(self.screen, CARD, r, 8)
            text_center(self.screen, self.fonts["tiny"], lab, (r.x, r.y + 6, r.w, 16), MUTED)
            text_center(self.screen, self.fonts["small"], val, (r.x, r.y + 24, r.w, 20), col)

    def draw_graphs_compact(self, x, y):
        panel = pygame.Rect(x, y, self.right_w - 32, 176)
        rounded(self.screen, (12, 22, 36), panel, 10)
        rounded(self.screen, BORDER, panel, 10, 1)
        text(self.screen, self.fonts["small"], "CANLI GRAFİKLER", panel.x + 12, panel.y + 8, BLUE)
        text(self.screen, self.fonts["tiny"], "Tam grafikler: Senaryoyu Kaydet", panel.right - 164, panel.y + 10, MUTED)
        charts = [
            ("Boşluk", "gap", GREEN, 0, 30),
            ("Akım", "current", BLUE, 0, 8),
            ("Sıcaklık", "temp", ORANGE, 20, 90),
        ]
        cw = (panel.w - 34) // 3
        ch = 118
        for i, (title, key, col, lo, hi) in enumerate(charts):
            rx = panel.x + 12 + i * (cw + 5)
            ry = panel.y + 42
            self.draw_chart((rx, ry, cw, ch), title, self.sim.history[key], col, lo, hi)

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
            ("Efektif Akım", f"{self.sim.effective_current:.2f} A", TEXT),
            ("Bus Voltaj", f"{self.sim.bus_voltage:.1f} V", TEXT),
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

    def draw_change_analysis(self, x, y):
        panel_h = 136 if not self.beginner_mode else 144
        panel = pygame.Rect(x, y, self.right_w - 32, panel_h)
        rounded(self.screen, (12, 22, 36), panel, 10)
        rounded(self.screen, self.last_change_color, panel, 10, 1)
        text(self.screen, self.fonts["small"], "SON DEĞİŞİKLİK ANALİZİ", panel.x + 12, panel.y + 10, self.last_change_color)
        text(self.screen, self.fonts["tiny"], "Slider oynatınca burası güncellenir", panel.right - 174, panel.y + 12, MUTED)
        yy = panel.y + 36
        for line in wrap_lines(self.last_change_title, self.fonts["small"], panel.w - 24):
            text(self.screen, self.fonts["small"], line, panel.x + 12, yy, TEXT)
            yy += 18
        yy += 2
        for line in wrap_lines(self.last_change_body, self.fonts["tiny"], panel.w - 24):
            if yy > panel.bottom - 34:
                break
            text(self.screen, self.fonts["tiny"], line, panel.x + 12, yy, MUTED)
            yy += 14
        if yy < panel.bottom - 18:
            text(self.screen, self.fonts["tiny"], "İzle: " + self.last_change_watch, panel.x + 12, panel.bottom - 20, YELLOW)

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

    # ========================================================
    # V10: SENARYO SEÇEREK KARŞILAŞTIRMA MODALI
    # ========================================================

    def handle_compare_picker_event(self, ev):
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                self.compare_picker_open = False
                self.toast("Karşılaştırma seçimi kapatıldı")
                return True
            if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.compare_selected_scenarios()
                return True
            if ev.key == pygame.K_r:
                self.compare_scenarios = self.saved_scenario_dirs()
                self.toast("Senaryo listesi yenilendi")
                return True
        if ev.type == pygame.MOUSEWHEEL:
            self.compare_scroll = clamp(self.compare_scroll - ev.y * 36, 0, self.compare_max_scroll)
            return True
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.compare_cancel_btn.collidepoint(ev.pos):
                self.compare_picker_open = False
                self.toast("Karşılaştırma seçimi kapatıldı")
                return True
            if self.compare_refresh_btn.collidepoint(ev.pos):
                self.compare_scenarios = self.saved_scenario_dirs()
                self.compare_selected = [p for p in self.compare_selected if p in self.compare_scenarios]
                self.toast("Senaryo listesi yenilendi")
                return True
            if self.compare_run_btn.collidepoint(ev.pos):
                self.compare_selected_scenarios()
                return True
            for row_rect, scenario_dir in self.compare_row_rects:
                if row_rect.collidepoint(ev.pos):
                    self.toggle_compare_selection(scenario_dir)
                    return True
        return True

    def draw_compare_picker_button(self, rect: pygame.Rect, label: str, color, enabled=True):
        fill = color if enabled else (42, 50, 64)
        rounded(self.screen, fill, rect, 10)
        rounded(self.screen, BORDER if enabled else (62, 68, 80), rect, 10, 1)
        text_center(self.screen, self.fonts["small"], label, rect, TEXT if enabled else MUTED)

    def draw_compare_picker(self):
        # Modal arka plan
        overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 175))
        self.screen.blit(overlay, (0, 0))
        modal_w = min(920, self.w - 90)
        modal_h = min(600, self.h - 80)
        modal = pygame.Rect((self.w - modal_w) // 2, (self.h - modal_h) // 2, modal_w, modal_h)
        rounded(self.screen, PANEL, modal, 18)
        rounded(self.screen, BLUE, modal, 18, 1)

        text(self.screen, self.fonts["title"], "Senaryo Karşılaştırma Seçimi", modal.x + 24, modal.y + 20, TEXT)
        text(self.screen, self.fonts["small"], "Karşılaştırmak istediğin iki kaydı seç. İlk seçim A, ikinci seçim B olur. Enter: karşılaştır, Esc: kapat.", modal.x + 24, modal.y + 52, MUTED)

        # Seçim özeti
        chip_y = modal.y + 82
        chip_a = pygame.Rect(modal.x + 24, chip_y, (modal.w - 72) // 2, 46)
        chip_b = pygame.Rect(chip_a.right + 24, chip_y, chip_a.w, 46)
        for idx, chip in enumerate([chip_a, chip_b]):
            sel = self.compare_selected[idx] if idx < len(self.compare_selected) else None
            rounded(self.screen, (10, 20, 36), chip, 12)
            rounded(self.screen, GREEN if sel else BORDER, chip, 12, 1)
            label = "A" if idx == 0 else "B"
            text(self.screen, self.fonts["small"], f"Senaryo {label}", chip.x + 14, chip.y + 6, GREEN if sel else MUTED)
            shown = self.scenario_display_name(sel) if sel else "Henüz seçilmedi"
            for line in wrap_lines(shown, self.fonts["tiny"], chip.w - 28)[:1]:
                text(self.screen, self.fonts["tiny"], line, chip.x + 14, chip.y + 26, TEXT if sel else FAINT)

        # Liste alanı
        list_rect = pygame.Rect(modal.x + 24, modal.y + 148, modal.w - 48, modal.h - 226)
        rounded(self.screen, (8, 16, 30), list_rect, 14)
        rounded(self.screen, BORDER, list_rect, 14, 1)
        text(self.screen, self.fonts["tiny"], "Seç", list_rect.x + 18, list_rect.y + 12, MUTED)
        text(self.screen, self.fonts["tiny"], "Senaryo", list_rect.x + 88, list_rect.y + 12, MUTED)
        text(self.screen, self.fonts["tiny"], "Skor", list_rect.right - 250, list_rect.y + 12, MUTED)
        text(self.screen, self.fonts["tiny"], "Ort. hata", list_rect.right - 178, list_rect.y + 12, MUTED)
        text(self.screen, self.fonts["tiny"], "Süre", list_rect.right - 82, list_rect.y + 12, MUTED)
        pygame.draw.line(self.screen, BORDER, (list_rect.x + 12, list_rect.y + 34), (list_rect.right - 12, list_rect.y + 34), 1)

        self.compare_row_rects = []
        row_h = 64
        content_h = max(0, len(self.compare_scenarios) * row_h)
        visible_h = list_rect.h - 44
        self.compare_max_scroll = max(0, content_h - visible_h)
        start_y = list_rect.y + 42 - int(self.compare_scroll)
        clip_old = self.screen.get_clip()
        self.screen.set_clip(list_rect.inflate(-6, -40).move(0, 22))

        for i, scenario_dir in enumerate(self.compare_scenarios):
            row = pygame.Rect(list_rect.x + 10, start_y + i * row_h, list_rect.w - 20, row_h - 8)
            if row.bottom < list_rect.y + 36 or row.y > list_rect.bottom - 8:
                continue
            selected = scenario_dir in self.compare_selected
            select_index = self.compare_selected.index(scenario_dir) + 1 if selected else 0
            rounded(self.screen, CARD_HOVER if selected else CARD, row, 12)
            rounded(self.screen, GREEN if selected else (42, 60, 86), row, 12, 1)
            self.compare_row_rects.append((row, scenario_dir))

            # seçim işareti
            circ = (row.x + 30, row.centery)
            pygame.draw.circle(self.screen, GREEN if selected else BORDER, circ, 14, 2)
            if selected:
                text_center(self.screen, self.fonts["small"], "A" if select_index == 1 else "B", pygame.Rect(circ[0] - 14, circ[1] - 14, 28, 28), GREEN)

            info = self.scenario_summary(scenario_dir)
            metrics = info.get("metrics", {}) if isinstance(info.get("metrics", {}), dict) else {}
            name = self.scenario_display_name(scenario_dir)
            text(self.screen, self.fonts["small"], name, row.x + 68, row.y + 10, TEXT)
            text(self.screen, self.fonts["tiny"], scenario_dir.name, row.x + 68, row.y + 34, MUTED)
            score = metrics.get("stability_score", metrics.get("score", 0)) if metrics else 0
            avg = metrics.get("avg_abs_error_mm", 0) if metrics else 0
            dur = metrics.get("duration_s", 0) if metrics else 0
            sc_col = GREEN if float(score) >= 75 else (ORANGE if float(score) >= 45 else RED)
            text(self.screen, self.fonts["small"], f"{float(score):.1f}", row.right - 250, row.y + 20, sc_col)
            text(self.screen, self.fonts["small"], f"{float(avg):.3f} mm", row.right - 178, row.y + 20, CYAN)
            text(self.screen, self.fonts["small"], f"{float(dur):.1f} s", row.right - 82, row.y + 20, TEXT)

        self.screen.set_clip(clip_old)
        # Kaydırma göstergesi
        if self.compare_max_scroll > 0:
            bar = pygame.Rect(list_rect.right - 10, list_rect.y + 42, 4, visible_h)
            pygame.draw.rect(self.screen, (38, 48, 66), bar, border_radius=2)
            thumb_h = max(34, int(visible_h * visible_h / max(content_h, 1)))
            thumb_y = bar.y + int((visible_h - thumb_h) * self.compare_scroll / max(self.compare_max_scroll, 1))
            pygame.draw.rect(self.screen, BLUE, (bar.x, thumb_y, bar.w, thumb_h), border_radius=2)

        # Alt butonlar
        by = modal.bottom - 58
        self.compare_refresh_btn = pygame.Rect(modal.x + 24, by, 120, 38)
        self.compare_cancel_btn = pygame.Rect(modal.right - 292, by, 120, 38)
        self.compare_run_btn = pygame.Rect(modal.right - 160, by, 136, 38)
        self.draw_compare_picker_button(self.compare_refresh_btn, "Yenile", BLUE_2, True)
        self.draw_compare_picker_button(self.compare_cancel_btn, "Vazgeç", (55, 65, 82), True)
        self.draw_compare_picker_button(self.compare_run_btn, "Karşılaştır", GREEN, len(self.compare_selected) == 2)
        text(self.screen, self.fonts["tiny"], "Not: Grafiklerde yeşil çizgiler best/ideal, kırmızı çizgiler worst/limit davranışı gösterir.", modal.x + 160, by + 11, MUTED)

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
    if "UYARI" in s or "LİMİT" in s or "SICAK" in s or "YAKIN" in s or "TERMAL" in s or "DOYUM" in s or "SENSÖR" in s:
        return ORANGE
    return RED


if __name__ == "__main__":
    App().run()
