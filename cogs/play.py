import discord, json, MySQLdb
from discord.ext import commands, tasks
from ..game import Game

with open('../config.json') as data:
   config = json.load(data)
with open('./cards.json') as data:
   cards = json.load(data)

class Play(commands.Cog):

   def __init__ (self, client):
      self.client = client

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
      
def setup (client):
   client.add_cog(Play(client))