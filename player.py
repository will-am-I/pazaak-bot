import json, mysql.connector

with open('./config.json') as data:
   config = json.load(data)
with open('./cards.json') as data:
   cards = json.load(data)

class Player:
   def __init__ (self, player):
      self.id = player.id
      self.name = player.display_name
      self.mention = player.mention
      self.selection = []
      self.sideDeck = []
      self.fieldCards = []
      self.fieldCardIDs = []
      self.points = 0
      self.double = False
      self.tiebreaker = False
      self.stood = False
      self.finishedSelection = False
      
      db = mysql.connector.connect(host=config['database_server'], user=config['database_user'], password=config['database_pass'], database=config['database_schema'])
      cursor = db.cursor()
      try:
         cursor.execute(f"INSERT IGNORE INTO pazaak_inventory (discordid) VALUES ({player.id})")
         db.commit()
      except Exception as e:
         db.rollback()
         print(str(e))
      cursor.close()
      db.close()

   def set (self, sideDeck):
      self.sideDeck = sideDeck

   def add (self, card):
      if len(self.selection) < 10:
         self.selection.append(card)

   def remove (self, card):
      self.selection.remove(card)

   def finish (self):
      self.finishedSelection = True

   def last (self):
      return self.fieldCards[len(self.fieldCards)-1]

   def stand (self):
      self.stood = True

   def play (self, value=0, card=None):
      if card is None:
         self.fieldCards.append(value)
         self.fieldCardIDs.append(str(value))
      else:
         self.sideDeck.remove(card)
         
         if card == "F2/4":
            values = [2,4,-2,-4]
            for i, fieldCard in enumerate(self.fieldCards):
               if fieldCard in values:
                  self.fieldCards[i] *= -1

         elif card == "F3/6":
            values = [3,6,-3,-6]
            for i, fieldCard in enumerate(self.fieldCards):
               if fieldCard in values:
                  self.fieldCards[i] *= -1

         elif card == "D":
            self.double = True
            self.fieldCards.append(value)
            self.fieldCardIDs.append(f"dc{value}")

         elif card == "T":
            self.tiebreaker = True
            self.fieldCards.append(value)
            if value > 0:
               self.fieldCardIDs.append("p_tc")
            else:
               self.fieldCardIDs.append("m_tc")

         else:
            self.fieldCards.append(value)
            if value > 0:
               if '+/-' in card:
                  self.fieldCardIDs.append(f"p_pm{value}")
               else:
                  self.fieldCardIDs.append(f"p{value}")
            else:
               if '+/-' in card:
                  self.fieldCardIDs.append(f"m_pm{abs(value)}")
               else:
                  self.fieldCardIDs.append(f"m{abs(value)}")

   def total (self):
      total = 0
      for value in self.fieldCards:
         total += value
      return total

   def won (self):
      self.points += 1
      
   def clear (self):
      self.fieldCards = []
      self.fieldCardIDs = []
      self.double = False
      self.tiebreaker = False
      self.stood = False