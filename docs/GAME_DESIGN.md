# Game Design Document: Triwersum Roguelike

## 1. Elevator Pitch

A GUI-based roguelike adventure set in the rich, philosophical world of Triwersum. Players will navigate a world governed by the flow of Mocaż and Dopa, making choices through dialogue, engaging in tactical, skill-based combat, and managing mystical equipment, all through a simple, window-driven, point-and-click interface.

## 2. Core Gameplay Loop

The game is structured around a classic roguelike loop:

1.  **Explore:** The player moves on a 2D grid map, discovering locations, NPCs, and enemies inspired by the Triwersum lore.
2.  **Interact:** The player engages with characters and events through a dialogue window with clickable options. Choices will affect faction relations and quest outcomes.
3.  **Combat:** The player fights enemies (e.g., Wrogowie Funkcji, corrupted beings) in a turn-based combat system. Skills will be based on the manipulation of Mocaż.
4.  **Loot & Progress:** The player finds and manages equipment (lore artifacts like a *Lufka* or *Rdzeń Mocażowy*) and develops their character's abilities.
5.  **Death & Meta-Progression:** Upon defeat, the player's soul might return to the *Czyściec Mocażu*, potentially unlocking new starting abilities or knowledge for the next run, embodying the theme of cycles and rebirth.

## 3. Lore Integration

The unique lore of Triwersum is the foundation of the game's mechanics.

*   **Player Character:** A *Mocażysta*, a practitioner of Mocaż, perhaps a novice from a known school like *Szkoła Bonglord-Hazet* or a neutral wanderer.

*   **Core Attributes:**
    *   **Gęstość Dopy (GD):** Functions as Health or Stamina. Represents the character's spiritual and physical integrity.
    *   **Strumień Mocażu (SM):** The primary resource (Mana/Energy) used to power combat skills and other abilities.
    *   **Współczynnik Generacji Kopcia (WGK):** A "corruption" or "debuff" stat. High WGK could lead to negative events, attract dangerous enemies, or cause *Płucna Zgnilizna*-like debuffs. It can be increased by using forbidden techniques or interacting with tainted artifacts.

*   **Factions:** The player's actions will influence their standing with factions like the *Siewcy Paradygmatu*, *Wrogowie Funkcji*, and *Ród Wujogniotnych*, unlocking different quests, dialogues, and items.

*   **Items & Equipment:** Artifacts from the lore will be usable items.
    *   *Lufka*: A tool for channeling Mocaż, could provide buffs but increase WGK if not properly maintained ("cleaned").
    *   *Rdzeń Mocażowy*: A consumable that restores Strumień Mocażu.
    *   *Fartuch Wuja*: Armor providing protection against *kopciowy* damage.

## 4. User Interface (UI) Windows

The game will be controlled via a set of interconnected windows:

*   **Main Window:** The primary container for all other UI elements.
*   **Map View:** A grid displaying the player, NPCs, locations, and enemies. The player moves by clicking on adjacent tiles.
*   **Character Sheet:** A window displaying the player's attributes (GD, SM, WGK), equipped items, and learned skills.
*   **Inventory Window:** A grid for managing all carried items.
*   **Dialogue Window:** Displays NPC portraits, text, and a list of clickable player responses.
*   **Combat Window:** Shows the player and enemies, a log of combat actions, and a clickable list of available combat skills.

## 5. Technology Stack

*   **Language:** Python 3
*   **GUI Library:** `tkinter` (part of the Python standard library, ideal for the requested window-based interface).
*   **Project Structure:**
    *   `docs/`: For design documents.
    *   `src/`: For all Python source code.
    *   `assets/`: For any future images, data files, or other non-code assets.
