import pygame
import random
import sys

# Initialize Pygame
pygame.init()

# Game constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRAVITY = 0.5
JUMP_POWER = 0.7
MAX_JUMP_HOLD = 30  # Maximum frames player can hold jump
JUMP_FORWARD_SPEED = 4  # Speed to move forward when jumping
PLATFORM_WIDTH = 100
PLATFORM_HEIGHT = 20
PLATFORM_GAP_MIN = 50  # Minimum gap between platforms
PLATFORM_GAP_MAX = 200  # Maximum gap between platforms
PLATFORM_HEIGHT_VARIATION = 60  # How much platforms can vary in height

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_GRAY = (34, 34, 34)
PLAYER_COLOR = (52, 152, 219)  # Blue
PLATFORM_COLOR = (39, 174, 96)  # Green
PLATFORM_REACHED_COLOR = (46, 204, 113)  # Brighter green
DEBUG_COLOR = (255, 255, 255)  # White
GOLD = (255, 215, 0)

# Create the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Codename 2")
clock = pygame.time.Clock()

# Font
debug_font = pygame.font.SysFont("Arial", 10)
score_font = pygame.font.SysFont("Arial", 24)
game_over_font = pygame.font.SysFont("Arial", 36)


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 30
        self.velocity_x = 0
        self.velocity_y = 0
        self.is_on_platform = False
        self.current_platform_id = None
        self.color = PLAYER_COLOR
        
    def update(self):
        # Apply gravity
        self.velocity_y += GRAVITY
        
        # Update position
        self.x += self.velocity_x
        self.y += self.velocity_y
        
        # When player lands on a platform, stop horizontal movement
        if self.is_on_platform and not is_jumping:
            self.velocity_x = 0
            
    def draw(self, surface, camera_offset):
        pygame.draw.rect(surface, self.color, (self.x - camera_offset, self.y, self.width, self.height))
        
        # Draw player hitbox (for debugging)
        pygame.draw.rect(surface, (255, 0, 0), (self.x - camera_offset, self.y, self.width, self.height), 1)
        
    def reset(self, x, y):
        self.x = x
        self.y = y
        self.velocity_x = 0
        self.velocity_y = 0
        self.is_on_platform = True


class Platform:
    def __init__(self, platform_id, x, y, width, height):
        self.id = platform_id
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        
    def draw(self, surface, camera_offset, reached):
        color = PLATFORM_REACHED_COLOR if reached else PLATFORM_COLOR
        pygame.draw.rect(surface, color, (self.x - camera_offset, self.y, self.width, self.height))
        
        # Draw platform hitbox (for debugging)
        pygame.draw.rect(surface, (255, 255, 0), (self.x - camera_offset, self.y, self.width, self.height), 1)


def get_random_gap():
    return random.uniform(PLATFORM_GAP_MIN, PLATFORM_GAP_MAX)


def get_random_height(previous_height):
    # Calculate the maximum height the player can reach
    max_jump_height = (MAX_JUMP_HOLD * JUMP_POWER) * 4
    
    min_height = previous_height - PLATFORM_HEIGHT_VARIATION
    max_height = previous_height + PLATFORM_HEIGHT_VARIATION
    
    # Ensure the height is within screen bounds
    min_height = max(100, min_height)
    max_height = min(SCREEN_HEIGHT - 100, max_height)
    
    # Ensure the height difference is within the player's jumping capability
    max_height = min(max_height, previous_height + max_jump_height)
    
    return random.uniform(min_height, max_height)


def check_platform_collisions(player, platforms):
    # Reset platform status
    player.is_on_platform = False
    player.current_platform_id = None
    
    for platform in platforms:
        # Only check if player is falling
        if player.velocity_y >= 0:
            # Check if player's feet are at platform level
            player_bottom = player.y + player.height
            platform_top = platform.y
            
            # Check if player is within platform width
            player_left = player.x
            player_right = player.x + player.width
            platform_left = platform.x
            platform_right = platform.x + platform.width
            
            # More precise collision detection
            prev_y = player_bottom - player.velocity_y
            if (player_right > platform_left and 
                player_left < platform_right and 
                player_bottom >= platform_top and 
                prev_y <= platform_top + 5):  # Small tolerance
                
                # Place player on top of platform
                player.y = platform.y - player.height
                player.velocity_y = 0
                player.is_on_platform = True
                player.velocity_x = 0  # Stop horizontal movement when landing
                player.current_platform_id = platform.id
                
                # Check if this is a new platform
                if platform.id not in platforms_reached:
                    platforms_reached.append(platform.id)
                    
                return True
                
    return False


def draw_debug_info(surface, player, platforms_reached_count, camera_offset, top_score):
    # Show player status
    on_platform_text = f"On Platform: {'Yes (ID: ' + str(player.current_platform_id) + ')' if player.is_on_platform else 'No'}"
    position_text = f"Position: ({int(player.x)}, {int(player.y)})"
    velocity_text = f"Velocity: ({player.velocity_x:.1f}, {player.velocity_y:.1f})"
    platforms_text = f"Platforms Reached: {platforms_reached_count}"
    top_score_text = f"Top Score: {top_score}"
    
    text1 = debug_font.render(on_platform_text, True, DEBUG_COLOR)
    text2 = debug_font.render(position_text, True, DEBUG_COLOR)
    text3 = debug_font.render(velocity_text, True, DEBUG_COLOR)
    text4 = debug_font.render(platforms_text, True, DEBUG_COLOR)
    text5 = debug_font.render(top_score_text, True, DEBUG_COLOR)
    
    surface.blit(text1, (10, 20))
    surface.blit(text2, (10, 35))
    surface.blit(text3, (10, 50))
    surface.blit(text4, (10, 65))
    surface.blit(text5, (10, 80))


