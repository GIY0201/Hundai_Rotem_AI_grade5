import random
import sys
from dataclasses import dataclass
from typing import List

import pygame

import sys, os

def resource_path(relative_path):
    """EXE 파일 안에서도 리소스를 찾을 수 있게 함"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# Screen configuration
WIDTH, HEIGHT = 480, 680
ROAD_MARGIN = 80
LANE_COUNT = 4
LANE_WIDTH = (WIDTH - ROAD_MARGIN * 2) // LANE_COUNT

# Car sizing
PLAYER_CAR_WIDTH = int(LANE_WIDTH * 0.65)
PLAYER_CAR_HEIGHT = 80
TRAFFIC_CAR_WIDTH = int(LANE_WIDTH * 0.6)
TRAFFIC_CAR_HEIGHT = 90

# Colors
ROAD_COLOR = (45, 45, 45)
BACKGROUND_COLOR = (20, 20, 20)
LANE_MARKER_COLOR = (200, 200, 200)
PLAYER_COLOR = (255, 215, 0)  # golden criminal car
PLAYER_ACCENT = (214, 162, 0)
PLAYER_WINDOW = (35, 35, 40)
POLICE_LIGHT_COLOR = (52, 152, 219)
TRAFFIC_COLOR = (236, 112, 99)
TRAFFIC_ACCENT = (203, 67, 53)
TRAFFIC_WINDOW = (45, 50, 65)
HUD_TEXT_COLOR = (245, 245, 245)
GAME_OVER_OVERLAY = (0, 0, 0, 160)


@dataclass
class TrafficCar:
    rect: pygame.Rect
    speed: float
    was_counted: bool = False


def lane_center(lane_index: int) -> int:
    lane_x = ROAD_MARGIN + lane_index * LANE_WIDTH
    return lane_x + (LANE_WIDTH - PLAYER_CAR_WIDTH) // 2


def init_player() -> pygame.Rect:
    x = lane_center(LANE_COUNT // 2)
    y = HEIGHT - PLAYER_CAR_HEIGHT - 20
    return pygame.Rect(x, y, PLAYER_CAR_WIDTH, PLAYER_CAR_HEIGHT)


def spawn_traffic_car() -> TrafficCar:
    lane_index = random.randrange(LANE_COUNT)
    x = ROAD_MARGIN + lane_index * LANE_WIDTH + (LANE_WIDTH - TRAFFIC_CAR_WIDTH) // 2
    rect = pygame.Rect(x, -TRAFFIC_CAR_HEIGHT, TRAFFIC_CAR_WIDTH, TRAFFIC_CAR_HEIGHT)
    base_speed = random.uniform(3.5, 5.0)
    return TrafficCar(rect=rect, speed=base_speed)


def draw_road(surface: pygame.Surface, scroll_offset: float) -> None:
    surface.fill(BACKGROUND_COLOR)
    pygame.draw.rect(surface, ROAD_COLOR, (ROAD_MARGIN, 0, WIDTH - ROAD_MARGIN * 2, HEIGHT))

    marker_height = 40
    gap = 20
    for lane_index in range(1, LANE_COUNT):
        x = ROAD_MARGIN + lane_index * LANE_WIDTH
        marker_x = x - 2
        y = -marker_height + scroll_offset % (marker_height + gap)
        while y < HEIGHT:
            pygame.draw.rect(surface, LANE_MARKER_COLOR, (marker_x, y, 4, marker_height))
            y += marker_height + gap

    # Stylized police lights at the top to set the chase mood
    pygame.draw.rect(surface, POLICE_LIGHT_COLOR, (0, 0, WIDTH // 3, 40))
    pygame.draw.rect(surface, (192, 57, 43), (WIDTH * 2 // 3, 0, WIDTH // 3, 40))


def draw_player(surface: pygame.Surface, rect: pygame.Rect) -> None:
    pygame.draw.rect(surface, PLAYER_COLOR, rect, border_radius=8)
    windshield = pygame.Rect(rect.x + rect.width * 0.15, rect.y + 10, rect.width * 0.7, 20)
    pygame.draw.rect(surface, (30, 30, 30), windshield, border_radius=4)


def draw_traffic(surface: pygame.Surface, traffic: List[TrafficCar]) -> None:
    for car in traffic:
        pygame.draw.rect(surface, TRAFFIC_COLOR, car.rect, border_radius=6)
        light_width = car.rect.width // 4
        pygame.draw.rect(
            surface,
            (255, 255, 255),
            (car.rect.x + car.rect.width // 2 - light_width // 2, car.rect.y + 10, light_width, 12),
            border_radius=2,
        )


def draw_hud(surface: pygame.Surface, font: pygame.font.Font, score: int, pace: float, heat_level: int) -> None:
    text = font.render(f"Escaped Cars: {score}", True, HUD_TEXT_COLOR)
    surface.blit(text, (16, 16))
    level_text = font.render(f"Heat Level: {heat_level}", True, HUD_TEXT_COLOR)
    surface.blit(level_text, (16, 50))
    pace_text = font.render(f"Pace: {pace:.1f}x", True, HUD_TEXT_COLOR)
    surface.blit(pace_text, (16, 84))


def draw_game_over(surface: pygame.Surface, font: pygame.font.Font, score: int) -> None:
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill(GAME_OVER_OVERLAY)
    surface.blit(overlay, (0, 0))

    title = font.render("Caught!", True, HUD_TEXT_COLOR)
    info = font.render("Press SPACE to try again", True, HUD_TEXT_COLOR)
    score_text = font.render(f"Escaped Cars: {score}", True, HUD_TEXT_COLOR)

    surface.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40)))
    surface.blit(score_text, score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
    surface.blit(info, info.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40)))


def update_traffic(traffic: List[TrafficCar], difficulty_scale: float, dt: float) -> None:
    for car in traffic:
        car.rect.y += (car.speed + difficulty_scale) * dt


def remove_offscreen_cars(traffic: List[TrafficCar]) -> List[TrafficCar]:
    return [car for car in traffic if car.rect.y <= HEIGHT + TRAFFIC_CAR_HEIGHT]


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Police Escape - Dodge & Dash")
    clock = pygame.time.Clock()

    hud_font = pygame.font.SysFont("arial", 26, bold=True)

    player = init_player()
    player_lane = LANE_COUNT // 2
    strafe_offset = 0.0
    traffic: List[TrafficCar] = []
    score = 0
    time_since_spawn = 0.0
    spawn_interval = 900  # milliseconds
    difficulty = 0.0
    scroll_offset = 0.0
    game_over = False

    while True:
        dt_ms = clock.tick(60)
        dt = dt_ms / 16.666  # normalize to ~60 FPS units
        scroll_offset += 200 * dt * 0.1
        difficulty += 0.00005 * dt_ms

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_SPACE and game_over:
                    player = init_player()
                    player_lane = LANE_COUNT // 2
                    strafe_offset = 0.0
                    traffic.clear()
                    score = 0
                    time_since_spawn = 0.0
                    difficulty = 0.0
                    game_over = False
                if not game_over:
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        player_lane = max(0, player_lane - 1)
                        strafe_offset = 0.0
                    if event.key in (pygame.K_RIGHT, pygame.K_d):
                        player_lane = min(LANE_COUNT - 1, player_lane + 1)
                        strafe_offset = 0.0

        score_tier = score // 10
        tier_bonus = score_tier * 0.6
        effective_difficulty = difficulty + tier_bonus

        keys = pygame.key.get_pressed()
        if not game_over:
            strafe_speed = 7.0
            if keys[pygame.K_q]:
                strafe_offset -= strafe_speed * dt
            if keys[pygame.K_e]:
                strafe_offset += strafe_speed * dt

            base_x = lane_center(player_lane)
            road_left = ROAD_MARGIN + 6
            road_right = WIDTH - ROAD_MARGIN - PLAYER_CAR_WIDTH - 6

            player.x = int(base_x + strafe_offset)
            if player.x < road_left:
                player.x = road_left
                strafe_offset = player.x - base_x
            if player.x > road_right:
                player.x = road_right
                strafe_offset = player.x - base_x

            time_since_spawn += dt_ms
            current_interval = max(360, spawn_interval - effective_difficulty * 120)
            if time_since_spawn >= current_interval:
                time_since_spawn = 0.0
                traffic.append(spawn_traffic_car())

            update_traffic(traffic, effective_difficulty * 0.5, dt)

            for car in traffic:
                if car.rect.colliderect(player):
                    game_over = True
                    break
                if car.rect.y > player.bottom and not car.was_counted:
                    car.was_counted = True
                    score += 1
                    score_tier = score // 10
                    tier_bonus = score_tier * 0.6
                    effective_difficulty = difficulty + tier_bonus

            traffic = remove_offscreen_cars(traffic)

        draw_road(screen, scroll_offset)
        draw_traffic(screen, traffic)
        draw_player(screen, player)
        draw_hud(screen, hud_font, score, 1 + effective_difficulty, score_tier)

        if game_over:
            draw_game_over(screen, hud_font, score)

        pygame.display.flip()


if __name__ == "__main__":
    main()
