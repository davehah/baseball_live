#!/usr/bin/env python3
import curses
from curses import wrapper
from curses.textpad import Textbox, rectangle
from .baseball_live import BaseballSchedule
from .baseball_live import BaseballLive
import textwrap
import time

screen = curses.initscr()
dims = screen.getmaxyx()
bs = BaseballSchedule()
gt = bs.games_today()
gt_split = gt.splitlines()
gt_split.append('')
gt_height = len(gt_split)
gt_length = len(max(gt_split, key=len))

class TerminalColorException(Exception):
    """Raised when terminal colour does not support 256"""

def check_256_support():
    curses.setupterm()
    nums = curses.tigetnum('colors')
    if nums >= 256:
        return True
    else:
        return False

def display_games_today(stdscr: 'curses._CursesWindow'):
    stdscr.erase()
    for i, j in enumerate(gt_split):
        ht = int(dims[0]/2) - int(gt_height/2) + i
        ln = int(dims[1]/2) - int(gt_length/2)
        stdscr.addstr(ht, ln, j)

    # get user input on game id
    win = curses.newwin(1, 3, ht, ln)
    box = Textbox(win)
    stdscr.refresh()
    box.edit()
    game_id = box.gather()
    return game_id

# check if terminal supports 256
if check_256_support() is True:
    curses.start_color()
    curses.use_default_colors()
    for i in range(0, curses.COLORS):
        curses.init_pair(i + 1, i, -1)
else:
    raise TerminalColorException("Terminal does not support 256 color")

def pitch_book(pitch_code):
    # Used for displaying the pitch type based on pitch_code
    if pitch_code == "FF":
        # four seam fastball
        return curses.color_pair(0)
    elif pitch_code == "SL":
        # slider
        return curses.color_pair(2)
    elif pitch_code == "CU":
        # curve ball
        return curses.color_pair(3)
    elif pitch_code == "CH":
        # changeup
        return curses.color_pair(4)
    elif pitch_code == "FS":
        # splitter
        return curses.color_pair(5)
    elif pitch_code == "FC":
        # cutter
        return curses.color_pair(6)
    elif pitch_code == "SI":
        # sinker
        return curses.color_pair(7)
    elif pitch_code == "FT":
        # two seam fastball
        return curses.color_pair(8)
    else:
        return curses.color_pair(9)


