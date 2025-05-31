import json
import os
import random

from Class import *

def loot_distribution(gracze, enemy, ITEMS_DB):
    #loot wrogow
    loot_slots_data = enemy.loot_table.slots_data

    print("--- Rozdanie lootu ---")
    #TODO ZMIENIC sposb by kazdy gracz osobno dostalwa by nie mnozyc lootu
    for gracz in gracze:
        print("Gracz:", gracz.name)

        for slot_data in loot_slots_data:
            item_id = slot_data["item"]
            chance = slot_data["chance"]

            if random.random() <= chance:
                item_data = ITEMS_DB.get(item_id)
                if not item_data:
                    print(f"Nie znaleziono przedmiotu o ID: {item_id}")
                    continue

                #dla consumable
                if item_data["tag"] == "consumable":
                    spell_id = item_data.get("spell")
                    linked_spell = None
                    if spell_id and spell_id in SPELLS_DB:
                        linked_spell = SPELLS_DB[spell_id]
                    dummy_spell_stats = Statystyki()  # Fallback if no spell or spell not found
                    new_item = Consumable(item_data["id"], item_data["name"], item_data["price"],
                                          linked_spell or Spell("dummy", 0, dummy_spell_stats),
                                          item_data.get("quantity", 1))
                elif item_data["tag"] == "equipment":
                    item_stats = Statystyki()
                    if "statystyki" in item_data:
                        for stat_name, value in item_data["statystyki"].items():
                            if stat_name == "element_dmg":
                                for elem, elem_val in value.items():
                                    setattr(item_stats.element_dmg, elem, elem_val)
                            else:
                                setattr(item_stats, stat_name, value)
                    spell_id = item_data.get("spell")
                    linked_spell = None
                    if spell_id and spell_id in SPELLS_DB:
                        linked_spell = SPELLS_DB[spell_id]
                    new_item = Equipment(item_data["id"], item_data["slot_tag"], item_data["name"], item_data["price"],
                                         item_stats, linked_spell, item_data.get("rarity", "common"))

                #to na razie smieci, do pozniejszego updatu
                elif item_data["tag"] == "material":
                    new_item = Material(item_data["id"], item_data["name"], item_data["price"], item_data.get("rarity", "common"))
                else:
                    new_item = Item(item_data["id"], item_data["tag"], item_data["name"], item_data["price"])


                found_bag = None # bool ktory aktywuje sie po znajeznieniu stackowanego itemu
                for bag in gracz.inventory:
                    if new_item.tag in bag.accepted_kinds:
                        # Szuka itemu ktore sie stackuja
                        if isinstance(new_item, Consumable):
                            for i, existing_item in enumerate(bag.items):
                                if isinstance(existing_item, Consumable) and existing_item.id == new_item.id:
                                    existing_item.quantity += new_item.quantity
                                    print(f"Zwiększono ilość: {new_item.name} => {existing_item.quantity} w {bag.accepted_kinds} plecaku.")
                                    found_bag = bag # aktywacja
                                    break
                            if found_bag: #dodano item, przejdz do nastepnego itemu
                                break

                        if not found_bag: # nowy item do plecaka
                            if bag.add_item(new_item):
                                print(f"Dodano do ekwipunku: {new_item.name} w {bag.accepted_kinds} plecaku.")
                                found_bag = bag
                                break #dodano item, przejdz do nastepnego itemu
                # pelny plecak lub jest nieprawidlowy
                if not found_bag:
                    print(f"Brak miejsca w plecaku dla {new_item.name}. Co zrobić?")
                    print("1. Zamień przedmiot")
                    print("2. Odrzuć nowy przedmiot")
                    print("3. Anuluj (nie przyjmuj)")

                    try:
                        wybor = int(input("Wybór [1-3]: "))
                    except ValueError:
                        wybor = 3 # ignoruje przedmiot i sie go pozbywa

                    if wybor == 1:
                        # szuka itemu
                        target_bag = None
                        for bag in gracz.inventory:
                            if new_item.tag in bag.accepted_kinds and any(item is not None for item in bag.items):
                                target_bag = bag
                                break
                        # show plecak
                        if target_bag:
                            print(f"Przedmioty w plecaku ({target_bag.accepted_kinds}):")
                            for i, it in enumerate(target_bag.items):
                                if it:
                                    print(f"{i}: {it.name} (ID: {it.id})")
                                else:
                                    print(f"{i}: PUSTY SLOT")

                            while True:
                                try:
                                    index_to_replace = int(input("Wybierz indeks przedmiotu do zamiany lub -1 aby anulować: "))
                                    if index_to_replace == -1:
                                        print(f"Nie przyjęto: {new_item.name}.")
                                        break
                                    if 0 <= index_to_replace < target_bag.num_slots:
                                        old_item = target_bag.items[index_to_replace]
                                        target_bag.items[index_to_replace] = new_item
                                        print(f"Zamieniono {old_item.name if old_item else 'PUSTY SLOT'} na {new_item.name}.")
                                        break
                                    else:
                                        print("Nieprawidłowy indeks. Spróbuj ponownie.")
                                except ValueError:
                                    print("Nieprawidłowe wejście. Wprowadź numer.")
                        else:
                            print("Brak plecaka z odpowiednim typem lub wolnym miejscem do zamiany.")
                            print(f"Odrzucono: {new_item.name}.")
                    elif wybor == 2:
                        print(f"Odrzucono: {new_item.name}.")
                    else:
                        print(f"Nie przyjęto: {new_item.name}.")

