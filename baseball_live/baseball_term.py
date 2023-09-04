#!/usr/bin/env python3
import curses
from curses.textpad import Textbox, rectangle
from .baseball_live import BaseballSchedule, BaseballLive, BaseballPitchData
import textwrap
from typing import Union

screen = curses.initscr()


class TerminalColorException(Exception):
    """Raised when terminal colour does not support 256"""


def check_256_support():
    curses.setupterm()
    nums = curses.tigetnum("colors")
    if nums >= 256:
        return True
    else:
        return False


# check if terminal supports 256
if check_256_support():
    curses.start_color()
    curses.use_default_colors()
    for i in range(0, curses.COLORS):
        curses.init_pair(i + 1, i, -1)
else:
    raise TerminalColorException("Terminal does not support 256 color")


def display_games_today(stdscr: "curses._CursesWindow", gt: str, dims: tuple):
    gt_split = gt.splitlines()
    gt_split.append("")
    gt_height = len(gt_split)
    gt_length = len(max(gt_split, key=len))
    stdscr.erase()
    for i, j in enumerate(gt_split):
        ht = int(dims[0] / 2) - int(gt_height / 2) + i
        ln = int(dims[1] / 2) - int(gt_length / 2)
        stdscr.addstr(ht, ln, j)

    # get user input on game id
    win = curses.newwin(1, 3, ht, ln)
    box = Textbox(win)
    stdscr.refresh()
    box.edit()
    game_id = box.gather()
    return game_id


def pitch_book(pitch_code: str):
    # Define a dictionary to map pitch codes to color pairs
    pitch_color_mapping = {
        "FF": 0,  # four seam fastball
        "SL": 2,  # slider
        "CU": 3,  # curve ball
        "CH": 4,  # changeup
        "FS": 5,  # splitter
        "FC": 6,  # cutter
        "SI": 7,  # sinker
        "FT": 8,  # two seam fastball
    }

    # Use a default color pair (9) if pitch_code is not found in the mapping
    return curses.color_pair(pitch_color_mapping.get(pitch_code, 9))


