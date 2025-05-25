import random

import pygame
import json
import os

# === Klasy podstawowe ===

class ElementDmg:
    def __init__(self, fire=0, frost=0, water=0, air=0, earth=0, nature=0, electr=0):
        self.fire = fire
        self.frost = frost
        self.water = water
        self.air = air
        self.earth = earth
        self.nature = nature
        self.electr = electr

class Statystyki:
    def __init__(self):
        self.max_hp = 100
        self.current_hp = 100
        self.max_mana = 100
        self.current_mana = 100
        self.shield = 0
        self.atk = 10
        self.crit_rate = 0.1
        self.crit_dmg = 1.5
        self.element_dmg = ElementDmg()
        self.defense = 5
        self.element_res = ElementDmg()
        self.def_shred = 0
        self.heal_bonus = 0
        self.atkspd = 1

# === Itemy i ekwipunek ===

class Item:
    def __init__(self, id, tag, name, price):
        self.id = id
        self.tag = tag
        self.name = name
        self.price = price

class Consumable(Item):
    def __init__(self,id, name, price, spell, quantity):
        super().__init__(id,'consumable', name, price)
        self.spell = spell
        self.quantity = quantity

class Equipment(Item):
    def __init__(self,id, tag, name, price, statystyki, spell, rarity):
        super().__init__(id,'equipment', name, price)
        self.slot_tag = tag
        self.stats = statystyki
        self.spell = spell
        self.rarity = rarity

class Material(Item):
    def __init__(self,id, name, price, rarity):
        super().__init__(id,'material', name, price)
        self.rarity = rarity

class Bag:
    def __init__(self, slots):
        self.slots = slots

class LootTable(Bag):
    def __init__(self, slots):
        super().__init__(slots)  # slots: list of (Item, drop_chance)

class Bagpack(Bag):
    def __init__(self, slots, type_tag):
        super().__init__(slots)
        self.type_tag = type_tag

class Armor:
    def __init__(self):
        self.helmet = None
        self.chest = None
        self.legs = None
        self.boots = None
        self.weapon = None
        self.off_hand = None
        self.wand = None

# === Umiejętności i walka ===

class Spell:
    def __init__(self,id, tick, statystyki, additive=True):
        self.id = id
        self.tick = tick
        self.stats = statystyki
        self.additive = additive

# === Postacie ===

class NPC:
    def __init__(self, ID, name, icon, level, base_stats, gold, armor, spells):
        self.ID = ID
        self.name = name
        self.icon = icon
        self.level = level
        self.base_stats = base_stats
        self.current_stats = base_stats
        self.gold = gold
        self.armor = armor
        self.spells = spells

class Enemy(NPC):
    def __init__(self, ID, name, icon, level, base_stats, gold, armor, spells, loot_table):
        super().__init__(ID, name, icon, level, base_stats, gold, armor, spells)
        self.loot_table = loot_table

class Gracz(NPC):
    def __init__(self, ID, name, icon, level, base_stats, gold, armor, spells, inventory, menu):
        super().__init__(ID, name, icon, level, base_stats, gold, armor, spells)
        self.inventory = inventory
        self.menu = menu

class Menu:
    def __init__(self):
        self.stage = 'start'  # może być 'start', 'battle', 'inventory', etc.



