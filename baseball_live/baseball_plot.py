from baseball_live.baseball_live import BaseballLive
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation

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