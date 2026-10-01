import pygame
import random
import math
from constants import *

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.randint(4, 10)
        self.life = random.randint(40, 80)
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1, 4)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.gravity = 0.15

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.life -= 1
        self.size = max(0, self.size - 0.1)

    def draw(self, screen):
        if self.life > 0:
            # 使用带透明度的Surface绘制
            s = pygame.Surface((int(self.size*2), int(self.size*2)), pygame.SRCALPHA)
            alpha = int(255 * (self.life / 80))
            pygame.draw.circle(s, (*self.color, alpha), (int(self.size), int(self.size)), int(self.size))
            screen.blit(s, (self.x - self.size, self.y - self.size))

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color, action=None, font=None, tooltip=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.base_color = color
        self.hover_color = hover_color
        self.current_color = color
        self.action = action
        self.is_hovered = False
        self.enabled = True
        self.font = font
        self.tooltip = tooltip
        
        # 动画属性
        self.scale = 1.0
        self.target_scale = 1.0
        self.anim_speed = 0.1

    def update(self):
        # 平滑缩放动画
        if self.is_hovered and self.enabled:
            self.target_scale = BUTTON_HOVER_SCALE
        else:
            self.target_scale = 1.0
            
        diff = self.target_scale - self.scale
        if abs(diff) > 0.01:
            self.scale += diff * self.anim_speed
        else:
            self.scale = self.target_scale

    def draw(self, screen):
        if not self.enabled:
            # 禁用状态绘制灰色
            draw_rect = self.rect.copy()
            pygame.draw.rect(screen, GRAY, draw_rect, border_radius=12)
            if self.font:
                text_surf = self.font.render(self.text, True, DARK_GRAY)
                text_rect = text_surf.get_rect(center=draw_rect.center)
                screen.blit(text_surf, text_rect)
            return

        # 计算缩放后的矩形
        w = int(self.rect.width * self.scale)
        h = int(self.rect.height * self.scale)
        cx, cy = self.rect.center
        draw_rect = pygame.Rect(cx - w//2, cy - h//2, w, h)
        
        # 绘制阴影
        shadow_rect = draw_rect.move(4, 4)
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(s, SHADOW_COLOR, s.get_rect(), border_radius=12)
        screen.blit(s, shadow_rect.topleft)

        # 绘制按钮主体
        color = self.hover_color if self.is_hovered else self.base_color
        pygame.draw.rect(screen, color, draw_rect, border_radius=12)
        
        # 绘制高光 (顶部亮线)
        highlight_rect = pygame.Rect(draw_rect.x + 5, draw_rect.y + 2, draw_rect.width - 10, 2)
        pygame.draw.rect(screen, (255, 255, 255, 100), highlight_rect, border_radius=1)

        # 绘制边框
        pygame.draw.rect(screen, WHITE, draw_rect, 2, border_radius=12)
        
        if self.font:
            text_surf = self.font.render(self.text, True, WHITE)
            text_rect = text_surf.get_rect(center=draw_rect.center)
            screen.blit(text_surf, text_rect)

    def check_hover(self, mouse_pos):
        if self.enabled:
            self.is_hovered = self.rect.collidepoint(mouse_pos)
            return self.is_hovered and self.tooltip is not None
        return False

    def handle_event(self, event):
        if self.enabled and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.action:
                    self.action()

class DiceVisual:
    def __init__(self, x, y, size=80, font=None, target_val=1):
        self.rect = pygame.Rect(x, y, size, size)
        self.start_x = x
        self.start_y = y
        self.value = 1
        self.target_value = target_val
        
        # 状态
        self.is_selected = False
        self.is_rolling = False
        self.is_locked = False
        self.is_skill = False
        
        # 动画相关
        self.anim_timer = 0
        self.anim_duration = 0
        self.rotation = 0
        self.scale = 1.0
        
        self.font = font

    def start_roll(self, duration=40):
        self.is_rolling = True
        self.anim_timer = duration
        self.anim_duration = duration
        # 抛物线动画参数
        self.jump_height = 150

    def update(self):
        if self.is_rolling:
            self.anim_timer -= 1
            progress = 1 - (self.anim_timer / self.anim_duration)
            
            # 抛物线运动: y = 4h * x * (1-x)
            # 这里我们让它原地跳起
            jump_y = 4 * self.jump_height * progress * (1 - progress)
            self.rect.y = self.start_y - jump_y
            
            # 旋转动画
            self.rotation = (self.rotation + 20) % 360
            
            # 随机变数
            if self.anim_timer % 5 == 0:
                if self.is_skill:
                    self.value = random.choice(['S', '-'])
                else:
                    self.value = random.randint(1, 6)
            
            if self.anim_timer <= 0:
                self.is_rolling = False
                self.value = self.target_value
                self.rect.y = self.start_y
                self.rotation = 0
                # 落地特效 (震动)
                self.scale = 1.2 
        
        # 落地回弹动画
        if self.scale > 1.0:
            self.scale -= 0.05
        elif self.scale < 1.0:
            self.scale = 1.0

    def draw(self, screen):
        # 准备绘制表面
        size = int(self.rect.width * self.scale)
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # 确定颜色
        if self.is_locked:
            bg_color = (200, 200, 200) # 锁定灰
            border_color = PURPLE
        elif self.is_selected:
            bg_color = YELLOW
            border_color = ORANGE
        else:
            bg_color = WHITE
            border_color = BLACK
            
        if self.is_skill:
            bg_color = (220, 180, 255) if not self.is_selected else (250, 200, 255)

        # 绘制圆角矩形背景
        rect = pygame.Rect(0, 0, size, size)
        pygame.draw.rect(surf, bg_color, rect, border_radius=15)
        pygame.draw.rect(surf, border_color, rect, 4, border_radius=15)
        
        # 绘制点数
        text_color = BLACK
        if self.value == 'S': text_color = RED
        elif self.is_locked: text_color = PURPLE
        
        if self.font:
            # 旋转文字
            text_surf = self.font.render(str(self.value), True, text_color)
            text_rect = text_surf.get_rect(center=(size//2, size//2))
            
            if self.is_rolling:
                text_surf = pygame.transform.rotate(text_surf, self.rotation)
                text_rect = text_surf.get_rect(center=(size//2, size//2))
                
            surf.blit(text_surf, text_rect)

        # 绘制到屏幕
        # 如果在旋转，整个骰子也旋转一下会更生动
        if self.is_rolling:
            rotated_surf = pygame.transform.rotate(surf, self.rotation)
            new_rect = rotated_surf.get_rect(center=self.rect.center)
            screen.blit(rotated_surf, new_rect)
        else:
            # 选中状态稍微上浮
            offset_y = -10 if (self.is_selected and not self.is_locked) else 0
            screen.blit(surf, (self.rect.x, self.rect.y + offset_y))

    def handle_event(self, event):
        if not self.is_locked and not self.is_rolling: 
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # 简单的碰撞检测
                if self.rect.collidepoint(event.pos):
                    self.is_selected = not self.is_selected

def draw_tooltip(screen, text, x, y, font):
    """绘制悬浮提示框"""
    if not text or not font:
        return
        
    lines = text.split('\n')
    surfs = [font.render(line, True, WHITE) for line in lines]
    
    max_w = max(s.get_width() for s in surfs)
    total_h = sum(s.get_height() for s in surfs) + (len(lines)-1) * 5
    
    padding = 12
    rect = pygame.Rect(x + 20, y + 20, max_w + padding*2, total_h + padding*2)
    
    # 边界检查
    if rect.right > SCREEN_WIDTH:
        rect.x -= rect.width + 40
    if rect.bottom > SCREEN_HEIGHT:
        rect.y -= rect.height + 40
        
    # 绘制半透明背景
    s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(s, TOOLTIP_BG, s.get_rect(), border_radius=8)
    screen.blit(s, rect.topleft)
    
    # 绘制边框
    pygame.draw.rect(screen, (100, 100, 100), rect, 1, border_radius=8)
    
    curr_y = rect.y + padding
    for s in surfs:
        screen.blit(s, (rect.x + padding, curr_y))
        curr_y += s.get_height() + 5
