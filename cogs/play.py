import discord, json, MySQLdb
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from random import randint
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
      self.wager = 0
      self.lastChannel = None
      self.timer.start()

   def cog_unload (self):
      self.timer.stop()

   @commands.command()
   async def duel (self, ctx, player2:discord.Member=None, wager=50):
      if playChannel(ctx.message.guild.id, ctx.message.channel.id):
         if player2 is None:
            await ctx.send("Please tag the member you'd like to challenge.")
         elif self.game is not None:
            await ctx.send(f"{ctx.message.author.mention}, a game is already in progress. Please wait for this to finish before starting another one.")
         else:
            player1 = ctx.message.author
            wager = int(wager)

            if wager < 50:
               await ctx.send(f"{player1.mention}, you have to bet at least 50 credits to play pazaak.")
            else:
               db = MySQLdb.connect(config['database_server'], config['database_user'], config['database_pass'], config['database_schema'])
               cursor = db.cursor()

               try:
                  cursor.execute(f"SELECT coins FROM member_rank WHERE discordid = {player1.id}")
                  p1coins = cursor.fetchone()[0]
                  cursor.execute(f"SELECT coins FROM member_rank WHERE discordid = {player2.id}")
                  p2coins = cursor.fetchone()[0]

                  if wager > p1coins and wager > p2coins:
                     await ctx.send(f"{player1.mention}, neither you nor {player2.mention} have enough credits for a {wager}-credit bet.")
                  elif wager > p1coins:
                     await ctx.send(f"{player1.mention}, you don't have enough credits to bet {wager} credits.")
                  elif wager > p1coins:
                     await ctx.send(f"{player1.mention}, {player2.mention} doesn't have enough credits to bet {wager} credits.")
                  else:
                     self.player1 = player1
                     self.player2 = player2
                     self.challengeTime = datetime.utcnow()
                     self.wager = wager
                     self.lastChannel = ctx.message.channel
                     await ctx.send(f"{player2.mention}, {player1.mention} has challenged you to a game of pazaak! Type !accept to accept the challenge or !decline to decline the challenge. The challenge expires after 3 minutes.")
               except Exception as e:
                  print(str(e))

               db.close()

   @commands.command()
   async def accept (self, ctx):
      if playChannel(ctx.message.guild.id, ctx.message.channel.id):
         if datetime.utcnow() - timedelta(minutes=3) > self.challengeTime:
            await ctx.send(f"{ctx.message.author.mention}, the challenge time has expired. Make a new challenge by typing !pazaak and tagging your opponent.")
         else:
            if ctx.message.author.id != self.player2.id:
               await ctx.send(f"{ctx.message.author.mention}, you can't accept the challenge for {self.player2.mention}.")
            else:
               self.game = Game(self.player1, self.player2, self.wager)
               await ctx.send(f"{self.player1.mention}, {self.player2.mention} has accepted the challenge! Please see your DM's for side deck selection.")

               user = self.client.get_user(self.player1.id)
               await user.send(embed=self.game.showCardOptions(PLAYER_1))
               user = self.client.get_user(self.player2.id)
               await user.send(embed=self.game.showCardOptions(PLAYER_2))

               if separateChannel(ctx.message.guild.id):
                  self.lastChannel = await ctx.message.guild.create_text_channel(f"{self.player1.name} v {self.player2.name}")
               else:
                  self.lastChannel = ctx.message.channel

   @commands.command()
   async def decline (self, ctx):
      if ctx.message.author.id != self.player2.id:
         await ctx.send(f"{ctx.message.author.mention}, you can't decline the challenge for {self.player2.mention}.")
      else:
         await ctx.send(f"{self.player1.mention}, {self.player2.mention} has declined the challenge. Please make another challenge by typing !pazaak and tagging your opponent.")
         self.game = None
         self.player1 = None
         self.player2 = None

   @commands.command()
   async def add (self, ctx, card, amount=1):
      if self.game is not None and isinstance(ctx.message.channel, discord.channel.DMChannel) and (ctx.message.author.id == self.player1.id or ctx.message.author.id == self.player2.id) and not self.finishedSelection:
         currentPlayer = -1
         if ctx.message.author.id == self.player1.id and not self.game.finishedSelection(PLAYER_1):
            currentPlayer = PLAYER_1
         if ctx.message.author.id == self.player2.id and not self.game.finishedSelection(PLAYER_2):
            currentPlayer = PLAYER_2
         
         if currentPlayer > 0:
            card = card.translate({ord(n): None for n in '[]'})
            amount = int(amount)

            if amount + self.game.selectedAmount(currentPlayer, card) <= self.game.ownedAmount(currentPlayer, card):
               for i in range(amount):
                  self.game.addSelection(currentPlayer, card)
            else:
               await ctx.message.channel.send(f"You currently own {self.game.ownedAmount(currentPlayer, card)} [{card}] cards. Please enter the right card and amount that you currently own that you would like to add.")
      
   @commands.command()
   async def remove (self, ctx, card, amount=1):
      if self.game is not None and isinstance(ctx.message.channel, discord.channel.DMChannel) and (ctx.message.author.id == self.player1.id or ctx.message.author.id == self.player2.id) and not self.finishedSelection:
         currentPlayer = -1
         if ctx.message.author.id == self.player1.id and not self.game.finishedSelection(PLAYER_1):
            currentPlayer = PLAYER_1
         if ctx.message.author.id == self.player2.id and not self.game.finishedSelection(PLAYER_2):
            currentPlayer = PLAYER_2
         
         if currentPlayer > 0:
            card = card.translate({ord(n): None for n in '[]'})
            amount = int(amount)

            if amount > self.game.selectedAmount(currentPlayer, card):
               for i in range(amount):
                  self.game.removeSelection(currentPlayer, card)
            else:
               await ctx.message.channel.send(f"You only have {self.game.selectedAmount(currentPlayer, card)} [{card}] cards selected. Please enter the right card and amount that you currently have selected that you would like to remove.")
      
   @commands.command()
   async def last (self, ctx):
      if self.game is not None and isinstance(ctx.message.channel, discord.channel.DMChannel) and (ctx.message.author.id == self.player1.id or ctx.message.author.id == self.player2.id) and not self.finishedSelection:
         currentPlayer = -1
         if ctx.message.author.id == self.player1.id and not self.game.finishedSelection(PLAYER_1):
            currentPlayer = PLAYER_1
         if ctx.message.author.id == self.player2.id and not self.game.finishedSelection(PLAYER_2):
            currentPlayer = PLAYER_2
         
         if currentPlayer > 0:
            cardOptions = next(item['code'] for item in cards['cards'])

            db = MySQLdb.connect("localhost", config['database_user'], config['database_pass'], config['database_schema'])
            cursor = db.cursor()

            try:
               cursor.execute(f"SELECT p1, p2, p3, p4, p5, p6, m1, m2, m3, m4, m5, m6, pm1, pm2, pm3, pm4, pm5, pm6, f24, f36, dc, tc FROM pazaak_side_deck WHERE discordid = {ctx.message.author.id}")
               lastDeck = cursor.fetchone()

               for i in range(len(cardOptions)):
                  for _ in range(lastDeck[i]):
                     self.game.makeSelection(currentPlayer, cardOptions[i], "add")
            except Exception as e:
               print(str(e))

            db.close()
      
   @commands.command()
   async def done (self, ctx):
      if self.game is not None and isinstance(ctx.message.channel, discord.channel.DMChannel) and (ctx.message.author.id == self.player1.id or ctx.message.author.id == self.player2.id) and not self.finishedSelection:
         currentPlayer = -1
         if ctx.message.author.id == self.player1.id and not self.game.finishedSelection(PLAYER_1):
            currentPlayer = PLAYER_1
         if ctx.message.author.id == self.player2.id and not self.game.finishedSelection(PLAYER_2):
            currentPlayer = PLAYER_2
         
         if currentPlayer > 0:
            if self.game.completedSideDeck(currentPlayer):
               self.game.finishSelection(currentPlayer)
               await ctx.message.channel.send(embed=self.game.showPlayableCards(currentPlayer))
            else:
               await ctx.message.channel.send("You need to select 10 cards before moving on.")

            if self.game.finishedSelection(PLAYER_1) and self.game.finishedSelection(PLAYER_2):
               self.finishedSelection = True
               
               await self.lastChannel.send(f"{self.player1.mention}, please type !heads or !tails for the coin toss to see who will start the first round.")

   @commands.command()
   async def heads (self, ctx):
      if ctx.message.author.id == self.player1.id and playChannel(ctx.message.guild.id, ctx.message.channel.id):
         await ctx.send(self.game.coinToss("heads"))
         self.game.setCard(randint(1,10))
         await ctx.send(embed=self.game.displayBoard())
      else:
         await ctx.send(f"{ctx.message.author.mention}, you can't play for {self.player1.mention}.")

   @commands.command()
   async def tails (self, ctx):
      if ctx.message.author.id == self.player1.id and playChannel(ctx.message.guild.id, ctx.message.channel.id):
         await ctx.send(self.game.coinToss("tails"))
         self.game.setCard(randint(1,10))
         await ctx.send(embed=self.game.displayBoard())
      else:
         await ctx.send(f"{ctx.message.author.mention}, you can't play for {self.player1.mention}.")

   @commands.command()
   async def end (self, ctx):
      if ctx.message.author.id == self.game.getCurrentPlayerID():
         self.cardPlayed = False
         self.game.endTurn()
         if await endTurn(self, ctx):
            await ctx.send(embed=self.game.displayBoard())
      else:
         await ctx.send(f"{ctx.message.author.mention}, you can't play for {self.game.mentionCurrentPlayer()}.")

   @commands.command()
   async def stand (self, ctx):
      if ctx.message.author.id == self.game.getCurrentPlayerID():
         self.cardPlayed = False
         self.game.stand()
         if await endTurn(self, ctx):
            await ctx.send(embed=self.game.displayBoard())
      else:
         await ctx.send(f"{ctx.message.author.mention}, you can't play for {self.game.mentionCurrentPlayer()}.")

   @commands.command()
   async def play (self, ctx, card, sign=None):
      if ctx.message.author.id == self.game.getCurrentPlayerID():
         card = card.translate({ord(i): None for i in '[]'})
         if self.cardPlayed:
            await ctx.send("You already played a card this turn. Type !end to end your turn or !stand to stay on your hand.")
         elif not self.game.canPlayCard(card):
            await ctx.send(f"You don't have a [{card}] card in your side deck.")
         else:
            try:
               if card == "T":
                  self.game.setCard(int(f"{sign}1"), True, card)
               elif card == "D" or card == "F2/4" or card == "F3/6":
                  self.game.setCard(0, True, card)
               else:
                  if sign is None:
                     self.game.setCard(int(card), True, card)
                  else:
                     value = [int(i) for i in card if i.isdigit()][0]
                     self.game.setCard(int(f"{sign}{value}"), True, card)

               self.cardPlayed = True
               user = self.client.get_user(self.game.players[self.game.currentPlayer].id)
               if self.game.hasCardsLeft(self.game.currentPlayer):
                  await user.send(embed=self.game.showCurrentCards(self.game.currentPlayer))

            except Exception as e:
               print(str(e))
               await ctx.send("There was a mistake in your play input. Please try again using the proper formatting.")

            if await endTurn(self, ctx):
               await ctx.send(embed=self.game.displayBoard())
      else:
         await ctx.send(f"{ctx.message.author.mention}, you can't play for {self.game.mentionCurrentPlayer()}.")

   @tasks.loop(seconds=15)
   async def timer (self):
      if self.game is not None and datetime.utcnow() - timedelta(minutes=3) > self.challengeTime:
         self.game = None
         self.player1 = None
         self.player2 = None
         await self.lastChannel.send("Challenge has expied.")

