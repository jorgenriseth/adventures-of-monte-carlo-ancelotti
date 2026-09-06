= Model for minutes played by a player

Want to build a model for predicting number of minutes played by a specific player.
Will assume full ignorance of player and club skills, and want to predict minutes played from Bayesian inference, starting with a prior distribution derived using the principle of indifference, and then iteratively update the prior with new data as it becomes available.

In Premier League, each club will, at the end of a transfer window, register a senior player squad of up to 25 players, as well as having a pool of as many junior players under 21 as they want registered with their clubs.
Fantasy Premier League will include the 25 senior players listed, as well as any junior players that they expect to be playing throughout the season.
Although surprising appearances by under-21 or junior players will probably appear in Fantasy Premier League if they happen during the season, I will work with an assumption that Fantasy Premier League is able to pre-determine all junior players and that no appearances or updates of the available players in Fantasy Premier League will happen between transfer windows.
During a match, a manager or a club can make up to five substitutes. There are no rules preventing the same player from being substituted on and then off again.
FPL ignores added time for the minutes played modidifiers.
A player can get somewhere between 0 and 90 minutes inclusive for a match.
To get more than zero, a player would need to be either in the starting eleven or among the twenty players in a matchday squad, And be subbed in during the match.
To get 90 minutes, a player would need to be in the starting 11 and not be subbed out.
The prior distribution based on the principle of indifference would be a mixed distribution where you have the spike at zero minutes, a spike at 90 minutes, and then some distribution of time in between.
I will be modeling time as continuous rather than discrete and then map the values to discrete values if needed.

== Scenarios
Before a match, the club selects a match day squad consisting of 20 players from the clubs  $N >= 25$ registered players.
The matchday squad consists of 11 starting players (with one designated goalkeeper) and 9 benched players or substitutes.

- A player will get zero minutes played either if
  - they are not selected for the match day squad
  - or if they are one of the 9 substitutes and are not subbed on during the match.
- A player will get 90 minutes if they are in the starting 11, and are not subbed throughout.
- A player will start accumulating minutes during the game if:
  - They are amongst the starting 11.
  - They are substituted on during the match.
- A player on the pitch will stop accumulating minutes during the gamge if:
  - They are substituted off during the match.
  - They are given a red card during the match.


== Substitutions
- Each team can perform up to 5 substitutions.
- Club managers can halt play up to three times to perform the substitutions, in addition to half-time. Any number of subsistutions may be done at each opportunity, as long as the totaol stays within the five-player limit.
- There also exists an opportunity for so-called concussion-substitutions. We will not include them in our model.
- A player that have already been subbed off cannot be subbed on later in the match.
- Nothing prevents a benched player from first being subbed on, and being subbed off again later in the game.

Based on the restriction to specific substitution opportunities, I would think that instead of modeling the substitution time for each player directly, we should model the probability of getting a substitution opportunity at a given time, and then model the probability for how many substitutions are being done, and then
