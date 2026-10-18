import math
import random
import sys
import pygame

# --- INITIALIZATION ---
pygame.init()
pygame.font.init()

WIDTH, HEIGHT = 1000, 650
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Neon Tank Battle - 2 Player")
CLOCK = pygame.time.Clock()
FPS = 60

# --- COLOR PALETTE ---
BG_DARK = (15, 17, 26)
GRID_COLOR = (25, 30, 45)
P1_CYAN = (0, 240, 255)
P2_MAGENTA = (255, 0, 127)
OBSTACLE_COLOR = (40, 50, 75)
OBSTACLE_BORDER = (80, 100, 140)
WHITE = (245, 245, 255)
GRAY = (100, 110, 130)

FONT_LARGE = pygame.font.SysFont("Trebuchet MS", 48, bold=True)
FONT_MED = pygame.font.SysFont("Trebuchet MS", 28, bold=True)
FONT_SMALL = pygame.font.SysFont("Trebuchet MS", 18)


# --- PARTICLE CLASS FOR IMPACT VISUALS ---
class Particle:

  def __init__(self, x, y, color):
    self.x = x
    self.y = y
    self.color = color
    angle = random.uniform(0, math.pi * 2)
    speed = random.uniform(2, 6)
    self.vx = math.cos(angle) * speed
    self.vy = math.sin(angle) * speed
    self.radius = random.uniform(3, 6)
    self.lifetime = random.randint(15, 30)

  def update(self):
    self.x += self.vx
    self.y += self.vy
    self.radius = max(0, self.radius - 0.15)
    self.lifetime -= 1

  def draw(self, surface):
    if self.lifetime > 0 and self.radius > 0:
      pygame.draw.circle(
          surface, self.color, (int(self.x), int(self.y)), int(self.radius)
      )


# --- BULLET CLASS ---
class Bullet:

  def __init__(self, x, y, angle, color, owner):
    self.x = x
    self.y = y
    self.angle = angle
    self.speed = 10
    self.radius = 4
    self.color = color
    self.owner = owner
    self.alive = True

  def update(self, obstacles):
    self.x += math.cos(self.angle) * self.speed
    self.y += math.sin(self.angle) * self.speed

    # Screen boundary collision
    if not (0 <= self.x <= WIDTH and 0 <= self.y <= HEIGHT):
      self.alive = False

    # Obstacle collision
    bullet_rect = pygame.Rect(
        self.x - self.radius,
        self.y - self.radius,
        self.radius * 2,
        self.radius * 2,
    )
    for obs in obstacles:
      if bullet_rect.colliderect(obs):
        self.alive = False
        break

  def draw(self, surface):
    pygame.draw.circle(
        surface, self.color, (int(self.x), int(self.y)), self.radius
    )
    # Inner bright core
    pygame.draw.circle(
        surface, (255, 255, 255), (int(self.x), int(self.y)), self.radius // 2
    )


