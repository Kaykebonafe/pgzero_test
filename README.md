# 🚀 Super Ninja Mario Sonic Copy: A Pygame Zero Platformer

## 🌟 Overview

This is a simple yet complete 2D platformer game built from scratch using the **Pygame Zero** framework. The project was developed to showcase proficiency in Python object-oriented programming, game physics implementation, and adherence to strict project constraints.

It features classic jump-and-run mechanics, enemy AI, collectible items, custom sprite animation logic, and a full main menu system.

## ✨ Features

  * **Genre:** Classic **Platformer** (Side-scrolling jump-and-run).
  * **Custom Physics:** Implemented gravity, velocity, jumping, and precise collision detection using the base `pygame.Rect` class.
  * **Object-Oriented Design (OOD):** Built on custom classes (`AnimatedSprite`, `Player`, `Enemy`, `Coin`, `Button`) for clear structure and code reusability.
  * **Rich Animation System:** Includes dedicated logic for handling multi-frame sprite animations for idle, walking, and jumping states, ensuring characters are never static.
      * *Note: If image assets are unavailable, the code intelligently switches to custom **geometric drawing** with procedural animation.*
  * **Menu & Audio Control:** A fully functional main menu with options to Start Game, Exit, and toggle **Music** and **Sound Effects** independently.
  * **Enemies & Hazards:** Features patrolled enemies with restricted movement areas, and implements player invincibility frames after taking damage.
  * **Win/Loss Conditions:** The player wins by collecting all coins in the level and loses when all lives are exhausted.

-----

## 🛠️ Installation & Setup

### Requirements

This project strictly adheres to the rule of using only core Python modules and the official Pygame Zero library.

  * **Python 3**
  * **Pygame Zero:**

<!-- end list -->

```bash
pip install pgzero
```

### Running the Game

1.  Place the `game.py` file (your code) inside a main project folder.
2.  Create an `images` folder and a `sounds` folder inside the project root for the assets (if you wish to use sprites and audio).
3.  Execute the game using the `pgzrun` command:

<!-- end list -->

```bash
pgzrun game.py
```

-----

## 🕹️ Controls

| Key | Action |
| :--- | :--- |
| **Left / A** | Move Left |
| **Right / D** | Move Right |
| **Space / Up** | Jump (only works when on the ground) |
| **Space (on Game Over)** | Return to Main Menu |
| **Mouse Click** | Interact with Menu Buttons |

-----

## 📂 Project Structure (Expected Assets)

To run the game with full sprite and audio features, the following file structure and assets (not included here) are expected:

```
/super-platformer/
├── game.py            # The main game code
├── images/            # Pygame Zero asset folder for images
│   ├── player/
│   │   ├── idle/
│   │   ├── walk/
│   │   └── jump/
│   ├── enemies/
│   └── coins/
└── sounds/            # Pygame Zero asset folder for sounds
    ├── background.ogg # Background music
    ├── jump.ogg       # Jump sound effect
    ├── coin.ogg       # Coin collection sound effect
    └── hit.ogg        # Damage/hit sound effect
```

-----

## 📝 Code Highlights (Technical)

The core movement and state logic is managed by the following classes:

  * **`AnimatedSprite`:** The base class handling position (`rect`), velocity (`vx`, `vy`), gravity, and animation timer updates (`update_animation`).
  * **`Player`:** Extends `AnimatedSprite` with input handling, jump logic, invincibility management, and complex state-based sprite selection.
  * **`Enemy`:** Extends `AnimatedSprite` with simple horizontal AI that checks fixed patrol boundaries (`patrol_left`, `patrol_right`) to reverse direction.
  * **`check_collision_y`:** A key method ensuring that collisions are handled differently based on the vertical direction (`vy`), correctly setting `on_ground = True` when landing.