def loot_distribution(gracze, enemy, ITEMS_DB):
    loot_slots = enemy.loot_table["slots"]

    print("--- Rozdanie łupów ---")

    for gracz in gracze:
        print("Gracz:", gracz.name)

        for slot in loot_slots:
            item_id = slot["item"]
            chance = slot["chance"]

            if random.random() <= chance:
                # Przedmiot wylosowany
                item_data = ITEMS_DB.get(item_id)
                if not item_data:
                    print("Nie znaleziono przedmiotu o ID:", item_id)
                    continue

                # Szukamy odpowiedniego plecaka (zgodnego z tagiem)
                matching_bags = [b for b in gracz.inventory if item_data["tag"] in b.kind]
                if not matching_bags:
                    print("Brak odpowiedniego plecaka na", item_data["name"])
                    continue

                bag = matching_bags[0]

                # Czy to consumable, które już mamy?
                if item_data["tag"] == "consumable":
                    found = False
                    for it in bag.items:
                        if it["id"] == item_id:
                            it["quantity"] += item_data.get("quantity", 1)
                            print("Zwiększono ilość:", item_data["name"], "=>", it["quantity"])
                            found = True
                            break
                    if found:
                        continue  # Nie trzeba dodawać nowego

                # Czy mamy miejsce?
                if len(bag.items) < bag.slots:
                    bag.items.append(item_data.copy())
                    print("Dodano do ekwipunku:", item_data["name"])
                else:
                    # Ekwipunek pełny
                    print("Ekwipunek pełny. Co zrobić z", item_data["name"], "?")
                    print("1. Zamień przedmiot")
                    print("2. Odrzuć nowy przedmiot")
                    print("3. Anuluj (nie przyjmuj)")

                    # Pseudo-interaktywne — dla testów wpisujemy numer opcji
                    try:
                        wybor = int(input("Wybór [1-3]: "))
                    except:
                        wybor = 3

                    if wybor == 1:
                        # Wypisz przedmioty i pozwól zamienić
                        for i, it in enumerate(bag.items):
                            print(str(i) + ": " + it["name"])
                        try:
                            index = int(input("Wybierz indeks przedmiotu do zamiany: "))
                            bag.items[index] = item_data.copy()
                            print("Zamieniono na:", item_data["name"])
                        except:
                            print("Nieprawidłowy wybór — pominięto.")
                    elif wybor == 2:
                        print("Odrzucono:", item_data["name"])
                    else:
                        print("Nie przyjęto:", item_data["name"])




def walka(gracze, enemy):
    wszyscy = gracze + enemy

    # Inicjalizacja pivotów
    for unit in wszyscy:
        unit.pivot = 0

    aktualna_druzyna = gracze  # gracze zaczynają

    while True:
        # Filtruj aktywnych uczestników
        aktywni = []
        for u in wszyscy:
            if u.current_stats.current_hp > 0 and u.pivot >= 0:
                aktywni.append(u)

        if not aktywni:
            print("--- Koniec rundy --- Reset inicjatywy ---")
            for unit in wszyscy:
                unit.pivot += 1

            # Zmiana drużyny na podstawie największego pivotu
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

        # Wybierz uczestników z najwyższym pivotem w aktualnej drużynie
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

        # Prosty atak
        cel = random.choice(zywi_przeciwnicy)
        dmg = actor.current_stats.atk
        cel.current_stats.current_hp -= dmg
        hp_left = max(cel.current_stats.current_hp, 0)

        print(actor.name + " atakuje " + cel.name + " za " + str(dmg) + " dmg. (" + str(hp_left) + " HP left)")

        actor.pivot -= 1.0 / actor.current_stats.atkspd

        # Zmiana tury
        aktualna_druzyna = enemy if aktualna_druzyna == gracze else gracze

        # Sprawdzenie końca walki
        gracze_martwi = all(u.current_stats.current_hp <= 0 for u in gracze)
        enemy_martwi = all(u.current_stats.current_hp <= 0 for u in enemy)

        if gracze_martwi:
            print("Wrogowie wygrali walkę!")
            break
        elif enemy_martwi:
            print("Gracze wygrali walkę!")
            break

def runda(gracz: Gracz, enemy: Enemy):
    print(f"{gracz.name} vs {enemy.name} - tura start")
    # Logika ataku gracza
    dmg = gracz.current_stats.atk
    enemy.current_stats.current_hp -= dmg
    print(f"{gracz.name} zadaje {dmg} obrażeń {enemy.name}")
    # Logika ataku przeciwnika
    if enemy.current_stats.current_hp > 0:
        dmg = enemy.current_stats.atk
        gracz.current_stats.current_hp -= dmg
        print(f"{enemy.name} zadaje {dmg} obrażeń {gracz.name}")

# === Ładowanie danych JSON ===

def wczytaj_json(sciezka):
    with open(sciezka, 'r', encoding='utf-8') as plik:
        return json.load(plik)

# === Uruchomienie gry ===

def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("RPG Game")
    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill((0, 0, 0))
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == '__main__':
    main()
