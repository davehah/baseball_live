#!/usr/bin/env python3
from dataclasses import dataclass
import statsapi
import arrow
from tabulate import tabulate
from dataclasses import dataclass

class BaseballSchedule:
    # Baseball schedule class
    #schedule = statsapi.schedule()

    def __init__(self, timezone = "US/Eastern"):
        self.schedule = statsapi.schedule()
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
    def check_game_state(gamePk):
        game = statsapi.get('game', {'gamePk' : gamePk})
        status = game['gameData']['status']
        if status['abstractGameState'] == 'Preview':
            # not started yet
            return 'Preview'
        elif status['abstractGameState'] == 'Final':
            return 'Final'
        else:
            return 'In progress'

@dataclass
class BaseballPitchData:
    pitch_speed: list
    sz_top: list
    sz_bottom: list
    pX: list
    pZ: list
    pitch_type: list

    def __len__(self):
        # the number of pitches in dataclass
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
            
            try:
                pitch_speed.append(pitch['pitchData']['startSpeed'])
            except KeyError:
                # if it fails reading the pitch speed append 'N'
                pitch_speed.append('N')
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
    
    def current_inning(self):
        inning = self.game['liveData']['linescore']['currentInning']
        half = self.game['liveData']['linescore']['inningHalf']
        return f"{inning} {half}"
    
    def current_score(self):
        box = self.game['liveData']['linescore']['teams']
        home = box['home']['runs']
        away = box['away']['runs']
        return away, home

class BaseballHighlights:
    def __init__(self, gamePk):
        self.gamePk = gamePk
        self.highlights = statsapi.game_highlights(gamePk)

# def main():
#     bs = BaseballSchedule()
#     print(bs.games_today())
#     game_id = bs.input_to_id()
#     gamePk = bs.id_to_gamepk(game_id)
#     game_finished = bs.is_game_finished(gamePk)
#     if game_finished is True:
#         bh = BaseballHighlights(gamePk)
#         print(bh.highlights)
#     else:
#         bp = BaseballPlot(gamePk)
#         bp.plot_animation()


# if __name__ == "__main__":
#     main()