def walka(gracze, enemy):
    wszyscy = gracze + enemy
    for gracz in gracze:
        gracz.reset_stats_for_combat()
    #Start pivotow
    for unit in wszyscy:
        unit.pivot = 0

    aktualna_druzyna = gracze  #gracze zaczynaja

    while True:
        #Filtruj aktywnych uczestnikow
        aktywni = []
        for u in wszyscy:
            if u.current_stats.current_hp > 0 and u.pivot >= 0:
                aktywni.append(u)

        if not aktywni:
            print("--- Koniec rundy --- Reset inicjatywy ---")
            for unit in wszyscy:
                unit.pivot += 1

            #Zmiana druzyny na podstawie najwiekszego pivotu
            zywi = []
            for u in wszyscy:
                if u.current_stats.current_hp > 0:
                    zywi.append(u)

            zywi.sort(key=lambda u: u.pivot, reverse=True)

            if not zywi:
                print("Brak żywych jednostek — koniec walki.")
                return

            if zywi[0] in gracze:
                aktualna_druzyna = gracze
            else:
                aktualna_druzyna = enemy
            continue

        # Sortowanie NPC i wybieranie kolejnosci
        kandydaci = []
        for u in aktualna_druzyna:
            if u.current_stats.current_hp > 0 and u.pivot >= 0:
                kandydaci.append(u)

        if not kandydaci:
            aktualna_druzyna = enemy if aktualna_druzyna == gracze else gracze
            continue

        max_pivot = max([u.pivot for u in kandydaci])
        top_pivoters = [u for u in kandydaci if u.pivot == max_pivot]
        actor = random.choice(top_pivoters)

        przeciwnicy = enemy if actor in gracze else gracze
        zywi_przeciwnicy = [u for u in przeciwnicy if u.current_stats.current_hp > 0]

        if not zywi_przeciwnicy:
            if actor in gracze:
                print("Walka zakończona! Gracze wygrali")
            else:
                print("Walka zakończona! Wrogowie wygrali")
            break

        # Gdy jest to gracz
        #TODO dodaj ture enemy z random atakiem (dac 1 atak default)
        if isinstance(actor, Gracz):
            action_result = actor.wybierz(gracze, enemy)
            if action_result == "ucieczka":
                print(f"{actor.name} uciekł z walki!")
                return
            elif action_result == "no_target" or action_result == "cancel" or action_result == "no_item" or action_result == "no_spell" or action_result == "no_effect":
                # opcja cofniecia i mozliwosc ponowienia
                continue
        else: # Simple AI for enemy (attack a random player)
            if zywi_przeciwnicy:
                cel = random.choice(zywi_przeciwnicy)
                dmg = actor.current_stats.atk
                cel.current_stats.current_hp -= dmg
                hp_left = max(cel.current_stats.current_hp, 0)
                print(f"{actor.name} atakuje {cel.name} za {dmg} dmg. ({hp_left} HP left)")


        actor.pivot -= 1.0 / actor.current_stats.atkspd

        # Zmiana tury
        aktualna_druzyna = enemy if aktualna_druzyna == gracze else gracze

        # Sprawdzenie czy ktoras druzyna jest martwa
        gracze_martwi = all(u.current_stats.current_hp <= 0 for u in gracze)
        enemy_martwi = all(u.current_stats.current_hp <= 0 for u in enemy)

        if gracze_martwi:
            print("Wrogowie wygrali walkę!")
            break
        elif enemy_martwi:
            print("Gracze wygrali walkę!")
            break
