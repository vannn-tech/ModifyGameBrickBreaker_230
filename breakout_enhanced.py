# breakout_enhanced.py
import tkinter as tk
import random
import os
import math

# ----------------------------
# Config
# ----------------------------
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 650
BRICK_COLS = 12
BRICK_ROWS_BASE = 4
BRICK_HEIGHT = 24
BRICK_GAP = 2
PADDLE_COLOR = "#0ea5a4"          # teal
BALL_COLOR = "#ffffff"
BG_COLOR = "#071022"              # deep navy
TEXT_COLOR = "#E6EEF6"
BRICK_COLORS = ['#60A5FA', '#34D399', '#F472B6', '#FCD34D', '#F87171']
HIGHSCORE_FILE = "highscore.txt"
POWERUP_CHANCE = 0.25  # chance that a destroyed brick spawns a powerup

# ----------------------------
# Sound helper (Windows winsound optional)
# ----------------------------
try:
    import winsound
    def play_sound(name):
        if name == 'hit':
            winsound.MessageBeep(winsound.MB_OK)
        elif name == 'brick':
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        elif name == 'power':
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        elif name == 'gameover':
            winsound.MessageBeep(winsound.MB_ICONHAND)
        else:
            pass
except Exception:
    def play_sound(name):
        # no-op when winsound not available
        return

# ----------------------------
# Highscore utilities
# ----------------------------
def load_highscore():
    if os.path.exists(HIGHSCORE_FILE):
        try:
            with open(HIGHSCORE_FILE, 'r') as f:
                return int(f.read().strip() or 0)
        except Exception:
            return 0
    return 0

def save_highscore(score):
    try:
        with open(HIGHSCORE_FILE, 'w') as f:
            f.write(str(score))
    except Exception:
        pass

# ----------------------------
# Particle for brick break
# ----------------------------
class Particle:
    def __init__(self, canvas, x, y, color):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.vx = random.uniform(-2.5, 2.5)
        self.vy = random.uniform(-4, -1)
        self.life = random.randint(10, 20)
        self.id = canvas.create_oval(x-2, y-2, x+2, y+2, fill=color, outline='')

    def update(self):
        self.life -= 1
        self.vy += 0.15  # gravity
        self.x += self.vx
        self.y += self.vy
        try:
            self.canvas.coords(self.id, self.x-2, self.y-2, self.x+2, self.y+2)
        except Exception:
            return False
        if self.life <= 0:
            try:
                self.canvas.delete(self.id)
            except Exception:
                pass
            return False
        return True

# ----------------------------
# PowerUp
# ----------------------------
class PowerUp:
    TYPES = ['paddle_big', 'slow_ball', 'multi_ball', 'laser', 'shield']

    def __init__(self, canvas, x, y, kind=None):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.kind = kind if kind else random.choice(PowerUp.TYPES)
        self.size = 18
        self.id = canvas.create_rectangle(x-self.size/2, y-self.size/2, x+self.size/2, y+self.size/2, fill='#111827', outline='')
        self.text = canvas.create_text(x, y, text=self._label(), fill='#fff', font=('Helvetica', 9))
        self.speed = 3

    def _label(self):
        short = {'paddle_big':'B', 'slow_ball':'S', 'multi_ball':'M', 'laser':'L', 'shield':'H'}
        return short.get(self.kind, '?')

    def update(self):
        self.y += self.speed
        try:
            self.canvas.move(self.id, 0, self.speed)
            self.canvas.move(self.text, 0, self.speed)
        except Exception:
            return False
        x1, y1, x2, y2 = self.canvas.coords(self.id)
        if y1 > WINDOW_HEIGHT:
            self.delete()
            return False
        return True

    def delete(self):
        try:
            self.canvas.delete(self.id)
            self.canvas.delete(self.text)
        except Exception:
            pass

# ----------------------------
# Ball (support multiple balls)
# ----------------------------
class Ball:
    def __init__(self, canvas, x, y, r, speed=5):
        self.canvas = canvas
        self.r = r
        self.id = canvas.create_oval(x-r, y-r, x+r, y+r, fill=BALL_COLOR, outline='')
        angle = random.uniform(-math.pi/4, math.pi/4)
        self.vx = speed * math.cos(angle)
        self.vy = -abs(speed * math.sin(angle) or -3)
        self.speed = speed

    def pos(self):
        return self.canvas.coords(self.id)

    def update(self):
        try:
            self.canvas.move(self.id, self.vx, self.vy)
        except Exception:
            return
        x1, y1, x2, y2 = self.canvas.coords(self.id)
        if x1 <= 0 or x2 >= WINDOW_WIDTH:
            self.vx *= -1
            play_sound('hit')
        if y1 <= 0:
            self.vy *= -1
            play_sound('hit')

    def reflect_y(self):
        self.vy = -abs(self.vy)

    def reflect_x(self):
        self.vx *= -1

    def speed_scale(self, scale):
        self.vx *= scale
        self.vy *= scale

    def delete(self):
        try:
            self.canvas.delete(self.id)
        except Exception:
            pass

