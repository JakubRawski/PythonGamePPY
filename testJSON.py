import pygame
pygame.init()

from Class import *
from Engine import *




try:
    screen = pygame.display.set_mode((1, 1), pygame.NOFRAME | pygame.HIDDEN)
except pygame.error as e:
    print(f"Could not set video mode for Pygame: {e}. Image loading might fail.")
os.makedirs("data/Enemies", exist_ok=True)
os.makedirs("data/Items", exist_ok=True)
os.makedirs("data/Spells", exist_ok=True)
os.makedirs("data/Player", exist_ok=True)
os.makedirs("assets/Enemies", exist_ok=True)
os.makedirs("assets/Players", exist_ok=True)

# testowanie polaczenia
try:
    pygame.image.save(pygame.Surface((32, 32)), "assets/Enemies/rat.png")
    pygame.image.save(pygame.Surface((32, 32)), "assets/Players/hero.png")
except Exception as e:
    print(f"Could not create dummy image files (might need a display server for pygame.image.save): {e}")

# Load data for world '0'
print("Loading game data for world '0'...")
load_game_data(world_id='0')

print("\n--- Loaded Data ---")
print("Enemies:", ENEMIES_DB)
print("Items:", ITEMS_DB)
print("Spells:", SPELLS_DB)
print("Players:", PLAYERS_DB)

# Test dostepu danych TODO usun
if "0e001" in ENEMIES_DB:
    rat = ENEMIES_DB["0e001"]
    print(f"\nEnemy: {rat.name}, Level: {rat.level}, HP: {rat.base_stats.max_hp}, ATK: {rat.base_stats.atk}")
    if rat.image:
        print(f"Rat image loaded: {rat.image.get_size()}")
    else:
        print("Rat image not loaded.")
    if rat.loot_table.slots_data:
        print(f"Rat loot: {rat.loot_table.slots_data[0]['item']} (chance: {rat.loot_table.slots_data[0]['chance']})")

if "0i002" in ITEMS_DB:
    hp_potion_data = ITEMS_DB["0i002"]
    print(f"Item: {hp_potion_data['name']}, Tag: {hp_potion_data['tag']}, Price: {hp_potion_data['price']}")

if "0s001" in SPELLS_DB:
    fire_spell = SPELLS_DB["0s001"]
    print(f"Spell: {fire_spell.id}, Tick: {fire_spell.tick}, Fire Dmg: {fire_spell.stats.element_dmg.fire}")

if "0p001" in PLAYERS_DB:
    player_char = PLAYERS_DB["0p001"]
    print(
        f"\nPlayer: {player_char.name}, HP: {player_char.current_stats.max_hp}, Spells: {[s.id for s in player_char.spells]}")
    if player_char.image:
        print(f"Player image loaded: {player_char.image.get_size()}")
    else:
        print("Player image not loaded.")

# Test walki
print("\n--- Starting a simulated combat ---")
if "0p001" in PLAYERS_DB and "0e001" in ENEMIES_DB:
    player1 = PLAYERS_DB["0p001"]
    enemy1 = ENEMIES_DB["0e001"]

    # do testow TODO ususn
    if not player1.inventory:
        player1.inventory = [
            Bagpack(num_slots=5, accepted_kinds=['consumable']),
            Bagpack(num_slots=5, accepted_kinds=['equipment']),
            Bagpack(num_slots=5, accepted_kinds=['material'])
        ]

    # dodawanie do testow pot
    if "0i002" in ITEMS_DB:
        hp_potion_data = ITEMS_DB["0i002"]
        spell_id = hp_potion_data.get("spell")
        linked_spell = SPELLS_DB.get(spell_id) if spell_id else None
        hp_potion_instance = Consumable(
            hp_potion_data["id"],
            hp_potion_data["name"],
            hp_potion_data["price"],
            linked_spell or Spell("dummy", 0, Statystyki()),
            quantity=2
        )
        player1.inventory[0].add_item(hp_potion_instance)
        print(f"Added {hp_potion_instance.name} to player inventory.")

    # walka
    walka([player1], [enemy1])

    # rozdawanie lootu
    if enemy1.current_stats.current_hp <= 0:
        loot_distribution([player1], enemy1, ITEMS_DB)
else:
    print("Could not run combat simulation: Player or Enemy not loaded.")