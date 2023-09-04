# baseball_live
Live MLB at-bats on the terminal using Python curses.

## Installation
Clone the library and install:
```
pip install -e .
```
## Usage
You can call the script using `baseball_live`. 
```
$ baseball_live
```
Which returns the baseball schedule for current day (default US-Eastern):
```

                  ID  Away                 Home                   Time
                ----  -------------------  ---------------------  ------
                  1  Atlanta Braves       Philadelphia Phillies  14:07
                  2  Houston Astros       Seattle Mariners       16:07
                  3  New York Yankees     Cleveland Guardians    19:37
                  4  Los Angeles Dodgers  San Diego Padres       21:37

```
Type the ID and hit Enter to display the game (pitcher's view, updates every 5 seconds):
<p align="center">
  <img src="figures/example.png" alt="Sublime's custom image"/>
</p>   
Left pannel displays innings, runs (away-home), pitch count, number of outs,
expected call (irrespective of umpire's call), and pitch result. The right pannel
displays the legend for pitch types.
