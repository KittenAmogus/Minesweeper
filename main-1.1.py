import time
import random
import threading
import tkinter as tk
from time import time_ns

from pygame import mixer


class Sound:
    def __init__(self):
        mixer.init()
        print("\x1b[2A\x1b[0K")
        print("\x1b[0K", end="")
        print("Minesweeper")
        self._win = mixer.Sound("assets/sounds/win.mp3")
        self._lose = mixer.Sound("assets/sounds/lose.mp3")
        self._tick = mixer.Sound("assets/sounds/tick.mp3")

    def win(self):
        mixer.stop()
        self._win.play()

    def lose(self):
        mixer.stop()
        self._lose.play()

    def tick(self):
        mixer.stop()
        self._tick.play()


class ButtonImages:
    def __init__(self):
        self.FLAG = tk.PhotoImage(file="assets/flag.png")
        self.CLOSED = tk.PhotoImage(file="assets/closed.png")
        self.EMPTY = tk.PhotoImage(file="assets/empty-open.png")
        self.DEAD_MINE = tk.PhotoImage(file="assets/dead-mine.png")
        self.MINE = tk.PhotoImage(file="assets/mine.png")
        self.FALSE_MINE = tk.PhotoImage(file="assets/not-mine.png")

        self.NUMS = [
            tk.PhotoImage(file=f"assets/nums/{i}.png") for i in range(1, 9)
        ]

        self.COUNTER_NUMS = [
            tk.PhotoImage(file=f"assets/counter/{i}.png") for i in range(0, 10)
        ]
        self.DASH = tk.PhotoImage(file="assets/counter/-.png")
        self.OFF = tk.PhotoImage(file="assets/counter/off.png")

        self.HAPPY = tk.PhotoImage(file="assets/smile/happy.png")
        self.SURPRISED = tk.PhotoImage(file="assets/smile/surprised.png")
        self.COOL = tk.PhotoImage(file="assets/smile/cool.png")
        self.DEAD = tk.PhotoImage(file="assets/smile/dead.png")


images: ButtonImages


