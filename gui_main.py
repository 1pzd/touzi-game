import pygame
import sys
import random
import threading
from dice import Dice
from skill import Skill
from character import Character
from player import Player
from game_engine import GameEngine
from constants import *
from ui_elements import Button, DiceVisual, Particle
from network import Network
from ui_manager import UIManager

class GameGUI:
    def __init__(self):
        pygame.init()
        # 全屏模式
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
        pygame.display.set_caption("划时代双人对战游戏 - 终极版")
        self.clock = pygame.time.Clock()
        
        # 初始化 UI 管理器
        self.ui = UIManager(self.screen)
        
        # 游戏状态
        self.state = "MODE_SELECT" 
        self.sub_state = "P1_SELECT_CHAR" 
        
        self.game_mode = "PVP" 
        self.p1_data = {"char": None, "skill": None}
        self.p2_data = {"char": None, "skill": None}
        
        self.coin_toss_timer = 0
        self.coin_result = None
        
        self.turn_skill_active = False 
        
        # 联机相关
        self.network = None
        self.is_online = False
        self.my_player_id = None # 1 or 2
        self.input_room_code = ""
        self.input_server_ip = "127.0.0.1" # 默认本地
        self.room_code = ""
        
        # 骰子视觉列表 (分离管理)
        self.attacker_dice_visuals = []
        self.defender_dice_visuals = []
        
        self.create_mode_select_screen()

    def wait_and_draw(self, duration_ms):
        start = pygame.time.get_ticks()
        while pygame.time.get_ticks() - start < duration_ms:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
            self.draw()
            self.clock.tick(FPS)

    # --- 角色与技能工厂 ---
    def create_character(self, type_id, skill_type):
        skill = None
        if skill_type == "magic":
            skill = Skill("魔术骰子", "每局一次，指定任意点数", 1, skill_type="magic_dice")
        elif skill_type == "satellite":
            skill = Skill("卫星骰子", "每局一次，投掷后可更改场地", 1, skill_type="satellite")
        elif skill_type == "heal":
            skill = Skill("治疗骰子", "每局一次，点数即为回血量", 1, skill_type="heal_dice")
        elif skill_type == "shield":
            skill = Skill("星盾骰子", "每局一次，防守投1免疫死亡", 1, skill_type="shield_dice")

        if type_id == "savior":
            c = Character("救世主", 20, 3, 2, "savior", "血量>10反伤50%，<10吸血50%")
        elif type_id == "necro":
            c = Character("死灵法师", 34, 4, 2, "necromancer", "首次死亡投3骰>12半血复活")
        elif type_id == "swordfish":
            c = Character("剑鱼骑士", 28, 3, 3, "swordfish", "全偶数伤害+50%")
        elif type_id == "silvermane":
            c = Character("银鬃铁卫", 32, 2, 3, "silvermane", "受击[3,7]反击造成真实伤害")
        elif type_id == "deer":
            c = Character("丰饶神鹿", 40, 2, 2, "deer", "造成伤害挂种，2回合后爆10真伤")
        elif type_id == "star_bug":
            c = Character("碎星王虫", 26, 4, 2, "star_bug", "若骰子点数成对出现，破甲50%")
        
        if c and skill:
            c.equipped_skill = skill
        return c

    # --- 界面构建 ---
    def create_mode_select_screen(self):
        self.ui.clear_buttons()
        self.ui.clear_visuals() # 清理残留
        self.attacker_dice_visuals = []
        self.defender_dice_visuals = []
        self.ui.log_messages = []
        self.ui.add_log("欢迎来到划时代双人对战游戏")
        
        self.ui.add_button(Button(SCREEN_WIDTH//2 - 150, 300, 300, 80, "玩家对战 (PvP)", BLUE, (40, 140, 200), lambda: self.select_mode("PVP"), self.ui.font_medium, "与朋友进行本地双人对战"))
        self.ui.add_button(Button(SCREEN_WIDTH//2 - 150, 400, 300, 80, "人机对战 (PvE)", RED, (200, 50, 50), lambda: self.select_mode("PVE"), self.ui.font_medium, "挑战高难度 AI 对手"))
        self.ui.add_button(Button(SCREEN_WIDTH//2 - 150, 500, 300, 80, "联机对战 (Online)", PURPLE, (142, 68, 173), lambda: self.select_mode("ONLINE"), self.ui.font_medium, "通过房间号远程联机"))

    def select_mode(self, mode):
        self.game_mode = mode
        if mode == "ONLINE":
            self.state = "INPUT_IP"
            self.ui.add_log("请输入服务器IP地址 (默认本机):")
        else:
            self.state = "SELECT_CHAR"
            self.sub_state = "P1_SELECT_CHAR"
            self.create_char_select_screen()

    def connect_to_server(self):
        self.state = "CONNECT_SERVER"
        self.ui.add_log(f"正在连接 {self.input_server_ip} ...")
        self.draw()
        pygame.display.flip()
        
        self.network = Network(self.input_server_ip) 
        if self.network.connect():
            self.ui.add_log("连接成功！")
            self.state = "ROOM_MENU"
            self.create_room_menu()
        else:
            self.ui.add_log("连接失败，请检查IP或服务器")
            self.wait_and_draw(2000)
            self.state = "INPUT_IP" # 返回输入IP界面

    def create_room_menu(self):
        self.ui.clear_buttons()
        self.ui.add_button(Button(SCREEN_WIDTH//2 - 150, 300, 300, 80, "创建房间", BLUE, (40, 140, 200), self.action_create_room, self.ui.font_medium))
        self.ui.add_button(Button(SCREEN_WIDTH//2 - 150, 400, 300, 80, "加入房间", GREEN, (46, 200, 113), self.action_join_input, self.ui.font_medium))
        self.input_room_code = ""

    def action_create_room(self):
        self.network.create_room()
        self.state = "WAITING_ROOM"
        self.ui.add_log("正在创建房间...")

    def action_join_input(self):
        self.state = "INPUT_CODE"
        self.input_room_code = ""
        self.ui.add_log("请输入4位房间号 (键盘输入):")

    def create_char_select_screen(self):
        self.ui.clear_buttons()
        self.ui.log_messages = []
        
        is_p1 = self.sub_state.startswith("P1")
        player_name = "玩家1" if is_p1 else "玩家2"
        if not is_p1 and self.game_mode == "PVE":
            player_name += " (AI)"
            
        self.ui.add_log(f"{player_name} 请选择角色")
        
        chars = [
            ("救世主", "savior", GREEN, "血量20 攻3 防2\n被动：血量>10时反伤50%\n血量<10时吸血50%"),
            ("死灵法师", "necro", PURPLE, "血量34 攻4 防2\n被动：首次死亡时投3骰\n总和>12则半血复活"),
            ("剑鱼骑士", "swordfish", BLUE, "血量28 攻3 防3\n被动：若进攻骰子全为偶数\n本次伤害增加50%"),
            ("银鬃铁卫", "silvermane", SILVER, "血量32 攻2 防3\n被动：受到伤害在[3,7]之间时\n反击造成1-6点真实伤害"),
            ("丰饶神鹿", "deer", CYAN, "血量40 攻2 防2\n被动：造成伤害时挂上树种\n2回合后爆发造成10点真实伤害"),
            ("碎星王虫", "star_bug", ORANGE, "血量26 攻4 防2\n被动：若骰子点数成对出现\n(如3,3,5,5) 破甲50%")
        ]
        
        for i, (name, type_id, color, desc) in enumerate(chars):
            x = 150 + (i % 3) * 330
            y = 200 + (i // 3) * 100
            # 联机模式下，只能选自己的角色
            enabled = True
            if self.game_mode == "ONLINE":
                if self.my_player_id == 1 and not is_p1: enabled = False
                if self.my_player_id == 2 and is_p1: enabled = False
            
            btn = Button(x, y, 280, 80, name, color, (min(255, color[0]+30), min(255, color[1]+30), min(255, color[2]+30)), lambda t=type_id: self.select_char(t), self.ui.font_medium, desc)
            if not enabled:
                btn.enabled = False
            self.ui.add_button(btn)

        if not is_p1 and self.game_mode == "PVE":
            self.wait_and_draw(500)
            self.select_char(random.choice([c[1] for c in chars]))

    def select_char(self, char_type):
        if self.game_mode == "ONLINE":
            # 发送选择给对方
            self.network.send_game_action("SELECT_CHAR", {"char": char_type, "player": self.sub_state[:2]})
            
        if self.sub_state == "P1_SELECT_CHAR":
            self.p1_data["char"] = char_type
            self.sub_state = "P1_SELECT_SKILL"
            self.create_skill_select_screen()
        elif self.sub_state == "P2_SELECT_CHAR":
            self.p2_data["char"] = char_type
            self.sub_state = "P2_SELECT_SKILL"
            self.create_skill_select_screen()

    def create_skill_select_screen(self):
        self.ui.clear_buttons()
        is_p1 = self.sub_state.startswith("P1")
        player_name = "玩家1" if is_p1 else "玩家2"
        if not is_p1 and self.game_mode == "PVE":
            player_name += " (AI)"
            
        self.ui.add_log(f"{player_name} 请选择技能骰子")
        
        skills = [
            ("魔术骰子", "magic", PURPLE, "每局一次\n投掷后可将任意一个骰子\n修改为指定点数(1-6)"),
            ("卫星骰子", "satellite", BLUE, "每局一次\n投掷后可召唤卫星\n强制更改当前场地天气"),
            ("治疗骰子", "heal", GREEN, "每局一次\n投掷的点数将直接\n转化为生命值回复"),
            ("星盾骰子", "shield", ORANGE, "每局一次 (防守专用)\n若投出1点，本回合\n免疫致死伤害(保留1血)")
        ]
        
        for i, (name, type_id, color, desc) in enumerate(skills):
            x = 150 + (i % 2) * 500
            y = 250 + (i // 2) * 120
            
            enabled = True
            if self.game_mode == "ONLINE":
                if self.my_player_id == 1 and not is_p1: enabled = False
                if self.my_player_id == 2 and is_p1: enabled = False
                
            btn = Button(x, y, 450, 100, name, color, (min(255, color[0]+30), min(255, color[1]+30), min(255, color[2]+30)), lambda t=type_id: self.select_skill(t), self.ui.font_medium, desc)
            if not enabled:
                btn.enabled = False
            self.ui.add_button(btn)

        if not is_p1 and self.game_mode == "PVE":
            self.wait_and_draw(500)
            self.select_skill(random.choice([s[1] for s in skills]))

    def select_skill(self, skill_type):
        if self.game_mode == "ONLINE":
            self.network.send_game_action("SELECT_SKILL", {"skill": skill_type, "player": self.sub_state[:2]})

        if self.sub_state == "P1_SELECT_SKILL":
            self.p1_data["skill"] = skill_type
            self.sub_state = "P2_SELECT_CHAR"
            self.create_char_select_screen()
        elif self.sub_state == "P2_SELECT_SKILL":
            self.p2_data["skill"] = skill_type
            self.start_coin_toss()

    def start_coin_toss(self):
        self.state = "COIN_TOSS"
        self.ui.clear_buttons()
        self.coin_toss_timer = 60 
        self.ui.add_log("正在抛硬币决定先手...")
        
        # 联机模式下，由房主(P1)决定结果并广播
        if self.game_mode == "ONLINE" and self.my_player_id == 1:
            result = random.choice(["P1", "P2"])
            self.network.send_game_action("COIN_RESULT", {"result": result})
            self.coin_result = result # 房主先存一下，等动画播完

    def update_coin_toss(self):
        if self.coin_toss_timer > 0:
            self.coin_toss_timer -= 1
            if self.coin_toss_timer == 0:
                if self.game_mode != "ONLINE":
                    self.coin_result = random.choice(["P1", "P2"])
                
                # 如果是联机且还没收到结果(非房主)，就卡住等待
                if self.game_mode == "ONLINE" and self.coin_result is None:
                    self.coin_toss_timer = 1 # 保持等待
                    return

                winner = "玩家1" if self.coin_result == "P1" else "玩家2"
                self.ui.add_log(f"硬币结果: {winner} 先手！")
                self.ui.spawn_particles(SCREEN_WIDTH//2, 400, YELLOW, 30)
                self.wait_and_draw(1000)
                self.start_game()

    def start_game(self):
        p1 = Player("玩家1", self.create_character(self.p1_data["char"], self.p1_data["skill"]))
        p2 = Player("玩家2", self.create_character(self.p2_data["char"], self.p2_data["skill"]), is_cpu=(self.game_mode == "PVE"))
        
        field_types = ["normal", "sandstorm", "storm", "mirror", "low_gravity", "blizzard", "fog", "hail", "acid_rain"]
        
        # 联机模式场地由房主决定
        if self.game_mode == "ONLINE":
            if self.my_player_id == 1:
                ft = random.choice(field_types)
                self.network.send_game_action("INIT_FIELD", {"field": ft})
                field_type = ft
            else:
                # 客户端等待场地信息，这里暂时用默认，收到消息会更新
                field_type = "normal" 
        else:
            field_type = random.choice(field_types)
        
        if self.coin_result == "P2":
            self.game_engine = GameEngine(p2, p1, field_type)
        else:
            self.game_engine = GameEngine(p1, p2, field_type)
            
        self.state = "GAME_START"
        self.ui.log_messages = []
        self.ui.clear_visuals() # 确保清理
        self.attacker_dice_visuals = []
        self.defender_dice_visuals = []
        self.ui.add_log(f"对战开始！场地: {self.game_engine.field.name}")
        self.ui.start_fade() # 转场淡入
        
        self.start_turn_phase()

    def check_game_over(self):
        """检查游戏是否结束"""
        p1_alive = self.game_engine.p1.character.is_alive()
        p2_alive = self.game_engine.p2.character.is_alive()
        
        if not p1_alive and not p2_alive:
            self.game_over("平局")
            return True
        elif not p1_alive:
            self.game_over(self.game_engine.p2.name)
            return True
        elif not p2_alive:
            self.game_over(self.game_engine.p1.name)
            return True
        return False

    def start_turn_phase(self):
        self.state = "ATTACK_PHASE"
        # 回合开始时，清空上一回合的所有骰子
        self.attacker_dice_visuals = []
        self.defender_dice_visuals = []
        self.update_ui_visuals()
        
        self.ui.clear_buttons()
        self.turn_skill_active = False 
        
        logs = self.game_engine.start_turn()
        for log in logs:
            self.ui.add_log(log)
            if "树种爆发" in log:
                self.ui.spawn_particles(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, GREEN, 50)
                self.ui.trigger_shake(15, 20)
        
        # 检查回合开始时的死亡 (如沙尘暴)
        if self.check_game_over():
            return

        self.ui.add_log(f"--- 第 {self.game_engine.turn_count} 回合 ---")
        attacker = self.game_engine.current_attacker
        self.ui.add_log(f"进攻方: {attacker.name} ({attacker.character.name})")
        
        # 判断是否是我的回合
        is_my_turn = True
        if self.game_mode == "ONLINE":
            if attacker.name == "玩家1" and self.my_player_id != 1: is_my_turn = False
            if attacker.name == "玩家2" and self.my_player_id != 2: is_my_turn = False
            
        if attacker.is_cpu:
            self.ai_attack_turn()
        elif is_my_turn:
            self.ui.add_button(Button(SCREEN_WIDTH//2 - 150, 600, 140, 50, "投掷骰子", BLUE, (40, 140, 200), self.action_attack_roll, self.ui.font_medium, "投掷普通攻击骰子"))
            
            skill = attacker.character.equipped_skill
            if skill and skill.can_use():
                btn_text = skill.name
                btn_color = PURPLE
                action = None
                desc = ""
                
                if skill.skill_type == "magic_dice":
                    action = self.action_magic_select
                    desc = "指定一个骰子点数"
                elif skill.skill_type == "satellite":
                    action = self.action_satellite_roll 
                    desc = "更改当前场地天气"
                elif skill.skill_type == "heal_dice":
                    action = self.action_heal_roll 
                    desc = "投掷回血骰子"
                
                if action:
                    self.ui.add_button(Button(SCREEN_WIDTH//2 + 10, 600, 140, 50, btn_text, btn_color, (142, 68, 173), action, self.ui.font_medium, desc))
        else:
            self.ui.add_log("等待对方行动...")

    def action_magic_select(self):
        self.ui.clear_buttons()
        self.ui.add_log("请选择魔术骰子点数:")
        for i in range(1, 7):
            btn = Button(SCREEN_WIDTH//2 - 210 + (i-1)*70, 500, 60, 60, str(i), PURPLE, (142, 68, 173), lambda val=i: self.apply_skill_dice("magic_dice", val), self.ui.font_medium)
            self.ui.add_button(btn)

    def action_satellite_roll(self):
        self.apply_skill_dice("satellite")

    def action_heal_roll(self):
        self.apply_skill_dice("heal_dice")

    def apply_skill_dice(self, skill_type, magic_val=None):
        attacker = self.game_engine.current_attacker
        skill = attacker.character.equipped_skill
        skill.use(attacker, None, self.game_engine, magic_value=magic_val)
        self.turn_skill_active = True 
        
        attacker.prepare_dice(attacker.character.atk_dice_count)
        results, _ = attacker.roll_all()
        
        if attacker.ordinary_dice_pool:
            if skill_type == "magic_dice":
                attacker.ordinary_dice_pool[0].current_value = magic_val
                results[0] = magic_val
            
            attacker.ordinary_dice_pool[0].is_locked = True
            
        self.create_dice_visuals(results, is_attacker=True)
        
        if self.attacker_dice_visuals:
            self.attacker_dice_visuals[0].is_locked = True
            self.attacker_dice_visuals[0].is_selected = False
            
        # 联机同步
        if self.game_mode == "ONLINE":
            self.network.send_game_action("SKILL_USE", {
                "skill_type": skill_type, 
                "magic_val": magic_val,
                "results": results
            })

        if skill_type == "magic_dice":
            self.show_reroll_ui()
        elif skill_type == "satellite":
            self.ui.add_log(f"卫星骰子投出: {results[0]} (已锁定)")
            self.show_field_select_ui()
        elif skill_type == "heal_dice":
            self.ui.add_log(f"治疗骰子投出: {results[0]} (已锁定)")
            self.show_reroll_ui()

    def show_field_select_ui(self):
        self.ui.clear_buttons()
        self.ui.add_log("卫星定位中... 请选择新场地:")
        fields = [
            ("晴天", "normal", "无特殊效果"), 
            ("沙尘暴", "sandstorm", "每回合双方扣2血"), 
            ("雷暴雨", "storm", "强制重投最大骰子"), 
            ("海市蜃楼", "mirror", "攻防数值互换"), 
            ("顺风", "low_gravity", "所有骰子点数+1"), 
            ("暴雪", "blizzard", "所有骰子点数-1"), 
            ("大雾", "fog", "防守方+1防御骰子"), 
            ("冰雹", "hail", "无法投出6点(变为5)"), 
            ("酸雨", "acid_rain", "防守点数减半")
        ]
        
        for i, (name, fid, desc) in enumerate(fields):
            x = 100 + (i % 4) * 280
            y = 450 + (i // 4) * 80
            self.ui.add_button(Button(x, y, 260, 60, name, BLUE, (100, 100, 255), lambda f=fid: self.apply_satellite_field(f), self.ui.font_medium, desc))

    def apply_satellite_field(self, field_id):
        self.game_engine.change_field(field_id)
        self.ui.add_log(f"场地变更为: {self.game_engine.field.name}")
        if self.game_mode == "ONLINE":
            self.network.send_game_action("CHANGE_FIELD", {"field": field_id})
        self.show_reroll_ui()

    def action_attack_roll(self):
        attacker = self.game_engine.current_attacker
        attacker.prepare_dice(attacker.character.atk_dice_count)
        results, _ = attacker.roll_all()
        self.create_dice_visuals(results, is_attacker=True)
        
        if self.game_mode == "ONLINE":
            self.network.send_game_action("ATTACK_ROLL", {"results": results})
            
        self.show_reroll_ui()
        self.ui.add_log(f"{attacker.name} 投掷了进攻骰子")

    def show_reroll_ui(self):
        self.ui.clear_buttons()
        # 只有当前操作者能看到按钮
        is_my_turn = True
        if self.game_mode == "ONLINE":
            attacker = self.game_engine.current_attacker
            if attacker.name == "玩家1" and self.my_player_id != 1: is_my_turn = False
            if attacker.name == "玩家2" and self.my_player_id != 2: is_my_turn = False
            
        if is_my_turn:
            self.ui.add_button(Button(SCREEN_WIDTH//2 - 150, 600, 140, 50, "重投选中", YELLOW, (220, 180, 10), self.action_reroll, self.ui.font_medium, "重投选中的黄色骰子"))
            self.ui.add_button(Button(SCREEN_WIDTH//2 + 10, 600, 140, 50, "结束进攻", RED, (200, 50, 50), self.start_defense_phase, self.ui.font_medium, "结束进攻回合"))
        else:
            self.ui.add_log("等待对方重投...")

    def action_reroll(self):
        attacker = self.game_engine.current_attacker
        reroll_indices = []
        ord_count = len(attacker.ordinary_dice_pool)
        
        # 注意：这里只检查 attacker_dice_visuals
        for i, dv in enumerate(self.attacker_dice_visuals):
            if dv.is_selected and not dv.is_locked and not dv.is_skill:
                if i < ord_count:
                    reroll_indices.append(i)
        
        if not reroll_indices:
            self.ui.add_log("未选择骰子")
            return

        keep_indices = [i for i in range(ord_count) if i not in reroll_indices]
        attacker.lock_ordinary_dice(keep_indices)
        
        new_results, _ = attacker.roll_all()
        
        for i, val in enumerate(new_results):
            if i < len(self.attacker_dice_visuals) and not self.attacker_dice_visuals[i].is_skill:
                self.attacker_dice_visuals[i].target_value = val
                if i in reroll_indices:
                    self.attacker_dice_visuals[i].start_roll()
                    self.attacker_dice_visuals[i].is_selected = False
        
        if self.game_mode == "ONLINE":
            self.network.send_game_action("REROLL", {"results": new_results, "indices": reroll_indices})
        
        self.ui.add_log("重投完成")
        self.ui.clear_buttons()
        self.ui.add_button(Button(SCREEN_WIDTH//2 - 70, 600, 140, 50, "结束进攻", RED, (200, 50, 50), self.start_defense_phase, self.ui.font_medium, "结束进攻回合"))

    def start_defense_phase(self):
        if self.game_mode == "ONLINE" and self.state == "ATTACK_PHASE":
             # 如果我是进攻方，我点了结束进攻，通知对方
            attacker = self.game_engine.current_attacker
            if (attacker.name == "玩家1" and self.my_player_id == 1) or (attacker.name == "玩家2" and self.my_player_id == 2):
                self.network.send_game_action("PHASE_CHANGE", {"phase": "DEFENSE"})

        self.state = "DEFENSE_PHASE"
        # 注意：这里不再清空 dice_visuals，保留进攻方的骰子
        defender = self.game_engine.current_defender
        self.ui.add_log(f"防守方: {defender.name} 准备防御")
        
        is_my_turn = True
        if self.game_mode == "ONLINE":
            if defender.name == "玩家1" and self.my_player_id != 1: is_my_turn = False
            if defender.name == "玩家2" and self.my_player_id != 2: is_my_turn = False

        if defender.is_cpu:
            self.ai_defense_turn()
        elif is_my_turn:
            self.ui.clear_buttons()
            self.ui.add_button(Button(SCREEN_WIDTH//2 - 70, 600, 140, 50, "防守投掷", BLUE, (40, 140, 200), self.action_defense_roll, self.ui.font_medium, "投掷防御骰子"))
            
            skill = defender.character.equipped_skill
            if skill and skill.skill_type == "shield_dice" and skill.can_use():
                self.ui.add_button(Button(SCREEN_WIDTH//2 + 90, 600, 140, 50, "星盾骰子", ORANGE, (230, 150, 50), self.action_shield_roll, self.ui.font_medium, "投出1点免疫死亡"))
        else:
            self.ui.clear_buttons()
            self.ui.add_log("等待对方防御...")

    def action_shield_roll(self):
        defender = self.game_engine.current_defender
        skill = defender.character.equipped_skill
        skill.use(defender, None, self.game_engine)
        self.turn_skill_active = True
        
        defender.prepare_dice(defender.character.def_dice_count)
        results, _ = defender.roll_all()
        
        if defender.ordinary_dice_pool:
            defender.ordinary_dice_pool[0].is_locked = True
            
        self.create_dice_visuals(results, is_attacker=False)
        if self.defender_dice_visuals:
            self.defender_dice_visuals[0].is_locked = True
            
        if self.game_mode == "ONLINE":
            self.network.send_game_action("SHIELD_ROLL", {"results": results})

        self.ui.add_log(f"星盾骰子投出: {results[0]} (已锁定)")
        self.ui.clear_buttons()
        self.ui.add_button(Button(SCREEN_WIDTH//2 - 70, 600, 140, 50, "结算伤害", RED, (200, 50, 50), self.action_resolve, self.ui.font_medium, "计算最终伤害"))

    def action_defense_roll(self):
        defender = self.game_engine.current_defender
        defender.prepare_dice(defender.character.def_dice_count)
        results, _ = defender.roll_all()
        self.create_dice_visuals(results, is_attacker=False)
        
        if self.game_mode == "ONLINE":
            self.network.send_game_action("DEFENSE_ROLL", {"results": results})

        self.ui.add_log(f"{defender.name} 投掷了防御骰子")
        self.ui.clear_buttons()
        self.ui.add_button(Button(SCREEN_WIDTH//2 - 70, 600, 140, 50, "结算伤害", RED, (200, 50, 50), self.action_resolve, self.ui.font_medium, "计算最终伤害"))

    def action_resolve(self):
        if self.game_mode == "ONLINE":
             # 只有防守方能点结算，点了之后通知对方
            defender = self.game_engine.current_defender
            if (defender.name == "玩家1" and self.my_player_id == 1) or (defender.name == "玩家2" and self.my_player_id == 2):
                self.network.send_game_action("RESOLVE", {})

        attacker = self.game_engine.current_attacker
        defender = self.game_engine.current_defender
        
        atk_total = attacker.calculate_total()
        def_total = defender.calculate_total()
        
        atk_special = None
        if self.turn_skill_active and attacker.character.equipped_skill.skill_type == "heal_dice" and attacker.ordinary_dice_pool and attacker.ordinary_dice_pool[0].is_locked:
            atk_special = attacker.ordinary_dice_pool[0].current_value
            
        def_special = None
        if defender.character.equipped_skill.skill_type == "shield_dice" and defender.ordinary_dice_pool and defender.ordinary_dice_pool[0].is_locked:
            def_special = defender.ordinary_dice_pool[0].current_value
        
        dmg, logs = self.game_engine.resolve_combat(atk_total, def_total, atk_special, def_special)
        
        # 震动效果
        if dmg > 5:
            self.ui.trigger_shake(10, 15)
        if dmg > 15:
            self.ui.trigger_shake(20, 30)
            
        for log in logs:
            self.ui.add_log(log)
            if "反击" in log or "爆发" in log or "复活" in log or "回复" in log or "破甲" in log:
                self.ui.spawn_particles(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, RED if "伤害" in log else (PURPLE if "破甲" in log else GREEN), 30)
            
        # 检查游戏是否结束 (双方都有可能死亡)
        if self.check_game_over():
            return

        self.game_engine.switch_turn()
        self.ui.clear_buttons()
        self.ui.add_button(Button(SCREEN_WIDTH//2 - 70, 600, 140, 50, "下一回合", GREEN, (46, 200, 113), self.start_turn_phase, self.ui.font_medium))

    def ai_attack_turn(self):
        attacker = self.game_engine.current_attacker
        self.ui.add_log("AI 正在思考...")
        self.wait_and_draw(800)
        
        skill = attacker.character.equipped_skill
        used_skill = False
        
        if skill and skill.can_use():
            if skill.skill_type == "magic_dice":
                self.apply_skill_dice("magic_dice", 6)
                used_skill = True
            elif skill.skill_type == "heal_dice" and attacker.character.current_hp < 15:
                self.apply_skill_dice("heal_dice")
                used_skill = True
            elif skill.skill_type == "satellite":
                self.apply_skill_dice("satellite")
                self.wait_and_draw(500)
                self.apply_satellite_field(random.choice(["storm", "sandstorm", "blizzard", "hail", "acid_rain"]))
                used_skill = True
        
        if not used_skill:
            self.action_attack_roll()
            
        self.wait_and_draw(1000)
        self.action_reroll_ai()
        self.wait_and_draw(1000)
        self.start_defense_phase()

    def action_reroll_ai(self):
        attacker = self.game_engine.current_attacker
        reroll_indices = []
        for i, d in enumerate(attacker.ordinary_dice_pool):
            if not d.is_locked and d.current_value < 4:
                reroll_indices.append(i)
        
        if reroll_indices:
            self.ui.add_log(f"AI 重投 {len(reroll_indices)} 个骰子")
            keep = [i for i in range(len(attacker.ordinary_dice_pool)) if i not in reroll_indices]
            attacker.lock_ordinary_dice(keep)
            attacker.roll_all()
            self.create_dice_visuals([d.current_value for d in attacker.ordinary_dice_pool], is_attacker=True)

    def ai_defense_turn(self):
        defender = self.game_engine.current_defender
        self.ui.add_log("AI 正在防御...")
        self.wait_and_draw(800)
        
        skill = defender.character.equipped_skill
        if skill and skill.skill_type == "shield_dice" and skill.can_use() and defender.character.current_hp < 10:
            self.action_shield_roll()
        else:
            self.action_defense_roll()
            
        self.wait_and_draw(1000)
        self.action_resolve()

    def create_dice_visuals(self, results, is_attacker):
        # 不再清空 self.ui.dice_visuals，而是更新对应的列表
        new_visuals = []
        total_dice = len(results)
        
        # 确定当前操作的是哪个玩家
        if is_attacker:
            player = self.game_engine.current_attacker
        else:
            player = self.game_engine.current_defender
            
        if player.name == "玩家1":
            start_x = 50
            start_y = 220
        else:
            start_x = SCREEN_WIDTH - 350
            start_y = 220
            
        # 骰子间距
        spacing = 90
        
        for i, val in enumerate(results):
            dv = DiceVisual(start_x + i * spacing, start_y, font=self.ui.font_large, target_val=val)
            dv.start_roll()
            new_visuals.append(dv)
            
        if is_attacker:
            self.attacker_dice_visuals = new_visuals
        else:
            self.defender_dice_visuals = new_visuals
            
        self.update_ui_visuals()

    def update_ui_visuals(self):
        """将攻守双方的骰子合并显示"""
        self.ui.dice_visuals = self.attacker_dice_visuals + self.defender_dice_visuals

    def game_over(self, winner_name):
        self.state = "GAME_OVER"
        self.ui.add_log(f"游戏结束！{winner_name} 获胜！")
        self.ui.clear_buttons()
        self.ui.add_button(Button(SCREEN_WIDTH//2 - 150, 500, 140, 60, "再来一局", GREEN, (46, 200, 113), self.restart_game, self.ui.font_medium))
        self.ui.add_button(Button(SCREEN_WIDTH//2 + 10, 500, 140, 60, "重新选人", ORANGE, (230, 100, 30), self.reset_to_select, self.ui.font_medium))

    def restart_game(self):
        self.ui.clear_visuals() # 清理
        self.attacker_dice_visuals = []
        self.defender_dice_visuals = []
        self.start_coin_toss()

    def reset_to_select(self):
        self.ui.clear_visuals() # 清理
        self.attacker_dice_visuals = []
        self.defender_dice_visuals = []
        self.state = "MODE_SELECT"
        self.create_mode_select_screen()

    def handle_network_messages(self):
        if not self.network or not self.is_online:
            return

        while True:
            msg = self.network.get_msg()
            if not msg:
                break
            
            action = msg.get("action")
            
            if action == "ROOM_CREATED":
                self.room_code = msg.get("code")
                self.my_player_id = 1
                self.state = "WAITING_PLAYER"
                self.ui.add_log(f"房间创建成功！房间号: {self.room_code}")
                self.ui.add_log("等待玩家加入...")
                self.ui.clear_buttons()
                
            elif action == "PLAYER_JOINED":
                self.ui.add_log("玩家已加入！即将开始...")
                self.wait_and_draw(1000)
                self.state = "SELECT_CHAR"
                self.sub_state = "P1_SELECT_CHAR"
                self.create_char_select_screen()
                
            elif action == "JOIN_SUCCESS":
                self.my_player_id = 2
                self.room_code = self.input_room_code
                self.ui.add_log("加入成功！")
                self.wait_and_draw(1000)
                self.state = "SELECT_CHAR"
                self.sub_state = "P1_SELECT_CHAR"
                self.create_char_select_screen()
                
            elif action == "ERROR":
                self.ui.add_log(f"错误: {msg.get('msg')}")
                self.wait_and_draw(2000)
                self.state = "ROOM_MENU"
                self.create_room_menu()
                
            elif action == "GAME_DATA":
                self.handle_game_data(msg)

    def handle_game_data(self, data):
        type = data.get("type")
        payload = data.get("payload")
        
        if type == "SELECT_CHAR":
            player = payload.get("player") # P1 or P2
            char_type = payload.get("char")
            if player == "P1":
                self.p1_data["char"] = char_type
                self.sub_state = "P1_SELECT_SKILL"
                self.create_skill_select_screen()
            else:
                self.p2_data["char"] = char_type
                self.sub_state = "P2_SELECT_SKILL"
                self.create_skill_select_screen()
                
        elif type == "SELECT_SKILL":
            player = payload.get("player")
            skill_type = payload.get("skill")
            if player == "P1":
                self.p1_data["skill"] = skill_type
                self.sub_state = "P2_SELECT_CHAR"
                self.create_char_select_screen()
            else:
                self.p2_data["skill"] = skill_type
                self.start_coin_toss()
                
        elif type == "COIN_RESULT":
            self.coin_result = payload.get("result")
            
        elif type == "INIT_FIELD":
            field_name = payload.get("field")
            self.game_engine.change_field(field_name)
            
        elif type == "ATTACK_ROLL":
            results = payload.get("results")
            attacker = self.game_engine.current_attacker
            attacker.prepare_dice(attacker.character.atk_dice_count)
            # 强制设置结果
            attacker.ordinary_dice_pool = []
            for val in results:
                d = Dice()
                d.current_value = val
                attacker.ordinary_dice_pool.append(d)
            
            self.create_dice_visuals(results, is_attacker=True)
            self.show_reroll_ui()
            self.ui.add_log(f"{attacker.name} 投掷了进攻骰子")
            
        elif type == "REROLL":
            results = payload.get("results")
            indices = payload.get("indices")
            attacker = self.game_engine.current_attacker
            
            # 更新骰子池
            for i, val in enumerate(results):
                if i < len(attacker.ordinary_dice_pool):
                    attacker.ordinary_dice_pool[i].current_value = val
            
            # 播放动画
            for i, val in enumerate(results):
                if i < len(self.attacker_dice_visuals):
                    self.attacker_dice_visuals[i].target_value = val
                    if i in indices:
                        self.attacker_dice_visuals[i].start_roll()
            
            self.ui.add_log("对方重投完成")
            
        elif type == "PHASE_CHANGE":
            if payload.get("phase") == "DEFENSE":
                self.start_defense_phase()
                
        elif type == "DEFENSE_ROLL":
            results = payload.get("results")
            defender = self.game_engine.current_defender
            defender.prepare_dice(defender.character.def_dice_count)
            # 强制设置结果
            defender.ordinary_dice_pool = []
            for val in results:
                d = Dice()
                d.current_value = val
                defender.ordinary_dice_pool.append(d)
                
            self.create_dice_visuals(results, is_attacker=False)
            self.ui.add_log(f"{defender.name} 投掷了防御骰子")
            # 只有防守方自己能看到结算按钮，这里不需要显示按钮，等待RESOLVE消息
            
        elif type == "SHIELD_ROLL":
            results = payload.get("results")
            defender = self.game_engine.current_defender
            defender.prepare_dice(defender.character.def_dice_count)
            defender.ordinary_dice_pool = []
            for val in results:
                d = Dice()
                d.current_value = val
                defender.ordinary_dice_pool.append(d)
            
            if defender.ordinary_dice_pool:
                defender.ordinary_dice_pool[0].is_locked = True
                
            self.create_dice_visuals(results, is_attacker=False)
            if self.defender_dice_visuals:
                self.defender_dice_visuals[0].is_locked = True
            self.ui.add_log(f"星盾骰子投出: {results[0]} (已锁定)")
            
        elif type == "SKILL_USE":
            skill_type = payload.get("skill_type")
            magic_val = payload.get("magic_val")
            results = payload.get("results")
            
            self.apply_skill_dice(skill_type, magic_val)
            
        elif type == "CHANGE_FIELD":
            self.apply_satellite_field(payload.get("field"))
            
        elif type == "RESOLVE":
            self.action_resolve()

    def draw(self):
        # 1. 绘制基础层 (背景、粒子、骰子、按钮)
        self.ui.update()
        self.ui.draw_base()
        
        # 2. 绘制特定状态的额外信息 (角色面板等)
        if self.state == "MODE_SELECT":
            self.ui.draw_text_centered("划时代双人对战 - 模式选择", 100, self.ui.font_large)

        elif self.state == "INPUT_IP":
            self.ui.draw_text_centered("请输入服务器IP:", 200, self.ui.font_large)
            self.ui.draw_text_centered(self.input_server_ip + "_", 300, self.ui.font_large, YELLOW)
            self.ui.draw_text_centered("输入IP地址，按回车连接，ESC返回", 400, self.ui.font_small, GRAY)
            self.ui.draw_text_centered("本机测试请输入: 127.0.0.1", 430, self.ui.font_small, DARK_GRAY)

        elif self.state == "CONNECT_SERVER":
            self.ui.draw_text_centered("正在连接服务器...", 300, self.ui.font_large)

        elif self.state == "ROOM_MENU":
            self.ui.draw_text_centered("联机大厅", 100, self.ui.font_large)

        elif self.state == "WAITING_ROOM":
            self.ui.draw_text_centered(f"房间号: {self.room_code}", 200, self.ui.font_large, YELLOW)
            self.ui.draw_text_centered("等待玩家加入...", 300, self.ui.font_medium)

        elif self.state == "INPUT_CODE":
            self.ui.draw_text_centered("请输入房间号:", 200, self.ui.font_large)
            self.ui.draw_text_centered(self.input_room_code + "_", 300, self.ui.font_large, YELLOW)
            self.ui.draw_text_centered("输入4位数字/字母，按回车确认，ESC返回", 400, self.ui.font_small, GRAY)

        elif self.state == "SELECT_CHAR":
            self.ui.draw_text_centered("角色与技能选择", 100, self.ui.font_large)

        elif self.state == "COIN_TOSS":
            self.update_coin_toss()
            self.ui.draw_text_centered("抛硬币中...", 300, self.ui.font_large)
            coin_color = YELLOW if (self.coin_toss_timer // 5) % 2 == 0 else WHITE
            pygame.draw.circle(self.screen, coin_color, (SCREEN_WIDTH//2, 400), 50)

        else:
            # 游戏内界面
            self.draw_character_info(self.game_engine.p1, 50, 50)
            self.draw_character_info(self.game_engine.p2, SCREEN_WIDTH - 350, 50)
            
            f_text = self.ui.font_medium.render(f"场地: {self.game_engine.field.name}", True, YELLOW)
            f_rect = f_text.get_rect(topleft=(SCREEN_WIDTH//2 - f_text.get_width()//2, 20))
            self.screen.blit(f_text, f_rect)
            
            # 场地提示
            mouse_pos = pygame.mouse.get_pos()
            if f_rect.collidepoint(mouse_pos):
                self.ui.tooltip = self.game_engine.field.description
            
            phase_text = ""
            color = WHITE
            if self.state == "ATTACK_PHASE":
                phase_text = f"当前阶段: {self.game_engine.current_attacker.name} 进攻"
                color = RED
            elif self.state == "DEFENSE_PHASE":
                phase_text = f"当前阶段: {self.game_engine.current_defender.name} 防守"
                color = BLUE
            elif self.state == "GAME_OVER":
                phase_text = "GAME OVER"
                color = RED
            
            if phase_text:
                p_surf = self.ui.font_medium.render(phase_text, True, color)
                self.screen.blit(p_surf, (SCREEN_WIDTH//2 - p_surf.get_width()//2, 60))

        # 3. 绘制顶层 (Tooltip, Fade)
        self.ui.draw_overlay()
        
        pygame.display.flip()

    def draw_character_info(self, player, x, y):
        border_color = DARK_GRAY
        if self.state == "ATTACK_PHASE" and player == self.game_engine.current_attacker:
            border_color = RED
        elif self.state == "DEFENSE_PHASE" and player == self.game_engine.current_defender:
            border_color = BLUE
            
        rect = pygame.Rect(x, y, 300, 160)
        # 使用半透明背景
        s = pygame.Surface((300, 160), pygame.SRCALPHA)
        pygame.draw.rect(s, PANEL_BG, s.get_rect(), border_radius=10)
        self.screen.blit(s, (x, y))
        
        pygame.draw.rect(self.screen, border_color, rect, 3, border_radius=10)
        
        mouse_pos = pygame.mouse.get_pos()
        if rect.collidepoint(mouse_pos):
            self.ui.tooltip = f"{player.character.name}\n{player.character.passive_desc}"
        
        name_str = f"{player.name} ({player.character.name})"
        if player.is_cpu:
            name_str += " [AI]"
        name = self.ui.font_medium.render(name_str, True, WHITE)
        self.screen.blit(name, (x + 10, y + 10))
        
        stats = self.ui.font_small.render(f"攻: {player.character.atk_dice_count}  防: {player.character.def_dice_count}", True, YELLOW)
        self.screen.blit(stats, (x + 10, y + 45))
        
        hp_ratio = player.character.current_hp / player.character.max_hp
        pygame.draw.rect(self.screen, (100, 0, 0), (x + 10, y + 70, 280, 25), border_radius=5)
        if hp_ratio > 0:
            pygame.draw.rect(self.screen, GREEN, (x + 10, y + 70, 280 * hp_ratio, 25), border_radius=5)
        
        hp_text = self.ui.font_small.render(f"{player.character.current_hp}/{player.character.max_hp}", True, WHITE)
        self.screen.blit(hp_text, (x + 130, y + 72))
        
        skill = player.character.equipped_skill
        if skill:
            s_text = self.ui.font_small.render(f"{skill.name}: {skill.current_uses}/{skill.max_uses}", True, PURPLE)
            self.screen.blit(s_text, (x + 10, y + 105))
            
        p_text = self.ui.font_small.render(f"被动: {player.character.passive_desc[:12]}...", True, GRAY)
        self.screen.blit(p_text, (x + 10, y + 130))

    def run(self):
        while True:
            # 处理网络消息
            self.handle_network_messages()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state == "INPUT_CODE":
                            self.state = "ROOM_MENU"
                            self.create_room_menu()
                        elif self.state == "INPUT_IP":
                            self.state = "MODE_SELECT"
                            self.create_mode_select_screen()
                        else:
                            pygame.quit()
                            sys.exit()
                    
                    if self.state == "INPUT_CODE":
                        if event.key == pygame.K_RETURN:
                            if len(self.input_room_code) == 4:
                                self.network.join_room(self.input_room_code)
                                self.ui.add_log("正在加入...")
                        elif event.key == pygame.K_BACKSPACE:
                            self.input_room_code = self.input_room_code[:-1]
                        else:
                            if len(self.input_room_code) < 4 and event.unicode.isalnum():
                                self.input_room_code += event.unicode.upper()
                                
                    elif self.state == "INPUT_IP":
                        if event.key == pygame.K_RETURN:
                            self.connect_to_server()
                        elif event.key == pygame.K_BACKSPACE:
                            self.input_server_ip = self.input_server_ip[:-1]
                        else:
                            # 允许输入数字和点
                            if event.unicode in "0123456789.":
                                self.input_server_ip += event.unicode
                
                for btn in self.ui.buttons:
                    btn.handle_event(event)
                    
                for dv in self.ui.dice_visuals:
                    dv.handle_event(event)

            self.draw()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = GameGUI()
    game.run()
