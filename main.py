# main.py
import json
import os
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

# Deterministic tick-based timing (used when settings.FIXED_TICK_MATCH and MODE="MATCH")
INTRO_TICKS_PER_COUNT = 60  # 1 second at FPS=60
intro_ticks_remaining = intro_count * INTRO_TICKS_PER_COUNT
ROUND_TIME_LIMIT_S = 90
round_ticks_remaining = ROUND_TIME_LIMIT_S * 60

score = [0, 0]
round_over = False
ROUND_OVER_COOLDOWN = 2000
round_time_limit = ROUND_TIME_LIMIT_S
round_start_time = pygame.time.get_ticks()

# Anti-stuck + calibration state
last_damage_time = pygame.time.get_ticks()
last_combined_health = 200
calibration_written_for_round = False

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
# Use standard readable system fonts for HUD. Keep the thematic font only for the big countdown.
count_font = pygame.font.Font("assets/fonts/turok.ttf", 80)
score_font = pygame.font.SysFont(None, 30)
ui_font = pygame.font.SysFont(None, 26)


def draw_text(text, font, color, x, y):
    img = font.render(text, True, color)
    screen.blit(img, (x, y))


def draw_text_shadow(text, font, color, x, y, shadow=(0, 0, 0)):
    # Subtle drop shadow for readability.
    sx, sy = 1, 1
    screen.blit(font.render(text, True, shadow), (x + sx, y + sy))
    screen.blit(font.render(text, True, color), (x, y))


def draw_text_right(text, font, color, right_x, y):
    img = font.render(text, True, color)
    rect = img.get_rect(topright=(right_x, y))
    screen.blit(img, rect)


def draw_text_center(text, font, color, center_x, y):
    img = font.render(text, True, color)
    rect = img.get_rect(midtop=(center_x, y))
    screen.blit(img, rect)


def draw_bg():
    screen.blit(pygame.transform.scale(bg, (SCREEN_WIDTH, SCREEN_HEIGHT)), (0, 0))


def draw_health_bar(h, x, y):
    ratio = h / 100
    pygame.draw.rect(screen, WHITE, (x - 2, y - 2, 404, 34))
    pygame.draw.rect(screen, RED, (x, y, 400, 30))
    pygame.draw.rect(screen, YELLOW, (x, y, 400 * ratio, 30))