async def endTurn (self, ctx):
   if self.game.turnOver():
      self.game.stand()
      self.cardPlayed = False
   if self.game.roundOver():
      self.game.findRoundWinner()
      if self.game.roundWinner != TIED:
         await ctx.send(content=self.game.declareRoundWinner(), embed=self.game.displayBoard())
         if self.game.gameOver():
            await ctx.send(self.game.declareGameWinner())
            self.game = None
            return False
      else:
         await ctx.send(content="Round tied!", embed=self.game.displayBoard())
      await ctx.send(self.game.nextRound())
   elif not self.cardPlayed:
      self.game.setCard(randint(1,10))
      if self.game.turnOver():
         self.game.stand()
         self.cardPlayed = False
         await ctx.send(embed=self.game.displayBoard())

   return True

def playChannel (serverid, channelid):
   try:
      db = MySQLdb.connect(config['database_server'], config['database_user'], config['database_pass'], config['database_schema'])
      cursor = db.cursor()

      cursor.execute(f"SELECT play_channel FROM server_info WHERE server_id = {serverid}")
      playChannel = cursor.fetchone()[0]

      db.close()
      return playChannel is None or playChannel == channelid

   except Exception as e:
      print(str(e))
      return False

def separateChannel (serverid):
   try:
      db = MySQLdb.connect(config['database_server'], config['database_user'], config['database_pass'], config['database_schema'])
      cursor = db.cursor()

      cursor.execute(f"SELECT separate_channel FROM server_info WHERE server_id = {serverid} AND separate_channel = 1")
      db.close()

      return cursor.rowcount == 1
   except Exception as e:
      print(str(e))
      return False

def setup (client):
   client.add_cog(Play(client))