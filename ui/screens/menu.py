"""
Главное меню: неоновый заголовок, кнопки с анимацией наведения,
экраны рекордов и управления. Является Screen-экраном; состояние хранит
внутри (menu | records | controls | play | quit) — приложение читает его
через свойство `next_action`.
"""

import math

import pygame

from config.settings import ACCENT, GOLD, TEXT_COLOR, WINDOW_H, WINDOW_W
from ui.fonts import font
from utils.mathx import lerp_color

MENU_ITEMS = [("ИГРАТЬ", "play"), ("РЕКОРДЫ", "records"),
              ("УПРАВЛЕНИЕ", "controls"), ("ВЫХОД", "quit")]


class MenuButton:
    def __init__(self, label, action, rect):
        self.label = label
        self.action = action
        self.rect = rect
        self.hover = 0.0      # 0..1 плавная анимация наведения


class MainMenu:
    def __init__(self, ctx):
        self.ctx = ctx                    # AppContext
        self.bg = ctx.bg
        self.get_high_scores = ctx.high_scores
        self.index = 0
        self.time = 0.0
        self.state = "menu"               # menu | records | controls | play | quit
        self.fade = 1.0                   # чёрный экран при входе -> прозрачный
        self.buttons = []
        self._layout_buttons()

    @property
    def next_action(self):
        return self.state

    def restart(self):
        """Сброс для повторного входа из игрового экрана."""
        self.state = "menu"
        self.time = 0.0
        self.fade = 1.0

    def _layout_buttons(self):
        bw, bh = 300, 52
        cx = WINDOW_W // 2
        y0 = WINDOW_H // 2 - 20
        self.buttons = []
        for i, (label, act) in enumerate(MENU_ITEMS):
            rect = pygame.Rect(cx - bw // 2, y0 + i * (bh + 14), bw, bh)
            self.buttons.append(MenuButton(label, act, rect))

    def handle_event(self, event):
        if self.state in ("records", "controls"):
            if event.type == pygame.KEYDOWN or \
               (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
                self.state = "menu"
            return
        if self.state != "menu":
            return
        if event.type == pygame.MOUSEMOTION:
            for i, b in enumerate(self.buttons):
                if b.rect.collidepoint(event.pos):
                    self.index = i
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, b in enumerate(self.buttons):
                if b.rect.collidepoint(event.pos):
                    self.index = i
                    self._activate()
                    break
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.index = (self.index - 1) % len(self.buttons)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.index = (self.index + 1) % len(self.buttons)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER,
                               pygame.K_SPACE):
                self._activate()
            elif event.key == pygame.K_ESCAPE:
                self.state = "quit"

    def _activate(self):
        act = self.buttons[self.index].action
        if act == "quit":
            self.state = "quit"
        elif act == "play":
            self.state = "play"
        else:
            self.state = act

    def update(self, dt):
        self.time += dt
        self.fade = max(0.0, self.fade - dt * 2.2)
        for i, b in enumerate(self.buttons):
            target = 1.0 if i == self.index else 0.0
            b.hover += (target - b.hover) * min(1.0, dt * 12)

    # ---------- отрисовка ----------
    def _title(self, screen):
        t_font = font("title", bold=True)
        sub_font = font("small", bold=True)

        title = "ТЕТРИС"
        # побуквенная радуга + синусоидальная волна + неоновое свечение
        letters = []
        total_w = 0
        hue_shift = self.time * 40
        for i, ch in enumerate(title):
            hue = ((i * 28 + hue_shift) % 360) / 360
            col = pygame.Color(0, 0, 0, 255)
            col.hsva = (hue * 360, 85, 100, 100)
            srf = t_font.render(ch, True, col)
            letters.append((srf, col, i))
            total_w += srf.get_width()
        x = WINDOW_W // 2 - total_w // 2
        base_y = WINDOW_H // 2 - 190
        for srf, col, i in letters:
            wave = math.sin(self.time * 2.4 + i * 0.55) * 7
            # glow-копия буквы
            shadow = pygame.Surface(srf.get_size(), pygame.SRCALPHA)
            shadow.fill((col.r, col.g, col.b, 120))
            shadow.blit(srf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            bigglow = pygame.transform.smoothscale(
                shadow, (srf.get_width() + 16, srf.get_height() + 16))
            screen.blit(bigglow,
                        bigglow.get_rect(
                            center=(x + srf.get_width() // 2,
                                    base_y + srf.get_height() // 2 +
                                    int(wave))),
                        special_flags=pygame.BLEND_ADD)
            screen.blit(srf, (x, base_y + int(wave)))
            x += srf.get_width()
        # подзаголовок
        sub_col = lerp_color((160, 160, 190), ACCENT,
                             0.5 + 0.5 * math.sin(self.time * 2))
        sub = sub_font.render("NEON EDITION · АНИМАЦИИ · ЭФФЕКТЫ",
                              True, sub_col)
        screen.blit(sub, sub.get_rect(
            center=(WINDOW_W // 2, base_y + 86)))

    def _draw_menu(self, screen):
        self._title(screen)
        fnt = font("mid", bold=True)
        for b in self.buttons:
            hov = b.hover
            r = b.rect.copy()
            r.inflate_ip(int(10 * hov), int(6 * hov))
            base_col = lerp_color((24, 24, 40), (44, 36, 74), hov)
            bg_s = pygame.Surface(r.size, pygame.SRCALPHA)
            bg_s.fill((*base_col, int(180 + 60 * hov)))
            screen.blit(bg_s, r.topleft)
            border = lerp_color((70, 70, 100), ACCENT, hov)
            if hov > 0.05:
                halo = pygame.Surface((r.w + 12, r.h + 12), pygame.SRCALPHA)
                pygame.draw.rect(halo, (*ACCENT, int(70 * hov)),
                                 halo.get_rect(), 6, border_radius=14)
                screen.blit(halo, (r.x - 6, r.y - 6))
                tri = [(r.x - 20, r.centery - 8),
                       (r.x - 20, r.centery + 8),
                       (r.x - 9, r.centery)]
                pygame.draw.polygon(screen, ACCENT, tri)
            pygame.draw.rect(screen, border, r, 2, border_radius=10)
            col = lerp_color((200, 200, 215), (255, 255, 255), hov)
            txt = fnt.render(b.label, True, col)
            screen.blit(txt, txt.get_rect(center=r.center))
        foot = font("tiny").render(
            "Enter / клик — выбрать · Esc — выход", True, (140, 140, 165))
        screen.blit(foot, foot.get_rect(
            center=(WINDOW_W // 2, WINDOW_H - 26)))

    def _draw_records(self, screen):
        head = font("head", bold=True)
        body = font("body", bold=True)
        t = head.render("РЕКОРДЫ", True, GOLD)
        wob = math.sin(self.time * 3) * 3
        screen.blit(t, t.get_rect(center=(WINDOW_W // 2, 90 + wob)))
        scores = self.get_high_scores()
        if not scores:
            msg = body.render("Пока пусто — сыграй партию!", True,
                              (190, 190, 210))
            screen.blit(msg, msg.get_rect(center=(WINDOW_W // 2,
                                                  WINDOW_H // 2)))
        for i, s in enumerate(scores[:5]):
            line = body.render(f"{i + 1}.  {s}", True,
                               GOLD if i == 0 else TEXT_COLOR)
            screen.blit(line, line.get_rect(
                midleft=(WINDOW_W // 2 - 110, 170 + i * 40)))
        back = font("foot").render(
            "Любая клавиша — назад", True, (150, 150, 175))
        screen.blit(back, back.get_rect(center=(WINDOW_W // 2,
                                                 WINDOW_H - 40)))

    def _draw_controls(self, screen):
        head = font("head", bold=True)
        body = font("body2")
        t = head.render("УПРАВЛЕНИЕ", True, ACCENT)
        screen.blit(t, t.get_rect(center=(WINDOW_W // 2, 90)))
        rows = [("← / →  или  A / D", "движение"),
                ("↓  или  S", "мягкое падение"),
                ("ПРОБЕЛ", "жёсткий сброс"),
                ("↑  /  X", "поворот по часовой"),
                ("Z", "поворот против часовой"),
                ("C", "удержание (hold)"),
                ("P", "пауза"),
                ("R", "рестарт"),
                ("ESC", "главное меню")]
        cy = 150
        for i, (k, v) in enumerate(rows):
            kk = body.render(k, True, GOLD)
            vv = body.render(v, True, TEXT_COLOR)
            screen.blit(kk, (WINDOW_W // 2 - 230, cy + i * 36))
            screen.blit(vv, (WINDOW_W // 2 + 10, cy + i * 36))
        back = font("foot").render(
            "Любая клавиша — назад", True, (150, 150, 175))
        screen.blit(back, back.get_rect(center=(WINDOW_W // 2,
                                                 WINDOW_H - 40)))

    def render(self):
        screen = self.ctx.screen
        self.bg.draw(screen, pieces_visible=True)
        if self.state == "menu":
            self._draw_menu(screen)
        elif self.state == "records":
            self._draw_records(screen)
        elif self.state == "controls":
            self._draw_controls(screen)
        # затемнение при переходе fade-in
        if self.fade > 0.01:
            black = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
            black.fill((5, 5, 12, int(255 * self.fade)))
            screen.blit(black, (0, 0))
