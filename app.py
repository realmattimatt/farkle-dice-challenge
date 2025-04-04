from flask import Flask, render_template, request, redirect, url_for, session
import random
from collections import Counter

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Required for session management

# Scorer class (same as you had before)
class Scorer:
    @staticmethod
    def calculate_score(dice):
        counts = Counter(dice)
        values = list(counts.values())
        score = 0

        for num, count in counts.items():
            if count >= 3:
                score += 1000 if num == 1 else num * 100
                counts[num] -= 3

        score += counts[1] * 100
        score += counts[5] * 50
        return score

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/players", methods=["GET", "POST"])
def players():
    if request.method == "POST":
        player_names = request.form.getlist("player_name")
        return render_template("game.html", players=player_names)
    return redirect(url_for("setup"))  # fallback if someone accesses it without data

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

    # Save to session
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
    
    # Show current player turn info
    return render_template("turn.html", player=players[current], score=scores[current])



# Dice graphics (same as your previous implementation)
dice_drawing = {
    1: (
        "┌─────────┐",
        "│         │",
        "│    ○    │",
        "│         │",
        "└─────────┘",
    ),
    2: (
        "┌─────────┐",
        "│  ○      │",
        "│         │",
        "│      ○  │",
        "└─────────┘",
    ),
    3: (
        "┌─────────┐",
        "│  ○      │",
        "│    ○    │",
        "│      ○  │",
        "└─────────┘",
    ),
    4: (
        "┌─────────┐",
        "│  ○   ○  │",
        "│         │",
        "│  ○   ○  │",
        "└─────────┘",
    ),
    5: (
        "┌─────────┐",
        "│  ○   ○  │",
        "│    ○    │",
        "│  ○   ○  │",
        "└─────────┘",
    ),    
    6: (
        "┌─────────┐",
        "│  ○   ○  │",
        "│  ○   ○  │",
        "│  ○   ○  │",
        "└─────────┘",
    )
}

# Update roll_dice() to include the dice graphics
@app.route("/roll", methods=["POST"])
def roll_dice():
    players = session.get("players")
    scores = session.get("scores")
    current = session.get("current_player", 0)

    # Simulate a dice roll (you could change the number of dice or add any other logic here)
    dice_roll = [random.randint(1, 6) for _ in range(6)]

    # Save the dice faces in session
    dice_faces = [dice_drawing[dice] for dice in dice_roll]

    # Calculate the score for the roll
    roll_score = Scorer.calculate_score(dice_roll)

    # Update the current player's score
    scores[current] += roll_score
    session["scores"] = scores

    # Proceed to next player
    current = (current + 1) % len(players)
    session["current_player"] = current

    # Render the current player's turn with updated score and dice faces
    return render_template("turn.html", player=players[current], score=scores[current], dice_faces=dice_faces)



if __name__ == "__main__":
    app.run(debug=True)

