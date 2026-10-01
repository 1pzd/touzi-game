class Skill:
    """
    技能定义
    """
    def __init__(self, name, description, max_uses, effect_func=None, skill_type="active"):
        self.name = name
        self.description = description
        self.max_uses = max_uses
        self.current_uses = 0
        self.effect_func = effect_func
        self.skill_type = skill_type 
        # skill_type: "active" (普通主动), "magic_dice" (魔术), "satellite" (卫星), "heal_dice" (治疗), "shield_dice" (星盾)

    def can_use(self):
        return self.current_uses < self.max_uses

    def use(self, user, target, game, **kwargs):
        if self.can_use():
            self.current_uses += 1
            if self.skill_type == "magic_dice":
                return 0, 0, f"使用了魔术骰子，点数变为 {kwargs.get('magic_value')}"
            elif self.skill_type == "satellite":
                return 0, 0, "使用了卫星骰子，准备更改场地"
            elif self.skill_type == "heal_dice":
                return 0, 0, "使用了治疗骰子"
            elif self.skill_type == "shield_dice":
                return 0, 0, "使用了星盾骰子"
            
            if self.effect_func:
                return self.effect_func(user, target, game)
        return 0, 0, "技能次数已耗尽"

    def reset(self):
        self.current_uses = 0
