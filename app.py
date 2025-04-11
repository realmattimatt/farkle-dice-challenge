# app.py (updated Flask logic with Hot Dice Phase 1)

from flask import Flask, render_template, request, redirect, url_for, session
import random
from collections import Counter
from Farkle_v3_animate import Analyzer, Scorer, dice_drawing

app = Flask(__name__)
app.secret_key = "your_secret_key"

@app.route("/roll_dice", methods=["POST"])
def roll_dice():
    players = session.get("players")
    scores = session.get("scores")
    current = session.get("current_player", 0)
    remaining = session.get("remaining_dice", 6)  # default: 6 dice

    # Roll the dice
    dice_roll = [random.randint(1, 6) for _ in range(remaining)]
    scoring_dice = Analyzer.get_scoring_dice(dice_roll)
    roll_score = Scorer.calculate_score(scoring_dice)
    score_details = Scorer.score_breakdown(scoring_dice)

    # Grouped ASCII dice
    dice_faces_grouped = [dice_drawing[val] for val in dice_roll]

    # Highlight logic
    def get_highlight_flags(dice_roll, scoring_dice):
        temp = scoring_dice.copy()
        flags = []
        for die in dice_roll:
            if die in temp:
                flags.append(True)
                temp.remove(die)
            else:
                flags.append(False)
        return flags

    highlight_flags = get_highlight_flags(dice_roll, scoring_dice)

    # Temporarily store data for keep_dice
    session["last_roll"] = dice_roll
    session["last_scoring"] = scoring_dice
    session["last_score"] = roll_score
    session["last_score_details"] = score_details
    session["dice_faces_grouped"] = dice_faces_grouped
    session["highlight_flags"] = highlight_flags
    turn_points = session.get("turn_points", 0)

    return render_template(
        "game.html",
        current_player=players[current],
        current_score=scores[current],
        dice=dice_roll,
        dice_faces_grouped=dice_faces_grouped,
        highlight_flags=highlight_flags,
        players=players,
        score_details=score_details,
        turn_points=turn_points
    )

@app.route("/keep_dice", methods=["POST"])
def keep_dice():
    action = request.form.get("action")
    
    if action == "bank":
        # Finalize turn, reset turn data
        session["turn_points"] = 0
        session["remaining_dice"] = 6
        session["current_player"] = (session["current_player"] + 1) % len(session["players"])
        return redirect(url_for("play_turn"))

    # Otherwise, action is to keep scoring dice and continue rolling
    scores = session.get("scores")
    current = session.get("current_player", 0)
    roll_score = session.get("last_score", 0)
    scoring_dice = session.get("last_scoring", [])
    last_roll = session.get("last_roll", [])
    remaining = session.get("remaining_dice", 6)

    # Update turn points
    turn_points = session.get("turn_points", 0) + roll_score
    session["turn_points"] = turn_points

    # Hot dice logic: all dice scored
    if sorted(scoring_dice) == sorted(last_roll):
        session["remaining_dice"] = 6
    else:
        session["remaining_dice"] = remaining - len(scoring_dice)

    return redirect(url_for("roll_dice"))


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/players", methods=["GET", "POST"])
def players():
    if request.method == "POST":
        player_names = request.form.getlist("player_name")
        return render_template("game.html", players=player_names)
    return redirect(url_for("setup"))

@app.route("/setup", methods=["GET", "POST"])
def setup():
    if request.method == "POST":
        num_players = int(request.form.get("num_players"))
        return render_template("players.html", num_players=num_players)
    return render_template("setup.html")

@app.route("/start_game", methods=["POST"])
def start_game():
    player_names = request.form.getlist("player_name")
    if not player_names or len(player_names) < 2:
        return redirect(url_for("players"))

    session["players"] = player_names
    session["scores"] = [0] * len(player_names)
    session["current_player"] = 0
    session["remaining_dice"] = 6
    return redirect(url_for("play_turn"))

@app.route("/play")
def play_turn():
    players = session.get("players")
    scores = session.get("scores")
    current = session.get("current_player", 0)

    if not players:
        return redirect(url_for("setup"))

    return render_template("turn.html", player=players[current], score=scores[current])

if __name__ == "__main__":
    app.run(debug=True)