# ----------------------------
# Paddle
# ----------------------------
class Paddle:
    def __init__(self, canvas):
        self.canvas = canvas
        self.width = 140
        self.height = 16
        self.x = WINDOW_WIDTH/2
        self.y = WINDOW_HEIGHT - 60
        self.id = canvas.create_rectangle(self.x - self.width/2, self.y - self.height/2,
                                          self.x + self.width/2, self.y + self.height/2,
                                          fill=PADDLE_COLOR, outline='')
        self.speed = 0
        self.keys_down = set()
        self.bind_keys()
        self.laser_ready = False

    def bind_keys(self):
        self.canvas.bind_all('<KeyPress-Left>', lambda e: self.set_key('Left', True))
        self.canvas.bind_all('<KeyPress-Right>', lambda e: self.set_key('Right', True))
        self.canvas.bind_all('<KeyRelease-Left>', lambda e: self.set_key('Left', False))
        self.canvas.bind_all('<KeyRelease-Right>', lambda e: self.set_key('Right', False))

    def set_key(self, key, pressed):
        if pressed:
            self.keys_down.add(key)
        else:
            self.keys_down.discard(key)
        self.set_speed(
            -10 if 'Left' in self.keys_down and 'Right' not in self.keys_down
            else 10 if 'Right' in self.keys_down and 'Left' not in self.keys_down
            else 0
        )

    def set_speed(self, v):
        self.speed = v

    def update(self):
        try:
            self.canvas.move(self.id, self.speed, 0)
            x1, _, x2, _ = self.canvas.coords(self.id)
            if x1 < 0:
                self.canvas.move(self.id, -x1, 0)
            if x2 > WINDOW_WIDTH:
                self.canvas.move(self.id, WINDOW_WIDTH - x2, 0)
        except Exception:
            pass

    def get_coords(self):
        return self.canvas.coords(self.id)

    def set_width(self, width):
        x1, y1, x2, y2 = self.get_coords()
        cx = (x1 + x2) / 2
        self.canvas.coords(self.id, cx - width/2, y1, cx + width/2, y2)

    def enable_laser(self):
        self.laser_ready = True

    def disable_laser(self):
        self.laser_ready = False

# ----------------------------
# Laser bullet
# ----------------------------
class Bullet:
    def __init__(self, canvas, x, y):
        self.canvas = canvas
        self.id = canvas.create_rectangle(x-3, y-12, x+3, y, fill='#fff', outline='')
        self.speed = -12

    def update(self):
        try:
            self.canvas.move(self.id, 0, self.speed)
            x1, y1, x2, y2 = self.canvas.coords(self.id)
            if y2 < 0:
                self.canvas.delete(self.id)
                return False
        except Exception:
            return False
        return True

