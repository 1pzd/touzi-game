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
        # 默认2/6的概率触发
        self.faces = ['-'] * (6 - success_rate) + ['S'] * success_rate
        self.current_value = None
        self.is_locked = False

    def roll(self):
        if not self.is_locked:
            self.current_value = random.choice(self.faces)
        return self.current_value

    def __str__(self):
        return str(self.current_value)
