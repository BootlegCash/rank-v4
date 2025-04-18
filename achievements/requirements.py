# achievements/requirements.py

def beer_beginner_requirement(profile):
    """Unlocked when the user logs at least 10 beers/seltzers."""
    return profile.beer >= 10

def whiskey_warrior_requirement(profile):
    """Unlocked when the user logs at least 25 whiskey shots."""
    return profile.whiskey >= 25

def rum_runner_requirement(profile):
    """Unlocked when the user logs at least 20 rum shots."""
    return profile.rum >= 20

def tequila_titan_requirement(profile):
    """Unlocked when the user logs at least 15 tequila shots."""
    return profile.tequila >= 15

def vodka_virtuoso_requirement(profile):
    """Unlocked when the user logs at least 20 vodka shots."""
    return profile.vodka >= 20

def floco_fanatic_requirement(profile):
    """Unlocked when the user logs at least 10 flocos."""
    return profile.floco >= 10

def shotgun_starter_requirement(profile):
    """Unlocked when the user completes their first shotgun."""
    return profile.shotguns >= 1

def snorkel_specialist_requirement(profile):
    """Unlocked when the user completes their first snorkel."""
    return profile.snorkels >= 1

def iron_stomach_requirement(profile):
    """
    Unlocked when the user logs at least 20 drinks (total of all types)
    without throwing up.
    """
    total_drinks = profile.beer + profile.floco + profile.rum + profile.whiskey + profile.vodka + profile.tequila
    return total_drinks >= 20 and profile.thrown_up == 0

def first_steps_requirement(profile):
    """Unlocked when the user reaches Silver Rank (assumed to be at least 600 XP)."""
    return profile.xp >= 600

def climbing_higher_requirement(profile):
    """Unlocked when the user reaches Gold Rank (assumed to be at least 1300 XP)."""
    return profile.xp >= 1300

def elite_drinker_requirement(profile):
    """Unlocked when the user reaches Platinum Rank (assumed to be at least 3200 XP)."""
    return profile.xp >= 3200

def legendary_drinker_requirement(profile):
    """Unlocked when the user reaches Diamond Rank (assumed to be at least 7300 XP)."""
    return profile.xp >= 7300

def steez_master_requirement(profile):
    """Unlocked when the user attains the highest rank, Steez (assumed to be at least 15000 XP)."""
    return profile.xp >= 15000



# Mapping of achievement codes to their respective requirement functions.
ACHIEVEMENT_REQUIREMENTS = {
    "BEER_BEGINNER": beer_beginner_requirement,
    "WHISKEY_WARRIOR": whiskey_warrior_requirement,
    "RUM_RUNNER": rum_runner_requirement,
    "TEQUILA_TITAN": tequila_titan_requirement,
    "VODKA_VIRTUOSO": vodka_virtuoso_requirement,
    "FLOCO_FANATIC": floco_fanatic_requirement,
    "SHOTGUN_STARTER": shotgun_starter_requirement,
    "SNORKEL_SPECIALIST": snorkel_specialist_requirement,
    "IRON_STOMACH": iron_stomach_requirement,
    "FIRST_STEPS": first_steps_requirement,
    "CLIMBING_HIGHER": climbing_higher_requirement,
    "ELITE_DRINKER": elite_drinker_requirement,
    "LEGENDARY_DRINKER": legendary_drinker_requirement,
    "STEEZ_MASTER": steez_master_requirement,
}

