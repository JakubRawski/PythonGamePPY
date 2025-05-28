from Class import *
from Engine import *



def test1():
    rat_base_stats = Statystyki()
    rat_base_stats.max_hp = 30
    rat_base_stats.current_hp = 30
    rat_base_stats.atk = 5
    rat_base_stats.defense = 1
    rat_base_stats.atkspd = 1

    player_base_stats = Statystyki()
    player_base_stats.max_hp = 100
    player_base_stats.current_hp = 100
    player_base_stats.atk = 15
    player_base_stats.atkspd = 1.2
    player_base_stats.defense = 5
    player_base_stats.atkspd = 1.2
    # Spell leczacy 20 HP
    heal_spell_stats = Statystyki()
    heal_spell_stats.current_hp = 20
    healing_spell = Spell("heal001", 0, heal_spell_stats, additive=True, harm=False, direct=True)

    # Fireball direct 15HP TODO zmienic sposob liczenia
    direct_fire_spell_stats = Statystyki()
    direct_fire_spell_stats.current_hp = -15
    direct_fire_spell = Spell("direct_fire001", 0, direct_fire_spell_stats, additive=True, harm=True, direct=True)

    # Fireball pod dmg 10HP TODO zmienic sposob liczenia
    formula_fire_spell_stats = Statystyki()
    formula_fire_spell_stats.element_dmg.fire = 10
    formula_fire_spell = Spell("formula_fire001", 0, formula_fire_spell_stats, additive=True, harm=True)

    # ATK UP buff spell +5 ATK na 3 tury
    atk_buff_stats = Statystyki()
    atk_buff_stats.atk = 5
    atk_buff = Spell("atk_buff001", 3, atk_buff_stats, additive=True, harm=False, direct=False)

    # DOT 5 dmg na 2 tury (deals 5 direct damage for 2 turns)
    dot_debuff_stats = Statystyki()
    dot_debuff_stats.current_hp = -5  # Negative for damage
    dot_debuff = Spell("dot_debuff001", 2, dot_debuff_stats, additive=True, harm=True, direct=True)

    # Heal pota ktora leczy spellem
    healing_potion = Consumable("potion001", "Healing Potion", 10, healing_spell, 2)
    # Potka buffa ataku
    atk_potion = Consumable("potion002", "Attack Potion", 15, atk_buff, 1)

    # Tworzymy szczura
    rat = Enemy("0e001", "Rat", "rat.png", 1, rat_base_stats, 5, Armor(), [], LootTable(
        slots_data=[
            {"item": "potion001", "chance": 1.0},
            {"item": "gold_pouch", "chance": 0.5},
            {"item": "rusty_sword", "chance": 0.3}   #loot
        ]
    ))

    # Uniwersalny plecak 10 slotow na wysztko
    player_backpack = Bagpack(10, ["consumable", "equipment", "material"])
    player_backpack.add_item(healing_potion)  # Add initial items to the backpack
    player_backpack.add_item(atk_potion)

    player = Gracz("0p001", "Hero", "hero.png", 1, player_base_stats, 100, Armor(),
                   [direct_fire_spell, formula_fire_spell, atk_buff, dot_debuff],  #Tablica zaklec
                   [player_backpack],  # lista plecakow
                   1) #TODO usunac lub zmienic

    # Tworzenie pseudo JSON z itemami
    ITEMS_DB = {
        "potion001": {"id": "potion001", "tag": "consumable", "name": "Healing Potion", "price": 10, "quantity": 1},
        "gold_pouch": {"id": "gold_pouch", "tag": "material", "name": "Gold Pouch", "price": 20, "rarity": "common"},
        "rusty_sword": {"id": "rusty_sword", "tag": "equipment", "name": "Rusty Sword", "price": 50, "rarity": "common"}
    }

    # Walka
    print("--- Rozpoczyna się walka! ---")
    walka([player], [rat])

    # po walce, statycznie, TODO zrob petle by kazdy loot byl osobno dzielony
    # TODO losowac przed roll 1000 czy cos
    if rat.current_stats.current_hp <= 0:
        loot_distribution([player], rat, ITEMS_DB)
    # test plecaka
    print("\n--- Zawartość plecaka gracza po walce ---")
    for bag in player.inventory:
        print(
            f"Plecaka {bag.accepted_kinds} ({len([item for item in bag.items if item is not None])}/{bag.num_slots} zajętych):")
        for i, item in enumerate(bag.items):
            if item:
                if isinstance(item, Consumable):
                    print(f"  Slot {i}: {item.name} (ID: {item.id}, Ilość: {item.quantity})")
                else:
                    print(f"  Slot {i}: {item.name} (ID: {item.id})")
            else:
                print(f"  Slot {i}: PUSTY")