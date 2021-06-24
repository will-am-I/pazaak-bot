import discord, json, MySQLdb
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from random import randint
from game import Game, PLAYER_1, PLAYER_2, TIED

with open('./config.json') as data:
   config = json.load(data)
with open('./cards.json') as data:
   cards = json.load(data)

class Play(commands.Cog):

   def __init__ (self, client):
      self.client = client
      self.awaiting = []
      self.games = {}
      self.timer.start()

   def cog_unload (self):
      self.timer.stop()

   @commands.command()
   async def duel (self, ctx, player2:discord.Member=None, wager=0):
      if playChannel(ctx.message.guild.id, ctx.message.channel.id):
         if player2 is None:
            await ctx.send("Please tag the member you'd like to challenge.")
         else:
            player1 = ctx.message.author
            
            if inGame(player1):
               await ctx.send(f"{player1.name}, you are already in a game.")
            elif inGame(player2):
               await ctx.send(f"{player2.name} is already in a game.")
            else:
               wager = int(wager)

               db = MySQLdb.connect(config['database_server'], config['database_user'], config['database_pass'], config['database_schema'])
               cursor = db.cursor()

               try:
                  cursor.execute(f"SELECT credits FROM pazaak_balance WHERE discordid = {player1.id}")
                  p1coins = cursor.fetchone()[0]
                  cursor.execute(f"SELECT credits FROM pazaak_balance WHERE discordid = {player2.id}")
                  p2coins = cursor.fetchone()[0]

                  if wager >= p1coins and wager >= p2coins:
                     await ctx.send(f"{player1.name}, neither you nor {player2.name} have enough credits for a {wager}-credit bet.")
                  elif wager >= p1coins:
                     await ctx.send(f"{player1.name}, you don't have enough credits to bet {wager} credits.")
                  elif wager >= p1coins:
                     await ctx.send(f"{player1.name}, {player2.name} doesn't have enough credits to bet {wager} credits.")
                  else:
                     cursor.execute(f"INSERT INTO game_instance (player1id, player2id) VALUES ({player1.id}, {player2.id})")
                     db.commit()
                     cursor.execute(f"SELECT gameid FROM game_instance WHERE player1id = {player1.id} AND player2id = {player2.id}")
                     gameid = cursor.fetchone()[0]
                     self.games[gameid] = Game(gameid, player1, player2, wager, ctx.message.channel)
                     self.awaiting.append(player2.id)

                     await ctx.send(f"{player2.name}, {player1.name} has challenged you to a game of pazaak! Type **p.accept** to accept the challenge or **p.decline** to decline the challenge. The challenge expires after 2 minutes.")
               except Exception as e:
                  db.rollback()
                  print(repr(e))
                  print(str(e))
                  print(e.args)

               db.close()

   @commands.command()
   async def accept (self, ctx):
      if playChannel(ctx.message.guild.id, ctx.message.channel.id):
         gameid = getCurrentGame(ctx.message.author.id)
         if gameid is not None and self.games[gameid].challenged:
            if datetime.utcnow() - timedelta(minutes=2) > self.games[gameid].challengeTime:
               await ctx.send(f"{ctx.message.author.name}, the challenge time has expired. Make a new challenge by typing !pazaak and tagging your opponent.")
            else:
               if ctx.message.author.id not in self.awaiting:
                  await ctx.send(f"{ctx.message.author.name}, you have not been challenged to a duel.")
               else:
                  self.games[gameid].accept()
                  self.awaiting.remove(ctx.message.author.id)
                  await ctx.send(f"{self.games[gameid].getPlayerName(PLAYER_1)}, {self.games[gameid].getPlayerName(PLAYER_2)} has accepted the challenge! Please see your DM's for side deck selection.")

                  if separateChannel(ctx.message.guild.id):
                     categoryExists = False

                     for category in ctx.message.guild.by_category():
                        if 'pazaak' in category[0].name.lower():
                           categoryExists = True
                           break
                     if categoryExists:
                        self.games[gameid].setChannel(await ctx.message.guild.create_text_channel(f"{self.games[gameid].getPlayerName(PLAYER_1)} v {self.games[gameid].getPlayerName(PLAYER_2)}", category=category[0]))
                     else:
                        self.games[gameid].setChannel(await ctx.message.guild.create_text_channel(f"{self.games[gameid].getPlayerName(PLAYER_1)} v {self.games[gameid].getPlayerName(PLAYER_2)}"))

                  i = 0
                  for player in self.games[gameid].getPlayers():
                     user = self.client.get_user(player)
                     await user.send(embed=self.games[gameid].showCardOptions(i))
                     i += 1

   @commands.command()
   async def decline (self, ctx):
      if playChannel(ctx.message.guild.id, ctx.message.channel.id):
         gameid = getCurrentGame(ctx.message.author.id)
         if gameid is not None and self.games[gameid].challenged:
            if ctx.message.author.id not in self.awaiting:
               await ctx.send(f"{ctx.message.author.mention}, you have not been challenged to a duel.")
            else:
               gameid = getCurrentGame(ctx.message.author.id)
               await ctx.send(f"{self.games[gameid].getPlayerName(PLAYER_1)}, {self.games[gameid].getPlayerName(PLAYER_2)} has declined the challenge. Please make another challenge by typing !pazaak and tagging your opponent.")
               self.awaiting.remove(ctx.message.author.id)
               await deleteGame(self, gameid, ctx.message.guild.id)

   @commands.command()
   async def add (self, ctx, card, amount=1):
      if isinstance(ctx.message.channel, discord.channel.DMChannel) and inGame(ctx.message.author):
         gameid = getCurrentGame(ctx.message.author.id)
         if gameid is not None and not finishedSelection(self.games[gameid]):
            currentPlayer = self.games[gameid].getCurrentPlayer(ctx.message.author.id)
            
            if currentPlayer >= 0:
               card = card.translate({ord(n): None for n in '[]'})
               amount = int(amount)

               if amount + self.games[gameid].selectedAmount(currentPlayer, card) <= self.games[gameid].ownedAmount(currentPlayer, card):
                  for i in range(amount):
                     self.games[gameid].addSelection(currentPlayer, card)
                  
                  await ctx.send(embed=self.games[gameid].showSelection(currentPlayer))
               else:
                  await ctx.message.channel.send(f"You currently own {self.games[gameid].ownedAmount(currentPlayer, card)} [{card}] cards. Please enter the right card and amount that you currently own that you would like to add.")
      
   @commands.command()
   async def remove (self, ctx, card, amount=1):
      if isinstance(ctx.message.channel, discord.channel.DMChannel) and inGame(ctx.message.author):
         gameid = getCurrentGame(ctx.message.author.id)
         if gameid is not None and not finishedSelection(self.games[gameid]):
            currentPlayer = self.games[gameid].getCurrentPlayer(ctx.message.author.id)
            
            if currentPlayer >= 0:
               card = card.translate({ord(n): None for n in '[]'})
               amount = int(amount)

               if amount <= self.games[gameid].selectedAmount(currentPlayer, card):
                  for i in range(amount):
                     self.games[gameid].removeSelection(currentPlayer, card)
                  
                  await ctx.send(embed=self.games[gameid].showSelection(currentPlayer))
               else:
                  await ctx.message.channel.send(f"You only have {self.games[gameid].selectedAmount(currentPlayer, card)} [{card}] cards selected. Please enter the right card and amount that you currently have selected that you would like to remove.")
      
   @commands.command()
   async def last (self, ctx):
      if isinstance(ctx.message.channel, discord.channel.DMChannel) and inGame(ctx.message.author):
         gameid = getCurrentGame(ctx.message.author.id)
         if gameid is not None and not finishedSelection(self.games[gameid]):
            currentPlayer = self.games[gameid].getCurrentPlayer(ctx.message.author.id)
            
            if currentPlayer >= 0:
               cardOptions = [item['code'] for item in cards['cards']]

               db = MySQLdb.connect("localhost", config['database_user'], config['database_pass'], config['database_schema'])
               cursor = db.cursor()

               try:
                  cursor.execute(f"SELECT p1, p2, p3, p4, p5, p6, m1, m2, m3, m4, m5, m6, pm1, pm2, pm3, pm4, pm5, pm6, f24, f36, dc, tc FROM pazaak_side_deck WHERE discordid = {ctx.message.author.id}")
                  lastDeck = cursor.fetchone()

                  for i in range(len(cardOptions)):
                     for _ in range(lastDeck[i]):
                        self.games[gameid].addSelection(currentPlayer, cardOptions[i])
               except Exception as e:
                  print(str(e))

               db.close()
               await ctx.send(embed=self.games[gameid].showSelection(currentPlayer))
      
   @commands.command()
   async def done (self, ctx):
      if isinstance(ctx.message.channel, discord.channel.DMChannel) and inGame(ctx.message.author):
         gameid = getCurrentGame(ctx.message.author.id)
         if gameid is not None and not finishedSelection(self.games[gameid]):
            currentPlayer = self.games[gameid].getCurrentPlayer(ctx.message.author.id)
            
            if currentPlayer >= 0:
               if self.games[gameid].completedSideDeck(currentPlayer):
                  self.games[gameid].finishSelection(currentPlayer)
                  await ctx.message.channel.send(embed=self.games[gameid].showPlayableCards(currentPlayer))
               else:
                  await ctx.message.channel.send("You need to select 10 cards before moving on.")

               if finishedSelection(self.games[gameid]):
                  await self.games[gameid].gameChannel.send(f"{self.games[gameid].mentionPlayer1}, please type **p.heads** or **p.tails** for the coin toss to see who will start the first round.")
                  self.games[gameid].resetPlayTimer()

   @commands.command()
   async def heads (self, ctx):
      if not isinstance(ctx.message.channel, discord.channel.DMChannel):
         gameid = getCurrentGame(ctx.message.author.id)
         if gameid is not None and ctx.message.author.id == self.games[gameid].getPlayerID(PLAYER_1):
            await ctx.send(self.games[gameid].coinToss("heads"))
            self.games[gameid].setCard(randint(1,10))
            await ctx.send(embed=self.games[gameid].displayBoard(), files=self.games[gameid].getImages())
            self.games[gameid].resetPlayTimer()
         else:
            await ctx.send(f"{ctx.message.author.name}, you are not a part of this game.")

   @commands.command()
   async def tails (self, ctx):
      if not isinstance(ctx.message.channel, discord.channel.DMChannel):
         gameid = getCurrentGame(ctx.message.author.id)
         if gameid is not None and ctx.message.author.id == self.games[gameid].getPlayerID(PLAYER_1):
            await ctx.send(self.games[gameid].coinToss("tails"))
            self.games[gameid].setCard(randint(1,10))
            await ctx.send(embed=self.games[gameid].displayBoard(), files=self.games[gameid].getImages())
            self.games[gameid].resetPlayTimer()
         else:
            await ctx.send(f"{ctx.message.author.name}, you are not a part of this game.")

   @commands.command()
   async def end (self, ctx):
      if not isinstance(ctx.message.channel, discord.channel.DMChannel):
         gameid = getCurrentGame(ctx.message.author.id)
         if gameid is not None and ctx.message.author.id in self.games[gameid].getPlayers():
            if self.games[gameid].isCurrentPlayer(ctx.message.author.id):
               self.games[gameid].cardNotPlayed()
               self.games[gameid].endTurn()
               
               if self.games[gameid].roundOver():
                  await endRound(self, ctx, gameid)
                  if self.games[gameid].gameOver():
                     await endGame(self, ctx, gameid)
                  else:
                     self.games[gameid].nextRound()
                     await ctx.send(embed=self.games[gameid].displayBoard(), files=self.games[gameid].getImages())
                     self.games[gameid].resetPlayTimer()
               else:
                  self.games[gameid].setCard(randint(1,10))
                  await ctx.send(embed=self.games[gameid].displayBoard(), files=self.games[gameid].getImages())
                  if self.games[gameid].turnOver():
                     if self.games[gameid].nat20():
                        await ctx.send(purePazaak(ctx.message.guild))
                     self.games[gameid].stand()
                     if self.games[gameid].roundOver():
                        await endRound(self, ctx, gameid)
                        if self.games[gameid].gameOver():
                           await endGame(self, ctx, gameid)
                        else:
                           self.games[gameid].nextRound()
                           await ctx.send(embed=self.games[gameid].displayBoard(), files=self.games[gameid].getImages())
                           self.games[gameid].resetPlayTimer()
                     else:
                        self.games[gameid].setCard(randint(1,10))
                        await ctx.send(embed=self.games[gameid].displayBoard(), files=self.games[gameid].getImages())
                        if self.games[gameid].turnOver():
                           if self.games[gameid].nat20():
                              await ctx.send(purePazaak(ctx.message.guild))
                           self.games[gameid].stand()
                           await endRound(self, ctx, gameid)
                           if self.games[gameid].gameOver():
                              await endGame(self, ctx, gameid)
                           else:
                              self.games[gameid].nextRound()
                              await ctx.send(embed=self.games[gameid].displayBoard(), files=self.games[gameid].getImages())
                              self.games[gameid].resetPlayTimer()
            else:
               await ctx.send(f"{ctx.message.author.name}, it is not your turn.")
         else:
            await ctx.send(f"{ctx.message.author.name}, you are not a part of this game.")

   @commands.command()
   async def stand (self, ctx):
      if not isinstance(ctx.message.channel, discord.channel.DMChannel):
         gameid = getCurrentGame(ctx.message.author.id)
         if gameid is not None and ctx.message.author.id in self.games[gameid].getPlayers():
            if self.games[gameid].isCurrentPlayer(ctx.message.author.id):
               self.games[gameid].cardNotPlayed()
               self.games[gameid].stand()

               if self.games[gameid].roundOver():
                  await endRound(self, ctx, gameid)
                  if self.games[gameid].gameOver():
                     await endGame(self, ctx, gameid)
                  else:
                     self.games[gameid].nextRound()
                     await ctx.send(embed=self.games[gameid].displayBoard(), files=self.games[gameid].getImages())
                     self.games[gameid].resetPlayTimer()
               else:
                  self.games[gameid].setCard(randint(1,10))
                  if self.games[gameid].turnOver():
                     if self.games[gameid].nat20():
                        await ctx.send(purePazaak(ctx.message.guild))
                     self.games[gameid].stand()
                     await endRound(self, ctx, gameid)
                     if self.games[gameid].gameOver():
                        await endGame(self, ctx, gameid)
                     else:
                        self.games[gameid].nextRound()
                        await ctx.send(embed=self.games[gameid].displayBoard(), files=self.games[gameid].getImages())
                        self.games[gameid].resetPlayTimer()
                  else:
                     await ctx.send(embed=self.games[gameid].displayBoard(), files=self.games[gameid].getImages())
                     self.games[gameid].resetPlayTimer()
            else:
               await ctx.send(f"{ctx.message.author.name}, it is not your turn.")
         else:
            await ctx.send(f"{ctx.message.author.name}, you are not a part of this game.")

   @commands.command()
   async def play (self, ctx, card, sign=None):
      if not isinstance(ctx.message.channel, discord.channel.DMChannel):
         gameid = getCurrentGame(ctx.message.author.id)
         if gameid is not None and ctx.message.author.id in self.games[gameid].getPlayers():
            if self.games[gameid].isCurrentPlayer(ctx.message.author.id):
               card = card.translate({ord(i): None for i in '[]'})
               if self.games[gameid].cardPlayed:
                  await ctx.send("You already played a card this turn. Type !end to end your turn or !stand to stay on your hand.")
               elif not self.games[gameid].canPlayCard(card):
                  await ctx.send(f"You don't have a [{card}] card in your side deck.")
               else:
                  try:
                     if card == "T":
                        self.games[gameid].setCard(int(f"{sign}1"), card)
                     elif card == "D" or card == "F2/4" or card == "F3/6":
                        self.games[gameid].setCard(0, card)
                     else:
                        if sign is None:
                           self.games[gameid].setCard(int(card), card)
                        else:
                           value = [int(i) for i in card if i.isdigit()][0]
                           self.games[gameid].setCard(int(f"{sign}{value}"), card)

                     self.games[gameid].cardIsPlayed()
                     if self.games[gameid].hasCardsLeft(self.games[gameid].currentPlayer):
                        user = self.client.get_user(self.games[gameid].players[self.games[gameid].currentPlayer].id)
                        await user.send(embed=self.games[gameid].showCurrentCards(self.games[gameid].currentPlayer))
                     
                     await ctx.send(embed=self.games[gameid].displayBoard(), files=self.games[gameid].getImages())
                     self.games[gameid].resetPlayTimer()
                     if self.games[gameid].turnOver():
                        self.games[gameid].stand()
                        self.games[gameid].cardNotPlayed()
                        if self.games[gameid].roundOver():
                           await endRound(self, ctx, gameid)
                           if self.games[gameid].gameOver():
                              await endGame(self, ctx, gameid)
                           else:
                              self.games[gameid].nextRound()
                              await ctx.send(embed=self.games[gameid].displayBoard(), files=self.games[gameid].getImages())
                              self.games[gameid].resetPlayTimer()
                        else:
                           self.games[gameid].setCard(randint(1,10))
                           await ctx.send(embed=self.games[gameid].displayBoard(), files=self.games[gameid].getImages())
                           self.games[gameid].resetPlayTimer()
                           if self.games[gameid].turnOver():
                              if self.games[gameid].nat20():
                                 await ctx.send(purePazaak(ctx.message.guild))
                              self.games[gameid].stand()
                              if self.games[gameid].roundOver():
                                 await endRound(self, ctx, gameid)
                                 if self.games[gameid].gameOver():
                                    await endGame(self, ctx, gameid)
                                 else:
                                    self.games[gameid].nextRound()
                                    await ctx.send(embed=self.games[gameid].displayBoard(), files=self.games[gameid].getImages())
                                    self.games[gameid].resetPlayTimer()

                  except Exception as e:
                     print(str(e))
                     await ctx.send("There was a mistake in your play input. Please try again using the proper formatting.")
            else:
               await ctx.send(f"{ctx.message.author.name}, it is not your turn.")
         else:
            await ctx.send(f"{ctx.message.author.name}, you are not a part of this game.")

   @tasks.loop(seconds=10)
   async def timer (self):
      gamesToDelete = []
      for game in self.games:
         if self.games[game].challenged and datetime.utcnow() - timedelta(minutes=3) > self.games[game].challengeTime:
            await self.games[game].playChannel.send("Challenge has expired.")
            gamesToDelete.append(game.gameid)
         if not self.games[game].challenged and datetime.utcnow() - timedelta(minutes=5) > self.games[game].playTime and finishedSelection(self.games[game]):
            await self.games[game].playChannel.send(f"{self.games[game].getPlayerName()} took too long. Game has been canceled.")
            gamesToDelete.append(self.games[game].gameid)
      for gameid in gamesToDelete:
         await deleteGame(self, gameid, self.games[game].playChannel.guild.id)