# --- TANK CLASS ---
class Tank:

  def __init__(self, x, y, color, controls, name):
    self.x = x
    self.y = y
    self.spawn_x = x
    self.spawn_y = y
    self.angle = 0
    self.color = color
    self.controls = controls  # Dict: 'up', 'down', 'left', 'right', 'shoot'
    self.name = name

    self.speed = 3.5
    self.turn_speed = 0.06
    self.health = 100
    self.max_health = 100
    self.score = 0
    self.cooldown = 0
    self.radius = 20

  def reset(self):
    self.x = self.spawn_x
    self.y = self.spawn_y
    self.health = self.max_health
    self.angle = 0
    self.cooldown = 0

  def handle_input(self, keys, bullets, obstacles):
    if self.cooldown > 0:
      self.cooldown -= 1

    # Movement & Turning
    if keys[self.controls['left']]:
      self.angle -= self.turn_speed
    if keys[self.controls['right']]:
      self.angle += self.turn_speed

    move = 0
    if keys[self.controls['up']]:
      move += self.speed
    if keys[self.controls['down']]:
      move -= self.speed * 0.6  # Slower backwards

    if move != 0:
      new_x = self.x + math.cos(self.angle) * move
      new_y = self.y + math.sin(self.angle) * move

      # Check screen collision
      if self.radius <= new_x <= WIDTH - self.radius:
        if not self._check_obstacle_collision(
            new_x, self.y, obstacles
        ):
          self.x = new_x
      if self.radius <= new_y <= HEIGHT - self.radius:
        if not self._check_obstacle_collision(
            self.x, new_y, obstacles
        ):
          self.y = new_y

    # Shooting
    if keys[self.controls['shoot']] and self.cooldown == 0:
      barrel_length = 26
      bullet_x = self.x + math.cos(self.angle) * barrel_length
      bullet_y = self.y + math.sin(self.angle) * barrel_length
      bullets.append(
          Bullet(bullet_x, bullet_y, self.angle, self.color, self.name)
      )
      self.cooldown = 18  # Frames between shots

  def _check_obstacle_collision(self, next_x, next_y, obstacles):
    tank_rect = pygame.Rect(
        next_x - self.radius,
        next_y - self.radius,
        self.radius * 2,
        self.radius * 2,
    )
    return any(tank_rect.colliderect(obs) for obs in obstacles)

  def draw(self, surface):
    # Base circle body
    pygame.draw.circle(
        surface, self.color, (int(self.x), int(self.y)), self.radius
    )
    pygame.draw.circle(
        surface, (20, 20, 30), (int(self.x), int(self.y)), self.radius - 4
    )

    # Turret Barrel
    barrel_len = 28
    end_x = self.x + math.cos(self.angle) * barrel_len
    end_y = self.y + math.sin(self.angle) * barrel_len
    pygame.draw.line(
        surface,
        self.color,
        (self.x, self.y),
        (end_x, end_y),
        6,
    )

    # Center Dome
    pygame.draw.circle(
        surface, self.color, (int(self.x), int(self.y)), self.radius // 3
    )


# --- DRAW ENVIRONMENT ---
def draw_background(surface):
  surface.fill(BG_DARK)
  # Subtle grid pattern
  for x in range(0, WIDTH, 40):
    pygame.draw.line(surface, GRID_COLOR, (x, 0), (x, HEIGHT), 1)
  for y in range(0, HEIGHT, 40):
    pygame.draw.line(surface, GRID_COLOR, (0, y), (WIDTH, y), 1)


def draw_obstacles(surface, obstacles):
  for rect in obstacles:
    pygame.draw.rect(surface, OBSTACLE_COLOR, rect, border_radius=6)
    pygame.draw.rect(surface, OBSTACLE_BORDER, rect, width=2, border_radius=6)


# --- HUD & HEALTH BARS ---
def draw_ui(surface, p1, p2):
  # Player 1 HUD (Left)
  pygame.draw.rect(surface, (25, 30, 45), (20, 15, 200, 20), border_radius=4)
  h1_width = int(200 * max(0, p1.health / p1.max_health))
  if h1_width > 0:
    pygame.draw.rect(surface, P1_CYAN, (20, 15, h1_width, 20), border_radius=4)
  p1_text = FONT_MED.render(
      f"P1 (WASD): {p1.score}", True, P1_CYAN
  )
  surface.blit(p1_text, (20, 40))

  # Player 2 HUD (Right)
  pygame.draw.rect(
      surface, (25, 30, 45), (WIDTH - 220, 15, 200, 20), border_radius=4
  )
  h2_width = int(200 * max(0, p2.health / p2.max_health))
  if h2_width > 0:
    pygame.draw.rect(
        surface, P2_MAGENTA, (WIDTH - 220, 15, h2_width, 20), border_radius=4
    )
  p2_text = FONT_MED.render(
      f"P2 (ARROWS): {p2.score}", True, P2_MAGENTA
  )
  surface.blit(p2_text, (WIDTH - 220, 40))


