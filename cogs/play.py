import discord, json, MySQLdb
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from ..game import Game, PLAYER_1, PLAYER_2, TIED

with open('../config.json') as data:
   config = json.load(data)
with open('./cards.json') as data:
   cards = json.load(data)

class Play(commands.Cog):

   def __init__ (self, client):
      self.client = client
      self.player1 = None
      self.player2 = None
      self.challengeTime = datetime.utcnow()
      self.game = None
      self.finishedSelection = False
      self.cardPlayed = False
      self.bet = 0
      self.content = "Type !end to end your turn, !stand to keep your hand, or !play <card> <+/-> to play one of your side deck cards.\nTo play a side deck card be sure to use the brackets and only put '+' or '-' after if the card is a '+/-' card or tiebreaker card.\nFor example \"!play [+2]\" or \"!play [+/-4] -\" or \"!play [T] +\"."
      self.timer.start()

   def cog_unload (self):
      self.timer.stop()

   @commands.command()
   async def duel (self, ctx, member : discord.Member, wager=50):
      pass

   @commands.command()
   async def accept (self, ctx):
      pass

   @commands.command()
   async def decline (self, ctx):
      pass

   @commands.Cog.listener()
   async def on_message (self, mesage):
      pass

   @commands.command()
   async def heads (self, ctx):
      pass

   @commands.command()
   async def tails (self, ctx):
      pass

   @commands.command()
   async def end (self, ctx):
      pass

   @commands.command()
   async def stand (self, ctx):
      pass

   @commands.command()
   async def play (self, ctx, card, sign=None):
      pass

   @tasks.loop(seconds=15)
   async def timer (self):
      pass
      
def setup (client):
   client.add_cog(Play(client))