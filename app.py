# app.py (updated Flask logic with Hot Dice Phase 1)

from flask import Flask, render_template, request, redirect, url_for, session, flash
import random
from collections import Counter
from Farkle_v3_animate import Analyzer, Scorer, dice_drawing

WINNING_SCORE = 5000

app = Flask(__name__)
app.secret_key = "your_secret_key"

@app.route("/roll_dice", methods=["GET", "POST"])
def roll_dice():
    players = session.get("players")
    scores = session.get("scores")
    current = session.get("current_player", 0)
    remaining = session.get("remaining_dice", 6)

    # Roll the dice
    dice_roll = [random.randint(1, 6) for _ in range(remaining)]
    scoring_dice = Analyzer.get_scoring_dice(dice_roll)

    # Detect Farkle (no scoring dice)
    if not scoring_dice:
        farkle_dice_faces = [dice_drawing[val] for val in dice_roll]
        highlight_flags = [True] * len(dice_roll)

        session["turn_points"] = 0
        session["remaining_dice"] = 6
        session["current_player"] = (current + 1) % len(players)

        return render_template(
            "farkle.html",
            player=players[current],
            dice=dice_roll,
            dice_faces_grouped=farkle_dice_faces,
            highlight_flags=highlight_flags,
            players=players,
            players_scores=zip(players, scores)
        )

    # If not a Farkle, continue as usual
    roll_score = Scorer.calculate_score(scoring_dice)
    score_details = Scorer.score_breakdown(scoring_dice)
    dice_faces_grouped = [dice_drawing[val] for val in dice_roll]

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

    # Store roll data for later
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
        turn_points=turn_points,
        last_scoring=scoring_dice,
        players_scores=zip(players, scores)
    )



@app.route("/keep_dice", methods=["POST"])
def keep_dice():
    action = request.form.get("action")

    players = session.get("players")
    scores = session.get("scores")
    current = session.get("current_player", 0)
    remaining = session.get("remaining_dice", 6)
    last_roll = session.get("last_roll", [])
    last_scoring = session.get("last_scoring", [])

    # Step 1: Build chosen_dice from user input
    chosen_dice = []
    for i in range(1, 7):
        try:
            count = int(request.form.get(f"keep_{i}", 0))
        except ValueError:
            count = 0
        chosen_dice.extend([i] * count)

    # Step 1.5: Prevent continuing if no dice were kept
    if not chosen_dice:
        flash("❗ You must keep at least one die to continue.", "error")

        return render_template(
            "game.html",
            current_player=players[current],
            current_score=scores[current],
            dice=session.get("last_roll", []),
            dice_faces_grouped=session.get("dice_faces_grouped", []),
            highlight_flags=session.get("highlight_flags", []),
            players=players,
            score_details=session.get("last_score_details", []),
            turn_points=session.get("turn_points", 0),
            last_scoring=session.get("last_scoring", []),
            players_scores=zip(players, scores)
        )




    # Step 2: Validate selection – full scoring sets must be kept
    valid = True
    scoring_counter = Counter(last_scoring)
    chosen_counter = Counter(chosen_dice)

    for face, count in chosen_counter.items():
        if count > scoring_counter[face]:
            valid = False
            break

    # Additional logic: enforce keeping full sets like 3 of a kind, not partials
    # Example: If 3 of a kind (e.g. 3 threes) were required for points, 2 is not allowed
    # Detecting 3 of a kind or better
    for face in set(last_scoring):
        if last_scoring.count(face) >= 3:
            if chosen_dice.count(face) not in [0, 3, 4, 5, 6]:  # must keep full set if any
                valid = False
                break

    if not valid:
        flash("❌ Invalid selection! You must keep full scoring sets (e.g., all 3s).", "error")
        return render_template(
            "game.html",
            current_player=players[current],
            current_score=scores[current],
            dice=session.get("last_roll", []),
            dice_faces_grouped=session.get("dice_faces_grouped", []),
            highlight_flags=session.get("highlight_flags", []),
            players=players,
            score_details=session.get("last_score_details", []),
            turn_points=session.get("turn_points", 0),
            last_scoring=session.get("last_scoring", []),
            players_scores=zip(players, scores)
        )





    # Step 3: Calculate and update turn points
    roll_score = Scorer.calculate_score(chosen_dice)
    turn_points = session.get("turn_points", 0) + roll_score
    session["turn_points"] = turn_points

    # Step 4: Check for Hot Dice
    if sorted(chosen_dice) == sorted(last_scoring) and sorted(last_scoring) == sorted(last_roll):
        session["remaining_dice"] = 6
        flash("🔥 Hot Dice! You scored with all 6 — roll again!", "success")
        return redirect(url_for("hot_dice_pause"))
    else:
        session["remaining_dice"] = remaining - len(chosen_dice)


    # Step 5: Handle bank request
    if action == "bank":
        scores[current] += turn_points
        session["scores"] = scores
        session["turn_points"] = 0
        session["remaining_dice"] = 6
        session["current_player"] = (current + 1) % len(scores)
        return redirect(url_for("roll_dice"))

    # Otherwise, continue turn
    session["scores"] = scores
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
    session["turn_points"] = 0  # ✅ Start at zero
    return redirect(url_for("roll_dice"))  # ✅ Not play_turn anymore!



@app.route("/play")
def play_turn():
    players = session.get("players")
    scores = session.get("scores")
    current = session.get("current_player", 0)

    if not players:
        return redirect(url_for("setup"))

    return render_template(
        "turn.html",
        player=players[current],
        score=scores[current],
        players_scores=zip(players, scores)
    )



@app.route("/hot_dice_pause")
def hot_dice_pause():
    return render_template("hot_dice.html")


if __name__ == "__main__":
    app.run(debug=True)