def generate_platforms():
    # Check if we need to generate more platforms
    if platforms:
        rightmost_platform = platforms[-1]
        visible_right = camera_offset + SCREEN_WIDTH
        
        if rightmost_platform.x + rightmost_platform.width < visible_right + 500:
            new_platform_x = rightmost_platform.x + rightmost_platform.width + get_random_gap()
            new_platform_y = get_random_height(rightmost_platform.y)
            
            platforms.append(Platform(
                platform_id_counter, 
                new_platform_x, 
                new_platform_y, 
                PLATFORM_WIDTH, 
                PLATFORM_HEIGHT
            ))
            return True
            
    return False


def remove_offscreen_platforms():
    global platforms
    
    # Remove platforms that are off-screen to the left
    while platforms and platforms[0].x + platforms[0].width < camera_offset - 100:
        platforms.pop(0)


def draw_score(surface, score):
    text = score_font.render(f"Score: {score}", True, WHITE)
    surface.blit(text, (700, 20))


def draw_game_over(surface, score, top_score, new_best):
    # Create a semi-transparent overlay
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))  # Black with alpha
    surface.blit(overlay, (0, 0))
    
    # Game over text
    game_over_text = game_over_font.render("Game Over!", True, WHITE)
    score_text = game_over_font.render(f"Score: {score}", True, WHITE)
    top_score_text = game_over_font.render(f"Top Score: {top_score}", True, WHITE)
    restart_text = game_over_font.render("Press Space to Restart", True, WHITE)
    
    # Position text
    game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 80))
    score_rect = score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 30))
    top_score_rect = top_score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20))
    restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 120))
    
    # Draw text
    surface.blit(game_over_text, game_over_rect)
    surface.blit(score_text, score_rect)
    surface.blit(top_score_text, top_score_rect)
    surface.blit(restart_text, restart_rect)
    
    # Draw new best score message if applicable
    if new_best:
        new_best_text = game_over_font.render("NEW BEST SCORE!", True, GOLD)
        new_best_rect = new_best_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 70))
        surface.blit(new_best_text, new_best_rect)


def reset_game():
    global player, platforms, camera_offset, platform_id_counter, platforms_reached
    global score, is_jumping, jump_hold_time, is_game_over, new_best_score
    
    # Reset game state
    score = 0
    is_game_over = False
    is_jumping = False
    jump_hold_time = 0
    camera_offset = 0
    platforms_reached = []
    platform_id_counter = 0
    new_best_score = False
    
    # Create initial platforms
    platforms = []
    platform_x = 0
    
    # Create initial platform under player
    platforms.append(Platform(
        platform_id_counter,
        platform_x,
        400,
        PLATFORM_WIDTH * 2,  # First platform is wider
        PLATFORM_HEIGHT
    ))
    platform_id_counter += 1
    
    # Reset player position to be on the first platform
    player.reset(100, 400 - player.height)
    player.current_platform_id = 0
    
    # Add first platform to reached platforms
    platforms_reached.append(0)
    
    # Generate a few more platforms ahead
    platform_x += PLATFORM_WIDTH * 2 + get_random_gap()
    for i in range(10):
        platform_y = get_random_height(platforms[-1].y)
        platforms.append(Platform(
            platform_id_counter,
            platform_x,
            platform_y,
            PLATFORM_WIDTH,
            PLATFORM_HEIGHT
        ))
        platform_id_counter += 1
        platform_x += PLATFORM_WIDTH + get_random_gap()


# Initialize game variables
player = Player(100, 300)
platforms = []
camera_offset = 0
platform_id_counter = 0
platforms_reached = []
score = 0
top_score = 0
is_jumping = False
jump_hold_time = 0
is_game_over = False
new_best_score = False

# Initialize game
reset_game()

# Game loop
running = True
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                # If game is over, restart the game
                if is_game_over:
                    reset_game()
                # If player is on a platform, initiate jump
                elif player.is_on_platform and not is_jumping:
                    is_jumping = True
                    jump_hold_time = 0
                    player.velocity_x = JUMP_FORWARD_SPEED  # Start moving forward when jumping
        
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                is_jumping = False
    
    # Update game state if not game over
    if not is_game_over:
        # Handle jump mechanics
        if is_jumping:
            if jump_hold_time < MAX_JUMP_HOLD:
                player.velocity_y -= JUMP_POWER
                jump_hold_time += 1
            else:
                is_jumping = False
        
        # Update player
        player.update()
        
        # Update camera offset to keep player in view
        camera_offset = player.x - 100
        
        # Check for platform collisions
        check_platform_collisions(player, platforms)
        
        # Generate new platforms as needed
        if generate_platforms():
            platform_id_counter += 1
        
        # Remove platforms that are off-screen
        remove_offscreen_platforms()
        
        # Update score
        score = len(platforms_reached) - 1  # Subtract 1 to not count starting platform
        
        # Check game over condition
        if player.y > SCREEN_HEIGHT:
            is_game_over = True
            
            # Check if player beat the top score
            if score > top_score:
                top_score = score
                new_best_score = True
    
    # Drawing
    screen.fill(DARK_GRAY)  # Background
    
    # Draw platforms
    for platform in platforms:
        platform.draw(screen, camera_offset, platform.id in platforms_reached)
    
    # Draw player
    player.draw(screen, camera_offset)
    
    # Draw debug info
    draw_debug_info(screen, player, len(platforms_reached), camera_offset, top_score)
    
    # Draw score
    draw_score(screen, score)
    
    # Draw game over screen if game is over
    if is_game_over:
        draw_game_over(screen, score, top_score, new_best_score)
    
    # Update display
    pygame.display.flip()
    
    # Cap the frame rate
    clock.tick(60)

# Quit pygame
pygame.quit()
sys.exit() 