import pgzrun
import math
from pygame import Rect

# Game constants
WIDTH = 800
HEIGHT = 600
GRAVITY = 0.5  # Defines the vertical acceleration applied to sprites each frame.
JUMP_STRENGTH = -12  # Initial upward velocity applied during a jump (negative for up).

# Game state
game_state = "menu"  # Current state of the game: "menu", "playing", "gameover", "win".
music_enabled = True
sounds_enabled = True
score = 0
lives = 3
game_over_message = ""  # Text displayed on game over/win screens.
music_started = False  # Flag to ensure background music is played only once.

# Sprite loading flag (set to True to use image sprites, False for geometric shapes)
USE_SPRITES = True  # Determines whether to load image files or use simple shapes for rendering.


class AnimatedSprite:
    """Base class for animated sprites with movement and basic physics.

    Handles rectangular collision bounds, velocity, gravity, and simple
    frame-based animation timing.
    """

    def __init__(self, x, y, width, height):
        # The collision and position rectangle for the sprite.
        self.rect = Rect(x, y, width, height)
        self.vx = 0  # Horizontal velocity.
        self.vy = 0  # Vertical velocity.
        self.on_ground = False  # Flag indicating if the sprite is currently touching a platform.
        self.animation_frame = 0  # Counter for the current animation frame index.
        self.animation_timer = 0  # Accumulator for animation timing.
        self.animation_speed = 0.15  # Time (in seconds) between animation frame changes.
        self.facing_right = True  # Direction the sprite is facing for drawing/flipping.

    def update_animation(self, dt):
        """Updates the animation frame based on the elapsed time (dt)."""
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            # Advance to the next frame. The modulo operation happens during draw.
            self.animation_frame += 1

    def apply_gravity(self):
        """Applies gravity to the vertical velocity if the sprite is airborne."""
        if not self.on_ground:
            self.vy += GRAVITY
            # Clamp the max falling speed to prevent excessive velocity (terminal velocity).
            if self.vy > 15:
                self.vy = 15

    def move(self, platforms):
        """Moves the sprite and checks for collisions with platforms."""
        # Horizontal movement and collision check.
        self.rect.x += self.vx
        self.check_collision_x(platforms)

        # Vertical movement and collision check.
        self.rect.y += self.vy
        self.check_collision_y(platforms)

    def check_collision_x(self, platforms):
        """Adjusts sprite position if a horizontal collision occurs."""
        for platform in platforms:
            if self.rect.colliderect(platform):
                # Correct position based on direction of movement.
                if self.vx > 0:
                    self.rect.right = platform.left  # Collided moving right.
                elif self.vx < 0:
                    self.rect.left = platform.right  # Collided moving left.

    def check_collision_y(self, platforms):
        """Adjusts position, resets vertical velocity, and sets on_ground flag."""
        self.on_ground = False
        for platform in platforms:
            if self.rect.colliderect(platform):
                # Check for collision from above (landing).
                if self.vy > 0:
                    self.rect.bottom = platform.top
                    self.vy = 0
                    self.on_ground = True
                # Check for collision from below (head-bumping).
                elif self.vy < 0:
                    self.rect.top = platform.bottom
                    self.vy = 0


