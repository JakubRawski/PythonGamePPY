import json
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
                    #TODO dodac spelle zgodne z JSON
                    dummy_spell_stats = Statystyki()
                    dummy_spell = Spell("dummy_spell", 0, dummy_spell_stats)
                    new_item = Consumable(item_data["id"], item_data["name"], item_data["price"], dummy_spell, item_data.get("quantity", 1))
                elif item_data["tag"] == "equipment":
                    #TODO dodac armor zgodne z JSON poodobnie do consumable
                    dummy_stats = Statystyki()
                    new_item = Equipment(item_data["id"], item_data["tag"], item_data["name"], item_data["price"], dummy_stats, None, item_data.get("rarity", "common"))
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
                        for bag in gracz.inventory_bags:
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
            elif action_result == "no_target" or action_result == "cancel":
                # opcja cofniecia i mozliwosc ponowienia
                continue
        else: pass  # Tura przeciwnika
        """
            cel = random.choice(zywi_przeciwnicy)
            dmg = actor.current_stats.atk
            cel.current_stats.current_hp -= dmg
            hp_left = max(cel.current_stats.current_hp, 0)

        print(f"{actor.name} atakuje {cel.name} za {dmg} dmg. ({hp_left} HP left)")
        """
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

def wczytaj_json(sciezka):
    with open(sciezka, 'r', encoding='utf-8') as plik:
        return json.load(plik)
