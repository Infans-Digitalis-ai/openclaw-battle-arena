# main.py
import pygame
from pygame import mixer

from fighter import Fighter

from controllers.factory import make_controller
from controllers.ws_server import BattleAgentsWSServer

import settings

mixer.init()
pygame.init()

# create game window
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
GROUND_HEIGHT = SCREEN_HEIGHT - 293

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Brawler")

clock = pygame.time.Clock()
FPS = 60

# colors
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)

# game variables
intro_count = 3
last_count_update = pygame.time.get_ticks()
score = [0, 0]
round_over = False
ROUND_OVER_COOLDOWN = 2000
round_time_limit = 90
round_start_time = pygame.time.get_ticks()

# fighter setup data (unchanged)
WARRIOR_DATA = [162, 4, [72, 56]]
WIZARD_DATA = [250, 3, [112, 107]]
WARRIOR_SHEET = pygame.image.load("assets/images/warrior/Sprites/warrior.png").convert_alpha()
WIZARD_SHEET = pygame.image.load("assets/images/wizard/Sprites/wizard.png").convert_alpha()
WARRIOR_STEPS = [10, 8, 1, 7, 7, 3, 7]
WIZARD_STEPS = [8, 8, 1, 8, 8, 3, 7]

# audio
pygame.mixer.music.load("assets/audio/music.mp3")
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1, 0.0, 5000)
sword_fx = pygame.mixer.Sound("assets/audio/sword.wav")
sword_fx.set_volume(0.5)
magic_fx = pygame.mixer.Sound("assets/audio/magic.wav")
magic_fx.set_volume(0.75)

# graphics
bg = pygame.image.load("assets/images/background/background.jpg").convert_alpha()
victory_img = pygame.image.load("assets/images/icons/victory.png").convert_alpha()

# fonts
count_font = pygame.font.Font("assets/fonts/turok.ttf", 80)
score_font = pygame.font.Font("assets/fonts/turok.ttf", 30)
ui_font = pygame.font.Font("assets/fonts/turok.ttf", 18)


def draw_text(text, font, color, x, y):
    img = font.render(text, True, color)
    screen.blit(img, (x, y))


def draw_bg():
    screen.blit(pygame.transform.scale(bg, (SCREEN_WIDTH, SCREEN_HEIGHT)), (0, 0))


def draw_health_bar(h, x, y):
    ratio = h / 100
    pygame.draw.rect(screen, WHITE, (x - 2, y - 2, 404, 34))
    pygame.draw.rect(screen, RED, (x, y, 400, 30))
    pygame.draw.rect(screen, YELLOW, (x, y, 400 * ratio, 30))


# Create two fighters (rendering unchanged)
fighter_1 = Fighter(
    player=1,
    x=200,
    y=310,
    flip=False,
    data=WARRIOR_DATA,
    sprite_sheet=WARRIOR_SHEET,
    animation_steps=WARRIOR_STEPS,
    attack_sound=sword_fx,
    screen_width=SCREEN_WIDTH,
)
fighter_2 = Fighter(
    player=2,
    x=700,
    y=310,
    flip=True,
    data=WIZARD_DATA,
    sprite_sheet=WIZARD_SHEET,
    animation_steps=WIZARD_STEPS,
    attack_sound=magic_fx,
    screen_width=SCREEN_WIDTH,
)

# Optional WS server (only used by remote controllers)
ws_server = None
if settings.P1_CONTROLLER.lower() in ("remote", "ws", "remote-ws", "websocket") or settings.P2_CONTROLLER.lower() in (
    "remote",
    "ws",
    "remote-ws",
    "websocket",
):
    ws_server = BattleAgentsWSServer(host=settings.WS_HOST, port=settings.WS_PORT)
    ws_server.start()

controller_1 = make_controller(settings.P1_CONTROLLER, player=1, screen_width=SCREEN_WIDTH, ws_server=ws_server)
controller_2 = make_controller(settings.P2_CONTROLLER, player=2, screen_width=SCREEN_WIDTH, ws_server=ws_server)

