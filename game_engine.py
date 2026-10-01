from field import NormalField, SandstormField, StormField, MirageField, TailwindField, BlizzardField, FogField, HailField, AcidRainField
import random
from collections import Counter

class GameEngine:
    def __init__(self, player1, player2, field_type="normal"):
        self.p1 = player1
        self.p2 = player2
        self.turn_count = 1
        self.current_attacker = self.p1
        self.current_defender = self.p2
        self.log = []
        self.change_field(field_type)

    def change_field(self, field_type):
        if field_type == "sandstorm":
            self.field = SandstormField()
        elif field_type == "storm":
            self.field = StormField()
        elif field_type == "mirror":
            self.field = MirageField()
        elif field_type == "low_gravity":
            self.field = TailwindField()
        elif field_type == "blizzard":
            self.field = BlizzardField()
        elif field_type == "fog":
            self.field = FogField()
        elif field_type == "hail":
            self.field = HailField()
        elif field_type == "acid_rain":
            self.field = AcidRainField()
        else:
            self.field = NormalField()

    def switch_turn(self):
        self.current_attacker, self.current_defender = self.current_defender, self.current_attacker
        self.turn_count += 1

    def check_necro_revive(self, character):
        """检查死灵法师复活逻辑"""
        logs = []
        if not character.is_alive() and character.passive_type == "necro":
            if not character.has_revived:
                character.has_revived = True
                revive_roll = [random.randint(1, 6) for _ in range(3)]
                revive_sum = sum(revive_roll)
                logs.append(f"【死灵法师】亡语触发！复活检定: {revive_roll} = {revive_sum}")
                if revive_sum > 12:
                    character.current_hp = character.max_hp // 2
                    logs.append("检定成功！死灵法师半血复活！")
                else:
                    logs.append("检定失败，死灵法师彻底死亡。")
        return logs

    def start_turn(self):
        """回合开始阶段"""
        self.log = []
        
        # 1. 丰饶神鹿树种结算
        if self.current_attacker.character.seed_timer > 0:
            self.current_attacker.character.seed_timer -= 1
            if self.current_attacker.character.seed_timer == 0:
                dmg = 10
                self.current_attacker.character.take_damage(dmg)
                self.log.append(f"【丰饶神鹿】树种爆发！{self.current_attacker.name} 受到 {dmg} 点真实伤害！")
            else:
                self.log.append(f"【丰饶神鹿】树种正在生长... (剩余 {self.current_attacker.character.seed_timer} 回合)")
        
        # 2. 触发场地效果
        field_effect = self.field.on_turn_start(self)
        if field_effect:
            self.log.append(field_effect)
            
        # 3. 检查回合开始时的死亡/复活 (例如被沙尘暴或树种烫死)
        self.log.extend(self.check_necro_revive(self.current_attacker.character))
        self.log.extend(self.check_necro_revive(self.current_defender.character))
            
        return self.log

    def resolve_combat(self, atk_total, def_total, atk_special_val=None, def_special_val=None):
        combat_log = []
        
        # 处理特殊骰子效果
        if atk_special_val and self.current_attacker.character.equipped_skill.skill_type == "heal_dice":
            heal_amt = atk_special_val
            self.current_attacker.character.heal(heal_amt)
            combat_log.append(f"【治疗骰子】生效！回复 {heal_amt} 点生命")

        undying = False
        if def_special_val and self.current_defender.character.equipped_skill.skill_type == "shield_dice":
            if def_special_val == 1:
                undying = True
                combat_log.append(f"【星盾骰子】触发不屈！本回合保留至少1点生命")
        
        # 1. 场地效果
        if isinstance(self.field, StormField):
            atk_max_idx = self.current_attacker.get_max_dice_index()
            if atk_max_idx != -1:
                old_val = self.current_attacker.ordinary_dice_pool[atk_max_idx].current_value
                new_val = self.current_attacker.force_reroll_dice(atk_max_idx)
                atk_total = atk_total - old_val + new_val
                combat_log.append(f"【雷暴雨】强制重投进攻方最大骰子: {old_val} -> {new_val}")

            def_max_idx = self.current_defender.get_max_dice_index()
            if def_max_idx != -1:
                old_val = self.current_defender.ordinary_dice_pool[def_max_idx].current_value
                new_val = self.current_defender.force_reroll_dice(def_max_idx)
                def_total = def_total - old_val + new_val
                combat_log.append(f"【雷暴雨】强制重投防守方最大骰子: {old_val} -> {new_val}")
        else:
            new_atk, new_def = self.field.on_before_damage(self, atk_total, def_total)
            if new_atk != atk_total or new_def != def_total:
                combat_log.append(f"【{self.field.name}】修正: 攻 {atk_total}->{new_atk}, 防 {def_total}->{new_def}")
                atk_total = new_atk
                def_total = new_def

        # 2. 碎星王虫被动 (破甲)
        if self.current_attacker.character.passive_type == "star_bug":
            # 统计点数
            counts = Counter()
            for d in self.current_attacker.ordinary_dice_pool:
                if isinstance(d.current_value, int):
                    counts[d.current_value] += 1
            
            # 检查是否所有出现的点数都是偶数次
            is_even_pattern = True
            if not counts: # 没有骰子不算
                is_even_pattern = False
            else:
                for val in counts.values():
                    if val % 2 != 0:
                        is_even_pattern = False
                        break
            
            if is_even_pattern:
                old_def = def_total
                def_total = int(def_total * 0.5)
                combat_log.append(f"【碎星王虫】共振破甲！防守方护盾减半: {old_def} -> {def_total}")

        # 3. 剑鱼骑士被动
        if self.current_attacker.character.passive_type == "swordfish":
            is_all_even = True
            for d in self.current_attacker.ordinary_dice_pool:
                if isinstance(d.current_value, int) and d.current_value % 2 != 0:
                    is_all_even = False
                    break
            if is_all_even and self.current_attacker.ordinary_dice_pool:
                bonus = int(atk_total * 0.5)
                atk_total += bonus
                combat_log.append(f"【剑鱼骑士】被动触发！全偶数，伤害加成 +{bonus}")

        # 4. 基础伤害计算
        raw_damage = atk_total - def_total
        final_damage = max(0, raw_damage)

        # 5. 救世主被动
        if self.current_attacker.character.passive_type == "savior":
            if self.current_attacker.character.current_hp < 10:
                lifesteal = int(final_damage * 0.5)
                if lifesteal > 0:
                    self.current_attacker.character.heal(lifesteal)
                    combat_log.append(f"【救世主】绝境爆发！吸血回复 {lifesteal} 点生命！")

        if self.current_defender.character.passive_type == "savior":
            if self.current_defender.character.current_hp > 10:
                thorns_damage = int(final_damage * 0.5)
                if thorns_damage > 0:
                    self.current_attacker.character.take_damage(thorns_damage)
                    combat_log.append(f"【救世主】圣光护体！反弹 {thorns_damage} 点伤害！")

        # 6. 应用伤害
        if undying and self.current_defender.character.current_hp - final_damage <= 0:
            final_damage = max(0, self.current_defender.character.current_hp - 1)
            combat_log.append("【星盾】生效！免疫致死伤害！")
            
        self.current_defender.character.take_damage(final_damage)
        combat_log.append(f"结算: 攻击 {atk_total} - 防御 {def_total} = {raw_damage} 点基础伤害")
        combat_log.append(f"最终造成伤害: {final_damage}")

        # 7. 丰饶神鹿被动
        if self.current_attacker.character.passive_type == "deer" and final_damage > 0:
            self.current_defender.character.seed_timer += 2
            combat_log.append(f"【丰饶神鹿】命中！在 {self.current_defender.name} 身上种下树种！(当前累计 {self.current_defender.character.seed_timer} 回合后爆发)")

        # 8. 银鬃铁卫被动
        if self.current_defender.character.passive_type == "silvermane":
            if 3 <= final_damage <= 7:
                counter_roll = random.randint(1, 6)
                self.current_attacker.character.take_damage(counter_roll)
                combat_log.append(f"【银鬃铁卫】坚守反击！受到 {final_damage} 点伤害，触发反击！")
                combat_log.append(f"反击投掷: {counter_roll} -> 造成 {counter_roll} 点真实伤害！")

        # 9. 检查双方死亡/复活
        # 注意：这里要检查双方，因为进攻方可能被反死
        combat_log.extend(self.check_necro_revive(self.current_defender.character))
        combat_log.extend(self.check_necro_revive(self.current_attacker.character))
        
        return final_damage, combat_log