#TODO usun albo rozwin
"""
def runda(gracz: Gracz, enemy: Enemy):
    print(f"{gracz.name} vs {enemy.name} - tura start")
    #Logika ataku gracza
    dmg = gracz.current_stats.atk
    enemy.current_stats.current_hp -= dmg
    print(f"{gracz.name} zadaje {dmg} obrażeń {enemy.name}")
    #Logika ataku przeciwnika
    if enemy.current_stats.current_hp > 0:
        dmg = enemy.current_stats.atk
        gracz.current_stats.current_hp -= dmg
        print(f"{enemy.name} zadaje {dmg} obrażeń {gracz.name}")
"""
#Ładowanie danych JSON

ITEMS_DB = {}
SPELLS_DB = {}
ENEMIES_DB = {}
PLAYERS_DB = {} # Multiplayer moze kiedys

def wczytaj_json_z_folderu(folder_path, id_prefix=None):
    data = {}
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            file_id = os.path.splitext(filename)[0] # Get ID from filename
            if id_prefix and not file_id.startswith(id_prefix):
                continue # pomija jak id sie nie zgadza TODO poprawic bo bierze 1 el a nie ciag liczb przed litera

            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as plik:
                json_data = json.load(plik)
                data[json_data.get("ID", json_data.get("id"))] = json_data
    return data


