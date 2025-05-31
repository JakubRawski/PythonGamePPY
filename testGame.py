import pygame
import sys
import os
import random

"""
WAZNE to jest test dzialania pygame
jest to w duzej czesci inspirowane innym projektem 
nie jest to finalny projekt (a przynajmniej mam taka nadzieje)
program pokazuje dzialanie silnika na 1 przeciwniku w jednej krainie
program nie pokazuje dystrybucji lootu i obslugi ekwipunku (pokazuje w playground)
"""
from Engine import *

# --- Pygame Initialization ---
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

pygame.display.set_caption("Test Game - Combat Panel")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 0, 0)
GREEN = (0, 200, 0)
BLUE = (0, 0, 200)
YELLOW = (255, 255, 0)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (50, 50, 50)
TRANSPARENT_BLACK = (0, 0, 0, 150)  # For overlay

# Fonts
FONT_SM = pygame.font.Font(None, 24)
FONT_MD = pygame.font.Font(None, 36)
FONT_LG = pygame.font.Font(None, 48)

# --- Game Data Loading (adjust world_id as needed) ---
print("Loading game data...")
load_game_data(world_id='0')

# Get player and enemy instances (assuming they exist after loading)
player_char = PLAYERS_DB.get("0p001")
enemy_rat = ENEMIES_DB.get("0e001")

if not player_char or not enemy_rat:
    print("Error: Player or Enemy data not loaded. Exiting.")
    pygame.quit()
    sys.exit()

# Set up player inventory for testing purposes
if not player_char.inventory:
    player_char.inventory = [
        Bagpack(num_slots=5, accepted_kinds=['consumable']),
        Bagpack(num_slots=5, accepted_kinds=['equipment']),
        Bagpack(num_slots=5, accepted_kinds=['material'])
    ]

# Add a health potion and a dummy item/spell to player's inventory for testing item/spell usage
if "0i002" in ITEMS_DB:
    hp_potion_data = ITEMS_DB["0i002"]
    spell_id = hp_potion_data.get("spell")
    linked_spell = SPELLS_DB.get(spell_id) if spell_id else None
    hp_potion_instance = Consumable(
        hp_potion_data["id"],
        hp_potion_data["name"],
        hp_potion_data["price"],
        linked_spell or Spell("dummy_heal", 0, Statystyki()),  # Fallback dummy spell
        quantity=2
    )
    if not player_char.inventory[0].add_item(hp_potion_instance):
        print("Could not add health potion to player's inventory.")
else:
    print("Health Potion (0i002) not found in ITEMS_DB. Cannot add to inventory.")

# Add a dummy spell to the player if they don't have any, for testing "Użyj spella"
if not player_char.spells:
    player_char.spells.append(SPELLS_DB.get("0s001") or Spell("dummy_attack_spell", 0, Statystyki()))
    player_char.spells.append(SPELLS_DB.get("0s002") or Spell("dummy_heal_spell", 0, Statystyki()))

# Prepare combat participants for walka function (reset stats)
gracze_in_combat = [player_char]
enemies_in_combat = [enemy_rat]
for gracz in gracze_in_combat:
    gracz.reset_stats_for_combat()


# --- UI Elements Configuration ---

# Character display positions
PLAYER_POS = (150, 200)  # Adjusted for better spacing
ENEMY_POS = (SCREEN_WIDTH - 150, 200)  # Adjusted
INITIATIVE_OFFSET_Y = -70  # Offset for initiative symbol
IMAGE_MAX_SIZE = 128  # Max width/height for character images

# Health/Mana bar dimensions
BAR_WIDTH = 120
BAR_HEIGHT = 15
BAR_OFFSET_Y = 80  # Below character image

# Action Panel
ACTION_PANEL_RECT = pygame.Rect(50, SCREEN_HEIGHT - 180, SCREEN_WIDTH - 100, 150)
ACTION_BUTTON_HEIGHT = 30
ACTION_BUTTON_MARGIN = 10

