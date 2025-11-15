import pygame
import sys
import math
#made using 9 prompts to gemini
# --- Configuration ---
# File names to update:
CUSTOM_BG_FILE = "image copy.png"  # <<< CHANGE THIS TO YOUR IMAGE FILE
MUSIC_FILE = "bg_music.mp3"     # <<< CHANGE THIS TO YOUR MUSIC FILE

# --- Initialization ---
pygame.init()
pygame.mixer.init() 

# Screen dimensions
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Archery Target Practice")

# --- Colors ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 150, 0)       # Fallback grass color
BLUE_SKY = (135, 206, 235) # Fallback sky color
YELLOW = (255, 255, 0)
BUTTON_COLOR = (50, 50, 50)
HOVER_COLOR = (80, 80, 80)

# Font setup
font_large = pygame.font.Font(None, 74)
font_medium = pygame.font.Font(None, 36)
font_small = pygame.font.Font(None, 28)

# --- Asset Loading ---

# Load Target (66x330)
try:
    target_img = pygame.image.load("Target.png").convert_alpha()
    TARGET_WIDTH = 66
    TARGET_HEIGHT = 330
    target_img = pygame.transform.scale(target_img, (TARGET_WIDTH, TARGET_HEIGHT))
except pygame.error as e:
    print(f"Could not load Target.png: {e}. Using fallback.")
    TARGET_WIDTH = 66
    TARGET_HEIGHT = 330
    target_img = pygame.Surface((TARGET_WIDTH, TARGET_HEIGHT), pygame.SRCALPHA)
    target_img.fill((100, 100, 100, 200))

# Load Arrow (100x20)
try:
    arrow_img = pygame.image.load("tucker.png").convert_alpha()
    ARROW_WIDTH = 100
    ARROW_HEIGHT = 20
    arrow_img = pygame.transform.scale(arrow_img, (ARROW_WIDTH, ARROW_HEIGHT))
