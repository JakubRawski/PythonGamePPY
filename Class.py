import random

import pygame


#Statystyki

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
        self.max_hp = 0
        self.current_hp = 0
        self.max_mana = 0
        self.current_mana = 0
        self.shield = 0
        self.atk = 0
        self.crit_rate = 0
        self.crit_dmg = 0
        self.element_dmg = ElementDmg()
        self.defense = 0
        self.element_res = ElementDmg()
        self.def_shred = 0
        self.heal_bonus = 0
        self.atkspd = 0

# Itemy i ekwipunek (bagi i loot)

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
    def __init__(self, num_slots):
        self.num_slots = num_slots
        self.items = [None] * num_slots # tworzenie pustych slotow

    def add_item(self, item):
        for i, slot_item in enumerate(self.items):
            if slot_item is None:
                self.items[i] = item
                return True # Item zlostal zlozony
        return False # Pelne sloty

    def remove_item(self, item_to_remove):
        for i, item in enumerate(self.items):
            if item == item_to_remove:
                self.items[i] = None # usuwanie znalezionego itemu
                return True
        return False

    def get_items(self):
        #zwraca liste przedmiotow
        return [item for item in self.items if item is not None]


class Bagpack(Bag):
    def __init__(self, num_slots, accepted_kinds):
        super().__init__(num_slots)
        self.accepted_kinds = accepted_kinds # Lista tagow ktore plecak moze przyjmowac

class LootTable: # No longer inherits from Bag
    def __init__(self, slots_data):
        self.slots_data = slots_data  # Przechowuj w JSON: [{"item": "id", "chance": 0.5}]


class Armor:
    def __init__(self):
        self.helmet = None
        self.chest = None
        self.legs = None
        self.boots = None
        self.weapon = None
        self.off_hand = None
        self.wand = None

#Spell

class Spell:
    def __init__(self, id, tick, statystyki, additive=True, harm=True, direct=False):
        self.id = id
        self.tick = tick # 1 tick to 1 tura, 0 tick to instant spell.
        self.stats = statystyki
        self.additive = additive # True dla dodawania, False dla mnozenia
        self.harm = harm # True dla damage/debuff, False dla heal/buff
        # TODO dodac rozne opcje przelicznika w wolnej chwili (czyli jak starczy czasu)
        # obecnie rozroznia prosty dmg i buffing
        self.direct = direct # True dla zmiany HP bezposrednio, False dla wyliczenia damage/heal

    def apply(self, caster, target):
        print(f"Rzucanie spell {self.id} na {target.name}...")

        if self.direct:
            # zmiana HP bezposrednio
            if self.harm:
                # Direct obrazenia
                damage_dealt = abs(self.stats.current_hp) # wartosc bezwgledna bo podawane na razie jest na minusie
                target.current_stats.current_hp -= damage_dealt
                print(f"{target.name} otrzymuje {damage_dealt:.2f} obrażeń bezpośrednich.")
            else:
                # Direct leczenie, zabezpieczony overhealing
                healing_done = self.stats.current_hp
                target.current_stats.current_hp += healing_done
                target.current_stats.current_hp = min(target.current_stats.current_hp, target.current_stats.max_hp)
                print(f"{target.name} zostaje uleczony o {healing_done:.2f} HP.")
        else:
            # Smieszne liczenie TODO rozszerzyc to
            if self.harm:
                total_damage = 0
                # Uwglednia bazowy atat castera
                total_damage += 0.5 * caster.current_stats.atk

                # Apply element damage from spell's stats
                for elem, elem_val in self.stats.element_dmg.__dict__.items():
                    if elem_val > 0: # Liczy tylko dla zywiolow niezerowych
                        total_damage += 0.5 * elem_val

                # Liczenie z armorem TODO dodac formule
                final_damage = max(0, total_damage - target.current_stats.defense)
                target.current_stats.current_hp -= final_damage
                print(f"{target.name} otrzymuje {final_damage:.2f} obrażeń.")

            # Bezposrednie dodawanie statow (heali/buff/debuff) - unika current_healt i poprawnie czyta ele_dmg
            for stat_name, value in self.stats.__dict__.items():
                #print(f"{stat_name} {value}") TODO usun debugging
                if stat_name == 'element_dmg':
                    # TODO zmienic bo debuffuje dmg ele przeciwnika XDDDD
                    for elem, elem_val in value.__dict__.items():
                        current_elem_val = getattr(target.current_stats.element_dmg, elem)
                        if self.additive:
                            setattr(target.current_stats.element_dmg, elem, current_elem_val + elem_val)
                        else:
                            setattr(target.current_stats.element_dmg, elem, current_elem_val * (1 + elem_val))
                elif stat_name == 'current_hp' and not self.harm: # nie direct leczenie
                    healing_done = value
                    target.current_stats.current_hp += healing_done
                    target.current_stats.current_hp = min(target.current_stats.current_hp, target.current_stats.max_hp)
                    print(f"{target.name} zostaje uleczony o {healing_done:.2f} HP.")

                elif stat_name == 'element_res':
                    # TODO zmienic bo to rozwiazanie tylko unika erroru XDDDD
                    for elem, elem_val in value.__dict__.items():
                        current_elem_val = getattr(target.current_stats.element_res, elem)
                        if self.additive:
                            setattr(target.current_stats.element_res, elem, current_elem_val + elem_val)
                        else:
                            setattr(target.current_stats.element_res, elem, current_elem_val * (1 + elem_val))
                else: # reszta prostych buffow bez przelicznikow
                    current_stat_val = getattr(target.current_stats, stat_name)
                    if self.additive:

                        setattr(target.current_stats, stat_name, current_stat_val + value)
                    else:
                        setattr(target.current_stats, stat_name, current_stat_val * value)


        # Dodawanie buffow do listy
        if self.tick > 0:
            target.buffs.append({'spell': self, 'current_tick': self.tick, 'applied_stats': Statystyki()})
            print(f"{target.name} otrzymał buff/debuff '{self.id}' na {self.tick} tury.")