async def endRound (self, ctx, gameid):
   self.games[gameid].findRoundWinner()
   if self.games[gameid].roundWinner != TIED:
      await ctx.send(content=self.games[gameid].declareRoundWinner(), embed=self.games[gameid].displayBoard(), files=self.games[gameid].getImages())
   else:
      await ctx.send(content="Round tied!", embed=self.games[gameid].displayBoard(), files=self.games[gameid].getImages())

async def endGame (self, ctx, gameid):
   await self.games[gameid].playChannel.send(self.games[gameid].declareGameWinner())
   await deleteGame(self, gameid, ctx.message.guild.id)

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

def inGame (player):
   try:
      db = MySQLdb.connect(config['database_server'], config['database_user'], config['database_pass'], config['database_schema'])
      cursor = db.cursor()
      cursor.execute(f"SELECT * FROM game_instance WHERE player1id = {player.id} OR player2id = {player.id}")
      rowcount = cursor.rowcount
      db.close()
      return rowcount > 0
   except Exception as e:
      print(str(e))
      return False

def getCurrentGame (player):
   try:
      db = MySQLdb.connect(config['database_server'], config['database_user'], config['database_pass'], config['database_schema'])
      cursor = db.cursor()
      cursor.execute(f"SELECT gameid FROM game_instance WHERE player1id = {player} OR player2id = {player}")
      gameid = cursor.fetchone()[0]
      db.close()
      return gameid
   except Exception as e:
      print(str(e))
      return 0

