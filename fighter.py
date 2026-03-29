import pygame

from controllers.base import Observation


class Fighter:
    """Fighter avatar.

    IMPORTANT: Rendering, audio, and physics stay here.
    The "brain" (policy) is external via controllers.
    """

    # Stable action ids for controllers
    # 0 noop, 1 move left, 2 move right, 3 jump, 4 heavy attack, 5 light attack
    # 6 jump-left, 7 jump-right
    ACTIONS = {
        0: "noop",
        1: "left",
        2: "right",
        3: "jump",
        4: "heavy",
        5: "light",
        6: "jump_left",
        7: "jump_right",
    }

    def __init__(self, player, x, y, flip, data, sprite_sheet, animation_steps, attack_sound, screen_width):
        # basic attributes
        self.player = player
        self.size, self.image_scale, self.offset = data
        self.flip = flip
        self.animation_list = self.load_images(sprite_sheet, animation_steps)
        self.action = 0
        self.frame_index = 0
        self.image = self.animation_list[0][0]
        self.update_time = pygame.time.get_ticks()
        self.rect = pygame.Rect(x, y, 80, 180)
        self.spawn_pos = (x, y)
        self.vel_y = 0
        self.jump = False
        self.attacking = False
        self.attack_type = ""  # "light"|"heavy" when attacking
        self.attack_cooldown = 0
        self.hit = False
        self.health = 100
        self.alive = True
        self.death_played = False
        self.attack_sound = attack_sound
        self.screen_width = screen_width

        # constants
        self.SPEED = 10
        self.GRAVITY = 2

    def load_images(self, sheet, steps):
        animation_list = []
        for y, count in enumerate(steps):
            frames = []
            for x in range(count):
                img = sheet.subsurface(x * self.size, y * self.size, self.size, self.size)
                frames.append(
                    pygame.transform.scale(img, (self.size * self.image_scale, self.size * self.image_scale))
                )
            animation_list.append(frames)
        return animation_list

    def make_observation(self, other, *, tick: int) -> Observation:
        return Observation(
            tick=tick,
            self_x=float(self.rect.x),
            self_y=float(self.rect.y),
            self_vy=float(self.vel_y),
            self_health=float(self.health),
            self_alive=bool(self.alive),
            self_flip=bool(self.flip),
            self_jump=bool(self.jump),
            self_attacking=bool(self.attacking),
            self_attack_cooldown=int(self.attack_cooldown),
            opp_x=float(other.rect.x),
            opp_y=float(other.rect.y),
            opp_vy=float(other.vel_y),
            opp_health=float(other.health),
            opp_alive=bool(other.alive),
            opp_flip=bool(other.flip),
            opp_jump=bool(other.jump),
            opp_attacking=bool(other.attacking),
            opp_attack_cooldown=int(other.attack_cooldown),
            screen_width=int(self.screen_width),
        )

    def step_from_action(self, other, *, action_id: int, round_over: bool) -> tuple[float, bool]:
        """Advance physics given an action.

        Returns (reward, done) where reward is a simple hit/miss signal
        useful for the existing DQN controller.
        """
        if round_over:
            return 0.0, False

        if not self.alive:
            return 0.0, True

        # auto face opponent
        self.flip = other.rect.x < self.rect.x

        reward = 0.0
        done = False

        dx, dy = 0, 0
        self.vel_y += self.GRAVITY
        dy += self.vel_y

        if action_id == 1:
            dx = -self.SPEED
        elif action_id == 2:
            dx = self.SPEED
        elif action_id in (3, 6, 7) and not self.jump:
            # Jump (optionally with horizontal intent).
            self.vel_y = -30
            self.jump = True
            if action_id == 6:
                dx = -self.SPEED
            elif action_id == 7:
                dx = self.SPEED
        elif action_id in (4, 5) and self.attack_cooldown == 0:
            # attacks
            self.attacking = True
            self.attack_type = "heavy" if action_id == 4 else "light"
            self.attack_sound.play()

            # light = shorter range, smaller dmg, shorter cooldown
            if self.attack_type == "light":
                reach = 2.0
                dmg = 6
                cd = 12
            else:
                reach = 3.0
                dmg = 10
                cd = 20

            rect = (
                pygame.Rect(self.rect.right, self.rect.y, reach * self.rect.width, self.rect.height)
                if not self.flip
                else pygame.Rect(self.rect.x - reach * self.rect.width, self.rect.y, reach * self.rect.width, self.rect.height)
            )
            if rect.colliderect(other.rect):
                other.health -= dmg
                reward = 1.0
            else:
                reward = -0.1
            self.attack_cooldown = cd

        # block overlap
        # NOTE: account for vertical movement when deciding whether horizontal movement would collide.
        # Without this, a fighter can be incorrectly prevented from moving "through" the opponent
        # during a jump because collision is tested at the pre-jump y-position.
        new_x = self.rect.x + dx
        new_y = self.rect.y + dy
        temp = self.rect.copy()
        temp.x = new_x
        temp.y = new_y
        if temp.colliderect(other.rect):
            dx = 0

        # clamp
        self.rect.x = max(0, min(self.rect.x + dx, self.screen_width - self.rect.width))
        self.rect.y = max(0, min(self.rect.y + dy, (self.screen_width / 2) - self.rect.height))
        if self.rect.y >= (self.screen_width / 2) - self.rect.height:
            self.jump = False

        if self.health <= 0:
            done = True
            self.alive = False

        self.attack_cooldown = max(0, self.attack_cooldown - 1)
        return reward, done

    def update(self):
        # death animation: play once and then hold last frame
        if not self.alive:
            if not self.death_played:
                self.update_action(6)
                if pygame.time.get_ticks() - self.update_time > 50:
                    self.frame_index += 1
                    self.update_time = pygame.time.get_ticks()
                    if self.frame_index >= len(self.animation_list[6]):
                        self.frame_index = len(self.animation_list[6]) - 1
                        self.death_played = True
            self.image = self.animation_list[6][self.frame_index]
            return

        # normal animations
        if self.hit:
            self.update_action(5)
        elif self.attacking:
            # Use separate animations for light vs heavy if available.
            self.update_action(4 if self.attack_type == "heavy" else 3)
        elif self.jump:
            self.update_action(2)
        else:
            self.update_action(1 if self.vel_y == 0 else 0)

        if pygame.time.get_ticks() - self.update_time > 50:
            self.frame_index += 1
            self.update_time = pygame.time.get_ticks()
            if self.frame_index >= len(self.animation_list[self.action]):
                self.frame_index = 0
                if self.action in [3, 4]:
                    self.attacking = False
                if self.action == 5:
                    self.hit = False

        self.image = self.animation_list[self.action][self.frame_index]

    def update_action(self, new_action):
        if new_action != self.action:
            self.action = new_action
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def draw(self, surf):
        img = pygame.transform.flip(self.image, self.flip, False)
        surf.blit(
            img,
            (
                self.rect.x - self.offset[0] * self.image_scale,
                self.rect.y - self.offset[1] * self.image_scale,
            ),
        )

    def reset(self):
        self.health = 100
        self.alive = True
        self.death_played = False
        self.vel_y = 0
        self.jump = False
        self.attacking = False
        self.attack_type = ""
        self.attack_cooldown = 0
        self.hit = False
        self.rect.x, self.rect.y = self.spawn_pos