# Sub-option panel (for items, spells, targets)
SUB_PANEL_RECT = pygame.Rect(ACTION_PANEL_RECT.x, ACTION_PANEL_RECT.y,
                             ACTION_PANEL_RECT.width, ACTION_PANEL_RECT.height)

# Initiative symbol (a simple arrow or star)
INITIATIVE_SYMBOL = FONT_LG.render(">", True, YELLOW)  # Can be an image later
INITIATIVE_SYMBOL_RECT = INITIATIVE_SYMBOL.get_rect()


# --- Helper Functions for Drawing ---

def draw_character_panel(surface, character, position, has_initiative):
    """Draws character image, HP/Mana bars, and initiative symbol, scaling images."""
    # Draw character image
    if character.image:
        img_width, img_height = character.image.get_size()
        # Calculate scale factor to fit within IMAGE_MAX_SIZE
        scale_factor = IMAGE_MAX_SIZE / max(img_width, img_height, 1)
        scaled_image = pygame.transform.scale(character.image,
                                              (int(img_width * scale_factor), int(img_height * scale_factor)))
        img_box = pygame.Rect(
            position[0] - IMAGE_MAX_SIZE // 2,
            position[1] - IMAGE_MAX_SIZE // 2,
            IMAGE_MAX_SIZE,
            IMAGE_MAX_SIZE
        )
        scaled_rect = scaled_image.get_rect(center=img_box.center)
        surface.blit(scaled_image, scaled_rect)
    else:
        # Placeholder if image not loaded
        pygame.draw.rect(surface, LIGHT_GRAY, (
        position[0] - IMAGE_MAX_SIZE // 2, position[1] - IMAGE_MAX_SIZE // 2, IMAGE_MAX_SIZE, IMAGE_MAX_SIZE))
        text_surf = FONT_SM.render("NO IMG", True, GREEN)
        text_rect = text_surf.get_rect(center=position)
        surface.blit(text_surf, text_rect)

    # Draw Name
    name_surf = FONT_MD.render(character.name, True, BLACK)
    name_rect = name_surf.get_rect(center=(position[0], position[1] + BAR_OFFSET_Y - 20))
    surface.blit(name_surf, name_rect)

    # Draw HP Bar
    hp_percent = character.current_stats.current_hp / max(character.current_stats.max_hp, 1)
    hp_bar_width = int(BAR_WIDTH * hp_percent)
    hp_bar_x = position[0] - BAR_WIDTH // 2
    hp_bar_y = position[1] + BAR_OFFSET_Y
    pygame.draw.rect(surface, RED, (hp_bar_x, hp_bar_y, hp_bar_width, BAR_HEIGHT))
    pygame.draw.rect(surface, BLACK, (hp_bar_x, hp_bar_y, BAR_WIDTH, BAR_HEIGHT), 2)  # Border

    # HP text
    hp_text = FONT_SM.render(
        f"HP: {max(0, int(character.current_stats.current_hp))}/{int(character.current_stats.max_hp)}", True, WHITE)
    hp_text_rect = hp_text.get_rect(center=(position[0], hp_bar_y + BAR_HEIGHT // 2))
    surface.blit(hp_text, hp_text_rect)

    # Draw Mana Bar (if character has mana)
    if character.current_stats.max_mana > 0:
        mana_percent = character.current_stats.current_mana / max(character.current_stats.max_mana, 1)
        mana_bar_width = int(BAR_WIDTH * mana_percent)
        mana_bar_x = position[0] - BAR_WIDTH // 2
        mana_bar_y = hp_bar_y + BAR_HEIGHT + 5
        pygame.draw.rect(surface, BLUE, (mana_bar_x, mana_bar_y, mana_bar_width, BAR_HEIGHT))
        pygame.draw.rect(surface, BLACK, (mana_bar_x, mana_bar_y, BAR_WIDTH, BAR_HEIGHT), 2)  # Border

        # Mana text
        mana_text = FONT_SM.render(
            f"MP: {int(character.current_stats.current_mana)}/{int(character.current_stats.max_mana)}", True, WHITE)
        mana_text_rect = mana_text.get_rect(center=(position[0], mana_bar_y + BAR_HEIGHT // 2))
        surface.blit(mana_text, mana_text_rect)

    # Draw Initiative Symbol
    if has_initiative:
        initiative_symbol_pos = (position[0] - INITIATIVE_SYMBOL_RECT.width // 2, position[1] + INITIATIVE_OFFSET_Y)
        surface.blit(INITIATIVE_SYMBOL, initiative_symbol_pos)


def draw_panel_buttons(surface, rect, options, selected_index, title=None, row_height=ACTION_BUTTON_HEIGHT):
    """Draws a panel with a list of selectable buttons."""
    pygame.draw.rect(surface, DARK_GRAY, rect)
    pygame.draw.rect(surface, BLACK, rect, 3)  # Border

    if title:
        title_surf = FONT_MD.render(title, True, WHITE)
        title_rect = title_surf.get_rect(center=(rect.centerx, rect.y + ACTION_BUTTON_MARGIN + 10))
        surface.blit(title_surf, title_rect)
        start_y = rect.y + ACTION_BUTTON_MARGIN + title_surf.get_height() + 10
    else:
        start_y = rect.y + ACTION_BUTTON_MARGIN

    buttons_rects = []
    for i, option_text in enumerate(options):
        button_y = start_y + i * (row_height + ACTION_BUTTON_MARGIN)
        button_rect = pygame.Rect(rect.x + ACTION_BUTTON_MARGIN,
                                  button_y,
                                  rect.width - 2 * ACTION_BUTTON_MARGIN,
                                  row_height)

        color = BLUE if i == selected_index else LIGHT_GRAY
        pygame.draw.rect(surface, color, button_rect)
        pygame.draw.rect(surface, BLACK, button_rect, 2)

        text_surf = FONT_SM.render(option_text, True, BLACK)
        text_rect = text_surf.get_rect(center=button_rect.center)
        surface.blit(text_surf, text_rect)
        buttons_rects.append(button_rect)
    return buttons_rects


def show_message_overlay(surface, message, duration_ms):
    """Displays a temporary message overlay."""
    overlay_rect = pygame.Rect(0, SCREEN_HEIGHT // 2 - 50, SCREEN_WIDTH, 100)
    overlay_surf = pygame.Surface(overlay_rect.size, pygame.SRCALPHA)
    overlay_surf.fill(TRANSPARENT_BLACK)  # Semi-transparent background

    text_surf = FONT_MD.render(message, True, WHITE)
    text_rect = text_surf.get_rect(center=(overlay_rect.width // 2, overlay_rect.height // 2))
    overlay_surf.blit(text_surf, text_rect)

    surface.blit(overlay_surf, overlay_rect.topleft)
    pygame.display.flip()
    pygame.time.wait(duration_ms)


# --- Game States ---
STATE_PLAYER_TURN = 0
STATE_SELECT_ITEM = 1
STATE_SELECT_SPELL = 2
STATE_SELECT_TARGET = 3
STATE_ENEMY_TURN = 4
STATE_COMBAT_END = 5  # New state for when combat is over


# --- Game Loop ---
def main():
    running = True
    turn_order = [player_char, enemy_rat]  # Simple turn order
    current_turn_index = 0
    current_actor = turn_order[current_turn_index]

    gracze_in_combat_list = [player_char]  # List for targeting
    enemies_in_combat_list = [enemy_rat]  # List for targeting
    all_targets_list = gracze_in_combat_list + enemies_in_combat_list

    current_state = STATE_PLAYER_TURN  # Start with player's turn
    main_action_options = ["Atakuj", "Użyj przedmiotu", "Użyj spella", "Ucieknij"]
    selected_main_action_index = 0

    # Variables for sub-selections
    selected_item = None
    selected_spell = None
    selected_sub_option_index = 0
    current_sub_options = []
    current_sub_option_type = ""  # "items", "spells", "targets"

    # Reset stats for combat before loop starts, just in case
    player_char.reset_stats_for_combat()

    while running:
        # Check for combat end condition (all enemies defeated or player defeated)
        if all(e.current_stats.current_hp <= 0 for e in enemies_in_combat_list):
            current_state = STATE_COMBAT_END
            show_message_overlay(SCREEN, "Wygrałeś!", 2000)
            running = False
        elif player_char.current_stats.current_hp <= 0:
            current_state = STATE_COMBAT_END
            show_message_overlay(SCREEN, "Porażka!", 2000)
            running = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if current_state == STATE_PLAYER_TURN or \
                    current_state == STATE_SELECT_ITEM or \
                    current_state == STATE_SELECT_SPELL or \
                    current_state == STATE_SELECT_TARGET:  # Only process input during player's turn states
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:  # Go back one step
                        if current_state == STATE_SELECT_ITEM or current_state == STATE_SELECT_SPELL:
                            current_state = STATE_PLAYER_TURN
                            selected_sub_option_index = 0
                            current_sub_options = []
                        elif current_state == STATE_SELECT_TARGET:
                            if selected_main_action_index == 0:  # Attack -> back to main actions
                                current_state = STATE_PLAYER_TURN
                            elif selected_main_action_index == 1:  # Item -> back to item selection
                                current_state = STATE_SELECT_ITEM
                                selected_sub_option_index = 0
                                # Refresh item list
                                current_sub_options = [f"{item.name} (x{item.quantity})" for item in
                                                       player_char.inventory[0].get_items() if item.quantity > 0]
                            elif selected_main_action_index == 2:  # Spell -> back to spell selection
                                current_state = STATE_SELECT_SPELL
                                selected_sub_option_index = 0
                                # Refresh spell list
                                current_sub_options = [f"{spell.id}" for spell in player_char.spells]
                        else:  # Main actions
                            running = False  # Exit game if no other state to go back to

                    if current_state != STATE_PLAYER_TURN:  # For sub-options, use UP/DOWN
                        if event.key == pygame.K_UP:
                            selected_sub_option_index = (selected_sub_option_index - 1) % len(current_sub_options)
                        elif event.key == pygame.K_DOWN:
                            selected_sub_option_index = (selected_sub_option_index + 1) % len(current_sub_options)
                    else:  # For main actions, use LEFT/RIGHT
                        if event.key == pygame.K_LEFT:
                            selected_main_action_index = (selected_main_action_index - 1) % len(main_action_options)
                        elif event.key == pygame.K_RIGHT:
                            selected_main_action_index = (selected_main_action_index + 1) % len(main_action_options)

                    if event.key == pygame.K_RETURN:
                        if current_state == STATE_PLAYER_TURN:
                            if selected_main_action_index == 0:  # Atakuj
                                print(f"{current_actor.name} selected: Atakuj")
                                alive_enemies = [e for e in enemies_in_combat_list if e.current_stats.current_hp > 0]
                                if not alive_enemies:
                                    print("No enemies to attack.")
                                    show_message_overlay(SCREEN, "Brak celów!", 1000)
                                    continue  # Stay in player turn
                                current_sub_options = [
                                    f"{e.name} (HP: {int(e.current_stats.current_hp)}/{int(e.current_stats.max_hp)})"
                                    for e in alive_enemies]
                                print("Test1")
                                current_sub_option_type = "targets"
                                selected_sub_option_index = 0
                                current_state = STATE_SELECT_TARGET
                            elif selected_main_action_index == 1:  # Użyj przedmiotu
                                print(f"{current_actor.name} selected: Użyj przedmiotu")
                                consumables = [item for item in player_char.inventory[0].get_items() if
                                               item.quantity > 0]  # Filter only available
                                if not consumables:
                                    print("Brak przedmiotów jednorazowych.")
                                    show_message_overlay(SCREEN, "Brak przedmiotów!", 1000)
                                    continue  # Stay in player turn
                                current_sub_options = [f"{item.name} (x{item.quantity})" for item in consumables]
                                current_sub_option_type = "items"
                                selected_sub_option_index = 0
                                current_state = STATE_SELECT_ITEM
                            elif selected_main_action_index == 2:  # Użyj spella
                                print(f"{current_actor.name} selected: Użyj spella")
                                if not player_char.spells:
                                    print("Nie posiadasz żadnych zaklęć.")
                                    show_message_overlay(SCREEN, "Brak zaklęć!", 1000)
                                    continue  # Stay in player turn
                                current_sub_options = [f"{spell.id}" for spell in player_char.spells]
                                current_sub_option_type = "spells"
                                selected_sub_option_index = 0
                                current_state = STATE_SELECT_SPELL
                            elif selected_main_action_index == 3:  # Ucieknij
                                print(f"{current_actor.name} selected: Ucieknij!")
                                # Implement escape logic here
                                # For simplicity, just end combat
                                show_message_overlay(SCREEN, "Uciekasz z walki!", 2000)
                                running = False  # End game for now

                        elif current_state == STATE_SELECT_ITEM:
                            consumables = [item for item in player_char.inventory[0].get_items() if item.quantity > 0]
                            if 0 <= selected_sub_option_index < len(consumables):
                                selected_item = consumables[selected_sub_option_index]
                                print(f"Wybrano przedmiot: {selected_item.name}")
                                current_sub_options = [
                                    f"{t.name} (HP: {int(t.current_stats.current_hp)}/{int(t.current_stats.max_hp)})"
                                    for t in all_targets_list]
                                current_sub_option_type = "targets"
                                selected_sub_option_index = 0
                                current_state = STATE_SELECT_TARGET
                            else:
                                print("Nie wybrano przedmiotu.")  # Should not happen with current logic

                        elif current_state == STATE_SELECT_SPELL:
                            if 0 <= selected_sub_option_index < len(player_char.spells):
                                selected_spell = player_char.spells[selected_sub_option_index]
                                print(f"Wybrano zaklęcie: {selected_spell.id}")
                                current_sub_options = [
                                    f"{t.name} (HP: {int(t.current_stats.current_hp)}/{int(t.current_stats.max_hp)})"
                                    for t in all_targets_list]
                                current_sub_option_type = "targets"
                                selected_sub_option_index = 0
                                current_state = STATE_SELECT_TARGET
                            else:
                                print("Nie wybrano zaklęcia.")  # Should not happen

                        elif current_state == STATE_SELECT_TARGET:
                            if current_sub_option_type == "targets":
                                if selected_main_action_index == 0:  # Atakuj
                                    alive_enemies = [e for e in enemies_in_combat_list if
                                                     e.current_stats.current_hp > 0]
                                    if not alive_enemies:
                                        show_message_overlay(SCREEN, "Brak celów do ataku!", 1000)
                                        continue  # Stay in current state

                                    # Ensure selected_sub_option_index is valid for alive_enemies
                                    if 0 <= selected_sub_option_index < len(alive_enemies):
                                        target = alive_enemies[selected_sub_option_index]
                                    else:
                                        # This case should ideally not happen if UI is correctly updating,
                                        # but good for safety
                                        show_message_overlay(SCREEN, "Nieprawidłowy cel!", 1000)
                                        continue

                                    # Perform attack and get details
                                    attack_result = player_char._wybierz_cel_i_atakuj([target])
                                    if attack_result:
                                        message = (
                                            f"{attack_result['attacker']} zaatakował {attack_result['target']} "
                                            f"za {int(attack_result['damage'])} dmg. "
                                            f"({int(attack_result['target_hp_left'])} HP zostało)"
                                        )
                                        print(message)
                                        show_message_overlay(SCREEN, message, 1500)
                                    else:
                                        # Should only happen if _wybierz_cel_i_atakuj returns None
                                        show_message_overlay(SCREEN, "Atak nie powiódł się.", 1500)

                                elif selected_main_action_index == 1:  # Item usage
                                    target = all_targets_list[selected_sub_option_index]
                                    if selected_item:
                                        # Manually call apply and decrease quantity
                                        if selected_item.spell:
                                            selected_item.spell.apply(current_actor,target)
                                            selected_item.quantity -= 1
                                            message = f"Użyto {selected_item.name} na {target.name}. {target.name} HP: {int(target.current_stats.current_hp)}"
                                            print(message)
                                            show_message_overlay(SCREEN, message, 1500)
                                        else:
                                            message = f"Przedmiot {selected_item.name} nie ma zaklęcia."
                                            print(message)
                                            show_message_overlay(SCREEN, message, 1500)
                                    else:
                                        message = "Nie wybrano przedmiotu do użycia."
                                        print(message)
                                        show_message_overlay(SCREEN, message, 1500)

                                elif selected_main_action_index == 2:  # Spell usage
                                    target = all_targets_list[selected_sub_option_index]
                                    if selected_spell:
                                        # Manually call apply
                                        selected_spell.apply(player_char, target)  # Spells need caster and target
                                        message = f"Rzucono {selected_spell.id} na {target.name}. {target.name} HP: {int(target.current_stats.current_hp)}"
                                        print(message)
                                        show_message_overlay(SCREEN, message, 1500)
                                    else:
                                        message = "Nie wybrano zaklęcia do użycia."
                                        print(message)
                                        show_message_overlay(SCREEN, message, 1500)

                                # Reset selected item/spell after use
                                selected_item = None
                                selected_spell = None

                                # End player turn and transition to enemy turn
                                current_state = STATE_ENEMY_TURN
                                selected_sub_option_index = 0  # Reset for next turn
                                current_sub_options = []  # Clear sub options

                            else:
                                print("Invalid target selection.")  # Should not happen

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1 and current_state != STATE_ENEMY_TURN:  # Left click, only if not enemy turn
                        if current_state == STATE_PLAYER_TURN:
                            # Check if a main action button was clicked
                            # We need to draw the buttons *before* checking clicks to get their rects
                            temp_buttons_rects = []
                            start_x = ACTION_PANEL_RECT.x + ACTION_BUTTON_MARGIN
                            start_y = ACTION_PANEL_RECT.y + ACTION_BUTTON_MARGIN
                            for i, option in enumerate(main_action_options):
                                button_rect = pygame.Rect(start_x + i * (BAR_WIDTH + ACTION_BUTTON_MARGIN),
                                                          start_y,
                                                          BAR_WIDTH, ACTION_BUTTON_HEIGHT)
                                temp_buttons_rects.append(button_rect)

                            for i, button_rect in enumerate(temp_buttons_rects):
                                if button_rect.collidepoint(event.pos):
                                    selected_main_action_index = i
                                    # Simulate RETURN key press for selected action
                                    event_return = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
                                    pygame.event.post(event_return)
                                    break
                        else:  # In sub-selection states (items, spells, targets)
                            # We need to draw the buttons *before* checking clicks to get their rects
                            temp_buttons_rects = draw_panel_buttons(SCREEN, SUB_PANEL_RECT, current_sub_options,
                                                                    selected_sub_option_index, title="Wybierz...")
                            for i, button_rect in enumerate(temp_buttons_rects):
                                if button_rect.collidepoint(event.pos):
                                    selected_sub_option_index = i
                                    # Simulate RETURN key press for sub-selection
                                    event_return = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
                                    pygame.event.post(event_return)
                                    break

        # --- Game Logic (Outside Event Loop for continuous actions) ---
        if current_state == STATE_ENEMY_TURN:
            show_message_overlay(SCREEN, f"Tura {enemy_rat.name}...", 1000)
            if enemy_rat.current_stats.current_hp > 0:
                # Enemy AI: Simple random attack
                if random.random() < 0.7:  # 70% chance to basic attack
                    target_player = gracze_in_combat_list[0]  # Assuming only one player
                    if target_player.current_stats.current_hp > 0:
                        enemy_rat._wybierz_cel_i_atakuj([target_player])  # Enemy attacks player
                        message = f"{enemy_rat.name} zaatakował {target_player.name}! {target_player.name} HP: {int(target_player.current_stats.current_hp)}"
                        print(message)
                        show_message_overlay(SCREEN, message, 1500)
                    else:
                        print("Player already defeated, enemy can't attack.")
                else:  # 30% chance to cast a random spell if available
                    if enemy_rat.spells:
                        spell_to_cast = random.choice(enemy_rat.spells)
                        target_player = gracze_in_combat_list[0]
                        if target_player.current_stats.current_hp > 0:
                            spell_to_cast.apply(enemy_rat, target_player)  # Enemy casts spell on player
                            message = f"{enemy_rat.name} użył {spell_to_cast.id} na {target_player.name}! {target_player.name} HP: {int(target_player.current_stats.current_hp)}"
                            print(message)
                            show_message_overlay(SCREEN, message, 1500)
                        else:
                            print("Player already defeated, enemy can't cast spell.")
                    else:
                        # If no spells, default to basic attack
                        target_player = gracze_in_combat_list[0]
                        if target_player.current_stats.current_hp > 0:
                            enemy_rat._wybierz_cel_i_atakuj([target_player])
                            message = f"{enemy_rat.name} zaatakował {target_player.name}! {target_player.name} HP: {int(target_player.current_stats.current_hp)}"
                            print(message)
                            show_message_overlay(SCREEN, message, 1500)
                        else:
                            print("Player already defeated, enemy can't attack.")
            else:
                print("Enemy already defeated, skipping turn.")

            # After enemy action, switch back to player's turn
            if current_state != STATE_COMBAT_END:  # Don't switch if combat ended
                current_state = STATE_PLAYER_TURN
                selected_main_action_index = 0  # Reset selection for player

        # --- Drawing ---
        SCREEN.fill(WHITE)  # Background

        # Draw player and enemy panels
        draw_character_panel(SCREEN, player_char, PLAYER_POS,
                             current_actor == player_char and current_state != STATE_ENEMY_TURN)
        draw_character_panel(SCREEN, enemy_rat, ENEMY_POS,
                             current_actor == enemy_rat and current_state == STATE_ENEMY_TURN)

        # Draw action panel or sub-option panel based on state
        if current_state == STATE_PLAYER_TURN:
            # Main action buttons (draw directly for positioning)
            start_x = ACTION_PANEL_RECT.x + ACTION_BUTTON_MARGIN
            start_y = ACTION_PANEL_RECT.y + ACTION_BUTTON_MARGIN
            for i, option in enumerate(main_action_options):
                button_rect = pygame.Rect(start_x + i * (BAR_WIDTH + ACTION_BUTTON_MARGIN),
                                          start_y,
                                          BAR_WIDTH, ACTION_BUTTON_HEIGHT)

                color = BLUE if i == selected_main_action_index else LIGHT_GRAY
                pygame.draw.rect(SCREEN, color, button_rect)
                pygame.draw.rect(SCREEN, BLACK, button_rect, 2)

                text_surf = FONT_SM.render(option, True, BLACK)
                text_rect = text_surf.get_rect(center=button_rect.center)
                SCREEN.blit(text_surf, text_rect)
        elif current_state == STATE_SELECT_ITEM:
            draw_panel_buttons(SCREEN, SUB_PANEL_RECT, current_sub_options, selected_sub_option_index,
                               title="Wybierz przedmiot")
        elif current_state == STATE_SELECT_SPELL:
            draw_panel_buttons(SCREEN, SUB_PANEL_RECT, current_sub_options, selected_sub_option_index,
                               title="Wybierz zaklęcie")
        elif current_state == STATE_SELECT_TARGET:
            draw_panel_buttons(SCREEN, SUB_PANEL_RECT, current_sub_options, selected_sub_option_index,
                               title="Wybierz cel")

        pygame.display.flip()  # Update the full display Surface to the screen

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()