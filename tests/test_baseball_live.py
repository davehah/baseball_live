from baseball_live.baseball_live import BaseballLive
import unittest

class TestBaseballLive(unittest.TestCase):
    def setUp(self):
        self.game = BaseballLive(565542)

    def test_get_current_play(self):
        self.assertIsInstance(self.game.get_current_play(), dict)

    def test_count(self):
        self.assertIsInstance(self.game.count, dict)

    def test_batter(self):
        self.assertIsInstance(self.game.batter, str)

    def test_pitcher(self):
        self.assertIsInstance(self.game.pitcher, str)

    def test_pitch(self):
        self.assertIsInstance(self.game.pitch, dict)

    def test_call(self):
        self.assertIsInstance(self.game.call, str)

    def test_score(self):
        self.assertIsInstance(self.game.score, tuple)
    
    def test_inning(self):
        self.assertIsInstance(self.game.inning, str)
    
    def test_atbat_result(self):
        self.assertIsInstance(self.game.atbat_result, str)
   

if __name__ == '__main__':
    unittest.main()