class Player(AnimatedSprite):
    """Player character with jump and movement logic, health, and invincibility."""

    def __init__(self, x, y):
        # Player specific size (40x50)
        super().__init__(x, y, 40, 50)
        self.jump_requested = False  # Input flag to trigger a jump on the next update.
        self.move_left = False  # Input flag for continuous left movement.
        self.move_right = False  # Input flag for continuous right movement.
        self.alive = True
        self.invincible = False  # Flag for temporary invulnerability after taking damage.
        self.invincible_timer = 0  # Countdown timer for invincibility period.

        # Try to load sprites
        self.has_sprites = False
        self.idle_sprites = []
        self.walk_sprites = []
        self.jump_sprites = []

        if USE_SPRITES:
            try:
                # Load idle animation (10 frames)
                self.idle_sprites = []
                for i in range(10):
                    # NOTE: 'Actor' is globally available in Pygame Zero.
                    actor = Actor(f"player/idle/idle__{i:03d}")
                    self.idle_sprites.append(actor)

                # Load run animation (10 frames)
                self.walk_sprites = []
                for i in range(10):
                    actor = Actor(f"player/walk/run__{i:03d}")
                    self.walk_sprites.append(actor)

                # Load jump animation (10 frames)
                self.jump_sprites = []
                for i in range(10):
                    actor = Actor(f"player/jump/jump__{i:03d}")
                    self.jump_sprites.append(actor)

                self.has_sprites = True
                print("Player sprites loaded successfully!")
            except Exception as e:
                print(f"Player sprites not found: {e}")
                print("Using geometric shapes instead")

    def update(self, dt, platforms):
        """Updates the player's physics, state, and animation."""
        if not self.alive:
            return  # Stop updating if the player has died.

        # Update invincibility countdown.
        if self.invincible:
            self.invincible_timer -= dt
            if self.invincible_timer <= 0:
                self.invincible = False

        # Handle horizontal input and set velocity/facing direction.
        self.vx = 0
        if self.move_left:
            self.vx = -4
            self.facing_right = False
        if self.move_right:
            self.vx = 4
            self.facing_right = True

        # Execute jump if requested and on the ground.
        if self.jump_requested and self.on_ground:
            self.vy = JUMP_STRENGTH
            # Play jump sound only if enabled.
            if sounds_enabled:
                try:
                    sounds.jump.play()
                except:
                    pass
            self.jump_requested = False

        # Physics application (Gravity and Movement/Collision)
        self.apply_gravity()
        self.move(platforms)

        # Update animation only if moving horizontally or airborne.
        if self.vx != 0 or not self.on_ground:
            self.update_animation(dt)

        # Death condition: falling below the screen.
        if self.rect.y > HEIGHT + 100:
            self.alive = False

    def take_damage(self):
        """Applies damage to the player if not currently invincible.

        Returns:
            bool: True if damage was successfully applied, False otherwise.
        """
        if not self.invincible:
            self.invincible = True
            self.invincible_timer = 2.0  # Set a 2.0 second invincibility period.
            return True
        return False

    def draw(self):
        """Draws the player, handling sprite selection and invincibility flashing."""
        # Invincibility flashing effect: skip drawing every other frame.
        if self.invincible and int(self.invincible_timer * 10) % 2 == 0:
            return

        if self.has_sprites:
            # Choose animation based on state
            if not self.on_ground:
                # Use jump animation when airborne.
                actor = self.jump_sprites[(int(self.animation_frame) % len(self.jump_sprites))]
            elif abs(self.vx) > 0:
                # Use walk animation when moving horizontally.
                actor = self.walk_sprites[(int(self.animation_frame) % len(self.walk_sprites))]
            else:
                # Default to idle animation.
                actor = self.idle_sprites[(int(self.animation_frame) % len(self.idle_sprites))]

            # Position the Actor (Pygame Zero's image object) based on the Rect's center.
            actor.center = self.rect.center

            # Flip the sprite horizontally if facing left.
            actor.flip_x = not self.facing_right

            actor.draw()
            # ---------------------------

        else:
            self.draw_geometric()

    def draw_geometric(self):
        """Draws a placeholder shape for the player when sprites are disabled."""
        idle_colors = [(100, 150, 255), (120, 170, 255)]
        walk_colors = [(100, 150, 255), (110, 160, 255),
                       (120, 170, 255), (110, 160, 255)]

        if abs(self.vx) > 0:
            frame_count = len(walk_colors)
            color = walk_colors[int(self.animation_frame) % frame_count]
        else:
            frame_count = len(idle_colors)
            color = idle_colors[int(self.animation_frame) % frame_count]

        screen.draw.filled_rect(self.rect, color)

        eye_y = self.rect.y + 15
        if int(self.animation_frame) % 20 == 0:
            screen.draw.line((self.rect.x + 12, eye_y),
                           (self.rect.x + 18, eye_y), (0, 0, 0))
            screen.draw.line((self.rect.x + 22, eye_y),
                           (self.rect.x + 28, eye_y), (0, 0, 0))
        else:
            screen.draw.filled_circle((self.rect.x + 15, eye_y), 3, (0, 0, 0))
            screen.draw.filled_circle((self.rect.x + 25, eye_y), 3, (0, 0, 0))

        leg_width = 6
        if abs(self.vx) > 0:
            leg_offset = int(math.sin(self.animation_frame * 3) * 5)
            screen.draw.filled_rect(
                Rect(self.rect.x + 10, self.rect.bottom - 10 + leg_offset,
                     leg_width, 10), (50, 100, 200))
            screen.draw.filled_rect(
                Rect(self.rect.x + 24, self.rect.bottom - 10 - leg_offset,
                     leg_width, 10), (50, 100, 200))
        else:
            screen.draw.filled_rect(
                Rect(self.rect.x + 10, self.rect.bottom - 10, leg_width, 10),
                (50, 100, 200))
            screen.draw.filled_rect(
                Rect(self.rect.x + 24, self.rect.bottom - 10, leg_width, 10),
                (50, 100, 200))


