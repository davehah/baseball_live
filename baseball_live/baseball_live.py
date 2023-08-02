#!/usr/bin/env python3
from dataclasses import dataclass
import statsapi
import arrow
from tabulate import tabulate
from dataclasses import dataclass
from typing import Union, Tuple

class BaseballSchedule:
    """Class for baseball schedule today.
    
    Attributes:
        schedule (dict): Schedule returned by statsapi.schedule method.
        timezone (str): Optional argument to set timezone 
        (default: "US/Eastern").
    """

    def __init__(self, timezone = "US/Eastern"):
        """Initialization for BaseballSchedule with optional timezone argument.
        """
        self.schedule = statsapi.schedule()
        self.timezone = timezone
    
    def games_today(self) -> str:
        """Generates a tabulated string of baseball games today.
        """
        table = [['ID', 'Away', 'Home', 'Time']]
        for i, game in enumerate(self.schedule):
            date = arrow.get(game['game_datetime'])
            date_local = date.to(self.timezone)
            time = date_local.datetime.strftime("%H:%M")
            table.append([i+1, game['away_name'], game['home_name'], time])
        
        return tabulate(table, headers = 'firstrow')
    
    def input_to_id(self) -> str:
        """A user defined input to choose game ID from games_today.
        """
        gameid = input("Choose game ID:")
        return gameid
    
    def id_to_gamepk(self, game_id: str) -> int:
        """Converts game ID to gamePk.

        Args:
            game_id (str or int): Game ID relative to games_today.
        
        Returns:
            The gamePk.
        """
        gamePk = self.schedule[(int(game_id) - 1)]['game_id']
        return gamePk

    @staticmethod
    def check_game_state(gamePk: int) -> str:
        """Checks the current game state to see if the game has started,
        in progress, or finished.

        Args:
            gamePk (int): The gamePk to check the current game state. 

        Returns:
            'Preview' if game did not start yet, 'In progress' if the game is
            in progress, or 'Final' if the game finished.
        """
        game = statsapi.get('game', {'gamePk' : gamePk})
        status = game['gameData']['status']
        if status['abstractGameState'] == 'Preview':
            return 'Preview'
        elif status['abstractGameState'] == 'Final':
            return 'Final'
        else:
            return 'In progress'

@dataclass
class BaseballPitchData:
    """Dataclass to store current at-bat pitch data.
    
    Note:
        The __len__ retrieves the number of pitches within the dataclass.
    
    Attributes:
        pitch_speed (list): Pitch speeds (mph).
        sz_top (list): Top of strike zone (ft).
        sz_bottom (list): Bottom of strike zone (ft).
        px (list): Horizontal location of pitch 0 is centre of plate (ft).
        px (list): Vertical location of pitch 0 is ground (ft).
        pitch_type (list): Pitch type given in two letter pitch code.

    """
    pitch_speed: list
    sz_top: list
    sz_bottom: list
    pX: list
    pZ: list
    pitch_type: list

    def __len__(self):
        return len(self.pitch_speed)


class BaseballLive:
    """Class for live baseball data.

    Args:
        gamePk (int): The gamePk for live data.
    
    Attributes:
        game (dict): The returned dictionary from statsapi using gamePk.
    """
    def __init__(self, gamePk: int):
        """Initialize BaseballLive with gamePk."""
        self.gamePk = gamePk
        self.game =  statsapi.get('game', {'gamePk' : self.gamePk})
    
    @property
    def current_play(self) -> dict:
        """Retrieves current play data from BaseballLive.game."""
        return self.game['liveData']['plays']['currentPlay']
    
    @property
    def count(self) -> Union[dict, None]:
        """Current count for at-bat."""
        atbat = self.current_play['playEvents']
        if not atbat:
            return None
        else:
            return atbat[-1]['count']
    
    @property
    def batter(self) -> str:
        """The current batter.""" 
        batter = self.current_play['matchup']['batter']['fullName']
        return batter
    
    @property
    def pitcher(self) -> str:
        """The current pitcher.""" 
        pitcher = self.current_play['matchup']['pitcher']['fullName']
        return pitcher
    
    @property
    def pitch(self) -> Union[dict, None]:
        """Most recent pitch metrics.""" 
        # returns current pitch metrics
        atbat = self.current_play['playEvents']
        if not atbat:
            return None
        elif 'pitchData' in atbat[-1]:
            return atbat[-1]['pitchData']
        else:
            return None
    
    @property
    def call(self) -> Union[str, None]:
        """Current pitch call."""
        atbat = self.current_play['playEvents']
        if not atbat:
            return None
        elif 'details' in atbat[-1]: 
            return atbat[-1]['details']['description']
        else:
            return None
    
    @property
    def pitch_data(self) -> Union[BaseballPitchData, None]:
        """Pitch data for current at-bat."""
        atbat = self.current_play['playEvents']
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
                try:
                    pitch_type.append(pitch['details']['type']['code'])
                except KeyError:
                    continue
            if pitch['isPitch'] == False:
                continue
            
            try:
                pitch_speed.append(pitch['pitchData']['startSpeed'])
            except KeyError:
                continue
            sz_top.append(pitch['pitchData']['strikeZoneTop'])
            sz_bottom.append(pitch['pitchData']['strikeZoneBottom'])
            pX.append(pitch['pitchData']['coordinates']['pX'])
            pZ.append(pitch['pitchData']['coordinates']['pZ'])
  
        bpd = BaseballPitchData(pitch_speed, sz_top, sz_bottom, 
                                pX, pZ, pitch_type)
        return bpd
    
    @property
    def pitch_type(self) -> Union[dict, None]:
        """Current pitch type."""
        atbat = self.current_play['playEvents']
        if not atbat:
            return None
        elif 'details' in atbat[-1]:
            if 'type' in atbat[-1]['details']:
                return atbat[-1]['details']['type']
            else:
                return None
    
    @property
    def expected_call(self) -> Union[str, None]:
        """Determines the expected call from current pitch irrespective of
        the umpire's call.
        """

        # pX is the horizontal coordinate of baseball relative to center (ft)
        # pZ is the vertical coordinate of baseball relative to the ground (ft)
        pitch = self.pitch
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
    
    @property
    def atbat_result(self) -> Union[str, None]:
        """The result of the at-bat."""
        atbat = self.current_play
        if not 'event' in atbat['result']:
            return None
        else:
            return atbat['result']['description']
    
    @property
    def inning(self) -> str:
        """The current inning."""
        inning = self.game['liveData']['linescore']['currentInning']
        half = self.game['liveData']['linescore']['inningHalf']
        return f"{inning} {half}"
    
    @property
    def score(self) -> Tuple[int, int]:
        """The current score (away-home)."""
        box = self.game['liveData']['linescore']['teams']
        home = box['home']['runs']
        away = box['away']['runs']
        return away, home

class BaseballHighlights:
    """Class for baseball highlights (finished games).
    
    Attributes:
        gamePk (int): The gamePk for highlights.
        highlights (str): The return value of statsapi.game_highlights method.
    """
    def __init__(self, gamePk):
        self.gamePk = gamePk
        self.highlights = statsapi.game_highlights(gamePk)