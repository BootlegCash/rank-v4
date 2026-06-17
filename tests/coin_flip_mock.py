# -*- coding: utf-8 -*-
"""
Rank V4 - Coin Flip Gambling Mock (v3)
Single-player with simulated friends.
Run: python coin_flip_mock.py
"""

import random
import time
import os
import sys
from datetime import datetime, timedelta

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


# ===============================================
# DJANGO-STYLE MODELS (how this maps to real app)
# ===============================================
#
# class TokenWallet(models.Model):
#     profile          = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='wallet')
#     balance          = models.IntegerField(default=0)
#     lifetime_earned  = models.IntegerField(default=0)
#     lifetime_spent   = models.IntegerField(default=0)
#
# class CoinFlipResult(models.Model):
#     player           = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='flips')
#     bet              = models.IntegerField()
#     won              = models.BooleanField()
#     payout           = models.IntegerField()
#     multiplier       = models.IntegerField(default=1)
#     created_at       = models.DateTimeField(auto_now_add=True)
#
# class ShotDebt(models.Model):
#     STATUS = [('pending','Pending'),('confirmed','Confirmed'),('disputed','Disputed')]
#     debtor           = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='shot_debts')
#     source           = models.CharField(max_length=50)  # 'flip', 'challenge', 'shop', 'penalty'
#     status           = models.CharField(max_length=20, default='pending')
#     created_at       = models.DateTimeField(auto_now_add=True)
#     confirmed_at     = models.DateTimeField(null=True, blank=True)
#     deadline         = models.DateTimeField()  # 5 min from created_at
#
# class WitnessVote(models.Model):
#     shot_debt        = models.ForeignKey(ShotDebt, on_delete=models.CASCADE, related_name='votes')
#     witness          = models.ForeignKey(Profile, on_delete=models.CASCADE)
#     called_bs        = models.BooleanField()
#     created_at       = models.DateTimeField(auto_now_add=True)
#
# class Challenge(models.Model):
#     STATUS = [('pending','Pending'),('accepted','Accepted'),('declined','Declined'),('complete','Complete')]
#     challenger       = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='challenges_sent')
#     opponent         = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='challenges_received')
#     stake            = models.IntegerField()
#     status           = models.CharField(max_length=20, default='pending')
#     winner           = models.ForeignKey(Profile, null=True, on_delete=models.SET_NULL, related_name='+')
#     created_at       = models.DateTimeField(auto_now_add=True)
#
# class ShopPurchase(models.Model):
#     buyer            = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='purchases')
#     item_key         = models.CharField(max_length=50)
#     target           = models.ForeignKey(Profile, null=True, on_delete=models.SET_NULL)
#     cost             = models.IntegerField()
#     created_at       = models.DateTimeField(auto_now_add=True)


# ===============================================
# TOKEN EARNING
# ===============================================

TOKEN_THRESHOLDS = [
    (3,  1),
    (6,  2),
    (10, 4),
    (15, 7),
]

def tokens_earned_from_drinks(drink_count):
    earned = 0
    for threshold, tokens in TOKEN_THRESHOLDS:
        if drink_count >= threshold:
            earned = tokens
    return earned


# ===============================================
# SHOP ITEMS
# ===============================================

SHOP_ITEMS = {
    "1": {"name": "Force Shot",        "cost": 3, "desc": "Force a friend to take a shot",              "target": True},
    "2": {"name": "Streak Breaker",    "cost": 5, "desc": "Reset a friend's win streak to 0",           "target": True},
    "3": {"name": "Double Punishment", "cost": 4, "desc": "Friend's next loss = 2 shots instead of 1",  "target": True},
    "4": {"name": "Shield",           "cost": 6, "desc": "Block your next shot penalty",                "target": False},
    "5": {"name": "Token Heist",      "cost": 8, "desc": "Steal 2 tokens from a friend",                "target": True},
}


# ===============================================
# SIMULATED FRIENDS
# ===============================================

class SimFriend:
    """Simulated friend for single-player mock."""
    def __init__(self, name):
        self.name = name
        self.tokens = random.randint(3, 12)
        self.streak = random.randint(0, 4)
        self.shots_owed = 0
        self.double_punishment = False
        self.bs_tendency = random.uniform(0.05, 0.30)

    def will_call_bs(self):
        return random.random() < self.bs_tendency

    def will_accept_challenge(self, stake):
        if stake > self.tokens:
            return False
        return random.random() < 0.7