class MyButton(tk.Label):
    def __init__(self, master: tk.Misc, xy: list[int], *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.x, self.y = xy
        self.near = 0

        self.is_mine = False
        self.is_flag = False
        self.is_open = False

    def flag(self, _event):
        if self.is_open:
            return 0
        self.is_flag = not self.is_flag
        if self.is_flag:
            self.config(image=images.FLAG)
            return -1
        else:
            self.config(image=images.CLOSED)
            return 1

    def game_over(self, win = False):
        if not win:
            if self.is_open: return
            self.is_open = True
            if self.is_flag:
                if self.is_mine:
                    return
                else:
                    self.config(image=images.FALSE_MINE)
            else:
                if self.is_mine:
                    self.config(image=images.MINE)
        else:
            if self.is_mine:
                self.config(image=images.FLAG)

    def open(self, _event):
        if self.is_open or self.is_flag: return
        self.unbind("<Button-1>")
        self.is_open = True
        if self.is_mine:
            self.config(image=images.DEAD_MINE)
        else:
            if self.near == 0:
                self.config(image=images.EMPTY)
            else:
                self.config(image=images.NUMS[self.near - 1])

    @property
    def xy(self):
        return self.x, self.y

    def __str__(self):
        return f"[{self.x} {self.y}] {self.is_flag} {self.is_mine} {self.is_open}"


class Smile:
    def __init__(self, master, func, row, col):
        self.func = func
        self.button = tk.Label(master, width=60, height=60, borderwidth=0, border=0, image=images.HAPPY)
        self.button.bind("<Button-1>", self.on_press)
        self.button.bind("<ButtonRelease-1>", self.on_release)
        self.button.grid(row=row, column=col, padx=15)
        # self._pop = False

    def on_press(self, _event):
        self.button.config(image=images.SURPRISED)

    def on_release(self, _event):
        self.button.config(image=images.HAPPY)
        self.func()
        # self._pop = False

    def game_over(self, win):
        if win:
            self.button.config(image=images.COOL)
        else:
            self.button.config(image=images.DEAD)

    # def pop(self):
    #     self._pop = True
    #     self.button.config(image=images.SURPRISED)



class Counter:
    def __init__(self, master, row, col):
        self.frame = tk.Frame(master)
        self.first, self.second, self.third = [
            tk.Label(self.frame, width=30, height=60, image=images.COUNTER_NUMS[0],
                     borderwidth=0, border=0) for _ in range(3)
        ]

        self.first.grid(row=0, column=0)
        self.second.grid(row=0, column=1)
        self.third.grid(row=0, column=2)

        self.frame.grid(row=row, column=col)

    @staticmethod
    def get_img(value):
        if value in "0123456789":
            return images.COUNTER_NUMS[int(value)]
        if value == "-":
            return images.DASH
        return images.COUNTER_NUMS[0]

    def draw(self, string):
        if len(string) < 3:
            string = (" " * (3 - len(string))) + string

        self.first.config(image=self.get_img(string[0]))
        self.second.config(image=self.get_img(string[1]))
        self.third.config(image=self.get_img(string[2]))


class Minesweeper:
    ROW = 16
    COLUMN = 16
    MINES = 40
    FONT = "Arial 15 bold"

    def _neighbors(self, cell: MyButton) -> list[MyButton]:
        nbs = []

        for ay in range(cell.y - 1, cell.y + 2):
            if ay < 0 or ay >= self.ROW:
                continue
            for ax in range(cell.x - 1, cell.x + 2):
                if ax < 0 or ax >= self.COLUMN:
                    continue
                if self.buttons[ay][ax] == cell:
                    continue
                nbs.append(self.buttons[ay][ax])

        return nbs

    def game_over(self, win = False):
        if not self.game:
            return
        self.game = False

        self.smile.game_over(win)

        print("\x1b[31m[LOSE]\x1b[0m" if not win else "\x1b[32m[WIN]\x1b[0m", "Game over")

        if win:
            if self._sound:
                self.sound.win()
            for row in self.buttons:
                for cell in row:
                    cell.game_over(True)
        else:
            if self._sound:
                self.sound.lose()
            for row in self.buttons:
                for cell in row:
                    cell.game_over()

    def _recalc_near(self, cell: MyButton):
        if cell.is_mine: return 0
        for nb in self._neighbors(cell):
            if nb.is_mine:
                cell.near += 1
        return cell.near

    def _open_with_near(self, button):
        queue: list[MyButton] = [button]
        checked = []
        while queue:
            cur = queue[0]
            queue.remove(cur)
            if cur.is_flag:
                checked.append(cur)
                continue
            if cur.is_open:
                checked.append(cur)
                continue
            cur.bind("<Button-3>", lambda _event, button=cur: self._open_near_if_flags(button))

            cur.open(None)
            self.free_cells -= 1

            if cur.near > 0:
                checked.append(cur)
                continue

            for neb in self._neighbors(cur):
                if not neb.is_mine:
                    queue.append(neb)

            checked.append(cur)

    def _flag_cell(self, event, cell: MyButton):
        if self.flags == 0 and not cell.is_flag:
            print("Run out of flags :(")
            return
        if not self.game:
            return
        self.flags += cell.flag(event)
        self.mine_counter.draw(str(self.flags))

    def _open_cell(self, cell: MyButton):
        if not self.game:
            return
        if cell.is_open or cell.is_flag:
            return
        if self._sound:
            self.sound.tick()
        if self.first:
            self.first = False
            seed = time.time_ns()**2%(10**8)  # 28082121 - 8 on 26, 12 (If not first-clicked)
            self._place_mines(seed, cell.xy)
            print(f"[SEED] \x1b[33m{seed}\x1b[0m")
        self._open_with_near(cell)
        if cell.is_mine:
            self.game_over(False)

        if self.free_cells == 0:
            self.game_over(True)

    def _difficulty(self, dif):
        match dif:
            case 0:
                self.ROW = 9; self.COLUMN = 9; self.MINES = 10
            case 1:
                self.ROW = 16; self.COLUMN = 16; self.MINES = 40
            case 2:
                self.ROW = 16; self.COLUMN = 30; self.MINES = 99
            case 3:
                self.ROW = 30; self.COLUMN = 30; self.MINES = 199
        self._restart()

    def _create_widgets(self):
        self.root.resizable(False, False)
        self.root.title("Minesweeper")

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        self.top_frame.grid(row=0, column=0)
        self.mine_area.grid(row=1, column=0, padx=5, pady=5)

        if not self.root["menu"]:
            self.main_menu = tk.Menu(self.root, tearoff=0)

            game_menu = tk.Menu(self.root, tearoff=0)
            difficulty_menu = tk.Menu(game_menu, tearoff=0)

            difficulty_menu.add_command(label="Easy", command=lambda: self._difficulty(0))
            difficulty_menu.add_command(label="Normal", command=lambda: self._difficulty(1))
            difficulty_menu.add_command(label="Expert", command=lambda: self._difficulty(2))
            difficulty_menu.add_command(label="God", command=lambda: self._difficulty(3))

            game_menu.add_cascade(menu=difficulty_menu, label="Difficulty")
            self.main_menu.add_cascade(menu=game_menu, label="Game")
            self.root["menu"] = self.main_menu

            self.time_counter = Counter(self.top_frame, row=0, col=2)
            self.mine_counter = Counter(self.top_frame, row=0, col=0)

        for row in range(self.ROW):
            _line = []
            for column in range(self.COLUMN):
                btn = MyButton(
                    self.mine_area, [column, row],
                    image=images.CLOSED,
                    highlightthickness=0,
                    borderwidth=0,
                    border=0,
                    padx=0, pady=0
               )
                btn.bind("<Button-1>", lambda _event, button=btn: self._open_cell(button))
                btn.bind("<Button-3>", lambda event, button=btn: self._flag_cell(event, button))
                _line.append(btn)
                btn.grid(row=row, column=column, padx=0, pady=0)
            self.buttons.append(_line)

    def _place_mines(self, seed=0, start=(0, 0)):
        random.seed(seed)
        cords = [(x, y) for y in range(self.ROW) for x in range(self.COLUMN)]
        cords.remove(start)

        for _ in range(self.MINES):
            cord = random.choice(cords)
            cords.remove(cord)

            self.buttons[cord[1]][cord[0]].is_mine = True
            # self.buttons[cord[1]][cord[0]].config(image=images.MINE)

        _max = 0
        for row in self.buttons:
            for cell in row:
                a = self._recalc_near(cell)
                _max = max([a, _max])
        print("Max cell:", _max)

    def _count_time(self, start):
        import time
        while self.game:
            if self.games > start:
                break
            self.time_counter.draw(str(round(self.time)))
            time.sleep(.1)
            self.time += .1
        return

    def _open_near_if_flags(self, cell: MyButton):
        # if not cell.is_open:
        #     return

        near_flags = 0
        for nb in self._neighbors(cell):
            if nb.is_flag:
                near_flags += 1
        if near_flags == cell.near:
            for nb in self._neighbors(cell):
                self._open_cell(nb)
        else:
            print(f"[{cell.x}, {cell.y}] \x1b[31m" + ("Too many flags" if near_flags > cell.near else "Not enough flags") + "\x1b[0m")
            # cell.unbind("<Button-3>")

    def _restart(self):
        for row in self.buttons:
            for btn in row:
                btn.destroy()
        self.sound.tick()
        self.smile.button.config(image=images.HAPPY)
        self.buttons.clear()
        self.games += 1
        self.game = False
        self.buttons.clear()
        self.flags = self.MINES
        self.free_cells = self.ROW * self.COLUMN - self.MINES
        self.time = 0
        self.run()

    def __init__(self):
        self.root = tk.Tk()
        self.main_menu: tk.Menu
        global images
        images = ButtonImages()
        self.top_frame = tk.Frame(self.root)
        self.mine_area = tk.Frame(self.root)
        self.sound = Sound()

        self.time_counter: Counter
        self.mine_counter: Counter

        self._sound = True

        self.smile = Smile(self.top_frame, self._restart, 0, 1)

        self.game = False
        self.first = False
        self.time = 0
        self.games = 0

        self.buttons: list[list[MyButton]] = []
        self.flags = self.MINES
        self.free_cells = self.ROW * self.COLUMN - self.MINES


    def run(self):
        self.game = True
        self.first = True
        self._create_widgets()
        self.mine_counter.draw(str(self.flags))
        # seed = time.time_ns()**2%(10**8)
        # self._place_mines(seed)
        # print(seed)
        # 28082121 - Max cell: 8
        self.root.after(0, lambda: threading.Thread(target=self._count_time, args=(self.games,), daemon=True).start())
        self.root.mainloop()



def main():
    game = Minesweeper()
    game.run()


if __name__ == '__main__':
    main()
