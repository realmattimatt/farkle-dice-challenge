from flask import Flask, render_template, request, redirect, url_for, session
import random
from collections import Counter
from Farkle_v3_animate import Analyzer

app = Flask(__name__)
app.secret_key = "your_secret_key"

# 🎯 Dice drawing dictionary
dice_drawing = {
    1: ("┌─────────┐", "│         │", "│    ○    │", "│         │", "└─────────┘"),
    2: ("┌─────────┐", "│  ○      │", "│         │", "│      ○  │", "└─────────┘"),
    3: ("┌─────────┐", "│  ○      │", "│    ○    │", "│      ○  │", "└─────────┘"),
    4: ("┌─────────┐", "│  ○   ○  │", "│         │", "│  ○   ○  │", "└─────────┘"),
    5: ("┌─────────┐", "│  ○   ○  │", "│    ○    │", "│  ○   ○  │", "└─────────┘"),
    6: ("┌─────────┐", "│  ○   ○  │", "│  ○   ○  │", "│  ○   ○  │", "└─────────┘"),
}

# ✅ Scoring logic
class Scorer:
    @staticmethod
    def calculate_score(dice):
        counts = Counter(dice)
        score = 0
        for num, count in counts.items():
            if count >= 3:
                score += 1000 if num == 1 else num * 100
                count -= 3
            if num == 1:
                score += count * 100
            elif num == 5:
                score += count * 50
        return score

# 🎲 Main dice roll route
@app.route("/roll_dice", methods=["POST"])
def roll_dice():
    players = session.get("players")
    scores = session.get("scores")
    current = session.get("current_player", 0)

    # Roll dice
    dice_roll = [random.randint(1, 6) for _ in range(6)]
    scoring_dice = Analyzer.get_scoring_dice(dice_roll)
    roll_score = Scorer.calculate_score(scoring_dice)

    # 🎨 Draw ASCII dice
    dice_faces = [dice_drawing[val] for val in dice_roll]
    merged_faces = ["  ".join(row) for row in zip(*dice_faces)]

    # Update player score
    scores[current] += roll_score
    session["scores"] = scores

    return render_template(
        "game.html",
        current_player=players[current],
        current_score=scores[current],
        dice=dice_roll,
        scoring_dice=scoring_dice,
        score=roll_score,
        dice_faces=merged_faces
    )


@app.route("/keep_dice", methods=["POST"])
def keep_dice():
    # 🔁 Placeholder: Eventually we'll process which dice the user chose to keep
    return redirect(url_for("roll_dice"))



# 🏠 Other Routes (unchanged)
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
