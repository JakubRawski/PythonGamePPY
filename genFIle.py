# wstepne generowanie jakbym musial czyscic foldery

"""
    enemy_json_content = {
      "ID": "0e001",
      "name": "Rat",
      "icon": "rat.png",
      "level": 1,
      "gold": 5,
      "base_stats": {
        "max_hp": 30,
        "current_hp": 30,
        "max_mana": 0,
        "current_mana": 0,
        "shield": 0,
        "atk": 5,
        "crit_rate": 0.05,
        "crit_dmg": 1.2,
        "element_dmg": {},
        "defense": 1,
        "element_res": {},
        "def_shred": 0,
        "heal_bonus": 0,
        "atkspd": 1
      },
      "armor": {},
      "spells": [],
      "loot_table": {
        "slots": [
          { "item": "0i001", "chance": 0.5 },
          { "item": "0i002", "chance": 0.2 }
        ]
      }
    }
    with open("data/Enemies/0e001.json", "w") as f:
        json.dump(enemy_json_content, f, indent=2)

    item_consumable_json_content = {
      "id" : "0i002",
      "tag": "consumable",
      "name": "Health Potion",
      "price": 10,
      "spell": "0s002",
      "quantity": 1
    }
    with open("data/Items/0i002.json", "w") as f:
        json.dump(item_consumable_json_content, f, indent=2)

    item_equipment_json_content = {
      "id" : "0i001",
      "tag": "equipment",
      "slot_tag": "wand",
      "name": "Basic Wand",
      "price": 50,
      "statystyki": {
        "atk": 2,
        "element_dmg": {
          "fire": 3
        }
      },
      "spell": "0s001",
      "rarity": "common"
    }
    with open("data/Items/0i001.json", "w") as f:
        json.dump(item_equipment_json_content, f, indent=2)

    spell_damage_json_content = {
      "id": "0s001",
      "tick": -1,
      "statystyki": {
        "atk": 15,
        "element_dmg": {
          "fire": 15
        }
      },
      "additive": True,
      "harm": True
    }
    with open("data/Spells/0s001.json", "w") as f:
        json.dump(spell_damage_json_content, f, indent=2)

    spell_heal_json_content = {
      "id": "0s002",
      "tick": -1,
      "statystyki": {
        "max_hp": 20
      },
      "additive": True,
      "harm": False
    }
    with open("data/Spells/0s002.json", "w") as f:
        json.dump(spell_heal_json_content, f, indent=2)

    player_json_content = {
      "ID": "0p001",
      "name": "Hero",
      "icon": "hero.png",
      "level": 1,
      "gold": 100,
      "base_stats": {
        "max_hp": 100,
        "current_hp": 100,
        "max_mana": 50,
        "current_mana": 50,
        "shield": 0,
        "atk": 10,
        "crit_rate": 0.1,
        "crit_dmg": 1.5,
        "element_dmg": {},
        "defense": 5,
        "element_res": {},
        "def_shred": 0,
        "heal_bonus": 0,
        "atkspd": 1
      },
      "armor": {},
      "spells": ["0s001", "0s002"]
    }
    with open("data/Player/0p001.json", "w") as f:
        json.dump(player_json_content, f, indent=2)

    """