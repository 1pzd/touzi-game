class Character:
    def __init__(self, name, hp, atk_dice_count, def_dice_count, passive_type, passive_desc):
        self.name = name
        self.max_hp = hp
        self.current_hp = hp
        self.atk_dice_count = atk_dice_count
        self.def_dice_count = def_dice_count
        self.passive_type = passive_type # "savior", "necro", "swordfish", "silvermane", "deer", "star_bug"
        self.passive_desc = passive_desc
        
        # 特殊状态标记
        self.has_revived = False # 死灵法师是否已复活
        self.seed_timer = 0 # 丰饶神鹿树种倒计时 (0表示无)

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
