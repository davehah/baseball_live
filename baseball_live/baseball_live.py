#!/usr/bin/env python3
# %%
from dataclasses import dataclass
import statsapi
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import arrow
from tabulate import tabulate
from matplotlib.animation import FuncAnimation
from dataclasses import dataclass

class BaseballSchedule:
    # Baseball schedule class
    schedule = statsapi.schedule()

    def __init__(self, timezone = "US/Eastern"):
        self.schedule = BaseballSchedule.schedule
        self.timezone = timezone
    
    def games_today(self):
        # Displays game available today and runs baseball live from user input
        table = [['ID', 'Away', 'Home', 'Time']]
        for i, game in enumerate(self.schedule):
            date = arrow.get(game['game_datetime'])
            date_local = date.to(self.timezone)
            time = date_local.datetime.strftime("%H:%M")
            table.append([i+1, game['away_name'], game['home_name'], time])
        
        return tabulate(table, headers = 'firstrow')
    
    def input_to_id(self):
        game_id = input("Choose game ID:")
        return game_id
    
    def id_to_gamepk(self, game_id):
        gamePk = self.schedule[(int(game_id) - 1)]['game_id']
        return gamePk

    @staticmethod
    def is_game_finished(gamePk):
        game = statsapi.get('game', {'gamePk' : gamePk})
        status = game['gameData']['status']
        if status['abstractGameState'] == 'Final':
            return True
        else:
            return False

@dataclass
class BaseballPitchData:
    pitch_speed: list
    sz_top: list
    sz_bottom: list
    pX: list
    pZ: list
    pitch_type: list

    def __len__(self):
        return len(self.pitch_speed)


class BaseballLive:
    def __init__(self, gamePk):
        self.gamePk = gamePk
        self.game =  statsapi.get('game', {'gamePk' : self.gamePk})
    
    def get_current_play(self):
        # returns current play GET
        return self.game['liveData']['plays']['currentPlay']

    def current_count(self):
        # returns current count for atbat
        atbat = self.get_current_play()['playEvents']
        if not atbat:
            return None
        else:
            return atbat[-1]['count']
    
    def current_batter(self):
        # returns current batter 
        batter = self.get_current_play()['matchup']['batter']['fullName']
        return batter
    
    def current_pitcher(self):
        # returns current pitcher
        pitcher = self.get_current_play()['matchup']['pitcher']['fullName']
        return pitcher
    
    def current_pitch(self):
        # returns current pitch metrics
        atbat = self.get_current_play()['playEvents']
        if not atbat:
            return None
        elif 'pitchData' in atbat[-1]:
            return atbat[-1]['pitchData']
        else:
            return None
    
    def current_call(self):
        # returns current pitch call
        atbat = self.get_current_play()['playEvents']
        if not atbat:
            return None
        elif 'details' in atbat[-1]: 
            return atbat[-1]['details']['description']
        else:
            return None
       
    def atbat_pitch_data(self):
        # NEW
        # returns all pitches in the current atbat:
        atbat = self.get_current_play()['playEvents']
        if not atbat:
            return None
        
        pitch_exists = False
        for pitch in atbat:
            if 'pitchData' in pitch:
                pitch_exists = True 

        if pitch_exists is False:
            return None 

        pitch_speed = []
        sz_top = []
        sz_bottom = []
        pX = []
        pZ = []
        pitch_type = []

        for pitch in atbat:
            # append pitch type to pitchData
            if 'pitchData' in pitch:
                # pitch['pitchData']['type'] = pitch['details']['type']
                try:
                    pitch_type.append(pitch['details']['type']['code'])
                except:
                    pitch_type.append('undefined')
            if pitch['isPitch'] == False:
                continue
     
            pitch_speed.append(pitch['pitchData']['startSpeed'])
            sz_top.append(pitch['pitchData']['strikeZoneTop'])
            sz_bottom.append(pitch['pitchData']['strikeZoneBottom'])
            pX.append(pitch['pitchData']['coordinates']['pX'])
            pZ.append(pitch['pitchData']['coordinates']['pZ'])
  
        bpd = BaseballPitchData(pitch_speed, sz_top, sz_bottom, 
                                pX, pZ, pitch_type)
        return bpd
    
    def current_pitch_type(self):
        # returns current pitch type
        atbat = self.get_current_play()['playEvents']
        if not atbat:
            return None
        elif 'details' in atbat[-1]:
            if 'type' in atbat[-1]['details']:
                return atbat[-1]['details']['type']
            else:
                return None
    
    def expected_call(self):
        # determines expected call from current pitch
        # pX is the horizontal coordinate of baseball relative to center (ft)
        # pZ is the vertical coordinate of baseball relative to the ground (ft)
        pitch = self.current_pitch()
        if pitch is None:
            return None
        pX = pitch['coordinates']['pX']
        pZ = pitch['coordinates']['pZ']
        sz_top = pitch['strikeZoneTop']
        sz_bottom = pitch['strikeZoneBottom']
        rad = 0.12 # radius of ball in ft
        moe = 0.08 # margin of error
        if abs(pX) <= 0.75:
            X_strike = 1
        elif abs(pX) <= 0.91 and abs(pX) >= 0.75:
            X_strike = 0.5
        else:
            return "Ball"
        
        if pZ >= sz_bottom and pZ <= sz_top:
            Y_strike = 1
        elif pZ >= (sz_bottom - rad - moe) and pZ <= (sz_top + rad + moe):
            Y_strike = 0.5
        else:
            return "Ball"
        
        if (X_strike + Y_strike) == 2:
            return "Strike"
        else:
            return "MOE"
    
    def atbat_result(self):
        atbat = self.get_current_play()
        if not 'event' in atbat['result']:
            return None
        else:
            return atbat['result']['description']