# --- MAIN GAME LOOP ---
def main():
  # Setup Players
  controls_p1 = {
      'up': pygame.K_w,
      'down': pygame.K_s,
      'left': pygame.K_a,
      'right': pygame.K_d,
      'shoot': pygame.K_SPACE,
  }

  controls_p2 = {
      'up': pygame.K_UP,
      'down': pygame.K_DOWN,
      'left': pygame.K_LEFT,
      'right': pygame.K_RIGHT,
      'shoot': pygame.K_RETURN,
  }

  p1 = Tank(100, HEIGHT // 2, P1_CYAN, controls_p1, 'P1')
  p2 = Tank(WIDTH - 100, HEIGHT // 2, P2_MAGENTA, controls_p2, 'P2')

  # Strategic Obstacles in Arena
  obstacles = [
      pygame.Rect(WIDTH // 2 - 25, 80, 50, 160),
      pygame.Rect(WIDTH // 2 - 25, HEIGHT - 240, 50, 160),
      pygame.Rect(200, HEIGHT // 2 - 40, 80, 80),
      pygame.Rect(WIDTH - 280, HEIGHT // 2 - 40, 80, 80),
  ]

  bullets = []
  particles = []

  round_over = False
  winner_text = ""

  while True:
    CLOCK.tick(FPS)

    # --- EVENT HANDLING ---
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        pygame.quit()
        sys.exit()
      if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
          pygame.quit()
          sys.exit()
        if round_over and event.key == pygame.K_r:
          # Reset round state
          p1.reset()
          p2.reset()
          bullets.clear()
          particles.clear()
          round_over = False

    keys = pygame.key.get_pressed()

    # --- UPDATE LOGIC ---
    if not round_over:
      p1.handle_input(keys, bullets, obstacles)
      p2.handle_input(keys, bullets, obstacles)

      # Update bullets and check collisions
      for b in bullets[:]:
        b.update(obstacles)
        if not b.alive:
          # Impact effect on wall hit
          for _ in range(5):
            particles.append(Particle(b.x, b.y, GRAY))
          bullets.remove(b)
          continue

        # Hit detection on Player 1
        if b.owner != 'P1':
          dist_p1 = math.hypot(b.x - p1.x, b.y - p1.y)
          if dist_p1 < p1.radius + b.radius:
            p1.health -= 15
            b.alive = False
            for _ in range(12):
              particles.append(Particle(b.x, b.y, P1_CYAN))
            if b in bullets:
              bullets.remove(b)

        # Hit detection on Player 2
        if b.owner != 'P2':
          dist_p2 = math.hypot(b.x - p2.x, b.y - p2.y)
          if dist_p2 < p2.radius + b.radius:
            p2.health -= 15
            b.alive = False
            for _ in range(12):
              particles.append(Particle(b.x, b.y, P2_MAGENTA))
            if b in bullets:
              bullets.remove(b)

      # Check Win Condition
      if p1.health <= 0 or p2.health <= 0:
        round_over = True
        if p1.health <= 0 and p2.health <= 0:
          winner_text = "IT'S A DRAW!"
        elif p1.health <= 0:
          p2.score += 1
          winner_text = "PLAYER 2 (MAGENTA) WINS!"
        else:
          p1.score += 1
          winner_text = "PLAYER 1 (CYAN) WINS!"

    # Update visual particles
    for p in particles[:]:
      p.update()
      if p.lifetime <= 0:
        particles.remove(p)

    # --- RENDER DISPLAY ---
    draw_background(SCREEN)
    draw_obstacles(SCREEN, obstacles)

    for p in particles:
      p.draw(SCREEN)

    for b in bullets:
      b.draw(SCREEN)

    p1.draw(SCREEN)
    p2.draw(SCREEN)
    draw_ui(SCREEN, p1, p2)

    # Overlay text when a round finishes
    if round_over:
      overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
      overlay.fill((10, 12, 20, 200))
      SCREEN.blit(overlay, (0, 0))

      t1 = FONT_LARGE.render(winner_text, True, WHITE)
      t2 = FONT_MED.render("Press 'R' for Next Round", True, GRAY)

      SCREEN.blit(t1, (WIDTH // 2 - t1.get_width() // 2, HEIGHT // 2 - 50))
      SCREEN.blit(t2, (WIDTH // 2 - t2.get_width() // 2, HEIGHT // 2 + 20))

    pygame.display.flip()


if __name__ == '__main__':
  main()
