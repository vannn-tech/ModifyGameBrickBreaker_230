# Breakout Game Modern Version (FULLY FIXED)

import tkinter as tk
import random
import os

# ===========================
# GLOBAL SETTINGS
# ===========================
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
BRICK_COLS = 10
BRICK_ROWS = 5
BRICK_COLORS = ["#6EE7B7", "#93C5FD", "#F9A8D4", "#FCD34D", "#FCA5A5"]
BALL_COLOR = "#FFFFFF"
PADDLE_COLOR = "#1E3A8A"
BG_COLOR = "#0F172A"
TEXT_COLOR = "#E2E8F0"

HIGHSCORE_FILE = "highscore.txt"


# ===========================
# LOAD/SAVE HIGH SCORE
# ===========================
def load_highscore():
    if os.path.exists(HIGHSCORE_FILE):
        try:
            return int(open(HIGHSCORE_FILE, "r").read())
        except:
            return 0
    return 0


def save_highscore(score):
    with open(HIGHSCORE_FILE, "w") as f:
        f.write(str(score))


# ===========================
# BASE CLASS
# ===========================
class GameObject:
    def __init__(self, canvas, x1, y1, x2, y2, color):
        self.canvas = canvas
        self.id = canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

    def intersects(self, other):
        x1, y1, x2, y2 = self.canvas.coords(self.id)
        ox1, oy1, ox2, oy2 = self.canvas.coords(other.id)
        return not (x2 < ox1 or x1 > ox2 or y2 < oy1 or y1 > oy2)


# ===========================
# BALL
# ===========================
class Ball(GameObject):
    def __init__(self, canvas, x, y, size, speed):
        super().__init__(canvas, x, y, x + size, y + size, BALL_COLOR)
        self.speed_x = speed
        self.speed_y = -speed

    def update(self):
        self.canvas.move(self.id, self.speed_x, self.speed_y)

        x1, y1, x2, y2 = self.canvas.coords(self.id)

        if x1 <= 0 or x2 >= WINDOW_WIDTH:
            self.speed_x *= -1
        if y1 <= 0:
            self.speed_y *= -1


# ===========================
# PADDLE
# ===========================
class Paddle(GameObject):
    def __init__(self, canvas):
        super().__init__(canvas, 350, 570, 450, 580, PADDLE_COLOR)
        self.speed_x = 0
        canvas.bind_all('<KeyPress-Left>', self.move_left)
        canvas.bind_all('<KeyPress-Right>', self.move_right)
        canvas.bind_all('<KeyRelease>', self.stop)

    def move_left(self, event):
        self.speed_x = -8

    def move_right(self, event):
        self.speed_x = 8

    def stop(self, event):
        self.speed_x = 0

    def update(self):
        self.canvas.move(self.id, self.speed_x, 0)
        x1, y1, x2, y2 = self.canvas.coords(self.id)
        if x1 < 0:
            self.canvas.move(self.id, -x1, 0)
        if x2 > WINDOW_WIDTH:
            self.canvas.move(self.id, WINDOW_WIDTH - x2, 0)


# ===========================
# BRICK
# ===========================
class Brick(GameObject):
    def __init__(self, canvas, x, y, width, height, color):
        super().__init__(canvas, x, y, x + width, y + height, color)


# ===========================
# GAME SYSTEM
# ===========================
class Game:
    def __init__(self, root):
        self.root = root
        self.canvas = tk.Canvas(root, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, bg=BG_COLOR, highlightthickness=0)
        self.canvas.pack()

        self.paddle = Paddle(self.canvas)
        self.ball = None

        self.lives = 3
        self.score = 0
        self.highscore = load_highscore()
        self.level = 1
        self.running = False

        self.create_ui()
        self.setup_level()

        self.root.after(16, self.game_loop)

    # ------------------------------
    def create_ui(self):
        self.score_text = self.canvas.create_text(70, 20, fill=TEXT_COLOR, font=("Montserrat", 18), text="Score: 0")
        self.level_text = self.canvas.create_text(400, 20, fill=TEXT_COLOR, font=("Montserrat", 18), text="Level 1")
        self.highscore_text = self.canvas.create_text(730, 20, fill="#FACC15", font=("Montserrat", 18),
                                                      text=f"High Score: {self.highscore}")

        # Start text
        self.draw_text = self.canvas.create_text(
            400, 300, text="Press SPACE to Start", fill=TEXT_COLOR, font=("Montserrat", 24)
        )

        self.root.bind("<KeyPress-space>", lambda e: self.start())

    # ------------------------------
    def setup_level(self):
        if self.ball:
            self.canvas.delete(self.ball.id)
        self.ball = Ball(self.canvas, 390, 300, 15, 4 + self.level)

        # Delete old bricks
        self.bricks = []
        self.canvas.delete("brick")

        brick_width = WINDOW_WIDTH // BRICK_COLS
        brick_height = 25

        for row in range(BRICK_ROWS):
            for col in range(BRICK_COLS):
                x = col * brick_width
                y = row * brick_height + 50
                color = BRICK_COLORS[row % len(BRICK_COLORS)]
                brick = Brick(self.canvas, x, y, brick_width - 2, brick_height - 2, color)
                self.bricks.append(brick)

    # ------------------------------
    def start(self):
        if not self.running:
            self.running = True
            self.canvas.delete(self.draw_text)

    # ------------------------------
    def game_loop(self):
        if self.running:
            self.ball.update()
            self.paddle.update()
            self.check_collisions()
            self.check_fail()

        self.root.after(16, self.game_loop)

    # ------------------------------
    def check_collisions(self):
        if self.ball.intersects(self.paddle):
            self.ball.speed_y *= -1

        for brick in self.bricks[:]:
            if self.ball.intersects(brick):
                self.score += 10
                self.canvas.itemconfig(self.score_text, text=f"Score: {self.score}")
                self.animate_brick(brick)
                self.ball.speed_y *= -1
                self.bricks.remove(brick)

        # LEVEL CLEAR
        if not self.bricks:
            self.level += 1
            self.canvas.itemconfig(self.level_text, text=f"Level {self.level}")
            self.running = False
            self.setup_level()

    # ------------------------------
    def animate_brick(self, brick):
        for _ in range(5):
            self.canvas.move(brick.id, 0, -2)
            self.canvas.update()
            self.canvas.after(5)
        self.canvas.delete(brick.id)

    # ------------------------------
    def check_fail(self):
        _, _, _, y2 = self.canvas.coords(self.ball.id)
        if y2 >= WINDOW_HEIGHT:
            self.lives -= 1

            if self.lives <= 0:
                self.game_over()
            else:
                self.running = False
                self.setup_level()

    # ------------------------------
    def game_over(self):
        self.running = False

        if self.score > self.highscore:
            save_highscore(self.score)

        self.canvas.create_text(
            400, 300, fill="#F87171", font=("Montserrat", 32),
            text="GAME OVER\nScore: {}".format(self.score)
        )


# ===========================
# RUN
# ===========================
root = tk.Tk()
root.title("Breakout Modern Edition")
root.resizable(False, False)
Game(root)
root.mainloop()