def write_calibration_snapshot(*, p1_obs, p2_obs, out_path: str):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    payload = {
        "note": "Non-strategy calibration snapshot to help duelists calibrate distance units.",
        "p1_obs": p1_obs.to_json(),
        "p2_obs": p2_obs.to_json(),
        "arena": {
            "screen_width": SCREEN_WIDTH,
            "screen_height": SCREEN_HEIGHT,
            "fps": FPS,
            "fighter": {
                "rect_width": 80,
                "speed_px_per_tick": 10,
                "jump_vel_y": -30,
                "gravity": 2,
                "light": {"reach_rect_widths": 2.0, "dmg": 6, "cooldown_ticks": 12},
                "heavy": {"reach_rect_widths": 3.0, "dmg": 10, "cooldown_ticks": 20},
            },
            "typical_units": {
                "x": "pixels (0..screen_width)",
                "distance": "abs(opp.x - self.x) in pixels",
            },
        },
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


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

controller_1 = make_controller(
    settings.P1_CONTROLLER,
    player=1,
    screen_width=SCREEN_WIDTH,
    ws_server=ws_server,
    script_path=getattr(settings, "P1_SCRIPT_PATH", None),
    script_timeout_ms=int(getattr(settings, "SCRIPT_ACT_TIMEOUT_MS", 8) or 8),
)
controller_2 = make_controller(
    settings.P2_CONTROLLER,
    player=2,
    screen_width=SCREEN_WIDTH,
    ws_server=ws_server,
    script_path=getattr(settings, "P2_SCRIPT_PATH", None),
    script_timeout_ms=int(getattr(settings, "SCRIPT_ACT_TIMEOUT_MS", 8) or 8),
)

def controller_label(player: int, kind: str, ctrl) -> str:
    name = getattr(ctrl, "name", "")
    name = str(name) if name is not None else ""
    base = f"P{player}={kind}"
    if name and name.lower() != kind.lower():
        return f"{base} ({name})"
    return base

p1_label = controller_label(1, settings.P1_CONTROLLER, controller_1)
p2_label = controller_label(2, settings.P2_CONTROLLER, controller_2)

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

    HUD_Y = 70
    HUD_Y2 = 100
    HUD_Y3 = 130

    # Score labels (left/right)
    draw_text_shadow(f"P1: {score[0]}", score_font, WHITE, 20, HUD_Y)
    draw_text_right(f"P2: {score[1]}", score_font, WHITE, SCREEN_WIDTH - 20, HUD_Y)

    # Round counter (center) — placed on its own line below the score
    rounds_played = score[0] + score[1]
    current_round = min(best_of, rounds_played + 1)
    draw_text_center(f"ROUND {current_round}/{best_of}", ui_font, WHITE, SCREEN_WIDTH / 2, HUD_Y2)

    # Controller overlay (left/right)
    draw_text_shadow(p1_label, ui_font, WHITE, 20, HUD_Y3)
    draw_text_right(p2_label, ui_font, WHITE, SCREEN_WIDTH - 20, HUD_Y3)

    fixed_match = bool(getattr(settings, "FIXED_TICK_MATCH", False)) and settings.MODE.upper() == "MATCH"

    if intro_count > 0:
        draw_text(str(intro_count), count_font, RED, SCREEN_WIDTH / 2 - 20, SCREEN_HEIGHT / 3)

        if fixed_match:
            # Tick-based 3..2..1 countdown (deterministic across machines)
            intro_ticks_remaining = max(0, intro_ticks_remaining - 1)
            intro_count = max(0, (intro_ticks_remaining + INTRO_TICKS_PER_COUNT - 1) // INTRO_TICKS_PER_COUNT)
            if intro_count == 0:
                round_ticks_remaining = ROUND_TIME_LIMIT_S * FPS
        else:
            if pygame.time.get_ticks() - last_count_update >= 1000:
                intro_count -= 1
                last_count_update = pygame.time.get_ticks()
                if intro_count == 0:
                    round_start_time = pygame.time.get_ticks()
    else:
        if fixed_match:
            round_ticks_remaining = max(0, round_ticks_remaining - 1)
            rem = round_ticks_remaining / FPS
        else:
            elapsed = (pygame.time.get_ticks() - round_start_time) / 1000
            rem = max(0, round_time_limit - elapsed)

        # HUD timer formatting:
        # - Show M:SS when >= 60s remaining (e.g., 1:00, 2:15)
        # - Once it drops below 60s, show just seconds (e.g., 59, 58, ... 0)
        # This avoids the 0:59 width jump that can overlap the right health bar.
        if rem >= 60:
            mins = int(rem) // 60
            secs = int(rem) % 60
            timer_text = f"{mins}:{secs:02d}"
        else:
            timer_text = str(int(rem))

        draw_text(timer_text, count_font, RED, SCREEN_WIDTH / 2 - 40, 10)

        # build observations
        obs1 = fighter_1.make_observation(fighter_2, tick=tick)
        obs2 = fighter_2.make_observation(fighter_1, tick=tick)

        # Write a non-strategy calibration snapshot once per round (first live tick).
        if not calibration_written_for_round:
            try:
                write_calibration_snapshot(
                    p1_obs=obs1,
                    p2_obs=obs2,
                    out_path="logs/calibration-latest.json",
                )
            except Exception:
                pass
            calibration_written_for_round = True

        # controllers choose actions
        a1 = int(controller_1.act(obs1))
        a2 = int(controller_2.act(obs2))

        # step physics
        prev_combined = fighter_1.health + fighter_2.health
        r1, d1 = fighter_1.step_from_action(fighter_2, action_id=a1, round_over=round_over)
        r2, d2 = fighter_2.step_from_action(fighter_1, action_id=a2, round_over=round_over)

        # Track damage events
        combined = fighter_1.health + fighter_2.health
        if combined < prev_combined:
            last_damage_time = pygame.time.get_ticks()
            last_combined_health = combined

        # optional DQN training hook
        if getattr(controller_1, "record", None):
            controller_1.record(reward=r1, next_obs=fighter_1.make_observation(fighter_2, tick=tick), done=not fighter_1.alive)
        if getattr(controller_2, "record", None):
            controller_2.record(reward=r2, next_obs=fighter_2.make_observation(fighter_1, tick=tick), done=not fighter_2.alive)

        # update animations/draw
        fighter_1.update()
        fighter_2.update()

        # Anti-stuck separation: if fighters are pressed together and no damage has occurred
        # for a while, nudge them apart slightly so exchanges can resume.
        stuck_ms = pygame.time.get_ticks() - last_damage_time
        if stuck_ms > 1500 and fighter_1.rect.colliderect(fighter_2.rect):
            # Push apart based on their relative positions.
            if fighter_1.rect.centerx <= fighter_2.rect.centerx:
                fighter_1.rect.x = max(0, fighter_1.rect.x - 8)
                fighter_2.rect.x = min(SCREEN_WIDTH - fighter_2.rect.width, fighter_2.rect.x + 8)
            else:
                fighter_1.rect.x = min(SCREEN_WIDTH - fighter_1.rect.width, fighter_1.rect.x + 8)
                fighter_2.rect.x = max(0, fighter_2.rect.x - 8)
            # Avoid repeated shoves every frame.
            last_damage_time = pygame.time.get_ticks()

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
            intro_ticks_remaining = intro_count * INTRO_TICKS_PER_COUNT
            if fixed_match:
                round_ticks_remaining = ROUND_TIME_LIMIT_S * FPS
            fighter_1.reset()
            fighter_2.reset()
            last_damage_time = pygame.time.get_ticks()
            last_combined_health = fighter_1.health + fighter_2.health
            calibration_written_for_round = False

            # MATCH mode: stop once someone reaches win_target (best-of-N)
            if settings.MODE.upper() == "MATCH":
                if score[0] >= win_target or score[1] >= win_target:
                    # Keep display intact; just exit loop after final round.
                    run = False

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            run = False

    pygame.display.update()

pygame.quit()

# --- OpenClaw script-bot cleanup ---
# By convention, OpenClaw duels write bot scripts into bots/openclaw_p1.py and bots/openclaw_p2.py.
# Delete them after the match so the next duel starts clean.
if bool(getattr(settings, "AUTO_DELETE_OPENCLAW_SCRIPTS", True)):
    def _safe_unlink(p: str) -> None:
        try:
            os.unlink(p)
        except FileNotFoundError:
            return
        except Exception as e:
            print(f"[cleanup] failed to delete {p}: {e}")

    p1 = getattr(settings, "P1_SCRIPT_PATH", "") or ""
    p2 = getattr(settings, "P2_SCRIPT_PATH", "") or ""

    # Only delete the OpenClaw-generated default files (avoid deleting arbitrary user scripts).
    if os.path.normpath(p1) == os.path.normpath("bots/openclaw_p1.py"):
        _safe_unlink(p1)
    if os.path.normpath(p2) == os.path.normpath("bots/openclaw_p2.py"):
        _safe_unlink(p2)
