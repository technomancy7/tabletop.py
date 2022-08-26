from enum import Enum
import random
from random import shuffle

#@todo
# Add a mode for just simulating a card table (creating/merging/destroying containers, moving cards)
# Dice roller command line
# More games

def parseDiceNotation(notation):
    try:
        if "d" in notation:
            count = 1
            if notation.split("d")[0] != "":
                count = int(notation.split("d")[0])
            sides = notation.split("d")[1]
            if "+" in sides:
                realsides = int(sides.split("+")[0])
                mod = int(sides.split("+")[1])
                return {"sides": realsides, "modifier": mod, "die": count, "valid": True}
            else:
                sides = int(sides)
                return {"sides": sides, "modifier": 0, "die": count, "valid": True}
        else:
            return {"sides": 0, "modifier": 0, "die": 0, "valid": False}
    except Exception as e:
        print(e)
        return {"sides": 0, "modifier": 0, "die": 0, "valid": False}

def roll(notation):
    d = parseDiceNotation(notation)
    out = {"rolls": [], "total": 0, **d}
    if d["valid"]:
        for die in range(0, d["die"]):
            tmp = random.randrange(1, d["sides"]+1)
            if d["modifier"] != 0:
                tmp += d["modifier"]
            out["rolls"].append(tmp)
            out["total"] += tmp
    return out

def quickRoll(notation):
    return roll()["total"]

def prettyPrintRoll(result):
    print(f"Rolling {result['die']}d{result['sides']} (+{result['modifier']})")
    print(f"Total: {result['total']}")
    print(f"Rolls: {result['rolls']}")

class Suits(Enum):
    NULL = 0
    HEARTS = 1
    DIAMONDS = 2
    CLUBS = 3
    SPADES = 4

    def as_string(self):
        return [
            "null",
            "hearts",
            "diamonds",
            "clubs",
            "spades"
        ][self.value]

class PlayingCard:
    def __init__(self, suit, value, *, container = None):
        self.suit_id = suit
        self.value = value
        self.container = container

    def move_to(self, cont):
        if issubclass(cont.__class__, CardContainer):
            if self.container != None:
                self.container.pull(self)

            cont.cards.append(self)
            self.container = cont

    @property
    def colour(self):
        if self.suit == Suits.DIAMONDS or self.suit == Suits.HEARTS:
            return "red"
        else:
            return "black"

    @property
    def value_name(self):
        if self.value == 1:
            return "ace"
        elif self.value == 11:
            return "jack"
        elif self.value == 12:
            return "queen"
        elif self.value == 13:
            return "king"
        else:
            return str(self.value)

    @property
    def suit(self):
        return Suits(self.suit_id)

    @property
    def suit_name(self):
        return Suits(self.suit_id).as_string()

    def __repr__(self):
        return f"{self.value_name} of {self.suit_name}"

class CardContainer:
    def __init__(self):
        self.cards = []

        for value in range(1, 14):
            for suit in range(1, 5):
                self.cards.append(PlayingCard(suit, value, container = self))
                
    @property
    def length(self):
        return len(self.cards)


    def merge_from(self, cont):
        if issubclass(cont.__class__, CardContainer):
            for card in cont.cards:
                card.move_to(self)
            del cont
            return self

    def pull(self, card):
        if card in self.cards:
            self.cards.remove(card)
            return card

    def shuffle(self):
        shuffle(self.cards)

    def draw(self):
        return self.cards.pop()


class AthenaTowers:
    def __init__(self):
        self.DEFAULT_HEALTH = 30
        self.NUM_TOWERS = 6
        self.PLAYER_HAND_SIZE = 7
        self.TYPE_ADVANTAGE_MODIFIER = 2

        self.state = {
            "towers": [],
            "health": 0,
            "status": "waiting"
        }

        self.action_log = []
        self.deck = CardContainer()
        self.deck.shuffle()
        self.player = CardContainer()
        self.discards = CardContainer()
        self.new_state()
    
    def action(self, **keys):
        self.action_log.append(**keys)

    def new_state(self):
        self.state["towers"] = []
        for _ in range(self.NUM_TOWERS):
            self.state["towers"].append({
                    "destroyed": False, "hidden": True, "card": self.deck.draw()
                })
        self.state["health"] = self.DEFAULT_HEALTH
        self.state["status"] = "playing"

        for i in range(self.PLAYER_HAND_SIZE):
            self.deck.draw().move_to(self.player)

    def check_type_advantage(self, card, tower):
        if card.suit == Suits.HEARTS and tower.suit == Suits.SPADES:
            return True
        elif card.suit == Suits.SPADES and tower.suit == Suits.DIAMONDS:
            return True
        elif card.suit == Suits.DIAMONDS and tower.suit == Suits.CLUBS:
            return True
        elif card.suit == Suits.CLUBS and tower.suit == Suits.HEARTS:
            return True
        else:
            return False

    def destroy_tower(self, tower_index:int, *, matched = False, from_type_advantage = False):
        tower = self.state["towers"][tower_index] 
        tower["destroyed"] = True
        self.action(event = "act", played = card, tower = tower, result = "destroyed", first = tower["hidden"], type_advantage = from_type_advantage, matched = matched)

    def reveal_tower(self, tower_index:int):
        tower = self.state["towers"][tower_index]
        tower["hidden"] = False
        self.action(event = "reveal", tower = tower)

    def act_on(self, hand_index:int, tower_index:int):
        card = self.player[hand_index]
        tower = self.state["towers"][tower_index]
        destroy_tower = False
        matched = False
        from_type_advantage = False

        if card.value_name == "king":
            if card.suit == tower.suit:
                destroy_tower = True
        else:
            if self.check_type_advantage(card, tower):
                if (card.value + self.TYPE_ADVANTAGE_MODIFIER) >= tower.value:
                    destroy_tower = True
                    from_type_advantage = True
            else:
                if card.value >= tower.value:
                    destroy_tower = True

        if destroy_tower:
            self.destroy_tower(tower_index, matched = matched, from_type_advantage = from_type_advantage)

        if tower["hidden"]:
            self.reveal_tower(tower_index)




if __name__ == "__main__":
    t = AthenaTowers()

    
    prompt = "> "
    print("Welcome to Athena's Towers.")
    print("Say Help for a command list.")

    playing = True
    while playing:
        msg = input(prompt)
        
        if msg == "help":
            print("new, quit, hand, act, observe")

        elif msg == "new":
            t.new_state()

        elif msg == "quit":
            playing = False

        elif msg == "hand":
            for i, card in enumerate(t.player.cards):
                print("#", i, " - ", card)

        elif msg == "act":
            pass

           

        elif msg == "observe":
            print("You have", t.state["health"], "health.")

            for i, tower in enumerate(t.state["towers"]):
                print("Tower #", i, "is", tower)