except pygame.error as e:
    print(f"Could not load arrow.png: {e}. Using fallback.")
    ARROW_WIDTH = 100
    ARROW_HEIGHT = 20
    arrow_img = pygame.Surface((ARROW_WIDTH, ARROW_HEIGHT), pygame.SRCALPHA)
    pygame.draw.polygon(arrow_img, RED, [(0, ARROW_HEIGHT // 2), (ARROW_WIDTH, 0), (ARROW_WIDTH, ARROW_HEIGHT)])

# Load Custom Background (Flexible choice)
try:
    # Try to load the custom background
    bg_img = pygame.image.load(CUSTOM_BG_FILE).convert()
    bg_img = pygame.transform.scale(bg_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
    custom_bg_loaded = True
except pygame.error as e:
    print(f"Could not load custom background: {e}. Falling back to gradient.")
    custom_bg_loaded = False

# Load Music (Flexible choice)
music_loaded = False
music_playing = False
try:
    pygame.mixer.music.load(MUSIC_FILE)
    music_loaded = True
except pygame.error as e:
    print(f"Could not load music file: {e}. Music functionality disabled.")


# --- Target & Scoring Setup ---
TARGET_X = 50
TARGET_Y = (SCREEN_HEIGHT - TARGET_HEIGHT) // 2
target_rect = target_img.get_rect(topleft=(TARGET_X, TARGET_Y))
TARGET_CENTER_Y = TARGET_Y + (TARGET_HEIGHT // 2)

BULLSEYE_HEIGHT = 15
YELLOW_HEIGHT = 100
RED_HEIGHT = 180
BLUE_HEIGHT = 300

# --- Game State Variables ---
total_score = 0
chances_left = 3
game_state = "START_MENU" 

arrow_x = SCREEN_WIDTH - ARROW_WIDTH - 50 
arrow_y = SCREEN_HEIGHT // 2
ARROW_START_X = arrow_x
arrow_speed_y = 0
arrow_speed_x = 5

swing_amplitude = 200 
swing_frequency = 0.010
time_elapsed = 0

# Button rects (Initialized for global access in event handlers)
play_button_rect = pygame.Rect(0, 0, 0, 0)
restart_button_rect = pygame.Rect(0, 0, 0, 0)
music_button_rect = pygame.Rect(0, 0, 0, 0)

# --- Functions ---

def calculate_score(arrow_impact_y):
    """Calculates the score based on the arrow's vertical impact position using the new rules."""
    
    # 1. Check for Miss (Arrow is outside the target's vertical range 330)
    if arrow_impact_y < TARGET_Y or arrow_impact_y > TARGET_Y + TARGET_HEIGHT:
        return 0, "Miss"
        
    # Find the vertical distance from the true target center (165 pixels from edge)
    dist_from_center = abs(arrow_impact_y - TARGET_CENTER_Y)

    # 2. Scoring Logic (Using specified pixel distances)
    
    # 10 Points: Black dot (Middle)
    # Target center is 0. dist_from_center <= 15
    if dist_from_center <= 15:
        return 10, "Black Dot (10 pts)"
        
    # 8 Points: Yellow Rings region (Beyond 15 and up to 71.5)
    if dist_from_center <= 71.5:
        return 8, "Yellow Rings (8 pts)"
        
    # 6 Points: Red Ring region (Beyond 71.5 and up to 107.5)
    if dist_from_center <= 107.5:
        return 6, "Red Ring Region (6 pts)"

    # 4 Points: Rest of the Board (Beyond 107.5 up to 165, which is half the 330 height)
    # The max possible distance on the board is TARGET_HEIGHT / 2 = 165
    if dist_from_center <= TARGET_HEIGHT / 2:
        return 4, "Outer Rings (4 pts)"
        
    # Fallback miss (shouldn't be reached if the initial check is correct)
    return 0, "Miss (Fallback)"

def reset_arrow():
    """Resets the arrow position for the next shot."""
    global arrow_x, arrow_y, arrow_speed_y, arrow_speed_x, game_state, ARROW_START_X
    
    ARROW_START_X = SCREEN_WIDTH - ARROW_WIDTH - 50 
    arrow_x = ARROW_START_X
    arrow_y = SCREEN_HEIGHT // 2
    arrow_speed_y = 0
    game_state = "AIMING"

def draw_background():
    """Draws the selected background."""
    if custom_bg_loaded:
        screen.blit(bg_img, (0, 0))
    else:
        # Fallback Gradient Background
        screen.fill(BLUE_SKY, rect=(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT * 2 // 3))
        screen.fill(GREEN, rect=(0, SCREEN_HEIGHT * 2 // 3, SCREEN_WIDTH, SCREEN_HEIGHT // 3))

def draw_button(rect, text, mouse_pos):
    """Draws a button and returns its rect."""
    color = HOVER_COLOR if rect.collidepoint(mouse_pos) else BUTTON_COLOR
    pygame.draw.rect(screen, color, rect, border_radius=5)
    text_surface = font_medium.render(text, True, WHITE)
    screen.blit(text_surface, (rect.x + (rect.width - text_surface.get_width()) // 2, 
                               rect.y + (rect.height - text_surface.get_height()) // 2))
    return rect

def draw_music_button(mouse_pos):
    """Draws the music toggle button with correct icon."""
    global music_button_rect
    
    # Use standard symbols
    icon = "II" if music_playing else "▶️" # Pause/Play icon
    text = f"Music {icon}"
    
    button_width, button_height = 120, 40
    music_button_rect = pygame.Rect(20, 20, button_width, button_height)
    
    draw_button(music_button_rect, text, mouse_pos)

def draw_start_menu(mouse_pos):
    """Draws the initial start menu."""
    global play_button_rect
    draw_background()
    
    title_text = font_large.render("ARCHERY CHALLENGE", True, WHITE)
    screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 100))
    
    button_width, button_height = 200, 60
    play_button_rect = pygame.Rect(SCREEN_WIDTH // 2 - button_width // 2, 
                                    SCREEN_HEIGHT // 2, 
                                    button_width, button_height)
    
    draw_button(play_button_rect, "P L A Y", mouse_pos)
    draw_music_button(mouse_pos)

def draw_game_over_screen(mouse_pos):
    """Draws the game over screen with restart button."""
    global restart_button_rect
    draw_background()
    
    game_over_text = font_large.render("GAME OVER", True, RED)
    final_score_text = font_medium.render(f"Final Score: {total_score}", True, WHITE)
    
    screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, 150))
    screen.blit(final_score_text, (SCREEN_WIDTH // 2 - final_score_text.get_width() // 2, 220))
    
    button_width, button_height = 200, 60
    restart_button_rect = pygame.Rect(SCREEN_WIDTH // 2 - button_width // 2, 
                                      SCREEN_HEIGHT // 2, 
                                      button_width, button_height)
    
    draw_button(restart_button_rect, "RESTART", mouse_pos)
    draw_music_button(mouse_pos)

def display_result(score, hit_type):
    """Displays the result of the last shot."""
    result_text = font_medium.render(f"{hit_type} +{score} points", True, YELLOW)
    screen.blit(result_text, (SCREEN_WIDTH // 2 - result_text.get_width() // 2, 120))
    pygame.display.flip()
    pygame.time.wait(1500) 

# --- Game Loop ---
running = True
clock = pygame.time.Clock()

# Start music if loaded
if music_loaded:
    pygame.mixer.music.play(-1) 
    music_playing = True

while running:
    mouse_pos = pygame.mouse.get_pos()
    dt = clock.tick(60)
    time_elapsed += dt

    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: 
                # Music button check (Always present)
                if music_button_rect.collidepoint(mouse_pos) and music_loaded:
                    if music_playing:
                        pygame.mixer.music.pause()
                        music_playing = False
                    else:
                        pygame.mixer.music.unpause()
                        music_playing = True

                if game_state == "START_MENU":
                    if play_button_rect.collidepoint(mouse_pos):
                        game_state = "AIMING"
                        reset_arrow()
                
                elif game_state == "GAME_OVER":
                    if restart_button_rect.collidepoint(mouse_pos):
                        total_score = 0
                        chances_left = 3
                        game_state = "AIMING"
                        reset_arrow()
        
        if event.type == pygame.KEYDOWN and game_state == "AIMING" and chances_left > 0:
            if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                game_state = "SHOT_FLYING"

    # --- Game Logic ---
    
    if game_state == "AIMING":
        center_y = SCREEN_HEIGHT // 2
        arrow_y = center_y + swing_amplitude * math.sin(time_elapsed * swing_frequency)

    elif game_state == "SHOT_FLYING":
        arrow_x -= arrow_speed_x 
        
        # STOP CONDITION: Arrow tip stops at half the target width
        STOPPING_POINT = TARGET_X + (TARGET_WIDTH / 2)
        
        if arrow_x < STOPPING_POINT:
            
            # Stop the arrow exactly at the desired point
            arrow_x = STOPPING_POINT
            
            impact_y = arrow_y + ARROW_HEIGHT // 2
            
            # Calculate score
            score, hit_type = calculate_score(impact_y)
            total_score += score
            chances_left -= 1
            
            # Draw final hit frame and result
            draw_background()
            screen.blit(target_img, target_rect)
            screen.blit(arrow_img, (arrow_x, arrow_y))
            
            display_result(score, hit_type)
            
            if chances_left > 0:
                reset_arrow()
            else:
                game_state = "GAME_OVER"

    # --- Drawing ---
    
    if game_state == "START_MENU":
        draw_start_menu(mouse_pos)
    elif game_state == "GAME_OVER":
        draw_game_over_screen(mouse_pos)
    else: # AIMING or SHOT_FLYING
        draw_background()
        
        # Draw Target and Arrow
        screen.blit(target_img, target_rect)
        screen.blit(arrow_img, (arrow_x, arrow_y))
        
        # Draw Scoreboard
        score_text = font_medium.render(f"Score: {total_score}", True, WHITE)
        chances_text = font_medium.render(f"Arrows Left: {chances_left}", True, WHITE)
        screen.blit(score_text, (SCREEN_WIDTH - score_text.get_width() - 20, 20))
        screen.blit(chances_text, (SCREEN_WIDTH - chances_text.get_width() - 20, 60))
        
        # Draw instructions/hints
        if game_state == "AIMING":
            instr_text = font_small.render("Press SPACE/ENTER to Shoot!", True, YELLOW)
            screen.blit(instr_text, (SCREEN_WIDTH // 2 - instr_text.get_width() // 2, SCREEN_HEIGHT - 50))
            
        draw_music_button(mouse_pos)

    # Update the full display
    pygame.display.flip()

# --- Quit Pygame ---
pygame.quit()
sys.exit()