def main(stdscr: 'curses._CursesWindow'):
    # display games today
    game_id = display_games_today(stdscr)
    
    # convert gameid to gamePk and and get data
    gamePk = bs.id_to_gamepk(game_id)

    # check game state and prompt accordingly
    game_state = bs.check_game_state(gamePk)
    if game_state == 'Preview':
        stdscr.erase()
        stdscr.addstr(0,0,'Game has not started yet!')
        stdscr.getch()
        return None


    while True:
        screen = curses.initscr()
        dims = screen.getmaxyx()
        stdscr.erase()
        
        # get game data
        bl = BaseballLive(gamePk)
        pitches = bl.pitch_data
        
        # plot strike zone
        midx = int(dims[1]/2)
        midy = int(dims[0]/2)
        widthx = int(dims[1]/6)
        heighty = round(widthx/1.5)
        ulx, uly = midx - int(widthx/2), midy - int(heighty/2)
        lrx, lry = midx + int(widthx/2), midy + int(heighty/2)
        rectangle(stdscr, uly, ulx, lry, lrx)
        stdscr.refresh()

        # turn off blinking cursor
        curses.curs_set(False)

        # if pitch does not exist try again in 5 seconds
        if not pitches:
            try:
                status = bl.atbat_result
                desy = int(dims[0] * (6/7))
                desx = int(dims[1]/2) - int(len(status)/2)
                stdscr.addstr(desy, desx, status)
                stdscr.refresh()
            except (KeyError, TypeError):
                pass

            try:
                for i in range(50):
                    curses.napms(100)
                continue
            except KeyboardInterrupt:
                break
        
        # get top and bottom strike zone 
        sz_top = pitches.sz_top[0]
        sz_bottom = pitches.sz_bottom[0]
        sz_height = sz_top - sz_bottom
        # plot pitch data if exists
        # scale the pitch rectangle against the rectangle on screen.
        # pX is relative to the centre of home plate
        # pZ starts from ground
        sz_top = pitches.sz_top[0]
        sz_bottom = pitches.sz_bottom[0]
        boty = midy + heighty / 2
        sz_height = sz_top - sz_bottom
        yfactor = heighty / sz_height
        xfactor = widthx / (17/12) # denominator is plate width in ft
        pXs, pZs = pitches.pX, pitches.pZ
        # set negative pZs to zero (ball touched the ground).
        pZs = [0 if i < 0 else i for i in pZs]
        # get relative pZs with respect to the screen
        pZ_rels = [i - sz_bottom for i in pZs]

        for i, pX in enumerate(pXs):
            plot_y = round(boty - pZ_rels[i] * yfactor)
            plot_x = round(midx + (-1 * pX) * xfactor)
            # if plot_y is bigger or smaller than screen dimensions, adjust
            if plot_y+5 >= dims[0]:
                plot_y = dims[0] - 2

            stdscr.addstr(plot_y, plot_x, "X", pitch_book(pitches.pitch_type[i]))
            stdscr.addstr(plot_y+1, plot_x-1, str(round(pitches.pitch_speed[i])))

        # plot pitch legend
        pitch_type_set = list(set(pitches.pitch_type))
        legx = int(dims[1] * (5/6))
        legy = int(dims[0] * (1/4))
        for i, pitch in enumerate(pitch_type_set):
            stdscr.addstr(legy + i, legx, "X", pitch_book(pitch))
            stdscr.addstr(legy + i, legx + 1, " - " + pitch)
        
        # plot current inning
        current_inning = bl.inning

        ix = int(dims[1] * (1/8))
        iy = int(dims[0] * (1/4))
        stdscr.addstr(iy, ix, f"I: {current_inning}")

        # plot score
        aw, hm = bl.score
        sx = ix
        sy = iy + 1
        stdscr.addstr(sy, sx, f"R: {aw}-{hm}")
        
        # plot pitch count
        current_count = bl.count
        if current_count is not None:
            strikes = current_count['strikes']
            balls = current_count['balls']
            outs = current_count['outs']
        else:
            strikes = 0
            balls = 0
            outs = 0
        
        countx = sx
        county = sy + 1
        stdscr.addstr(county, countx, f"{balls}-{strikes} O: {outs}")

        # plot expected call
        ecx = countx
        ecy = county + 1
        stdscr.addstr(ecy, ecx, f"EC: {bl.expected_call}")

        # plot current call
        ccx = countx
        ccy = ecy + 1
        stdscr.addstr(ccy, ccx, bl.call)

        # add title
        pitcher = bl.pitcher
        batter = bl.batter
        titlepitcher = f"Pitcher: {pitcher}"
        titlebatter = f"Batter: {batter}"
        titleypitcher = int(dims[0]/7)
        titlexpitcher = int(dims[1]/2) - int(len(titlepitcher)/2)
        titleybatter = titleypitcher + 1
        titlexbatter = int(dims[1]/2) - int(len(titlebatter)/2)
        stdscr.addstr(titleypitcher, titlexpitcher, titlepitcher)
        stdscr.addstr(titleybatter, titlexbatter, titlebatter)

        # add result if exists
        atbat_result = bl.atbat_result
        if atbat_result is not None:
            resy = int(dims[0] * (6/7))
            resx = int(dims[1]/2) - int(len(atbat_result)/2)
            # if the string is too long, need to chop it up to display to next
            if len(atbat_result) > dims[1]:
                # wrap text 
                res = textwrap.fill(atbat_result, width = dims[1]-int(dims[1] * (2/8)))
                atbat_result_list = res.splitlines()
                resx = int(dims[1]/2) - int(len(atbat_result_list[0])/2)
                for i, ar in enumerate(atbat_result_list):
                    stdscr.addstr(resy+i, resx, ar)

            else:
                stdscr.addstr(resy, resx, atbat_result)
        
        stdscr.refresh()

        # refresh every 5 seconds
        try:
            for i in range(50):
                curses.napms(100)
        except KeyboardInterrupt:
            break

wrapper(main)
