from datetime import datetime, timedelta
import discord, json, MySQLdb, collections, os
from random import randint
from player import Player
from PIL import Image, ImageDraw, ImageFont

with open('./config.json') as data:
   config = json.load(data)
with open('./cards.json') as data:
   cards = json.load(data)

PLAYER_1 = 0
PLAYER_2 = 1
TIED = -1

TURN_COORDS = [(26, 17), (489, 17)]
POINT_COORDS = [[(103, 49), (123, 49), (142, 49)], [(385, 49), (405, 49), (424, 49)]]
TOTAL_COORDS = [[(222, 63), (219, 63), (220, 63), (222, 63), (218, 63)], [(326, 63), (323, 63), (324, 63), (326, 63), (322, 63)]]
TOTAL_CROP_COORDS = [(203, 49, 240, 66), (305, 49, 342, 66)]
FIELD_COORDS = [[(74, 83), (128, 83), (183, 83), (74, 151), (128, 151), (183, 151), (74, 219), (128, 219), (183, 219)], [(314, 83), (368, 83), (422, 83), (314, 151), (368, 151), (422, 151), (314, 219), (368, 219), (422, 219)]]
DECK_COORDS = [[(36, 306), (90, 306), (144, 306), (198, 306)], [(298, 306), (352, 306), (406, 306), (460, 306)]]
DECK_CROP_COORDS = [[(36, 306, 85, 369), (90, 306, 139, 369), (144, 306, 193, 369), (198, 306, 247, 369)], [(298, 306, 347, 369), (352, 306, 401, 369), (406, 306, 455, 369), (460, 306, 509, 369)]]
CARD_SIZE = (49, 63)

