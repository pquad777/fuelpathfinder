import pygame
import os
import time

# 설정
TILE_SIZE = 60


FPS = 60

# 색상
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
DARKGRAY = (50, 50, 50)
ORANGE = (255, 165, 0)

from fuelpathfinder import FuelPathFinder

class Map: #맵 생성 규칙(첫 줄에 연료량, 벽 부수기 개수, 주유소 개수 지정. 두번째 줄부터 맵 나타냄. 가로는 20 세로 15 제한)
    def __init__(self, level=1):
        self.level = level
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.load_level(level)

    def load_level(self, level):
        filepath = os.path.join(self.BASE_DIR, 'levels', f'level{level}.txt')
        with open(filepath, 'r') as f:
            lines = [line.strip() for line in f.readlines()]
        self.fuel_capacity, self.break_limit, self.max_stations = map(int, lines[0].split(','))
        self.grid = [list(row) for row in lines[1:]]
        self.height = len(self.grid)
        self.width = max(len(row) for row in self.grid)
        self.start = self.find_symbol('S')
        self.goal = self.find_symbol('G')
        self.fuel_stations = set()
        self.breakable = level >= 1

    def find_symbol(self, symbol):
        for y, row in enumerate(self.grid):
            for x, val in enumerate(row):
                if val == symbol:
                    return (x, y)
        return None

    def is_valid(self, x, y):
        if 0 <= y < self.height:
            if 0 <= x < len(self.grid[y]):
                return self.grid[y][x] != 'X'
        return False

class Game:
    def __init__(self):
        pygame.init()
        self.current_level = 1
        self.font = pygame.font.SysFont("malgungothic", 18)
        self.big_font = pygame.font.SysFont("malgungothic", 48, bold=True)
        self.SIDE_UI_WIDTH = 300
        self.load_level(self.current_level)

        pygame.display.set_caption("A* Fuel Puzzle")
        self.load_images()
        self.clock = pygame.time.Clock()
        self.running = True
        self.blink_counter = 0
        self.blink_pos = None



    def load_level(self, level):
        self.map = Map(level)
        self.pathfinder = FuelPathFinder(self.map)
        self.path = None
        self.finished = False
        self.success = False
        self.car_pos_index = 0
        self.car_timer = 0
        self.blink_counter = 0
        self.blink_pos = None

        self.SCREEN_WIDTH = TILE_SIZE * self.map.width + self.SIDE_UI_WIDTH
        self.SCREEN_HEIGHT = TILE_SIZE * self.map.height
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))

    def load_image(self, path):
        image = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE))

    def load_images(self):
        self.images = {
            "floor": self.load_image("images/floor.png"),
            "wall": self.load_image("images/wall.png"),
            "start": self.load_image("images/start.png"),
            "goal": self.load_image("images/goal.png"),
            "path": self.load_image("images/path.png"),
            "blink": self.load_image("images/blink.png"),
            "fuel": self.load_image("images/fuel.png"),
            "car": self.load_image("images/car.png")
        }

    def draw_map(self):
        for y in range(self.map.height):
            for x in range(len(self.map.grid[y])):
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                tile = self.map.grid[y][x]
                pos = (x, y)

                # 기본 이미지 선택
                image = self.images["floor"]

                # 조건별 이미지 교체
                if self.blink_pos == pos and self.blink_counter % 10 < 5:
                    image = self.images["blink"]
                elif tile == 'X':
                    image = self.images["wall"]
                elif pos == self.map.start:
                    image = self.images["start"]
                elif pos == self.map.goal:
                    image = self.images["goal"]
                elif self.path and pos in self.path:
                    image = self.images["path"]

                self.screen.blit(image, rect)

                # UI용 테두리
                pygame.draw.rect(self.screen, DARKGRAY, rect, 1)

                # 주유소
                if pos in self.map.fuel_stations:
                    self.screen.blit(self.images["fuel"], rect)

        if self.blink_counter > 15:
            self.blink_pos = None

    def draw_ui(self):
        x_offset = self.map.width * TILE_SIZE + 10
        texts = [
            "[게임 규칙]",
            "- 마우스: 주유소 설치",
            "- 벽 클릭: 벽 제거 ",
            "- Enter: 경로 탐색 실행",
            "- R: 재시도",
            "- ●: 주유소, ㅁ: 벽",
            "",
            f"시작 연료: {self.map.fuel_capacity}",
            f"남은 주유소 설치 수: {self.map.max_stations - len(self.map.fuel_stations)}",
            f"남은 벽 제거 수: {self.map.break_limit}"
        ]
        for i, line in enumerate(texts):
            text = self.font.render(line, True, WHITE)
            self.screen.blit(text, (x_offset, 30 + i * 25))

    def animate_car(self):
        if self.path and self.car_pos_index < len(self.path):
            if pygame.time.get_ticks() - self.car_timer > 150:
                self.car_timer = pygame.time.get_ticks()
                self.car_pos_index += 1
            if self.car_pos_index < len(self.path):
                x, y = self.path[self.car_pos_index]
                rect = self.images["car"].get_rect(center=(x * TILE_SIZE + TILE_SIZE//2, y * TILE_SIZE + TILE_SIZE//2))
                self.screen.blit(self.images["car"], rect)

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and not self.finished:
                    mx, my = pygame.mouse.get_pos()    #위치를 픽셀단위로 받아옴
                    gx, gy = mx // TILE_SIZE, my // TILE_SIZE  #격자좌표로 반환
                    if gx >= self.map.width or gy >= self.map.height:
                        continue
                    if (gx, gy) in [self.map.start, self.map.goal]:
                        continue
                    if self.map.grid[gy][gx] == 'X' and self.map.break_limit > 0:
                        self.map.grid[gy][gx] = '.'
                        self.map.break_limit -= 1
                        self.blink_pos = (gx, gy)
                        self.blink_counter = 0
                    elif self.map.grid[gy][gx] == '.' and self.map.is_valid(gx, gy) and len(self.map.fuel_stations) < self.map.max_stations:
                        self.map.fuel_stations.add((gx, gy))

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and not self.finished:
                        self.path = self.pathfinder.find_path()
                        self.finished = True
                        self.success = self.path is not None
                        self.car_pos_index = 0
                        self.car_timer = pygame.time.get_ticks()
                    elif event.key == pygame.K_r:
                        self.load_level(self.current_level)

            self.screen.fill(BLACK)
            self.draw_map()
            self.draw_ui()
            if self.finished:
                if self.success:
                    text = self.big_font.render("CLEAR!", True, YELLOW)
                    rect = text.get_rect(center=(self.map.width * TILE_SIZE // 2, self.map.height * TILE_SIZE // 2))
                    self.screen.blit(text, rect)
                    self.animate_car()
                    if self.car_pos_index >= len(self.path):
                        pygame.display.flip()
                        time.sleep(2)
                        self.current_level += 1
                        try:
                            self.load_level(self.current_level)
                        except FileNotFoundError:
                            print("모든 레벨을 클리어했습니다!")
                            self.running = False
                else:
                    text = self.big_font.render("도달 실패! R 키로 재시도", True, RED)
                    rect = text.get_rect(center=(self.map.width * TILE_SIZE// 2, self.map.height * TILE_SIZE// 2))
                    self.screen.blit(text, rect)

            self.blink_counter += 1
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()

if __name__ == "__main__":
    Game().run()