# Postacie

class NPC:
    def __init__(self, ID, name, icon, level, base_stats, gold, armor, spells):
        self.ID = ID
        self.name = name
        self.icon = icon  # Path obrazka
        self.image = None  # Obiekt image
        self.level = level
        self.base_stats = base_stats
        self.current_stats = base_stats
        self.gold = gold
        self.armor = armor
        self.spells = spells # Lista spelli
        self.buffs = []  # Lista buffow debuffow
        self.pivot = 0  # poczatkowy pivot
    def load_image(self, image_path):
        # Laduje zdjecie

        try:
            self.image = pygame.image.load(image_path).convert_alpha()
        except pygame.error as e:
            print(f"Error loading image {image_path}: {e}")
            self.image = None  # Set to None if loading fails

    def apply_buffs(self):
        # naklada buffy oraz usuwa nieaktualne
        # lista buffow do usuniecia
        buffs_to_remove = []
        for buff_info in self.buffs:
            spell = buff_info['spell']

            print(f"Applying effects of '{spell.id}' on {self.name} (Tick: {buff_info['current_tick']})...")

            if spell.direct:
                if spell.harm:
                    damage_dealt = abs(spell.stats.current_hp) # analogicznie jak wyzej z ujemnym znakiem TODO zmienic na cos lepszego
                    self.current_stats.current_hp -= damage_dealt
                    print(f"{self.name} otrzymuje {damage_dealt:.2f} obrażeń z '{spell.id}'.")
                else:
                    healing_done = spell.stats.current_hp
                    self.current_stats.current_hp += healing_done
                    self.current_stats.current_hp = min(self.current_stats.current_hp, self.current_stats.max_hp)
                    print(f"{self.name} zostaje uleczony o {healing_done:.2f} HP z '{spell.id}'.")
            else:
                # TODO zmienic podobnie jak w spelle
                for stat_name, value in spell.stats.__dict__.items():
                    if stat_name == 'element_dmg':
                        for elem, elem_val in value.__dict__.items():
                            current_elem_val = getattr(self.current_stats.element_dmg, elem)
                            if spell.additive:
                                setattr(self.current_stats.element_dmg, elem, current_elem_val + elem_val)
                            else:
                                setattr(self.current_stats.element_dmg, elem, current_elem_val * (1 + elem_val))
                    elif stat_name != 'current_hp':  # unika current hp bo liczone bylo wczesniej
                        current_stat_val = getattr(self.current_stats, stat_name)
                        if spell.additive:
                            setattr(self.current_stats, stat_name, current_stat_val + value)
                        else:
                            setattr(self.current_stats, stat_name, current_stat_val * value)

                # Sprawdzanie HoT
                if not spell.harm and spell.stats.current_hp > 0 and not spell.direct:
                    healing_done = spell.stats.current_hp
                    self.current_stats.current_hp += healing_done
                    self.current_stats.current_hp = min(self.current_stats.current_hp, self.current_stats.max_hp)
                    print(f"{self.name} zostaje uleczony o {healing_done:.2f} HP z '{spell.id}'.")

            buff_info['current_tick'] -= 1
            if buff_info['current_tick'] <= 0:
                buffs_to_remove.append(buff_info)
                print(f"Buff/debuff '{spell.id}' na {self.name} wygasł.")
                # TODO cofnac buffy po obecnie oba sa pernamentne
                # dla add dodac buff co reverse robi na statach (mnozenie *1)
                # obecne rozwiazanie naklada co tick a nie utrzymuje

        # Usuwa nieaktywne buffy
        for expired_buff in buffs_to_remove:
            # TODO tutaj dac logike reverse buffow przed remove
            self.buffs.remove(expired_buff)