class Game:
   def __init__ (self, gameid, player1, player2, bet, channel):
      self.gameid = gameid
      self.players = [Player(player1), Player(player2)]
      self.mentionPlayer1 = player1.mention
      self.bet = bet
      self.playChannel = channel
      self.gameChannel = channel
      self.cardPlayed = False
      self.challenged = True
      self.challengeTime = datetime.utcnow()
      self.playTime = datetime.utcnow()
      self.round = 1
      self.currentPlayer = -1
      self.roundWinner = None
      self.roundStarter = -1
      self.playedCards = []
      self.gameWinner = -1
      self.gameLoser = -1
      self.playedCardImage = None

      base = Image.open("./images/board.png")
      covered = Image.open("./images/covered.png")

      covered = covered.resize(CARD_SIZE)
      play = base.copy()
      
      draw = ImageDraw.Draw(play)
      font = ImageFont.truetype("./BankGothic Regular.ttf", size=20)
      draw.text((67, 34), player1.display_name, (255, 255, 255), anchor="ls", font=font)
      draw.text((484, 34), player2.display_name, (255, 255, 255), anchor="rs", font=font)

      for i in range(2):
         for j in range(4):
            play.paste(covered, DECK_COORDS[i][j], covered)

      play.save(f"./images/play{gameid}.png")

   def getPlayerID (self, player=None):
      if player is None:
         return self.players[self.currentPlayer].id
      else:
         return self.players[player].id

   def getPlayerName (self, player=None):
      if player is None:
         return self.players[self.currentPlayer].name
      else:
         return self.players[player].name

   def getCurrentPlayer (self, playerid):
      if playerid == self.players[PLAYER_1].id:
         return PLAYER_1
      elif playerid == self.players[PLAYER_2].id:
         return PLAYER_2
      else:
         return -1

   def getPlayers (self):
      return [player.id for player in self.players]

   def isCurrentPlayer (self, playerid):
      return playerid == self.players[self.currentPlayer].id

   def setChannel (self, channel):
      self.gameChannel = channel

   def accept (self):
      self.challenged = False

   def showCardOptions (self, player):
      db = MySQLdb.connect("localhost", config['database_user'], config['database_pass'], config['database_schema'])
      cursor = db.cursor()

      embed = discord.Embed(title="Choose your side deck", colour=discord.Colour(0x4e7e8a), description="You may choose up to 10 cards, and 4 will be chosen at random to play.")
      try:
         cursor.execute(f"SELECT p1, p2, p3, p4, p5, p6, m1, m2, m3, m4, m5, m6, pm1, pm2, pm3, pm4, pm5, pm6, f24, f36, dc, tc FROM pazaak_inventory WHERE discordid = {self.players[player].id}")
         cardAmounts = cursor.fetchone()

         for i in range(len(cards['cards'])):
            if any(j in cards['cards'][i]['code'] for j in ['F', 'D', 'T']):
               embed.add_field(name=f"[{cards['cards'][i]['code']}] {cards['cards'][i]['name']}", value=str(cardAmounts[i]), inline=False)
            else:
               embed.add_field(name=f"[{cards['cards'][i]['code']}]", value=str(cardAmounts[i]), inline=True)
      except Exception as e:
         print(str(e))
      embed.set_footer(text="Use **p.help sidedeck** if you need help with how to choose your side deck or **p.sidedeck** to view your inventory again.")
      db.close()

      return embed

   def selectedAmount (self, player, card):
      selected = 0
      for selectedCard in self.players[player].selection:
         if selectedCard == card:
            selected += 1

      return selected

   def ownedAmount (self, player, card):
      dbcard = next(item['db_name'] for item in cards['cards'] if item['code'] == card)
      amountOwned = 0

      db = MySQLdb.connect(config['database_server'], config['database_user'], config['database_pass'], config['database_schema'])
      cursor = db.cursor()

      try:
         cursor.execute(f"SELECT {dbcard} FROM pazaak_inventory WHERE discordid = {self.players[player].id}")
         amountOwned = cursor.fetchone()[0]
      except Exception as e:
         print(str(e))

      db.close()

      return amountOwned

   def addSelection (self, player, card):
      self.players[player].add(card)
   
   def removeSelection (self, player, card):
      self.players[player].remove(card)
         
   def showSelection (self, player):
      selectionCards = [i for n, i in enumerate(self.players[player].selection) if i not in self.players[player].selection[:n]]
      selectionCount = collections.Counter(self.players[player].selection)

      deck = ""
      for card in selectionCards:
         deck += f"\n{selectionCount[card]} [{card}]\n"
      deck += f"\nTotal cards: {len(self.players[player].selection)}"

      embed = discord.Embed(title="Your current selection:", colour=discord.Colour(0x4e7e8a), description=deck)
      embed.set_footer(text="Use **p.help 2** if you need help with how to choose your side deck or **p.sidedeck** to view your inventory again.")
      return embed

   def completedSideDeck (self, player):
      return len(self.players[player].selection) == 10

   def finishSelection (self, player):
      db = MySQLdb.connect("localhost", config['database_user'], config['database_pass'], config['database_schema'])
      cursor = db.cursor()

      try:
         cursor.execute(f"DELETE FROM pazaak_side_deck WHERE discordid = {self.players[player].id}")
         cursor.execute(f"INSERT INTO pazaak_side_deck (discordid) VALUES ({self.players[player].id})")
         for selected in self.players[player].selection:
            dbcard = next(item['db_name'] for item in cards['cards'] if item['code'] == selected)
            cursor.execute(f"UPDATE pazaak_side_deck SET {dbcard} = {dbcard} + 1 WHERE discordid = {self.players[player].id}")
         db.commit()

      except Exception as e:
         db.rollback()
         print(str(e))

      db.close()
      self.players[player].finish()

   def finishedSelection (self, player):
      return self.players[player].finishedSelection
      
   def showPlayableCards (self, player):
      selected = []
      cards = []

      while True:
         rand = randint(0, 9)

         if rand not in selected:
            selected.append(rand)
            cards.append(self.players[player].selection[rand])

         if len(selected) == 4:
            break

      self.players[player].set(cards)
      
      deck = ""
      for card in cards:
         deck += f"\n[{card}]\n"

      return discord.Embed(title="Your playable cards:", colour=discord.Colour(0x4e7e8a), description=deck)

   def coinToss (self, side):
      sides = ['heads', 'tails']
      result = sides[randint(0,1)]

      if side[0] == result[0]:
         self.roundStarter = self.currentPlayer = PLAYER_2
      else:
         self.roundStarter = self.currentPlayer = PLAYER_1

      return f"The coin landed on {result}. {self.players[self.roundStarter].name} will start the game."

   def resetPlayTimer (self):
      self.playTime = datetime.utcnow()

   def getImages (self):
      if self.roundWinner is None:
         return [discord.File(f"./images/{self.playedCardImage}", filename=self.playedCardImage), discord.File(f"./images/play{self.gameid}.png", filename="play.png")]
      else:
         return [discord.File(f"./images/play{self.gameid}.png", filename="play.png")]

   def setCard (self, value, card=None):
      if card is not None:
         self.findCardImage(value, card)
         self.players[self.currentPlayer].play(value, card)
      else:
         while True:
            count = 0
            for played in self.playedCards:
               if played == value:
                  count += 1

            if count < 4:
               self.playedCards.append(value)
               break
            else:
               value = randint(1,10)

         self.findCardImage(value)
         self.players[self.currentPlayer].play(value)

   def findCardImage (self, value, card=None):
      play = Image.open(f"./images/play{self.gameid}.png")

      if card is not None:
         card = card.translate({ord(i): None for i in '[]'})

         board = Image.open("./images/board.png")
         crop = board.crop(DECK_CROP_COORDS[self.currentPlayer][len(self.players[self.currentPlayer].sideDeck)-1])
         play.paste(crop, DECK_COORDS[self.currentPlayer][len(self.players[self.currentPlayer].sideDeck)-1])

         if 'F' in card:
            self.playedCardImage = f"{card.lower().replace('/', '')}.png"

            for i in range(len(self.players[self.currentPlayer].fieldCards)):
               setCard = self.players[self.currentPlayer].fieldCards[i]
               setCardID = self.players[self.currentPlayer].fieldCardIDs[i]

               if setCard in [3, 6, 2, 4]:
                  if 'dc' in setCardID:
                     newCard = Image.open(f"./images/dc{setCard}.png")
                  else:
                     newCard = Image.open(f"./images/f_p_{setCardID}.png")
                     
                  newCard = newCard.resize(CARD_SIZE)
                  play.paste(newCard, FIELD_COORDS[self.currentPlayer][i], newCard)

               if setCard in [-3, -6, -2, -4]:
                  newCard = Image.open(f"./images/f_m_{setCardID}.png")
                  newCard = newCard.resize(CARD_SIZE)
                  play.paste(newCard, FIELD_COORDS[self.currentPlayer][i], newCard)
                  
         elif 'D' in card:
            self.playedCardImage = f"dc.png"
            newCard = Image.open(f"./images/dc{value}.png")
            newCard = newCard.resize(CARD_SIZE)
            play.paste(newCard, FIELD_COORDS[self.currentPlayer][len(self.players[self.currentPlayer].fieldCards)], newCard)

         elif 'T' in card:
            if value > 0:
               self.playedCardImage = f"p_tc.png"
               newCard = Image.open(f"./images/p_tc.png")
            else:
               self.playedCardImage = f"m_tc.png"
               newCard = Image.open(f"./images/m_tc.png")
               
            newCard = newCard.resize(CARD_SIZE)
            play.paste(newCard, FIELD_COORDS[self.currentPlayer][len(self.players[self.currentPlayer].fieldCards)], newCard)

         elif '+/-' in card:
            if value > 0:
               self.playedCardImage = f"p_pm{value}.png"
               newCard = Image.open(f"./images/p_pm{value}.png")
            else:
               self.playedCardImage = f"m_pm{abs(value)}.png"
               newCard = Image.open(f"./images/m_pm{abs(value)}.png")
               
            newCard = newCard.resize(CARD_SIZE)
            play.paste(newCard, FIELD_COORDS[self.currentPlayer][len(self.players[self.currentPlayer].fieldCards)], newCard)

         else:
            if value > 0:
               self.playedCardImage = f"p{value}.png"
               newCard = Image.open(f"./images/p{value}.png")
            else:
               self.playedCardImage = f"m{abs(value)}.png"
               newCard = Image.open(f"./images/m{abs(value)}.png")
            
            newCard = newCard.resize(CARD_SIZE)
            play.paste(newCard, FIELD_COORDS[self.currentPlayer][len(self.players[self.currentPlayer].fieldCards)], newCard)

      else:
         self.playedCardImage = f"{value}.png"
         newCard = Image.open(f"./images/{value}.png")
         newCard = newCard.resize(CARD_SIZE)
         play.paste(newCard, FIELD_COORDS[self.currentPlayer][len(self.players[self.currentPlayer].fieldCards)], newCard)
      
      play.save(f"./images/play{self.gameid}.png")

   def displayBoard (self):
      play = Image.open(f"./images/play{self.gameid}.png")
      board = Image.open("./images/board.png")
      draw = ImageDraw.Draw(play)
      font = ImageFont.truetype("./BankGothic Regular.ttf", size=20)
      turn = Image.open("./images/turn.png")
      notTurn = Image.open("./images/not_turn.png")

      if self.currentPlayer == PLAYER_1:
         play.paste(turn, TURN_COORDS[PLAYER_1], turn)
         play.paste(notTurn, TURN_COORDS[PLAYER_2], notTurn)
      if self.currentPlayer == PLAYER_2:
         play.paste(turn, TURN_COORDS[PLAYER_2], turn)
         play.paste(notTurn, TURN_COORDS[PLAYER_1], notTurn)

      for i in range(2):
         crop = board.crop(TOTAL_CROP_COORDS[i])
         play.paste(crop, TOTAL_CROP_COORDS[i])

         total = self.players[i].total()
         if total >= 0:
            draw.text(TOTAL_COORDS[i][int(total / 10)], str(total), (255, 255, 255), anchor="ms", font=font)
         else:
            draw.text(TOTAL_COORDS[i][int(abs(total) / 10) + 3], str(total), (255, 255, 255), anchor="ms", font=font)

      play.save(f"./images/play{self.gameid}.png")

      if self.roundWinner is not None:
         embed = discord.Embed(title="Current Board", colour=discord.Colour(0x4e7e8a))
      else:
         embed = discord.Embed(title="Current Board", colour=discord.Colour(0x4e7e8a), description=f"{self.players[self.currentPlayer].name}'s turn.")
         embed.set_thumbnail(url=f"attachment://{self.playedCardImage}")

      embed.set_image(url="attachment://play.png")
      embed.set_footer(text="Use **p.help 1** for help with how to play the game.")
      return embed

   def endTurn (self):
      if self.currentPlayer == PLAYER_1 and not self.players[PLAYER_2].stood:
         self.currentPlayer = PLAYER_2
      elif self.currentPlayer == PLAYER_2 and not self.players[PLAYER_1].stood:
         self.currentPlayer = PLAYER_1

   def stand (self):
      if self.currentPlayer == PLAYER_1:
         self.players[PLAYER_1].stand()
         if not self.players[PLAYER_2].stood:
            self.currentPlayer = PLAYER_2
      elif self.currentPlayer == PLAYER_2:
         self.players[PLAYER_2].stand()
         if not self.players[PLAYER_1].stood:
            self.currentPlayer = PLAYER_1

   def canPlayCard (self, card):
      return card in self.players[self.currentPlayer].sideDeck

   def hasCardsLeft (self, player):
      return len(self.players[player].sideDeck) > 0

   def cardIsPlayed (self):
      self.cardPlayed = True

   def cardNotPlayed (self):
      self.cardPlayed = False

   def showCurrentCards (self, player):
      deck = ""

      for card in self.players[player].sideDeck:
         deck += f"\n[{card}]\n"

      return discord.Embed(title="Your playable cards:", colour=discord.Colour(0x4e7e8a), description=deck)

   def turnOver (self):
      if self.players[self.currentPlayer].total() == 20:
         return True
      elif len(self.players[self.currentPlayer].fieldCards) == 9:
         return True
      else:
         return False

   def roundOver (self):
      if self.players[PLAYER_1].total() > 20 or self.players[PLAYER_2].total() > 20:
         return True
      elif self.players[PLAYER_1].stood and self.players[PLAYER_2].stood:
         return True
      elif len(self.players[PLAYER_1].fieldCards) == 9 or len(self.players[PLAYER_2].fieldCards) == 9:
         return True
      else:
         return False

   def findRoundWinner (self):
      p1Total = self.players[PLAYER_1].total()
      p2Total = self.players[PLAYER_2].total()

      if p1Total > 20:
         self.roundWinner = PLAYER_2
      elif p2Total > 20:
         self.roundWinner = PLAYER_1
      elif len(self.players[PLAYER_1].fieldCards) == 9:
         self.roundWinner = PLAYER_1
      elif len(self.players[PLAYER_2].fieldCards) == 9:
         self.roundWinner = PLAYER_2
      elif p1Total > p2Total:
         self.roundWinner = PLAYER_1
      elif p1Total < p2Total:
         self.roundWinner = PLAYER_2
      elif self.players[PLAYER_1].tiebreaker:
         self.roundWinner = PLAYER_1
      elif self.players[PLAYER_2].tiebreaker:
         self.roundWinner = PLAYER_2
      else:
         self.roundWinner = TIED

   def declareRoundWinner (self):
      self.players[self.roundWinner].won()

      play = Image.open(f"./images/play{self.gameid}.png")
      point = Image.open("./images/point.png")

      play.paste(point, POINT_COORDS[self.roundWinner][self.players[self.roundWinner].points-1])
      play.save(f"./images/play{self.gameid}.png")

      return f"{self.players[self.roundWinner].name} has won the round!"

   def nextRound (self):
      self.round += 1
      self.playedCards = []

      if self.roundWinner != TIED:
         self.roundStarter = self.currentPlayer = self.roundWinner
      else:
         self.currentPlayer = self.roundStarter

      play = Image.open(f"./images/play{self.gameid}.png")
      board = Image.open("./images/board.png")

      crop = board.crop((0, 78, 547, 287))
      play.paste(crop, (0, 78))
      play.save(f"./images/play{self.gameid}.png")

      self.players[PLAYER_1].clear()
      self.players[PLAYER_2].clear()
      self.setCard(randint(1,10))
      self.roundWinner = None

      return f"{self.players[self.currentPlayer].mention} will start the next round."

   def gameOver (self):
      if self.players[PLAYER_1].points == 3:
         self.gameWinner = PLAYER_1
         self.gameLoser = PLAYER_2
         return True
      elif self.players[PLAYER_2].points == 3:
         self.gameWinner = PLAYER_2
         self.gameLoser = PLAYER_1
         return True
      else:
         return False

   def declareGameWinner (self):
      db = MySQLdb.connect("localhost", config['database_user'], config['database_pass'], config['database_schema'])
      cursor = db.cursor()

      try:
         cursor.execute(f"UPDATE pazaak_balance SET credits = credits + {self.bet}, wins = wins + 1 WHERE discordid = {self.players[self.gameWinner].id}")
         cursor.execute(f"UPDATE pazaak_balance SET credits = credits - {self.bet}, losses = losses + 1 WHERE discordid = {self.players[self.gameLoser].id}")
         os.remove(f"./images/play{self.gameid}.png")
         db.commit()
      except Exception as e:
         db.rollback()
         print(str(e))
      db.close()

      statement = f"{self.players[self.gameWinner].mention} has won the game!"
      if self.bet > 0:
         statement += f" {self.bet} coins have been awarded from {self.players[self.gameLoser].name}!"

      return statement