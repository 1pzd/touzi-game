from dice import Dice, SkillDice

class Player:
    def __init__(self, name, character, is_cpu=False):
        self.name = name
        self.character = character
        self.ordinary_dice_pool = []
        self.skill_dice = None
        self.is_cpu = is_cpu # 是否为 AI

    def prepare_dice(self, count):
        """准备普通骰子和技能骰子"""
        self.ordinary_dice_pool = [Dice() for _ in range(count)]
        
        # 检查技能次数
        if self.character.equipped_skill and self.character.equipped_skill.can_use():
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

    def get_max_dice_index(self):
        """获取点数最大的普通骰子索引"""
        if not self.ordinary_dice_pool:
            return -1
        max_val = -1
        max_idx = -1
        for i, d in enumerate(self.ordinary_dice_pool):
            if isinstance(d.current_value, int) and d.current_value > max_val:
                max_val = d.current_value
                max_idx = i
        return max_idx

    def force_reroll_dice(self, index):
        """强制重投指定索引的骰子"""
        if 0 <= index < len(self.ordinary_dice_pool):
            self.ordinary_dice_pool[index].is_locked = False # 确保未锁定
            return self.ordinary_dice_pool[index].roll()
        return None