class Enemy(NPC):
    def __init__(self, ID, name, icon, level, base_stats, gold, armor, spells, loot_table):
        super().__init__(ID, name, icon, level, base_stats, gold, armor, spells)
        self.loot_table = loot_table
    def _wybierz_cel_i_atakuj(self, przeciwnicy):
        #TODO to jest basic atak, na arzie zostawic dopoki AI bedzie gotowe
        zywi_przeciwnicy = [u for u in przeciwnicy if u.current_stats.current_hp > 0]
        if not zywi_przeciwnicy:
            print("Brak przeciwników do ataku.")
            return "no_target"

        cel = self._wybierz_cel(zywi_przeciwnicy)
        if cel:
            dmg = self.current_stats.atk
            cel.current_stats.current_hp -= dmg
            hp_left = max(cel.current_stats.current_hp, 0)
            print(f"{self.name} atakuje {cel.name} za {dmg} dmg. ({hp_left} HP left)")
            return "atak"
        return "cancel"
    def _wybierz_cel(self, possible_targets):
        # sluzy do targetu daje liste i graczy i przeciwnikow (tak, mozna zabic swojego i buffowac przeciwnika)
        # to nie bug tylko feature ktory chce zachowac
        if not possible_targets:
            print("Brak dostępnych celów.")
            return None

        print("Wybierz cel:")
        for i, target in enumerate(possible_targets):
            print(f"{i + 1}. {target.name} (HP: {target.current_stats.current_hp}/{target.current_stats.max_hp})")

        while True:
            try:
                return random.choice(possible_targets)
            except ValueError:
                print("Nieprawidłowe wejście. Wprowadź numer.")
