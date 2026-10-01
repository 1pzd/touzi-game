import pygame
import random
from constants import *
from ui_elements import Button, DiceVisual, Particle, draw_tooltip

class UIManager:
    def __init__(self, screen):
        self.screen = screen
        self.buttons = []
        self.dice_visuals = []
        self.particles = []
        self.log_messages = []
        self.shake_timer = 0
        self.shake_intensity = 0
        self.fade_alpha = 0
        self.fade_speed = 5
        self.tooltip = None
        
        # 字体初始化
        self.init_fonts()

    def init_fonts(self):
        font_names = ["simhei", "microsoftyahei", "fangsong", "kaiti", "arialunicode"]
        font_name = None
        available = pygame.font.get_fonts()
        for name in font_names:
            if name in available:
                font_name = name
                break
        
        if font_name:
            self.font_large = pygame.font.SysFont(font_name, 60)
            self.font_medium = pygame.font.SysFont(font_name, 30)
            self.font_small = pygame.font.SysFont(font_name, 20)
        else:
            self.font_large = pygame.font.Font(None, 60)
            self.font_medium = pygame.font.Font(None, 30)
            self.font_small = pygame.font.Font(None, 20)

    def add_button(self, btn):
        self.buttons.append(btn)

    def clear_buttons(self):
        self.buttons = []

    def clear_visuals(self):
        """清理所有视觉元素（骰子、粒子）"""
        self.dice_visuals = []
        self.particles = []

    def add_log(self, msg):
        self.log_messages.append(msg)
        if len(self.log_messages) > 8:
            self.log_messages.pop(0)

    def spawn_particles(self, x, y, color, count=15):
        for _ in range(count):
            self.particles.append(Particle(x, y, color))

    def trigger_shake(self, intensity=10, duration=20):
        self.shake_intensity = intensity
        self.shake_timer = duration

    def start_fade(self, speed=5):
        self.fade_alpha = 255
        self.fade_speed = speed

    def update(self):
        # 更新粒子
        for p in self.particles[:]:
            p.update()
            if p.life <= 0:
                self.particles.remove(p)
        
        # 更新按钮动画
        for btn in self.buttons:
            btn.update()
            
        # 更新骰子动画
        for dv in self.dice_visuals:
            dv.update()

        # 更新震动
        if self.shake_timer > 0:
            self.shake_timer -= 1

        # 更新淡入淡出
        if self.fade_alpha > 0:
            self.fade_alpha -= self.fade_speed
            if self.fade_alpha < 0:
                self.fade_alpha = 0

    def draw_base(self):
        """绘制基础层（背景、粒子、骰子、按钮）"""
        # 应用震动偏移
        offset_x = 0
        offset_y = 0
        if self.shake_timer > 0:
            offset_x = random.randint(-self.shake_intensity, self.shake_intensity)
            offset_y = random.randint(-self.shake_intensity, self.shake_intensity)
        
        # 创建临时 Surface 用于震动效果
        shake_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        shake_surf.fill(BG_COLOR)
        
        # 绘制粒子
        for p in self.particles:
            p.draw(shake_surf)

        # 绘制骰子
        for dv in self.dice_visuals:
            dv.draw(shake_surf)

        # 绘制按钮
        mouse_pos = pygame.mouse.get_pos()
        self.tooltip = None
        for btn in self.buttons:
            btn.draw(shake_surf)
            if btn.check_hover(mouse_pos):
                self.tooltip = btn.tooltip

        # 绘制日志
        for i, msg in enumerate(self.log_messages):
            text = self.font_small.render(msg, True, WHITE)
            bg_rect = text.get_rect(topleft=(SCREEN_WIDTH//2 - text.get_width()//2, 100 + i * 28))
            bg_rect.inflate_ip(10, 4)
            s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            s.fill((0, 0, 0, 100))
            shake_surf.blit(s, bg_rect)
            shake_surf.blit(text, (bg_rect.x + 5, bg_rect.y + 2))

        # 将震动层绘制到主屏幕
        self.screen.blit(shake_surf, (offset_x, offset_y))

    def draw_overlay(self):
        """绘制顶层（淡入淡出、Tooltip）"""
        # 绘制淡入淡出层
        if self.fade_alpha > 0:
            fade_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            fade_surf.fill((0, 0, 0, int(self.fade_alpha)))
            self.screen.blit(fade_surf, (0, 0))

        # 绘制 Tooltip (最上层)
        if self.tooltip:
            mouse_pos = pygame.mouse.get_pos()
            draw_tooltip(self.screen, self.tooltip, mouse_pos[0], mouse_pos[1], self.font_small)

    def draw_text_centered(self, text, y, font, color=WHITE):
        surf = font.render(text, True, color)
        rect = surf.get_rect(center=(SCREEN_WIDTH//2, y))
        self.screen.blit(surf, rect)
