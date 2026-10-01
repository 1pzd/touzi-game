import random
from dice import Dice
from skill import Skill
from character import Character
from player import Player
from game_engine import GameEngine

def main():
    print("=== 欢迎来到划时代双人对战游戏 ===")
    
    # 定义技能 (数值调整)
    def berserk_effect(user, target, game):
        return 3, 0, "狂暴打击！造成额外3点伤害"

    def heal_effect(user, target, game):
        return 0, 2, "圣光庇护！回复2点生命"

    skill_berserk = Skill("狂暴打击", "造成额外3点伤害", 3, berserk_effect) # 限制3次
    skill_heal = Skill("圣光庇护", "回复2点生命", 3, heal_effect) # 限制3次

    # 创建角色 (血量调整)
    char1 = Character("狂战士", 40, 5, 3, "每损失10点生命，攻击力+1")
    char1.equipped_skill = skill_berserk

    char2 = Character("圣骑士", 50, 3, 5, "每回合回复2点生命")
    char2.equipped_skill = skill_heal

    # 创建玩家
    p1 = Player("玩家1", char1)
    p2 = Player("玩家2", char2)

    # 随机选择场地
    field_types = ["normal", "sandstorm", "storm", "mirror", "low_gravity"]
    field_type = random.choice(field_types)
    field_names = {
        "normal": "平安夜 (无效果)",
        "sandstorm": "沙尘暴 (每回合扣2血)",
        "storm": "暴风雨 (强制重投最大骰子)",
        "mirror": "镜像空间 (攻防互换)",
        "low_gravity": "低重力区 (所有骰子+1)"
    }
    print(f"\n🎲 本局随机场地: {field_names.get(field_type, '未知')}")
    
    game = GameEngine(p1, p2, field_type)

    while p1.character.is_alive() and p2.character.is_alive():
        print(f"\n--- 第 {game.turn_count} 回合 ---")
        
        # 回合开始阶段 (场地效果)
        turn_logs = game.start_turn()
        for log in turn_logs:
            print(log)

        attacker = game.current_attacker
        defender = game.current_defender
        
        print(f"进攻方: {attacker.name} ({attacker.character.name}) HP: {attacker.character.current_hp}")
        print(f"防守方: {defender.name} ({defender.character.name}) HP: {defender.character.current_hp}")

        # 进攻阶段
        attacker.prepare_dice(attacker.character.atk_dice_count)
        print(f"{attacker.name} 投掷攻击骰子...")
        results, skill_result = attacker.roll_all()
        print(f"初次投掷结果: {results} (技能骰: {skill_result})")

        # 重投机会 (简单模拟，实际需要交互)
        # 这里假设玩家总是重投数值小于3的骰子
        reroll_indices = [i for i, val in enumerate(results) if val < 3]
        if reroll_indices:
            # 转换为 1-based 显示
            display_indices = [i + 1 for i in reroll_indices]
            print(f"{attacker.name} 选择重投第 {display_indices} 个骰子...")
            
            # 锁定不需要重投的 (逻辑保持 0-based 内部处理)
            keep_indices = [i for i, val in enumerate(results) if val >= 3]
            attacker.lock_ordinary_dice(keep_indices)
            
            # 技能骰子如果没触发，也重投
            if skill_result != 'S':
                attacker.lock_skill_dice(False)
            else:
                attacker.lock_skill_dice(True)

            new_results, new_skill_result = attacker.roll_all()
            print(f"重投后结果: {new_results} (技能骰: {new_skill_result})")
            results = new_results
            skill_result = new_skill_result

        atk_total = sum(results)
        atk_triggered = (skill_result == 'S')
        print(f"最终攻击点数: {atk_total} (技能触发: {atk_triggered})")

        # 防守阶段
        defender.prepare_dice(defender.character.def_dice_count)
        print(f"{defender.name} 投掷防御骰子...")
        def_results, def_skill_result = defender.roll_all()
        print(f"防御投掷结果: {def_results} (技能骰: {def_skill_result})")
        
        def_total = sum(def_results)
        def_triggered = (def_skill_result == 'S')
        print(f"最终防御点数: {def_total} (技能触发: {def_triggered})")

        # 结算伤害
        damage, combat_log = game.resolve_combat(atk_total, def_total, atk_triggered, def_triggered)
        for log_entry in combat_log:
            print(log_entry)

        if not defender.character.is_alive():
            print(f"\n!!! {defender.name} 被击败了 !!!")
            print(f"游戏结束，{attacker.name} 获胜！")
            break

        game.switch_turn()
        input("按回车键继续下一回合...")

if __name__ == "__main__":
    main()
