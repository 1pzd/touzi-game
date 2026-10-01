import random

class Dice:
    """
    普通骰子：1-6
    """
    def __init__(self):
        self.faces = [1, 2, 3, 4, 5, 6]
        self.current_value = None
        self.is_locked = False

    def roll(self):
        if not self.is_locked:
            self.current_value = random.choice(self.faces)
        return self.current_value

    def __str__(self):
        return str(self.current_value)

class SkillDice:
    """
    技能骰子
    面值：
    -: 空面 (无事发生)
    S: 技能触发面 (Trigger)
    """
    def __init__(self, success_rate=2):
        # 默认2/6的概率触发，即2个S，4个-
        self.faces = ['-'] * (6 - success_rate) + ['S'] * success_rate
        self.current_value = None
        self.is_locked = False

    def roll(self):
        if not self.is_locked:
            self.current_value = random.choice(self.faces)
        return self.current_value

    def __str__(self):
        return str(self.current_value)

class Skill:
    """
    技能定义
    """
    def __init__(self, name, description, effect_func):
        self.name = name
        self.description = description
        self.effect_func = effect_func

    def trigger(self, user, target, game):
        return self.effect_func(user, target, game)

class Character:
    def __init__(self, name, hp, atk_dice_count, def_dice_count, passive_desc):
        self.name = name
        self.max_hp = hp
        self.current_hp = hp
        self.atk_dice_count = atk_dice_count
        self.def_dice_count = def_dice_count
        self.passive_desc = passive_desc
        self.equipped_skill = None # 携带的特殊技 (Skill对象)

    def take_damage(self, amount):
        self.current_hp -= amount
        if self.current_hp < 0:
            self.current_hp = 0
        return self.current_hp

    def heal(self, amount):
        self.current_hp += amount
        if self.current_hp > self.max_hp:
            self.current_hp = self.max_hp
        return self.current_hp

    def is_alive(self):
        return self.current_hp > 0

class Player:
    def __init__(self, name, character):
        self.name = name
        self.character = character
        self.ordinary_dice_pool = []
        self.skill_dice = None

    def prepare_dice(self, count):
        """准备普通骰子和技能骰子"""
        self.ordinary_dice_pool = [Dice() for _ in range(count)]
        if self.character.equipped_skill:
            self.skill_dice = SkillDice() # 假设技能骰子是标准的2/6概率
        else:
            self.skill_dice = None

    def roll_all(self):
        results = [d.roll() for d in self.ordinary_dice_pool]
        skill_result = None
        if self.skill_dice:
            skill_result = self.skill_dice.roll()
        return results, skill_result

    def lock_ordinary_dice(self, indices):
        for i in indices:
            if 0 <= i < len(self.ordinary_dice_pool):
                self.ordinary_dice_pool[i].is_locked = True
    
    def lock_skill_dice(self, lock=True):
        if self.skill_dice:
            self.skill_dice.is_locked = lock

    def calculate_total(self):
        total = sum([d.current_value for d in self.ordinary_dice_pool if isinstance(d.current_value, int)])
        return total

    def is_skill_triggered(self):
        return self.skill_dice and self.skill_dice.current_value == 'S'

class Game:
    def __init__(self, player1, player2):
        self.p1 = player1
        self.p2 = player2
        self.turn_count = 1
        self.current_attacker = self.p1
        self.current_defender = self.p2

    def switch_turn(self):
        self.current_attacker, self.current_defender = self.current_defender, self.current_attacker
        self.turn_count += 1

    def resolve_combat(self, atk_total, def_total, atk_triggered, def_triggered):
        log = []
        
        # 1. 技能结算 (先于伤害还是后于伤害？通常先结算buff/debuff，这里简单处理)
        # 进攻方技能
        atk_skill_bonus = 0
        if atk_triggered and self.current_attacker.character.equipped_skill:
            skill = self.current_attacker.character.equipped_skill
            # 执行技能逻辑，这里简化为直接调用，假设技能返回 (伤害加成, 治疗量, 描述)
            bonus_dmg, heal, desc = skill.trigger(self.current_attacker, self.current_defender, self)
            atk_skill_bonus += bonus_dmg
            if heal > 0:
                self.current_attacker.character.heal(heal)
            log.append(f"【进攻技】{self.current_attacker.name} 触发 '{skill.name}': {desc}")

        # 防守方技能
        def_skill_bonus = 0
        if def_triggered and self.current_defender.character.equipped_skill:
            skill = self.current_defender.character.equipped_skill
            bonus_dmg, heal, desc = skill.trigger(self.current_defender, self.current_attacker, self)
            # 防守方技能通常增加防御或回血，或者反伤
            # 这里假设 bonus_dmg 是反伤或者减伤？
            # 为了通用性，假设 bonus_dmg 是直接造成的额外伤害(反击)，heal是回血
            if bonus_dmg > 0:
                self.current_attacker.character.take_damage(bonus_dmg)
                log.append(f"【防守技】{self.current_defender.name} 触发 '{skill.name}' 反击: 造成 {bonus_dmg} 伤害")
            if heal > 0:
                self.current_defender.character.heal(heal)
                log.append(f"【防守技】{self.current_defender.name} 触发 '{skill.name}': 回复 {heal} 生命")

        # 2. 基础伤害结算
        raw_damage = atk_total - def_total
        final_damage = max(0, raw_damage) + atk_skill_bonus
        
        self.current_defender.character.take_damage(final_damage)
        
        log.append(f"结算: 攻击点数 {atk_total} - 防御点数 {def_total} = {max(0, raw_damage)}")
        if atk_skill_bonus > 0:
            log.append(f"技能额外伤害: +{atk_skill_bonus}")
        log.append(f"最终受到伤害: {final_damage}")

        return final_damage, log