DEFAULT_FRIENDS = [
    SimFriend("Jake"),
    SimFriend("Trey"),
    SimFriend("Maddie"),
    SimFriend("Soph"),
]


# ===============================================
# SHOT DEBT + WITNESS SYSTEM
# ===============================================

class ShotDebt:
    def __init__(self, source="flip"):
        self.source = source
        self.status = "pending"
        self.created_at = datetime.now()
        self.deadline = self.created_at + timedelta(minutes=5)
        self.confirmed_at = None
        self.votes = []  # list of (friend_name, called_bs)

    def confirm(self):
        self.status = "confirmed"
        self.confirmed_at = datetime.now()

    def is_expired(self):
        return datetime.now() > self.deadline and self.status == "pending"


class WitnessSystem:
    """
    After you confirm a shot, friends vote.
    If 2+ friends call BS -> shot gets marked 'disputed',
    you get a penalty shot added, and your confirmed shot
    doesn't count (stays pending).
    """
    def __init__(self, friends):
        self.friends = friends

    def run_vote(self, debt):
        print("\n  --- WITNESS VOTE ---")
        print("  Your friends are checking if you actually took that shot...\n")
        time.sleep(0.5)

        bs_count = 0
        confirm_count = 0

        for friend in self.friends:
            time.sleep(0.3)
            called_bs = friend.will_call_bs()
            debt.votes.append((friend.name, called_bs))

            if called_bs:
                bs_count += 1
                print(f"  {friend.name}: CALLED BS")
            else:
                confirm_count += 1
                print(f"  {friend.name}: Confirmed")

        print()
        verdict_disputed = bs_count >= 2
        return {
            "bs_count": bs_count,
            "confirm_count": confirm_count,
            "disputed": verdict_disputed,
        }


# ===============================================
# PLAYER
# ===============================================

class Player:
    def __init__(self, name):
        self.name = name
        self.tokens = 0
        self.lifetime_earned = 0
        self.lifetime_spent = 0
        self.total_flips = 0
        self.wins = 0
        self.losses = 0
        self.streak = 0
        self.best_streak = 0
        self.shot_debts = []
        self.has_shield = False
        self.double_punishment = False
        self.challenges_won = 0
        self.challenges_lost = 0
        self.shop_purchases = 0

    @property
    def pending_shots(self):
        return [s for s in self.shot_debts if s.status == "pending"]

    @property
    def confirmed_shots(self):
        return [s for s in self.shot_debts if s.status == "confirmed"]

    @property
    def disputed_shots(self):
        return [s for s in self.shot_debts if s.status == "disputed"]

    @property
    def is_locked(self):
        return len(self.pending_shots) > 0

    def earn_tokens(self, count):
        self.tokens += count
        self.lifetime_earned += count

    def spend_tokens(self, count):
        self.tokens -= count
        self.lifetime_spent += count

    def add_shot_debt(self, source="flip"):
        debt = ShotDebt(source)
        self.shot_debts.append(debt)
        return debt

    def streak_multiplier(self):
        if self.streak >= 5:
            return 4
        elif self.streak >= 3:
            return 3
        return 1

    def flip(self, bet=1):
        if self.tokens < bet:
            return None

        self.spend_tokens(bet)
        self.total_flips += 1

        result = random.choice(["heads", "tails"])
        call = random.choice(["heads", "tails"])
        won = result == call
        shielded = False

        if won:
            multiplier = self.streak_multiplier()
            payout = bet * 2 * multiplier
            self.earn_tokens(payout)
            self.wins += 1
            self.streak += 1
            self.best_streak = max(self.streak, self.best_streak)
        else:
            multiplier = 1
            payout = 0
            self.losses += 1
            self.streak = 0

            if self.has_shield:
                self.has_shield = False
                shielded = True
            else:
                shot_count = 2 if self.double_punishment else 1
                for _ in range(shot_count):
                    self.add_shot_debt("flip")
                self.double_punishment = False

        return {
            "call": call,
            "result": result,
            "won": won,
            "bet": bet,
            "multiplier": multiplier,
            "payout": payout,
            "balance": self.tokens,
            "streak": self.streak,
            "shielded": shielded,
        }

    def stats_display(self):
        win_rate = (self.wins / self.total_flips * 100) if self.total_flips else 0
        mult = self.streak_multiplier()
        lines = [
            f"\n{'=' * 50}",
            f"  {self.name}'s Stats",
            f"{'=' * 50}",
            f"  Tokens:         {self.tokens} ({self.lifetime_earned} earned / {self.lifetime_spent} spent)",
            f"  Flips:          {self.total_flips}",
            f"  Record:         {self.wins}W - {self.losses}L ({win_rate:.0f}%)",
            f"  Streak:         {self.streak} (best: {self.best_streak})",
            f"  Multiplier:     {mult}x" + (f" -> {mult+1 if self.streak==2 else mult+1}x next!" if self.streak in [2,4] else ""),
            f"  Challenges:     {self.challenges_won}W - {self.challenges_lost}L",
            f"  Shop purchases: {self.shop_purchases}",
        ]
        if self.has_shield:
            lines.append(f"  Shield:         ACTIVE")
        if self.double_punishment:
            lines.append(f"  WARNING:        Next loss = 2 shots!")

        total_confirmed = len(self.confirmed_shots)
        total_disputed = len(self.disputed_shots)
        total_pending = len(self.pending_shots)
        lines.append(f"  Shots taken:    {total_confirmed}")
        if total_pending:
            lines.append(f"  Shots pending:  {total_pending} !!!")
        if total_disputed:
            lines.append(f"  Shots disputed: {total_disputed} (shame)")
        lines.append(f"{'=' * 50}")
        return "\n".join(lines) + "\n"