def controller_label(player: int, kind: str, ctrl) -> str:
    name = getattr(ctrl, "name", "")
    name = str(name) if name is not None else ""
    base = f"P{player}={kind}"
    if name and name.lower() != kind.lower():
        return f"{base} ({name})"
    return base

p1_label = controller_label(1, settings.P1_CONTROLLER, controller_1)
p2_label = controller_label(2, settings.P2_CONTROLLER, controller_2)
ws_label = f"WS={settings.WS_HOST}:{settings.WS_PORT}" if ws_server is not None else "WS=off"

# Match format
best_of = max(1, int(settings.MATCH_BEST_OF))
win_target = (best_of // 2) + 1

run = True
tick = 0
while run:
    clock.tick(FPS)
    tick += 1

    draw_bg()
    draw_health_bar(fighter_1.health, 20, 20)
    draw_health_bar(fighter_2.health, 580, 20)
    draw_text(f"P1: {score[0]}", score_font, RED, 20, 60)
    draw_text(f"P2: {score[1]}", score_font, RED, 580, 60)

    # Controller overlay (always visible for demos)
    draw_text(f"{p1_label} | {p2_label} | {ws_label}", ui_font, WHITE, 20, 95)

    if intro_count > 0:
        draw_text(str(intro_count), count_font, RED, SCREEN_WIDTH / 2 - 20, SCREEN_HEIGHT / 3)
        if pygame.time.get_ticks() - last_count_update >= 1000:
            intro_count -= 1
            last_count_update = pygame.time.get_ticks()
            if intro_count == 0:
                round_start_time = pygame.time.get_ticks()
    else:
        elapsed = (pygame.time.get_ticks() - round_start_time) / 1000
        rem = round_time_limit - elapsed
        mins = int(rem) // 60
        secs = int(rem) % 60
        draw_text(f"{mins}:{secs:02d}", count_font, RED, SCREEN_WIDTH / 2 - 40, 10)

        # build observations
        obs1 = fighter_1.make_observation(fighter_2, tick=tick)
        obs2 = fighter_2.make_observation(fighter_1, tick=tick)

        # controllers choose actions
        a1 = int(controller_1.act(obs1))
        a2 = int(controller_2.act(obs2))

        # step physics
        r1, d1 = fighter_1.step_from_action(fighter_2, action_id=a1, round_over=round_over)
        r2, d2 = fighter_2.step_from_action(fighter_1, action_id=a2, round_over=round_over)

        # optional DQN training hook
        if getattr(controller_1, "record", None):
            controller_1.record(reward=r1, next_obs=fighter_1.make_observation(fighter_2, tick=tick), done=not fighter_1.alive)
        if getattr(controller_2, "record", None):
            controller_2.record(reward=r2, next_obs=fighter_2.make_observation(fighter_1, tick=tick), done=not fighter_2.alive)

        # update animations/draw
        fighter_1.update()
        fighter_2.update()
        fighter_1.draw(screen)
        fighter_2.draw(screen)

        if not round_over:
            if not fighter_1.alive:
                score[1] += 1
                round_over = True
                round_over_time = pygame.time.get_ticks()
            elif not fighter_2.alive:
                score[0] += 1
                round_over = True
                round_over_time = pygame.time.get_ticks()

        # end-of-round handling
        if rem <= 0 or (round_over and pygame.time.get_ticks() - round_over_time > ROUND_OVER_COOLDOWN):
            round_over = False
            intro_count = 3
            fighter_1.reset()
            fighter_2.reset()

            # MATCH mode: stop once someone reaches win_target
            if settings.MODE.upper() == "MATCH":
                if score[0] >= win_target or score[1] >= win_target:
                    # Keep display intact; just exit loop after final round.
                    run = False

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            run = False

    pygame.display.update()

pygame.quit()
