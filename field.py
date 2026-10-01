import random

class Field:
    def __init__(self, name, description):
        self.name = name
        self.description = description

    def on_turn_start(self, game):
        pass

    def on_before_damage(self, game, atk_total, def_total):
        return atk_total, def_total

class NormalField(Field):
    def __init__(self):
        super().__init__("晴天", "无特殊效果")

class SandstormField(Field):
    def __init__(self):
        super().__init__("沙尘暴", "每回合双方扣除2点生命值")

    def on_turn_start(self, game):
        dmg = 2
        game.p1.character.take_damage(dmg)
        game.p2.character.take_damage(dmg)
        return f"【沙尘暴】肆虐！双方受到 {dmg} 点伤害！"

class StormField(Field):
    def __init__(self):
        super().__init__("雷暴雨", "结算伤害时，双方点数最大的骰子将被强制重投")

class MirageField(Field):
    def __init__(self):
        super().__init__("海市蜃楼", "攻守双方互换骰子点数总和")

    def on_before_damage(self, game, atk_total, def_total):
        return def_total, atk_total

class TailwindField(Field):
    def __init__(self):
        super().__init__("顺风", "所有骰子点数 +1 (最大为6)")

    def on_before_damage(self, game, atk_total, def_total):
        new_atk = 0
        for d in game.current_attacker.ordinary_dice_pool:
            if isinstance(d.current_value, int):
                new_atk += min(6, d.current_value + 1)
        
        new_def = 0
        for d in game.current_defender.ordinary_dice_pool:
            if isinstance(d.current_value, int):
                new_def += min(6, d.current_value + 1)
        return new_atk, new_def

class BlizzardField(Field):
    def __init__(self):
        super().__init__("暴雪", "严寒！所有骰子点数 -1 (最小为1)")

    def on_before_damage(self, game, atk_total, def_total):
        new_atk = 0
        for d in game.current_attacker.ordinary_dice_pool:
            if isinstance(d.current_value, int):
                new_atk += max(1, d.current_value - 1)
        
        new_def = 0
        for d in game.current_defender.ordinary_dice_pool:
            if isinstance(d.current_value, int):
                new_def += max(1, d.current_value - 1)
        return new_atk, new_def

class FogField(Field):
    def __init__(self):
        super().__init__("大雾", "视野受阻！防守方额外获得 1 个防御骰子")

class HailField(Field):
    def __init__(self):
        super().__init__("冰雹", "无法投出最大值！所有6点强制变为5")

    def on_before_damage(self, game, atk_total, def_total):
        # 修正数值：遍历骰子，如果是6则按5计算
        # 注意：这里只修正计算值，不修改骰子显示值（为了视觉效果保留6但算5？或者直接改值？）
        # 为了直观，通常应该改值。但 on_before_damage 是结算前修正。
        # 如果要改显示值，应该在 roll 之后处理。
        # 这里我们只做数值修正。
        new_atk = 0
        for d in game.current_attacker.ordinary_dice_pool:
            if isinstance(d.current_value, int):
                val = d.current_value
                if val == 6: val = 5
                new_atk += val
        
        new_def = 0
        for d in game.current_defender.ordinary_dice_pool:
            if isinstance(d.current_value, int):
                val = d.current_value
                if val == 6: val = 5
                new_def += val
        return new_atk, new_def

class AcidRainField(Field):
    def __init__(self):
        super().__init__("酸雨", "腐蚀护甲！防守方骰子点数之和减半")

    def on_before_damage(self, game, atk_total, def_total):
        return atk_total, int(def_total * 0.5)