class BaseballHighlights:
    def __init__(self, gamePk):
        self.gamePk = gamePk
        self.highlights = statsapi.game_highlights(gamePk)

       

class BaseballPlot:
    def __init__(self, gamePk):
        self.gamePk = gamePk
  
    def plot_animation(self):

        fig, ax = plt.subplots(figsize=(3,5), frameon=False)
        ax.axis('off')
        pitch_count = 0

        def plot_atbat(i, gamePk = self.gamePk):
            # plots atbat pitches to strike zone (pitcher view)
            # TODO plot live data
            bl = BaseballLive(gamePk)
            #pitches = bl.atbat_pitch_data()
            pitches = bl.atbat_pitch_data()
            if not pitches:
                return None
            
            # get top and bottom strike zone 
            sz_top = pitches.sz_top[0]
            sz_bottom = pitches.sz_bottom[0]
            sz_height = sz_top - sz_bottom

            # plot strike zone
            rect = patches.Rectangle(
                (-0.83,sz_bottom),
                width = 1.66,
                height = sz_height,
                linewidth = 1,
                edgecolor = 'black',
                facecolor = 'none')
            
            plt.cla()
            
            # plot pitches
            for p in range(len(pitches)):
                pX = pitches.pX[p]
                pZ = pitches.pZ[p]
                if pZ < 0:
                    pZ = 0
                pitch_code = pitches.pitch_type[p]
                colour = self.pitch_colours(pitch_code)
                plt.scatter((-1 * pX), pZ, color = colour, label = pitch_code)
                pitch_speed = pitches.pitch_speed[p]
                plt.annotate(pitch_speed, ((-1 * pX), pZ))
            
            pitcher = bl.current_pitcher()
            batter = bl.current_batter()
            
            plt.gca().add_patch(rect)
            plt.xlim([-2,2])
            plt.ylim([0, 5])
            # don't show repeated legends
            handles, labels = plt.gca().get_legend_handles_labels()
            by_label = dict(zip(labels, handles))
            plt.legend(by_label.values(), by_label.keys())
            plt.title(f"Pitcher: {pitcher}\nBatter: {batter}")
            plt.tight_layout()
            ax.axis('off')
            fig.patch.set_visible(False)

            # plot current count
            plot_height = 0.95
            bl = BaseballLive(self.gamePk)
            current_count = bl.current_count()
            if current_count is not None:
                strikes = current_count['strikes']
                balls = current_count['balls']
                outs = current_count['outs']
            else:
                strikes = 0
                balls = 0
                outs = 0
            plt.text(0, plot_height, 
                     f"{balls}-{strikes} O:{outs}", 
                     transform=ax.transAxes)

            # plot expected call
            plt.text(0, (plot_height-0.03),
                     f'Expected call: {bl.expected_call()}', 
                     transform=ax.transAxes)
           
            # plot the atbat result if found
            nonlocal pitch_count
            atbat_result = bl.atbat_result()
            if atbat_result is not None:
                plt.text(0, 0,
                         atbat_result, 
                         transform=ax.transAxes, 
                         wrap=True)
            else:
                plt.text(0, 0,
                         '',
                         transform=ax.transAxes)
                

            pitch_count = len(pitches)
            
        ani = FuncAnimation(plt.gcf(), plot_atbat, 
                            fargs=(self.gamePk,), interval=15000)

        plt.show()

    @staticmethod
    def pitch_colours(pitch_code):
        if pitch_code == "FF":
            # four seam fastball
            return 'blue'
        elif pitch_code == "SL":
            # slider
            return 'orange'
        elif pitch_code == "CU":
            # curve ball
            return 'red'
        elif pitch_code == "CH":
            # changeup
            return 'green'
        elif pitch_code == "FS":
            # splitter
            return 'yellow'
        elif pitch_code == "FC":
            # cutter
            return 'pink'
        elif pitch_code == "SI":
            # sinker
            return 'purple'
        elif pitch_code == "FT":
            # two seam fastball
            return 'beige'
        else:
            return 'black'

# %%
def main():
    # bs = BaseballSchedule()
    # print(bs.games_today())
    # game_id = bs.input_to_id()
    # gamePk = bs.id_to_gamepk(game_id)
    # game_finished = bs.is_game_finished(gamePk)
    # if game_finished is True:
    #     bh = BaseballHighlights(gamePk)
    #     print(bh.highlights)
    # else:
    #     bp = BaseballPlot(gamePk)
    #     bp.plot_animation()
    gamePk = 662062
    bl = BaseballLive(gamePk)
    # bp = BaseballPlot(gamePk)
    # bp.plot_animation()
    


if __name__ == "__main__":
    main()

# %%
# gamePk = 662063
# bl = BaseballLive(gamePk)
# pitches = bl.pitch_data()
# print(pitches)