class Enemy(AnimatedSprite):
    """Patrolling enemy that moves back and forth between two defined points."""

    def __init__(self, x, y, patrol_left, patrol_right):
        # Enemy specific size (35x40)
        super().__init__(x, y, 35, 40)
        self.patrol_left = patrol_left  # The minimum X coordinate for patrolling (left boundary).
        self.patrol_right = patrol_right  # The maximum X coordinate for patrolling (right boundary).
        self.speed = 2
        self.vx = self.speed  # Start moving right.

        # Try to load sprites
        self.has_sprites = False
        self.sprites = []

        if USE_SPRITES:
            try:
                self.sprites = []
                for i in range(1, 11):
                    actor = Actor(f"enemies/walk_{i}")
                    self.sprites.append(actor)
                self.has_sprites = True
                print("Enemy sprites loaded successfully!")
            except Exception as e:
                print(f"Enemy sprites not found: {e}")
                print("Using geometric shapes instead")

    def update(self, dt, platforms):
        """Updates the enemy's movement logic, physics, and animation."""
        # Check and reverse direction at the patrol boundaries.
        if self.rect.left <= self.patrol_left:
            self.vx = self.speed
            self.facing_right = True
        elif self.rect.right >= self.patrol_right:
            self.vx = -self.speed
            self.facing_right = False

        self.apply_gravity()
        self.move(platforms)
        self.update_animation(dt)

    def draw(self):
        """Draws the enemy, handling sprite selection and flipping."""
        if self.has_sprites:
            # Select the current animation frame using modulo.
            actor = self.sprites[int(self.animation_frame) % len(self.sprites)]

            actor.center = self.rect.center

            # Flip the sprite based on current horizontal direction.
            actor.flip_x = not self.facing_right

            actor.draw()
            # ---------------------------
        else:
            self.draw_geometric()

    def draw_geometric(self):
        """Draws a placeholder shape for the enemy when sprites are disabled."""
        body_colors = [(255, 100, 100), (255, 120, 120), (255, 110, 110)]
        frame_count = len(body_colors)
        color = body_colors[int(self.animation_frame) % frame_count]

        screen.draw.filled_rect(self.rect, color)

        spike_offset = int(math.sin(self.animation_frame * 2) * 3)
        spike_positions = [self.rect.x + 5, self.rect.x + 15, self.rect.x + 25]
        spike_size = 8
        for spike_x in spike_positions:
            spike_rect = Rect(spike_x, self.rect.y + spike_offset - 5,
                            spike_size, spike_size)
            screen.draw.filled_rect(spike_rect, (150, 50, 50))

        eye_x_offset = int(math.sin(self.animation_frame) * 2)
        screen.draw.filled_circle(
            (self.rect.x + 10 + eye_x_offset, self.rect.y + 20),
            2, (255, 255, 0))
        screen.draw.filled_circle(
            (self.rect.x + 25 + eye_x_offset, self.rect.y + 20),
            2, (255, 255, 0))

        mouth_y = self.rect.y + 28
        mouth_width = int(abs(math.sin(self.animation_frame * 1.5)) * 10) + 5
        screen.draw.line((self.rect.centerx - mouth_width//2, mouth_y),
                        (self.rect.centerx + mouth_width//2, mouth_y),
                        (100, 0, 0))


class Coin:
    """Collectible coin with animation and proximity-based collision."""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 12
        self.collected = False  # State of the coin.
        self.animation_frame = 0  # Counter for the coin's spinning animation.

        # Try to load sprites
        self.has_sprites = False
        self.sprites = []

        if USE_SPRITES:
            try:
                self.sprites = []
                for i in range(1, 11):
                    actor = Actor(f"coins/gold_{i}")
                    self.sprites.append(actor)
                self.has_sprites = True
                print("Coin sprites loaded successfully!")
            except Exception as e:
                print(f"Coin sprites not found: {e}")
                print("Using geometric shapes instead")

    def update(self, dt):
        """Updates the coin's animation frame."""
        # Increase frame counter faster (dt * 5) for a quicker animation cycle.
        self.animation_frame += dt * 5

    def check_collision(self, player):
        """Checks for collision with the player using distance (circular collision).

        Returns:
            bool: True if the coin was collected, False otherwise.
        """
        if self.collected:
            return False
        # Calculate distance between coin center and player center.
        dist = math.sqrt((self.x - player.rect.centerx)**2 +
                        (self.y - player.rect.centery)**2)
        # Check if centers are closer than the sum of radii/approximate hitboxes.
        if dist < self.radius + 20:
            self.collected = True
            return True
        return False

    def draw(self):
        """Draws the coin if it hasn't been collected."""
        if self.collected:
            return

        if self.has_sprites:
            # Select the current animation frame using modulo.
            actor = self.sprites[int(self.animation_frame) % len(self.sprites)]

            actor.center = (self.x, self.y)

            actor.draw()
        else:
            self.draw_geometric()

    def draw_geometric(self):
        """Draws a simple 3D-spinning effect using scaling/width change."""
        scale = abs(math.cos(self.animation_frame))
        width = int(self.radius * 2 * scale)
        if width < 2:
            width = 2

        screen.draw.filled_circle((self.x, self.y), self.radius, (255, 215, 0))
        inner_rect = Rect(self.x - width//2, self.y - self.radius,
                         width, self.radius * 2)
        screen.draw.filled_rect(inner_rect, (255, 255, 100))


class Button:
    """Clickable button for menu screens."""

    def __init__(self, x, y, width, height, text):
        self.rect = Rect(x, y, width, height)
        self.text = text
        self.hovered = False  # State used to change color when the mouse is over it.

    def update(self, mouse_pos):
        """Checks if the mouse is hovering over the button."""
        self.hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, mouse_pos):
        """Checks if the given mouse position is inside the button's area."""
        return self.rect.collidepoint(mouse_pos)

    def draw(self):
        """Draws the button with hover effect and centered text."""
        color = (100, 200, 100) if self.hovered else (80, 180, 80)
        screen.draw.filled_rect(self.rect, color)
        screen.draw.rect(self.rect, (255, 255, 255))
        screen.draw.text(self.text, center=(self.rect.centerx, self.rect.centery),
                        fontsize=30, color=(255, 255, 255))


# Game objects
player = Player(100, 400)
enemies = []
coins = []
platforms = []
buttons = []
mouse_pos = (0, 0)

# Create menu buttons
buttons.append(Button(300, 200, 200, 50, "Start Game"))
buttons.append(Button(300, 280, 200, 50, "Toggle Music"))
buttons.append(Button(300, 360, 200, 50, "Toggle Sounds"))
buttons.append(Button(300, 440, 200, 50, "Exit"))


def init_level():
    """Initializes/resets all game objects and state variables for a new level."""
    global player, enemies, coins, platforms, score, game_over_message, lives

    player = Player(100, 400)  # Recreate player at starting position.
    enemies.clear()  # Clear all lists of game objects.
    coins.clear()
    platforms.clear()
    score = 0
    lives = 3
    game_over_message = ""

    # Define platform geometry.
    platforms.append(Rect(0, 550, 800, 50))  # Ground platform.
    platforms.append(Rect(150, 450, 200, 20))
    platforms.append(Rect(450, 400, 200, 20))
    platforms.append(Rect(200, 300, 150, 20))
    platforms.append(Rect(500, 250, 180, 20))
    platforms.append(Rect(300, 175, 150, 20))

    enemies.append(Enemy(160, 400, 150, 330))
    enemies.append(Enemy(460, 350, 450, 630))
    enemies.append(Enemy(510, 200, 500, 660))

    coins.append(Coin(250, 420))
    coins.append(Coin(550, 370))
    coins.append(Coin(275, 270))
    coins.append(Coin(590, 220))
    coins.append(Coin(375, 150))
    coins.append(Coin(700, 500))


def update(dt):
    """Main game loop update function (called automatically by pgzrun).

    Handles game state transitions, input processing, and updates all game objects.

    Args:
        dt (float): Delta time, the time elapsed since the last update call.
    """
    global game_state, game_over_message, score, lives, music_started

    # Start background music if not started and enabled.
    if not music_started and music_enabled:
        try:
            music.play("background")
            music_started = True
        except:
            pass

    if game_state == "playing":
        # Map keyboard inputs to player movement flags (allows for diagonal movement).
        player.move_left = keyboard.left or keyboard.a
        player.move_right = keyboard.right or keyboard.d

    if game_state == "menu":
        # Update button hover states in the menu.
        for button in buttons:
            button.update(mouse_pos)

    elif game_state == "playing":
        player.update(dt, platforms)

        # Update enemy movement and coin animation/collision.
        for enemy in enemies:
            enemy.update(dt, platforms)

        for coin in coins:
            coin.update(dt)
            if coin.check_collision(player):
                score += 10
                if sounds_enabled:
                    try:
                        sounds.coin.play()
                    except:
                        pass

        # Check for player-enemy collision only if the player is alive.
        if player.alive:
            for enemy in enemies:
                if player.rect.colliderect(enemy.rect):
                    # Attempt to apply damage and check if it was successful (not invincible).
                    if player.take_damage():
                        lives -= 1
                        if sounds_enabled:
                            try:
                                sounds.hit.play()
                            except:
                                pass
                        # Check for game over after losing a life.
                        if lives <= 0:
                            player.alive = False
                            game_over_message = "Game Over! No lives left!"

        # Win condition: all coins collected and player is alive.
        if all(coin.collected for coin in coins) and player.alive:
            game_state = "win"
            game_over_message = f"You Won! Score: {score}"

        # Transition to game over state if the player dies from falling or running out of lives.
        if not player.alive:
            game_state = "gameover"


def draw():
    """Main game loop draw function (called automatically by pgzrun).

    Renders the scene based on the current game state.
    """
    screen.clear()

    if game_state == "menu":
        screen.fill((30, 30, 60))
        screen.draw.text("SUPER NINJA MARIO SONIC COPY", center=(400, 100),
                        fontsize=60, color=(255, 255, 255))
        screen.draw.text(f"Music: {'ON' if music_enabled else 'OFF'}  "
                        f"Sounds: {'ON' if sounds_enabled else 'OFF'}",
                        center=(400, 520), fontsize=25, color=(200, 200, 200))

        for button in buttons:
            button.draw()

    elif game_state in ["playing", "gameover", "win"]:
        screen.fill((135, 206, 235))

        for platform in platforms:
            # Simple platform rendering.
            screen.draw.filled_rect(platform, (100, 200, 100))
            screen.draw.rect(platform, (80, 180, 80))

        # Draw objects in layer order (coins, then enemies, then player).
        for coin in coins:
            coin.draw()

        for enemy in enemies:
            enemy.draw()

        if player.alive:
            player.draw()

        # Draw HUD elements (Score, Coin count).
        screen.draw.text(f"Score: {score}", (20, 20), fontsize=30, color=(255, 255, 255))
        screen.draw.text(f"Coins: {sum(1 for c in coins if not c.collected)}/{len(coins)}",
                        (20, 60), fontsize=30, color=(255, 255, 255))

        # Draw 'lives' as small hearts.
        for i in range(lives):
            heart_x = 20 + i * 35
            heart_y = 100
            # Simple heart shape drawing.
            screen.draw.filled_circle((heart_x, heart_y), 8, (255, 0, 0))
            screen.draw.filled_circle((heart_x + 10, heart_y), 8, (255, 0, 0))
            screen.draw.filled_circle((heart_x + 5, heart_y + 10), 10, (255, 0, 0))

        # Draw game over/win message overlay.
        if game_state in ["gameover", "win"]:
            screen.draw.text(game_over_message, center=(400, 250),
                           fontsize=50, color=(255, 255, 0))
            screen.draw.text("Press SPACE to return to menu", center=(400, 320),
                           fontsize=30, color=(255, 255, 255))


def on_key_down(key):
    """Handles key press events."""
    global game_state

    if game_state == "playing":
        # Request a jump on space or up arrow press.
        if key == keys.SPACE or key == keys.UP:
            player.jump_requested = True
    elif game_state in ["gameover", "win"]:
        # Return to menu from end screens.
        if key == keys.SPACE:
            game_state = "menu"


def on_mouse_down(pos):
    """Handles mouse click events, primarily for menu buttons."""
    global game_state, music_enabled, sounds_enabled, music_started

    if game_state == "menu":
        for i, button in enumerate(buttons):
            if button.is_clicked(pos):
                # Handle button actions based on index.
                if i == 0:  # Start Game button
                    init_level()
                    game_state = "playing"
                    # Ensure music starts if enabled on game start.
                    if music_enabled and not music_started:
                        try:
                            music.play("background")
                            music_started = True
                        except:
                            pass
                elif i == 1:  # Toggle Music
                    music_enabled = not music_enabled
                    # Control music playback based on new state.
                    if music_enabled:
                        try:
                            music.play("background")
                            music_started = True
                        except:
                            pass
                    else:
                        music.stop()
                        music_started = False
                elif i == 2:  # Toggle Sounds
                    sounds_enabled = not sounds_enabled
                elif i == 3:  # Exit
                    exit()


def on_mouse_move(pos):
    """Updates the global mouse position for use in button hover checks."""
    global mouse_pos
    mouse_pos = pos


# Start the Pygame Zero application.
pgzrun.go()