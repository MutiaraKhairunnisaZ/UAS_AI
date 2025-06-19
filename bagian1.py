import tkinter as tk
from tkinter import messagebox
import heapq
import time
import threading

GRID_SIZE = 20
CELL_SIZE = 30
ANIMATION_DELAY = 0.01

TOOLTIP_TEXT = {
    "empty": "Kosong",
    "wall": "Tembok",
    "start": "Titik Awal",
    "goal": "Titik Tujuan",
    "visited": "Telah Dikunjungi",
    "path": "Jalur Akhir"
}

class Node:
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.g = float('inf')
        self.h = 0
        self.f = float('inf')
        self.parent = None
        self.state = "empty"
        self.rect = None

    def __lt__(self, other):
        return self.f < other.f

class AStarGUI:
    def __init__(self, master):
        self.master = master
        self.grid = [[Node(r, c) for c in range(GRID_SIZE)] for r in range(GRID_SIZE)]

        self.frame = tk.Frame(master)
        self.frame.pack()

        self.canvas = tk.Canvas(self.frame, width=GRID_SIZE * CELL_SIZE, height=GRID_SIZE * CELL_SIZE)
        self.canvas.grid(row=0, column=0)

        self.info_panel = tk.Frame(self.frame)
        self.info_panel.grid(row=0, column=1, sticky="ns", padx=10)

        self.coord_label = tk.Label(self.info_panel, text="Koordinat: -, -")
        self.coord_label.pack(anchor="w")

        self.desc_label = tk.Label(self.info_panel, text="Status: -")
        self.desc_label.pack(anchor="w")

        tk.Label(self.info_panel, text="Legenda:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(10, 0))
        for color, label in [
            ("white", "Kosong"),
            ("black", "Tembok"),
            ("green", "Start"),
            ("red", "Goal"),
            ("skyblue", "Dikunjungi"),
            ("yellow", "Jalur")
        ]:
            f = tk.Frame(self.info_panel)
            f.pack(anchor="w")
            tk.Label(f, width=2, height=1, bg=color).pack(side="left")
            tk.Label(f, text=" " + label).pack(side="left")

        self.start_node = None
        self.goal_node = None
        self.draw_grid()

        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Motion>", self.on_hover)

        self.dragged_node_type = None

        self.control_frame = tk.Frame(master)
        self.control_frame.pack(pady=5)
        tk.Button(self.control_frame, text="Mulai", command=self.run_search).pack(side=tk.LEFT, padx=2)
        tk.Button(self.control_frame, text="Reset", command=self.reset_grid).pack(side=tk.LEFT, padx=2)

    def draw_grid(self):
        for row in self.grid:
            for node in row:
                x1 = node.col * CELL_SIZE
                y1 = node.row * CELL_SIZE
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE
                node.rect = self.canvas.create_rectangle(x1, y1, x2, y2, fill="white", outline="gray")

    def redraw_cell(self, node):
        color = self.get_color(node.state)
        self.canvas.itemconfig(node.rect, fill=color)

    def get_color(self, state):
        return {
            "empty": "white",
            "wall": "black",
            "start": "green",
            "goal": "red",
            "path": "yellow",
            "visited": "skyblue"
        }.get(state, "white")

    def get_node_at(self, event):
        row = event.y // CELL_SIZE
        col = event.x // CELL_SIZE
        if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
            return self.grid[row][col]
        return None

    def on_click(self, event):
        node = self.get_node_at(event)
        if node:
            if node.state == "start":
                self.dragged_node_type = "start"
            elif node.state == "goal":
                self.dragged_node_type = "goal"
            elif node.state == "wall":
                self.dragged_node_type = "wall"
            elif not self.start_node:
                node.state = "start"
                self.start_node = node
                self.redraw_cell(node)
            elif not self.goal_node and node != self.start_node:
                node.state = "goal"
                self.goal_node = node
                self.redraw_cell(node)
            elif node != self.start_node and node != self.goal_node:
                node.state = "wall"
                self.redraw_cell(node)

    def on_drag(self, event):
        node = self.get_node_at(event)
        if node and self.dragged_node_type:
            if self.dragged_node_type == "start" and node != self.goal_node:
                self.start_node.state = "empty"
                self.redraw_cell(self.start_node)
                node.state = "start"
                self.start_node = node
                self.redraw_cell(node)
            elif self.dragged_node_type == "goal" and node != self.start_node:
                self.goal_node.state = "empty"
                self.redraw_cell(self.goal_node)
                node.state = "goal"
                self.goal_node = node
                self.redraw_cell(node)
            elif self.dragged_node_type == "wall" and node not in [self.start_node, self.goal_node]:
                node.state = "wall"
                self.redraw_cell(node)

    def on_release(self, event):
        self.dragged_node_type = None

    def on_hover(self, event):
        node = self.get_node_at(event)
        if node:
            self.coord_label.config(text=f"Koordinat: ({node.row}, {node.col})")
            self.desc_label.config(text=f"Status: {TOOLTIP_TEXT.get(node.state, '-')}")
        else:
            self.coord_label.config(text="Koordinat: -, -")
            self.desc_label.config(text="Status: -")

    def reset_grid(self):
        self.start_node = None
        self.goal_node = None
        self.dragged_node_type = None
        for row in self.grid:
            for node in row:
                node.state = "empty"
                node.g = float('inf')
                node.f = float('inf')
                node.parent = None
                self.redraw_cell(node)

    def neighbors(self, node):
        directions = [(-1,0), (1,0), (0,-1), (0,1)]
        result = []
        for dr, dc in directions:
            r, c = node.row + dr, node.col + dc
            if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE:
                neighbor = self.grid[r][c]
                if neighbor.state != "wall":
                    result.append(neighbor)
        return result

    def heuristic(self, a, b):
        return abs(a.row - b.row) + abs(a.col - b.col)

    def run_search(self):
        thread = threading.Thread(target=self.start_search)
        thread.start()

    def start_search(self):
        if not self.start_node or not self.goal_node:
            messagebox.showwarning("Peringatan", "Tentukan titik START dan GOAL terlebih dahulu.")
            return

        print(f"=== Mencari jalur dari ({self.start_node.row}, {self.start_node.col}) ke ({self.goal_node.row}, {self.goal_node.col}) ===")

        for row in self.grid:
            for node in row:
                if node.state not in ["start", "goal", "wall"]:
                    node.state = "empty"
                node.g = float('inf')
                node.f = float('inf')
                node.parent = None
                self.redraw_cell(node)

        open_list = []
        self.start_node.g = 0
        self.start_node.f = self.heuristic(self.start_node, self.goal_node)
        heapq.heappush(open_list, self.start_node)

        visited_count = 0

        while open_list:
            current = heapq.heappop(open_list)

            if current == self.goal_node:
                self.reconstruct_path(current)
                print("✅ Jalur ditemukan!")
                print(f"Total node dijelajahi: {visited_count}")
                return

            if current != self.start_node:
                current.state = "visited"
                self.redraw_cell(current)
                print(f"Menjelajahi: ({current.row}, {current.col})")
                visited_count += 1
                time.sleep(ANIMATION_DELAY)

            for neighbor in self.neighbors(current):
                tentative_g = current.g + 1
                if tentative_g < neighbor.g:
                    neighbor.parent = current
                    neighbor.g = tentative_g
                    neighbor.f = tentative_g + self.heuristic(neighbor, self.goal_node)
                    if neighbor not in open_list:
                        heapq.heappush(open_list, neighbor)

        print("❌ Tidak ada jalur ke tujuan.")
        messagebox.showinfo("Info", "Tidak ada jalur ke tujuan.")

    def reconstruct_path(self, current):
        steps = []
        while current.parent and current != self.start_node:
            current = current.parent
            if current != self.start_node:
                current.state = "path"
                self.redraw_cell(current)
                steps.append((current.row, current.col))
                time.sleep(ANIMATION_DELAY)
        steps.reverse()
        print(f"Panjang jalur: {len(steps)} langkah")
        print("Langkah-langkah menuju goal:")
        for step in steps:
            print(f"→ {step}")

# === RUN APP ===
if __name__ == "__main__":
    root = tk.Tk()
    root.title("A* Pathfinding GUI + Tooltip + Legenda + Output")
    app = AStarGUI(root)
    root.mainloop()