def load_game_data(world_id):
    # przykladowy prefix 0
    global ITEMS_DB, SPELLS_DB, ENEMIES_DB, PLAYERS_DB

    base_data_path = "data"

    # ladowanie spellow najpierw by laczyc z itemami i graczami
    spells_path = os.path.join(base_data_path, "Spells")
    spell_data = wczytaj_json_z_folderu(spells_path)
    for spell_id, s_data in spell_data.items():
        stats = Statystyki()
        for stat_name, value in s_data["statystyki"].items():
            if stat_name == "element_dmg":
                for elem, elem_val in value.items():
                    setattr(stats.element_dmg, elem, elem_val)
            else:
                setattr(stats, stat_name, value)
        SPELLS_DB[spell_id] = Spell(
            id=s_data["id"],
            tick=s_data["tick"],
            statystyki=stats,
            additive=s_data.get("additive", True),
            harm=s_data.get("harm", True),
            direct=s_data.get("direct", False)
        )
    print(f"Loaded {len(SPELLS_DB)} spells.")

    # Load Items
    items_path = os.path.join(base_data_path, "Items")
    item_data = wczytaj_json_z_folderu(items_path)
    for item_id, i_data in item_data.items():
        if i_data["tag"] == "consumable":
            spell_id = i_data.get("spell")
            linked_spell = SPELLS_DB.get(spell_id) if spell_id else None
            ITEMS_DB[item_id] = {
                "id": i_data["id"],
                "tag": i_data["tag"],
                "name": i_data["name"],
                "price": i_data["price"],
                "spell": spell_id, # Zaweira ID
                "quantity": i_data.get("quantity", 1)
            }
        elif i_data["tag"] == "equipment":
            ITEMS_DB[item_id] = {
                "id": i_data["id"],
                "tag": i_data["tag"],
                "slot_tag": i_data["slot_tag"],
                "name": i_data["name"],
                "price": i_data["price"],
                "statystyki": i_data.get("statystyki", {}),
                "spell": i_data.get("spell"),
                "rarity": i_data.get("rarity", "common")
            }
        elif i_data["tag"] == "material":
            ITEMS_DB[item_id] = {
                "id": i_data["id"],
                "tag": i_data["tag"],
                "name": i_data["name"],
                "price": i_data["price"],
                "rarity": i_data.get("rarity", "common")
            }
        else:
            ITEMS_DB[item_id] = {
                "id": i_data["id"],
                "tag": i_data["tag"],
                "name": i_data["name"],
                "price": i_data["price"]
            }
    print(f"Loaded {len(ITEMS_DB)} items.")

    # Ladowanie przeciwnika
    enemies_path = os.path.join(base_data_path, "Enemies")
    # Zczytywanie na podstawie krain
    enemy_data = wczytaj_json_z_folderu(enemies_path, id_prefix=world_id)
    for enemy_id, e_data in enemy_data.items():
        base_stats = Statystyki()
        for stat_name, value in e_data["base_stats"].items():
            if stat_name == "element_dmg" or stat_name == "element_res":
                for elem, elem_val in value.items():
                    setattr(getattr(base_stats, stat_name), elem, elem_val)
            else:
                setattr(base_stats, stat_name, value)

        enemy_spells = []
        for spell_id in e_data.get("spells", []):
            if spell_id in SPELLS_DB:
                enemy_spells.append(SPELLS_DB[spell_id])
            else:
                print(f"Warning: Spell '{spell_id}' for enemy '{enemy_id}' not found in SPELLS_DB.")

        loot_table = LootTable(e_data.get("loot_table", {}).get("slots", []))

        new_enemy = Enemy(
            ID=e_data["ID"],
            name=e_data["name"],
            icon=e_data["icon"],
            level=e_data["level"],
            base_stats=base_stats,
            gold=e_data["gold"],
            armor=e_data.get("armor", {}), # Armor to JSON z elementami, inaczej dict
            spells=enemy_spells,
            loot_table=loot_table
        )
        new_enemy.load_image(os.path.join("assets", "Enemies", new_enemy.icon)) # Ladowanie obrazu
        ENEMIES_DB[enemy_id] = new_enemy
    print(f"Loaded {len(ENEMIES_DB)} enemies for world ID '{world_id}'.")

    # Ladowanie graczy
    players_path = os.path.join(base_data_path, "Player")
    player_data = wczytaj_json_z_folderu(players_path)
    for player_id, p_data in player_data.items():
        base_stats = Statystyki()
        for stat_name, value in p_data["base_stats"].items():
            if stat_name == "element_dmg" or stat_name == "element_res":
                for elem, elem_val in value.items():
                    setattr(getattr(base_stats, stat_name), elem, elem_val)
            else:
                setattr(base_stats, stat_name, value)

        player_spells = []
        for spell_id in p_data.get("spells", []):
            if spell_id in SPELLS_DB:
                player_spells.append(SPELLS_DB[spell_id])
            else:
                print(f"Warning: Spell '{spell_id}' for player '{player_id}' not found in SPELLS_DB.")


        # do testow TODO ususn
        player_inventory = [
            Bagpack(num_slots=5, accepted_kinds=['consumable']),
            Bagpack(num_slots=5, accepted_kinds=['equipment']),
            Bagpack(num_slots=5, accepted_kinds=['material'])
        ]

        new_player = Gracz(
            ID=p_data["ID"],
            name=p_data["name"],
            icon=p_data["icon"],
            level=p_data["level"],
            base_stats=base_stats,
            gold=p_data["gold"],
            armor=p_data.get("armor", {}),
            spells=player_spells,
            inventory=player_inventory,
            menu=None # Potencjalne menu TODO usun lub zaimplementuj
        )
        new_player.load_image(os.path.join("assets", "Players", new_player.icon)) # Assuming 'assets/players' for images
        PLAYERS_DB[player_id] = new_player
    print(f"Loaded {len(PLAYERS_DB)} players.")