class GameDisplay:
    def __init__(self, stdscr: "curses._CursesWindow"):
        self.stdscr = stdscr
        self.dims = stdscr.getmaxyx()
        self.midx = int(self.dims[1] / 2)
        self.midy = int(self.dims[0] / 2)
        self.widthx = int(self.dims[1] / 6)
        self.heighty = round(self.widthx / 1.5)
        self.ix = int(self.dims[1] * (1 / 8))  # for plottings innings, etc.
        self.iy = int(self.dims[0] * (1 / 4))

    def strike_zone(self):
        ulx, uly = self.midx - int(self.widthx / 2), self.midy - int(self.heighty / 2)
        lrx, lry = self.midx + int(self.widthx / 2), self.midy + int(self.heighty / 2)
        rectangle(self.stdscr, uly, ulx, lry, lrx)
        self.stdscr.refresh()

    def status_when_no_pitch(self, status: Union[str, None]):
        desy = int(self.dims[0] * (6 / 7))
        desx = int(self.dims[1] / 2) - int(len(status) / 2)
        self.stdscr.addstr(desy, desx, status)
        self.stdscr.refresh()

    def pitches_plot(self, pitches: Union[BaseballPitchData, None]):
        sz_top = pitches.sz_top[0]
        sz_bottom = pitches.sz_bottom[0]
        sz_height = sz_top - sz_bottom
        # scale the pitch rectangle against the rectangle on screen.
        # pX is relative to the centre of home plate
        # pZ starts from ground
        sz_top = pitches.sz_top[0]
        sz_bottom = pitches.sz_bottom[0]
        boty = self.midy + self.heighty / 2
        sz_height = sz_top - sz_bottom
        yfactor = self.heighty / sz_height
        xfactor = self.widthx / (17 / 12)  # denominator is plate width in ft
        pXs, pZs = pitches.pX, pitches.pZ
        # set negative pZs to zero (ball touched the ground).
        pZs = [0 if i < 0 else i for i in pZs]
        # get relative pZs with respect to the screen
        pZ_rels = [i - sz_bottom for i in pZs]

        for i, pX in enumerate(pXs):
            plot_y = round(boty - pZ_rels[i] * yfactor)
            plot_x = round(self.midx + (-1 * pX) * xfactor)
            # if plot_y is bigger or smaller than screen dimensions, adjust (+ 5 is arbitrary)
            if plot_y + 5 >= self.dims[0]:
                plot_y = self.dims[0] - 2
            # same for plot_x
            if plot_x + 5 >= self.dims[1]:
                plot_x = self.dims[1] - 2
            # plot_x and plot_y cannot be negative
            if plot_x < 0:
                plot_x = 0
            if plot_y < 0:
                plot_y = 0
            

            self.stdscr.addstr(plot_y, plot_x, "X", pitch_book(pitches.pitch_type[i]))
            self.stdscr.addstr(
                plot_y + 1, plot_x - 1, str(round(pitches.pitch_speed[i]))
            )

    def pitches_legend(self, pitches: Union[BaseballPitchData, None]):
        pitch_type_set = list(set(pitches.pitch_type))
        legx = int(self.dims[1] * (5 / 6))
        legy = int(self.dims[0] * (1 / 4))
        for i, pitch in enumerate(pitch_type_set):
            self.stdscr.addstr(legy + i, legx, "X", pitch_book(pitch))
            self.stdscr.addstr(legy + i, legx + 1, " - " + pitch)

    def current_inning(self, inning: str):
        self.stdscr.addstr(self.iy, self.ix, f"I: {inning}")

    def score(self, score: tuple):
        aw, hm = score
        self.stdscr.addstr(self.iy + 1, self.ix, f"R: {aw}-{hm}")

    def pitch_count(self, current_count: dict):
        if current_count is not None:
            strikes = current_count["strikes"]
            balls = current_count["balls"]
            outs = current_count["outs"]
        else:
            strikes = 0
            balls = 0
            outs = 0
        self.stdscr.addstr(self.iy + 2, self.ix, f"{balls}-{strikes} O: {outs}")

    def expected_call(self, expected_call: str):
        self.stdscr.addstr(self.iy + 3, self.ix, f"EC: {expected_call}")

    def current_call(self, current_call: str):
        self.stdscr.addstr(self.iy + 4, self.ix, current_call)

    def title(self, pitcher: str, batter: str):
        titlepitcher = f"Pitcher: {pitcher}"
        titlebatter = f"Batter: {batter}"
        titleypitcher = int(self.dims[0] / 7)
        titlexpitcher = int(self.dims[1] / 2) - int(len(titlepitcher) / 2)
        titleybatter = titleypitcher + 1
        titlexbatter = int(self.dims[1] / 2) - int(len(titlebatter) / 2)
        self.stdscr.addstr(titleypitcher, titlexpitcher, titlepitcher)
        self.stdscr.addstr(titleybatter, titlexbatter, titlebatter)

    def result(self, atbat_result: str):
        resy = int(self.dims[0] * (6 / 7))
        resx = int(self.dims[1] / 2) - int(len(atbat_result) / 2)
        # if the string is too long, need to chop it up to display to next
        if len(atbat_result) > self.dims[1]:
            # wrap text
            res = textwrap.fill(
                atbat_result, width=self.dims[1] - int(self.dims[1] * (2 / 8))
            )
            atbat_result_list = res.splitlines()
            resx = int(self.dims[1] / 2) - int(len(atbat_result_list[0]) / 2)
            for i, ar in enumerate(atbat_result_list):
                self.stdscr.addstr(resy + i, resx, ar)

        else:
            self.stdscr.addstr(resy, resx, atbat_result)


def live(stdscr: "curses._CursesWindow"):
    # get games today
    bs = BaseballSchedule()
    gt = bs.games_today()

    # display games today
    dims = stdscr.getmaxyx()
    game_id = display_games_today(stdscr, gt, dims)

    # convert gameid to gamePk and and get data
    gamePk = bs.id_to_gamepk(game_id)

    # check game state and prompt accordingly
    game_state = bs.check_game_state(gamePk)
    if game_state == "Preview":
        stdscr.erase()
        stdscr.addstr(0, 0, "Game has not started yet!")
        stdscr.getch()
        return None

    while True:
        dims = stdscr.getmaxyx()
        stdscr.erase()

        # get game data
        bl = BaseballLive(gamePk)
        pitches = bl.pitch_data

        gd = GameDisplay(stdscr)
        gd.strike_zone()

        # turn off blinking cursor
        curses.curs_set(False)

        # if pitch does not exist try again in 5 seconds
        if not pitches:
            try:
                gd.status_when_no_pitch(bl.atbat_result)
            except (KeyError, TypeError):
                pass
            try:
                for _ in range(50):
                    curses.napms(100)
                continue
            except KeyboardInterrupt:
                break

        gd.pitches_plot(pitches)
        gd.pitches_legend(pitches)
        gd.current_inning(bl.inning)
        gd.score(bl.score)
        gd.pitch_count(bl.count)
        gd.expected_call(bl.expected_call)
        gd.current_call(bl.call)
        gd.title(bl.pitcher, bl.batter)
        if bl.atbat_result is not None:
            # need to do this since because some atbat_result has extra spaces
            words = bl.atbat_result.split()
            atbat_result = ' '.join(words)
            gd.result(atbat_result)
        stdscr.refresh()

        # refresh every 5 seconds
        try:
            for _ in range(50):
                curses.napms(100)
        except KeyboardInterrupt:
            break


def main():
    try:
        curses.wrapper(live)
    except KeyboardInterrupt:
        curses.endwin()


if __name__ == "__main__":
    main()
