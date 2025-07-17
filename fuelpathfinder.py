# fuelpathfinder.py
import heapq

class FuelPathFinder:
    def __init__(self, game_map):
        self.map = game_map
        self.fuel_capacity = game_map.fuel_capacity          # 연료 한도

    def manhattan(self, a, b):
        return abs(a[0]-b[0]) + abs(a[1]-b[1])

    def find_path(self):
        move = [(-1,0),(1,0),(0,-1),(0,1)]
        start, goal = self.map.start, self.map.goal

        # (f, g, x, y, fuel, path)
        heap = [(self.manhattan(start, goal), 0,
                 start[0], start[1], self.fuel_capacity, [start])]
        visited = {}                   # (x,y) ➜ 남은 연료 최대값

        while heap:
            f, g, x, y, fuel, path = heapq.heappop(heap)
            if (x, y) == goal:
                return path

            if visited.get((x, y), -1) >= fuel:
                continue
            visited[(x, y)] = fuel

            for dx, dy in move:
                nx, ny = x + dx, y + dy
                if not self.map.is_valid(nx, ny):      # 벽(X) 은 여기서 걸러진다
                    continue

                new_fuel = (self.fuel_capacity
                         if (nx, ny) in self.map.fuel_stations
                         else fuel - 1)
                if new_fuel < 0:
                    continue

                new_g = g + 1
                new_f = new_g + self.manhattan((nx, ny), goal)
                heapq.heappush(heap, (new_f, new_g, nx, ny, new_fuel, path + [(nx, ny)]))

        return None    # 도달 불가