def finishedSelection (game):
   return game.finishedSelection(PLAYER_1) and game.finishedSelection(PLAYER_2)

def separateChannel (serverid):
   try:
      db = MySQLdb.connect(config['database_server'], config['database_user'], config['database_pass'], config['database_schema'])
      cursor = db.cursor()
      cursor.execute(f"SELECT separate_channel FROM server_info WHERE server_id = {serverid} AND separate_channel = 1")
      rowcount = cursor.rowcount
      db.close()
      return rowcount == 1
   except Exception as e:
      print(str(e))
      return False

async def deleteGame (self, gameid, serverid):
   db = MySQLdb.connect(config['database_server'], config['database_user'], config['database_pass'], config['database_schema'])
   cursor = db.cursor()

   try:
      cursor.execute(f"DELETE FROM game_instance WHERE gameid = {gameid}")
      if separateChannel(serverid):
         await self.games[gameid].gameChannel.delete()
      self.games[gameid].deleteBoardImage()
      del self.games[gameid]
      db.commit()
   except Exception as e:
      db.rollback()
      print(str(e))

   db.close()

def purePazaak (guild):
   for emoji in guild.emojis:
      if "pure" in emoji.name.lower() and "pazaak" in emoji.name.lower():
         return f":{emoji.name}:"
   return "Pure Pazaak!"

def setup (client):
   client.add_cog(Play(client))