# ===============================================
# CLI HELPERS
# ===============================================

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def coin_animation():
    frames = ["  [ / ]", "  [ - ]", "  [ \\ ]", "  [ | ]"]
    for _ in range(3):
        for frame in frames:
            print(f"\r{frame}", end="", flush=True)
            time.sleep(0.08)
    print("\r       \r", end="")

def header_bar(player):
    extras = ""
    if player.has_shield:
        extras += " [SHIELD]"
    if player.streak >= 3:
        extras += f" [{player.streak_multiplier()}x]"
    if player.double_punishment:
        extras += " [2x SHOT NEXT LOSS]"
    print(f"\n  +------------------------------------------------+")
    print(f"  |  Tokens: {player.tokens:<5} Streak: {player.streak:<3} Shots due: {len(player.pending_shots):<3}{extras}")
    print(f"  +------------------------------------------------+")

def pick_friend(friends, prompt="  Pick a friend"):
    print()
    for i, f in enumerate(friends, 1):
        extras = ""
        if f.double_punishment:
            extras = " [2x SHOT PENDING]"
        print(f"  [{i}] {f.name} ({f.tokens} tokens, streak: {f.streak}){extras}")
    print(f"  [0] Cancel")
    choice = input(f"\n{prompt}: ").strip()
    if choice == "0" or not choice.isdigit():
        return None
    idx = int(choice) - 1
    if 0 <= idx < len(friends):
        return friends[idx]
    return None


# ===============================================
# SHOT ENFORCEMENT + WITNESS FLOW
# ===============================================