class Gracz(NPC):
    def __init__(self, ID, name, icon, level, base_stats, gold, armor, spells, inventory, menu):
        super().__init__(ID, name, icon, level, base_stats, gold, armor, spells)
        self.inventory = inventory
        self.menu = menu

    def wybierz(self, gracze, enemy):
        print(f"\n{self.name}, co chcesz zrobić?")
        options = ["1. Atakuj", "2. Użyj przedmiotu", "3. Użyj spella", "4. Ucieknij"]
        for option in options:
            print(option)

        choice = input("Wybierz akcję (1-4): ")

        if choice == '1':  # Atakuj
            return self._wybierz_cel_i_atakuj(enemy)
        elif choice == '2':  # Użyj przedmiotu
            return self._wybierz_przedmiot_i_cel(gracze, enemy)
        elif choice == '3':  # Użyj spella
            return self._wybierz_spell_i_cel(gracze, enemy)
        elif choice == '4':  # Ucieknij
            print(f"{self.name} próbuje uciec z walki!")
            return "ucieczka"
        else:
            print("Nieprawidłowy wybór. Spróbuj ponownie.")
            return self.wybierz(gracze, enemy)  # Rekursja dopoki gracz poprawnie wybierze opcje

    def _wybierz_cel(self, possible_targets):
        # sluzy do targetu daje liste i graczy i przeciwnikow (tak, mozna zabic swojego i buffowac przeciwnika)
        # to nie bug tylko feature ktory chce zachowac
        if not possible_targets:
            print("Brak dostępnych celów.")
            return None
        print("Wybierz cel:")
        for i, target in enumerate(possible_targets):
            print(f"{i + 1}. {target.name} (HP: {target.current_stats.current_hp}/{target.current_stats.max_hp})")

        while True:
            try:
                target_choice = int(input(f"Wybierz cel (1-{len(possible_targets)}): "))
                if 1 <= target_choice <= len(possible_targets):
                    return possible_targets[target_choice - 1]
                else:
                    print("Nieprawidłowy numer celu. Spróbuj ponownie.")
            except ValueError:
                print("Nieprawidłowe wejście. Wprowadź numer.")

    def _wybierz_cel_i_atakuj(self, targets):

        if not targets:
            print("Brak celów do ataku.")
            return


        # jest to lista ale ma 1 wartosc
        target_to_attack = targets[0]

        # Prosty atak TODO zmienic
        damage_dealt = max(0, self.current_stats.atk - target_to_attack.current_stats.defense)
        target_to_attack.current_stats.current_hp -= damage_dealt

        # Zeruje hp gdy jest ujemne
        if target_to_attack.current_stats.current_hp < 0:
            target_to_attack.current_stats.current_hp = 0

        # dict z info co i jak
        return {
            "attacker": self.name,
            "target": target_to_attack.name,
            "damage": damage_dealt,
            "target_hp_left": target_to_attack.current_stats.current_hp
        }

    def _wybierz_przedmiot_i_cel(self, gracze, enemy):
        # wybor itemu
        consumables = [item for item in self.inventory if isinstance(item, Consumable) and item.quantity > 0]
        if not consumables:
            print("Brak przedmiotów jednorazowych w ekwipunku.")
            return "no_item"

        print("Dostępne przedmioty:")
        for i, item in enumerate(consumables):
            print(f"{i + 1}. {item.name} (Ilość: {item.quantity})")

        while True:
            try:
                item_choice = int(input(f"Wybierz przedmiot (1-{len(consumables)}) lub 0 aby anulować: "))
                if item_choice == 0:
                    return "cancel"
                if 1 <= item_choice <= len(consumables):
                    selected_item = consumables[item_choice - 1]
                    break
                else:
                    print("Nieprawidłowy numer przedmiotu. Spróbuj ponownie.")
            except ValueError:
                print("Nieprawidłowe wejście. Wprowadź numer.")

        if selected_item.spell:
            print("Wybierz cel dla przedmiotu:")
            possible_targets = gracze + enemy
            target = self._wybierz_cel(possible_targets)
            if target:
                selected_item.spell.apply(target)
                selected_item.quantity -= 1
                return "item_used"
        else:
            print(f"Przedmiot {selected_item.name} nie ma przypisanego zaklęcia.")
            return "no_effect"
        return "cancel"

    def _wybierz_spell_i_cel(self, gracze, enemy):
        #rzucanie spella
        if not self.spells:
            print("Nie posiadasz żadnych zaklęć.")
            return "no_spell"

        print("Dostępne zaklęcia:")
        for i, spell in enumerate(self.spells):
            print(f"{i + 1}. Zaklęcie ID: {spell.id}")

        while True:
            try:
                spell_choice = int(input(f"Wybierz zaklęcie (1-{len(self.spells)}) lub 0 aby anulować: "))
                if spell_choice == 0:
                    return "cancel"
                if 1 <= spell_choice <= len(self.spells):
                    selected_spell = self.spells[spell_choice - 1]
                    break
                else:
                    print("Nieprawidłowy numer zaklęcia. Spróbuj ponownie.")
            except ValueError:
                print("Nieprawidłowe wejście. Wprowadź numer.")

        print("Wybierz cel dla zaklęcia:")
        possible_targets = gracze + enemy
        target = self._wybierz_cel(possible_targets)
        if target:
            selected_spell.apply(self,target)
            return "spell_used"
        return "cancel"

    def reset_stats_for_combat(self):
        #metoda pomocnicza do resetu statow przed runda
        self.current_stats = Statystyki()
        self.current_stats.max_hp = self.base_stats.max_hp
        self.current_stats.current_hp = self.base_stats.current_hp
        self.current_stats.max_mana = self.base_stats.max_mana
        self.current_stats.current_mana = self.base_stats.current_mana
        self.current_stats.shield = self.base_stats.shield
        self.current_stats.atk = self.base_stats.atk
        self.current_stats.crit_rate = self.base_stats.crit_rate
        self.current_stats.crit_dmg = self.base_stats.crit_dmg
        self.current_stats.element_dmg = ElementDmg(
            fire=self.base_stats.element_dmg.fire,
            frost=self.base_stats.element_dmg.frost,
            water=self.base_stats.element_dmg.water,
            air=self.base_stats.element_dmg.air,
            earth=self.base_stats.element_dmg.earth,
            nature=self.base_stats.element_dmg.nature,
            electr=self.base_stats.element_dmg.electr
        )
        self.current_stats.defense = self.base_stats.defense
        self.current_stats.element_res = ElementDmg(
            fire=self.base_stats.element_res.fire,
            frost=self.base_stats.element_res.frost,
            water=self.base_stats.element_res.water,
            air=self.base_stats.element_res.air,
            earth=self.base_stats.element_res.earth,
            nature=self.base_stats.element_res.nature,
            electr=self.base_stats.element_res.electr
        )
        self.current_stats.def_shred = self.base_stats.def_shred
        self.current_stats.heal_bonus = self.base_stats.heal_bonus
        self.current_stats.atkspd = self.base_stats.atkspd
        self.buffs = []  # Czysci buffy debuffy
        print(
            f"{self.name}: Statystyki zresetowane do bazowych. HP: {self.current_stats.current_hp}/{self.current_stats.max_hp}")


class Menu:
    def __init__(self):
        self.stage = 'start'  # pomoc przy grafice, atak, invertory, przygoda itp
        # TODO do dopisania