# ----------------------------
# Main Game
# ----------------------------
class Game:
    def __init__(self, root):
        self.root = root
        root.title('Breakout — Enhanced')
        self.canvas = tk.Canvas(root, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, bg=BG_COLOR, highlightthickness=0)
        self.canvas.pack()

        # HUD
        self.score = 0
        self.lives = 3
        self.level = 1
        self.highscore = load_highscore()

        # Entities
        self.paddle = Paddle(self.canvas)
        self.balls = []
        self.bricks = []
        self.particles = []
        self.powerups = []
        self.bullets = []

        # Game state
        self.running = False
        self.game_over_flag = False

        # UI text
        self.score_text = self.canvas.create_text(14, 12, anchor='nw', fill=TEXT_COLOR, font=('Helvetica', 14), text=f'Score: {self.score}')
        self.lives_text = self.canvas.create_text(140, 12, anchor='nw', fill=TEXT_COLOR, font=('Helvetica', 14), text=f'Lives: {self.lives}')
        self.level_text = self.canvas.create_text(260, 12, anchor='nw', fill=TEXT_COLOR, font=('Helvetica', 14), text=f'Level: {self.level}')
        self.high_text = self.canvas.create_text(WINDOW_WIDTH-14, 12, anchor='ne', fill='#fca5a5', font=('Helvetica', 14), text=f'High: {self.highscore}')

        # Menu
        self.menu_id = None
        self.create_menu()

        # Bind mouse for restart button clicks
        self.canvas.bind('<Button-1>', self.on_click)
        self.canvas.bind_all('<space>', self.on_space)

        # Start loop
        self.loop()

    # ----------------------------
    def create_menu(self):
        # Simple center menu with Start and Restart
        w, h = 380, 220
        x0, y0 = WINDOW_WIDTH/2 - w/2, WINDOW_HEIGHT/2 - h/2
        self.menu_bg = self.canvas.create_rectangle(x0, y0, x0+w, y0+h, fill='#081226', outline='')
        self.menu_title = self.canvas.create_text(WINDOW_WIDTH/2, y0+40, text='BREAKOUT — ENHANCED', fill=TEXT_COLOR, font=('Helvetica', 20))
        self.start_btn = self.canvas.create_rectangle(WINDOW_WIDTH/2 - 80, y0+90, WINDOW_WIDTH/2 + 80, y0+130, fill='#10B981', outline='')
        self.start_text = self.canvas.create_text(WINDOW_WIDTH/2, y0+110, text='START', fill='#fff', font=('Helvetica', 14))

        self.restart_btn = self.canvas.create_rectangle(WINDOW_WIDTH/2 - 80, y0+140, WINDOW_WIDTH/2 + 80, y0+180, fill='#3B82F6', outline='')
        self.restart_text = self.canvas.create_text(WINDOW_WIDTH/2, y0+160, text='RESTART', fill='#fff', font=('Helvetica', 14))

        self.menu_id = (self.menu_bg, self.menu_title, self.start_btn, self.start_text, self.restart_btn, self.restart_text)

    def destroy_menu(self):
        if self.menu_id:
            for i in self.menu_id:
                try:
                    self.canvas.delete(i)
                except Exception:
                    pass
            self.menu_id = None

    def on_click(self, event):
        x, y = event.x, event.y
        if self.menu_id:
            # Start button
            x0, y0, x1, y1 = self.canvas.coords(self.start_btn)
            if x0 <= x <= x1 and y0 <= y <= y1:
                self.start_game()
                return
            # Restart button
            x0, y0, x1, y1 = self.canvas.coords(self.restart_btn)
            if x0 <= x <= x1 and y0 <= y <= y1:
                self.reset_game()
                return

    def on_space(self, event=None):
        if self.game_over_flag:
            self.reset_game()
        elif self.menu_id:
            self.start_game()

    # ----------------------------
    def start_game(self):
        self.destroy_menu()
        play_sound('power')
        self.running = True
        self.game_over_flag = False
        self.setup_level()

    def reset_game(self):
        # Reset entire game
        self.canvas.delete('gameover')
        self.score = 0
        self.lives = 3
        self.level = 1
        self.highscore = load_highscore()
        self.update_hud()
        self.clear_entities()
        self.destroy_menu()
        self.running = True
        self.setup_level()

    def clear_entities(self):
        for b in list(self.balls):
            b.delete()
        self.balls = []
        for br in list(self.bricks):
            try:
                self.canvas.delete(br['id'])
            except Exception:
                pass
        self.bricks = []
        for p in list(self.particles):
            try:
                self.canvas.delete(p.id)
            except Exception:
                pass
        self.particles = []
        for pu in list(self.powerups):
            pu.delete()
        self.powerups = []
        for bl in list(self.bullets):
            try:
                self.canvas.delete(bl.id)
            except Exception:
                pass
        self.bullets = []
        # remove shield if exists
        if hasattr(self, 'shield'):
            try:
                self.canvas.delete(self.shield)
                delattr(self, 'shield')
            except Exception:
                pass

    # ----------------------------
    def setup_level(self):
        self.clear_entities()
        self.create_bricks()
        self.spawn_ball()
        self.update_hud()

    def create_bricks(self):
        rows = BRICK_ROWS_BASE + self.level - 1
        brick_w = WINDOW_WIDTH / BRICK_COLS
        for r in range(rows):
            for c in range(BRICK_COLS):
                x = c * brick_w
                y = r * (BRICK_HEIGHT + BRICK_GAP) + 60
                color = BRICK_COLORS[r % len(BRICK_COLORS)]
                id = self.canvas.create_rectangle(x+1, y+1, x+brick_w-1, y+BRICK_HEIGHT-1, fill=color, outline='')
                self.bricks.append({'id': id, 'hits': 1 + (r // 2), 'color': color})

    def spawn_ball(self):
        # place ball above paddle
        px1, py1, px2, py2 = self.paddle.get_coords()
        cx = (px1 + px2)/2
        ball = Ball(self.canvas, cx, py1 - 16, 8, speed=5 + self.level)
        self.balls.append(ball)

    # ----------------------------
    def update_hud(self):
        self.canvas.itemconfig(self.score_text, text=f'Score: {self.score}')
        self.canvas.itemconfig(self.lives_text, text=f'Lives: {self.lives}')
        self.canvas.itemconfig(self.level_text, text=f'Level: {self.level}')
        self.canvas.itemconfig(self.high_text, text=f'High: {self.highscore}')

    # ----------------------------
    def loop(self):
        # update all moving entities
        if self.running and not self.game_over_flag:
            # update paddle
            self.paddle.update()

            # update balls
            for ball in list(self.balls):
                ball.update()
                self.handle_ball_collisions(ball)

            # update bullets
            for b in list(self.bullets):
                alive = b.update()
                if not alive:
                    try:
                        self.bullets.remove(b)
                    except ValueError:
                        pass
                else:
                    self.check_bullet_hits(b)

            # update particles
            for p in list(self.particles):
                alive = p.update()
                if not alive:
                    try:
                        self.particles.remove(p)
                    except ValueError:
                        pass

            # update powerups
            for pu in list(self.powerups):
                alive = pu.update()
                if not alive:
                    try:
                        self.powerups.remove(pu)
                    except ValueError:
                        pass
                else:
                    self.check_powerup_catch(pu)

            # automatic laser fire
            if self.paddle.laser_ready and random.random() < 0.03:
                x1, y1, x2, y2 = self.paddle.get_coords()
                bx = (x1+x2)/2
                bullet = Bullet(self.canvas, bx, y1)
                self.bullets.append(bullet)

            # check level completion
            if not self.bricks:
                self.level += 1
                self.running = False
                play_sound('power')
                self.canvas.create_text(WINDOW_WIDTH/2, WINDOW_HEIGHT/2, text=f'Level {self.level}', fill=TEXT_COLOR, font=('Helvetica', 28), tag='levelup')
                def next_level():
                    try:
                        self.canvas.delete('levelup')
                    except Exception:
                        pass
                    self.setup_level()
                    self.running = True
                self.root.after(1300, next_level)

        self.root.after(16, self.loop)

    # ----------------------------
    def handle_ball_collisions(self, ball):
        x1, y1, x2, y2 = ball.pos()
        if hasattr(self, 'shield') and ball.vy > 0 and y2 >= WINDOW_HEIGHT - 20:
            self.canvas.move(ball.id, 0, WINDOW_HEIGHT - 20 - y2)
            ball.reflect_y()
            play_sound('hit')
            x1, y1, x2, y2 = ball.pos()

        # bottom check
        if y2 >= WINDOW_HEIGHT:
            # remove this ball
            ball.delete()
            try:
                self.balls.remove(ball)
            except ValueError:
                pass
            if not self.balls:
                self.lives -= 1
                self.update_hud()
                play_sound('gameover')
                if self.lives <= 0:
                    self.end_game()
                else:
                    # restart level after short pause and resume running
                    def restart_level():
                        self.setup_level()
                        self.running = True
                    self.running = False
                    self.root.after(800, restart_level)
            return

        # paddle collision
        px1, py1, px2, py2 = self.paddle.get_coords()
        if not (x2 < px1 or x1 > px2 or y2 < py1 or y1 > py2):
            # reflect with angle based on hit position
            cx = (x1+x2)/2
            rel = (cx - (px1+px2)/2) / ((px2-px1)/2)  # -1..1
            angle = rel * (math.pi/3)  # max 60 degrees
            speed = math.hypot(ball.vx, ball.vy)
            ball.vx = speed * math.sin(angle)
            ball.vy = -abs(speed * math.cos(angle))
            play_sound('hit')

        # brick collisions
        for br in list(self.bricks):
            bx1, by1, bx2, by2 = self.canvas.coords(br['id'])
            if not (x2 < bx1 or x1 > bx2 or y2 < by1 or y1 > by2):
                # collision
                play_sound('brick')
                self.spawn_particles((bx1+bx2)/2, (by1+by2)/2, br['color'])
                br['hits'] -= 1
                # score depends on hits initial value - simpler: +10 per brick
                self.score += 10
                self.update_hud()

                if random.random() < POWERUP_CHANCE:
                    pu = PowerUp(self.canvas, (bx1+bx2)/2, (by1+by2)/2)
                    self.powerups.append(pu)

                # remove or recolor
                if br['hits'] <= 0:
                    try:
                        self.canvas.delete(br['id'])
                    except Exception:
                        pass
                    try:
                        self.bricks.remove(br)
                    except ValueError:
                        pass
                else:
                    # darken color
                    try:
                        self.canvas.itemconfig(br['id'], fill=br['color'])
                    except Exception:
                        pass

                # reflect ball - simple reflect y
                ball.vy *= -1
                break

    # ----------------------------
    def spawn_particles(self, x, y, color):
        for _ in range(12):
            p = Particle(self.canvas, x, y, color)
            self.particles.append(p)

    # ----------------------------
    def check_powerup_catch(self, pu):
        try:
            x1, y1, x2, y2 = self.canvas.coords(pu.id)
        except Exception:
            return
        px1, py1, px2, py2 = self.paddle.get_coords()
        if not (x2 < px1 or x1 > px2 or y2 < py1 or y1 > py2):
            kind = pu.kind
            pu.delete()
            try:
                self.powerups.remove(pu)
            except ValueError:
                pass
            play_sound('power')
            # apply effect
            if kind == 'paddle_big':
                self.paddle.set_width(260)
                self.root.after(10000, lambda: self.paddle.set_width(140))
            elif kind == 'slow_ball':
                for b in self.balls:
                    b.speed_scale(0.6)
                self.root.after(8000, lambda: [b.speed_scale(1/0.6) for b in self.balls])
            elif kind == 'multi_ball':
                # duplicate existing balls (max 5 total)
                new = []
                for b in list(self.balls):
                    if len(self.balls) + len(new) >= 5: break
                    cx1, cy1, cx2, cy2 = b.pos()
                    cx = (cx1+cx2)/2
                    nb = Ball(self.canvas, cx+10, cy1, 8, speed=abs(b.vx)+1)
                    nb.vx = -b.vx
                    nb.vy = -b.vy
                    new.append(nb)
                self.balls.extend(new)
            elif kind == 'laser':
                self.paddle.enable_laser()
                self.root.after(10000, lambda: self.paddle.disable_laser())
            elif kind == 'shield':
                # create shield rect above bottom (safe create)
                try:
                    self.shield = self.canvas.create_rectangle(0, WINDOW_HEIGHT-20, WINDOW_WIDTH, WINDOW_HEIGHT, fill='#0ea5a4', stipple='gray25', outline='')
                    def remove_shield():
                        try:
                            if hasattr(self, 'shield'):
                                self.canvas.delete(self.shield)
                                delattr(self, 'shield')
                        except Exception:
                            pass
                    self.root.after(8000, remove_shield)
                except Exception:
                    pass

    # ----------------------------
    def check_bullet_hits(self, bullet):
        try:
            bx1, by1, bx2, by2 = self.canvas.coords(bullet.id)
        except Exception:
            return
        for br in list(self.bricks):
            bx1b, by1b, bx2b, by2b = self.canvas.coords(br['id'])
            if not (bx2 < bx1b or bx1 > bx2b or by2 < by1b or by1 > by2b):
                # hit
                self.spawn_particles((bx1b+bx2b)/2, (by1b+by2b)/2, br['color'])
                self.score += 10
                self.update_hud()
                try:
                    self.canvas.delete(br['id'])
                except Exception:
                    pass
                try:
                    self.bricks.remove(br)
                except ValueError:
                    pass
                try:
                    self.canvas.delete(bullet.id)
                except Exception:
                    pass
                try:
                    self.bullets.remove(bullet)
                except Exception:
                    pass
                break

    # ----------------------------
    def end_game(self):
        self.running = False
        self.game_over_flag = True
        if self.score > self.highscore:
            self.highscore = self.score
            save_highscore(self.score)
        self.canvas.create_text(WINDOW_WIDTH/2, WINDOW_HEIGHT/2, text=f'GAME OVER\nScore: {self.score}', fill='#f87171', font=('Helvetica', 28), tag='gameover')

# ----------------------------
# Run
# ----------------------------
if __name__ == '__main__':
    root = tk.Tk()
    root.resizable(False, False)
    Game(root)
    root.mainloop()