def shot_enforcement(player, witness_system):
    pending = player.pending_shots
    if not pending:
        return

    sources = {}
    for s in pending:
        sources[s.source] = sources.get(s.source, 0) + 1
    source_str = ", ".join(f"{v} from {k}" for k, v in sources.items())

    print(f"\n  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print(f"  !!!  YOU OWE {len(pending)} SHOT(S)  !!!")
    print(f"  !!!  ({source_str})")
    print(f"  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print(f"\n  You CANNOT flip, shop, or challenge until you drink.")
    print(f"\n  In the real app:")
    print(f"    - Push notification sent to you")
    print(f"    - 5 min countdown starts")
    print(f"    - If timer expires: +1 penalty shot added")
    print(f"    - Friends get notified to watch for your confirmation")
    print(f"    - After you confirm, friends vote: legit or BS?")
    print()

    while player.pending_shots:
        count = len(player.pending_shots)
        print(f"  You owe {count} shot(s).")
        resp = input(f"  Take them and type 'done' (or 'info' for details): ").strip().lower()

        if resp == "info":
            print("\n  Shot breakdown:")
            for i, debt in enumerate(player.pending_shots, 1):
                time_ago = (datetime.now() - debt.created_at).seconds
                print(f"    {i}. Source: {debt.source} | {time_ago}s ago")
            print()

        elif resp == "done":
            debts_to_confirm = list(player.pending_shots)
            for debt in debts_to_confirm:
                debt.confirm()

            print(f"\n  {count} shot(s) confirmed. Sending to witnesses...\n")
            time.sleep(0.3)

            for debt in debts_to_confirm:
                verdict = witness_system.run_vote(debt)

                if verdict["disputed"]:
                    debt.status = "disputed"
                    print(f"  DISPUTED! {verdict['bs_count']} friends called BS.")
                    print(f"  Penalty: +1 extra shot added. Don't fake it.\n")
                    player.add_shot_debt("penalty_bs")
                else:
                    print(f"  Confirmed by friends. ({verdict['confirm_count']}/{len(witness_system.friends)} vouched)\n")

            remaining = len(player.pending_shots)
            if remaining:
                print(f"  You still owe {remaining} shot(s) from BS penalties.\n")
            else:
                print(f"  All clear. Game unlocked.\n")
        else:
            print(f"  Take the shot. No shortcuts.\n")


# ===============================================
# CHALLENGE FLOW
# ===============================================

def challenge_flow(player, friends):
    print("\n  -- CHALLENGE A FRIEND --")
    print("  Both put up tokens. One coin flip.")
    print("  Winner takes the pot. Loser takes a shot.")

    friend = pick_friend(friends, "  Who do you want to challenge")
    if not friend:
        return

    max_stake = min(player.tokens, friend.tokens)
    if max_stake < 1:
        print(f"\n  Can't challenge -- someone's broke.\n")
        return

    print(f"\n  Max stake: {max_stake} (limited by whoever has fewer tokens)")
    stake_input = input(f"  How many tokens to stake (1-{max_stake}): ").strip()
    if not stake_input.isdigit():
        return
    stake = int(stake_input)
    if stake < 1 or stake > max_stake:
        print(f"  Invalid stake.\n")
        return

    # Opponent decides
    accepted = friend.will_accept_challenge(stake)
    if not accepted:
        print(f"\n  {friend.name} declined the challenge. (In real app: push notification, they accept/decline)\n")
        return

    print(f"\n  {friend.name} ACCEPTED!")
    print(f"  {player.name} vs {friend.name} -- {stake} tokens each on the line.")
    input("  Press Enter to flip...")

    coin_animation()
    result = random.choice(["heads", "tails"])
    call = random.choice(["heads", "tails"])
    won = result == call

    print(f"  Coin landed: {result.upper()}")
    time.sleep(0.3)

    if won:
        print(f"\n  YOU WIN! +{stake} tokens from {friend.name}")
        print(f"  {friend.name} owes a shot.")
        player.earn_tokens(stake)
        friend.tokens -= stake
        friend.shots_owed += 1
        player.challenges_won += 1
    else:
        print(f"\n  YOU LOSE! {friend.name} takes {stake} of your tokens.")
        print(f"  You owe a shot.")
        player.spend_tokens(stake)
        friend.tokens += stake
        player.add_shot_debt("challenge")
        player.challenges_lost += 1
    print()


# ===============================================
# SHOP FLOW
# ===============================================

def shop_flow(player, friends):
    print(f"\n  -- TOKEN SHOP -- (balance: {player.tokens} tokens)\n")
    for key, item in SHOP_ITEMS.items():
        tag = " [friend]" if item["target"] else " [self]"
        affordable = "" if player.tokens >= item["cost"] else " (can't afford)"
        print(f"  [{key}] {item['name']} - {item['cost']} tokens{tag}{affordable}")
        print(f"      {item['desc']}")
    print(f"\n  [0] Leave shop")

    choice = input("\n  Buy what: ").strip()
    if choice == "0" or choice not in SHOP_ITEMS:
        return

    item = SHOP_ITEMS[choice]
    if player.tokens < item["cost"]:
        print(f"\n  Need {item['cost']} tokens, you have {player.tokens}.\n")
        return

    target = None
    if item["target"]:
        target = pick_friend(friends, "  Use on who")
        if not target:
            return

    player.spend_tokens(item["cost"])
    player.shop_purchases += 1

    if choice == "1":
        target.shots_owed += 1
        print(f"\n  FORCE SHOT sent to {target.name}!")
        print(f"  In real app: {target.name} gets a push notification")
        print(f"  and can't play until they confirm the shot.\n")

    elif choice == "2":
        old = target.streak
        target.streak = 0
        print(f"\n  STREAK BREAKER! {target.name}'s streak: {old} -> 0")
        print(f"  Their multiplier is back to 1x.\n")

    elif choice == "3":
        target.double_punishment = True
        print(f"\n  DOUBLE PUNISHMENT set on {target.name}!")
        print(f"  Their next coin flip loss = 2 shots.\n")

    elif choice == "4":
        player.has_shield = True
        print(f"\n  SHIELD activated!")
        print(f"  Your next loss won't cost you a shot.\n")

    elif choice == "5":
        stolen = min(2, target.tokens)
        target.tokens -= stolen
        player.earn_tokens(stolen)
        if stolen == 0:
            print(f"\n  {target.name} is broke -- nothing to steal.\n")
        else:
            print(f"\n  TOKEN HEIST! Stole {stolen} tokens from {target.name}!")
            print(f"  In real app: {target.name} gets a notification showing who robbed them.\n")


# ===============================================
# ALL-IN FLOW
# ===============================================

def all_in_flow(player):
    if player.tokens < 1:
        print("\n  You're broke. Can't go all in on nothing.\n")
        return

    print(f"\n  -- ALL IN --")
    print(f"  Your entire stack: {player.tokens} tokens.")
    print(f"  Win: double it. Lose: lose everything + take a shot.\n")

    if player.streak >= 3:
        print(f"  Current multiplier: {player.streak_multiplier()}x (streak of {player.streak})")
        print(f"  If you win: {player.tokens * 2 * player.streak_multiplier()} tokens!\n")

    confirm = input(f"  Type 'send it' to go all in: ").strip().lower()
    if confirm != "send it":
        print("  Lived to flip another day.\n")
        return

    bet = player.tokens
    print()
    coin_animation()
    result = player.flip(bet=bet)

    if result["won"]:
        mult_str = f" ({result['multiplier']}x streak!)" if result['multiplier'] > 1 else ""
        print(f"  {result['call'].upper()} / {result['result'].upper()}")
        print(f"  ALL-IN WIN!!! {result['payout']} tokens!{mult_str}")
    else:
        if result["shielded"]:
            print(f"  {result['call'].upper()} / {result['result'].upper()}")
            print(f"  ALL-IN LOSS... but SHIELD saved you from the shot!")
        else:
            print(f"  {result['call'].upper()} / {result['result'].upper()}")
            print(f"  ALL-IN LOSS. Everything gone. Take your shot.")
    print(f"  Balance: {result['balance']} tokens\n")


# ===============================================
# FRIEND STATUS
# ===============================================

def show_friends(friends):
    print(f"\n  -- YOUR FRIENDS --\n")
    for f in friends:
        extras = []
        if f.double_punishment:
            extras.append("2x SHOT NEXT LOSS")
        if f.shots_owed:
            extras.append(f"{f.shots_owed} shots owed")
        extra_str = f" ({', '.join(extras)})" if extras else ""
        print(f"  {f.name:<10} {f.tokens} tokens | streak: {f.streak}{extra_str}")
    print()


# ===============================================
# MAIN
# ===============================================

def main():
    clear()
    print("+================================================+")
    print("|         RANK V4 -- COIN FLIP GAME v3           |")
    print("|    Flip it or drink it. No mercy.               |")
    print("+================================================+")
    print()

    name = input("  Your name: ").strip() or "Player"
    player = Player(name)
    friends = list(DEFAULT_FRIENDS)
    witness_system = WitnessSystem(friends)

    # Drink logging
    print(f"\n  Token earning: 3 drinks=1, 6=2, 10=4, 15=7 tokens\n")
    while True:
        try:
            drinks = int(input("  How many drinks have you had? "))
            break
        except ValueError:
            print("  Number.")

    earned = tokens_earned_from_drinks(drinks)
    if earned == 0:
        print(f"\n  {drinks} drinks -- need at least 3 for tokens.")
        print("  Here's 5 free tokens to test the game.\n")
        player.earn_tokens(5)
    else:
        player.earn_tokens(earned)
        print(f"\n  {drinks} drinks -> {earned} tokens. Let's go.\n")

    # Main loop
    while True:
        header_bar(player)

        if player.is_locked:
            shot_enforcement(player, witness_system)
            continue

        print()
        print("  [1] Flip        (1 token)")
        print("  [2] Double flip (2 tokens)")
        print("  [3] ALL IN")
        print("  [4] Challenge a friend")
        print("  [5] Token shop")
        print("  [6] Stats")
        print("  [7] Friends")
        print("  [8] Log more drinks (earn tokens)")
        print("  [9] Quit")
        print()

        choice = input("  > ").strip()

        if choice == "1":
            if player.tokens < 1:
                print("\n  Broke. Log more drinks or get lucky in a challenge.\n")
                continue
            print()
            coin_animation()
            r = player.flip(bet=1)
            if r["won"]:
                mult_str = f" ({r['multiplier']}x streak)" if r['multiplier'] > 1 else ""
                print(f"  {r['call'].upper()} / {r['result'].upper()} -- WIN! +{r['payout']-1} net{mult_str}")
                if player.streak == 3:
                    print(f"  3 wins! Multiplier unlocked: 3x payout on next win!")
                elif player.streak == 5:
                    print(f"  5 wins! Multiplier maxed: 4x payout!")
                elif player.streak >= 3:
                    print(f"  Streak: {player.streak} ({player.streak_multiplier()}x)")
            else:
                if r["shielded"]:
                    print(f"  {r['call'].upper()} / {r['result'].upper()} -- LOSS... but SHIELD blocked the shot!")
                else:
                    count = 2 if any(s.source == "flip" for s in player.pending_shots) and len(player.pending_shots) > 1 else len(player.pending_shots)
                    print(f"  {r['call'].upper()} / {r['result'].upper()} -- LOSS. You owe a shot.")
            print(f"  Balance: {r['balance']} tokens\n")

        elif choice == "2":
            if player.tokens < 2:
                print(f"\n  Need 2 tokens (have {player.tokens}).\n")
                continue
            print()
            coin_animation()
            r = player.flip(bet=2)
            if r["won"]:
                mult_str = f" ({r['multiplier']}x)" if r['multiplier'] > 1 else ""
                print(f"  {r['call'].upper()} / {r['result'].upper()} -- BIG WIN! +{r['payout']-2} net{mult_str}")
            else:
                if r["shielded"]:
                    print(f"  {r['call'].upper()} / {r['result'].upper()} -- LOSS... SHIELD saved you!")
                else:
                    print(f"  {r['call'].upper()} / {r['result'].upper()} -- LOSS. Shot time.")
            print(f"  Balance: {r['balance']} tokens\n")

        elif choice == "3":
            all_in_flow(player)

        elif choice == "4":
            if player.tokens < 1:
                print("\n  Need at least 1 token to challenge.\n")
                continue
            challenge_flow(player, friends)

        elif choice == "5":
            shop_flow(player, friends)

        elif choice == "6":
            print(player.stats_display())

        elif choice == "7":
            show_friends(friends)

        elif choice == "8":
            try:
                more = int(input("\n  How many more drinks since last log? "))
            except ValueError:
                more = 0
            if more < 1:
                print("  Nothing logged.\n")
                continue
            drinks += more
            new_earned = tokens_earned_from_drinks(drinks)
            bonus = new_earned - tokens_earned_from_drinks(drinks - more)
            if bonus > 0:
                player.earn_tokens(bonus)
                print(f"  +{bonus} tokens! (total drinks tonight: {drinks})\n")
            else:
                print(f"  Logged, but no new token threshold hit yet. (total: {drinks})\n")

        elif choice == "9":
            print(player.stats_display())
            pending = len(player.pending_shots)
            if pending:
                print(f"  You still owe {pending} shot(s). Don't dodge.\n")
            confirmed = len(player.confirmed_shots)
            disputed = len(player.disputed_shots)
            if confirmed:
                print(f"  Shots taken tonight: {confirmed}")
            if disputed:
                print(f"  Shots disputed (shame): {disputed}")
            print(f"\n  Later, {player.name}.\n")
            break

        else:
            print("  Pick 1-9.\n")


if __name__ == "__main__":
    main()
