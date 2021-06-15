import discord, json, MySQLdb
from random import randint
from player import Player

with open('./config.json') as data:
   config = json.load(data)
with open('./cogs/cards.json') as data:
   cards = json.load(data)

PLAYER_1 = 0
PLAYER_2 = 1
TIED = -1

class Game:
   def __init__ (self, player1, player2, bet):
      self.players = [Player(player1.id, player1.name, player1.mention), Player(player2.id, player2.name, player2.mention)]
      self.bet = bet
      self.round = 1
      self.currentPlayer = -1
      self.roundWinner = -1
      self.roundStarter = -1
      self.playedCards = []
      self.gameWinner = -1
      self.gameLoser = -1

   def getCurrentPlayerID (self):
      return self.players[self.currentPlayer].id

   def mentionCurrentPlayer (self):
      return self.players[self.currentPlayer].id

   def showCardOptions (self, player):
      db = MySQLdb.connect("localhost", config['database_user'], config['database_pass'], config['database_schema'])
      cursor = db.cursor()

      cursor.execute(f"SELECT plus_one, plus_two, plus_three, plus_four, plus_five, plus_six, minus_one, minus_two, minus_three, minus_four, minus_five, minus_six, plus_minus_one, plus_minus_two, plus_minus_three, plus_minus_four, plus_minus_five, plus_minus_six, flip_two_four, flip_three_six, double_card, tiebreaker_card FROM pazaak WHERE discordid = {self.players[player].id}")
      cardAmounts = cursor.fetchone()

      embed = discord.Embed(title="Choose your side deck", colour=discord.Colour(0x4e7e8a), description="You may choose up to 10 cards, and 4 will be chosen at random to play.")
      for i in range(len(cards['cards'])):
         if any(j in cards['cards'][i] for j in ['F', 'D', 'T']):
            embed.add_field(name=f"[{cards['cards'][i]['code']}] {cards['cards'][i]['name']}", value=str(cardAmounts[i]), inline=False)
         else:
            embed.add_field(name=f"[{cards['cards'][i]['code']}]", value=str(cardAmounts[i]), inline=True)
      
      db.close()

      return embed