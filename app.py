from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start_game():
    player_names = request.form.getlist("player_name")
    # Pass to game logic or render the next page
    return render_template("game.html", players=player_names)



@app.route("/players", methods=["GET", "POST"])
def players():
    if request.method == "POST":
        num_players = int(request.form.get("num_players"))
        return render_template("players.html", num_players=num_players)
    return redirect(url_for("setup"))  # fallback if someone goes to /players directly


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
        return redirect(url_for("players"))  # fallback if somehow empty

    # You can pass these names into your game template for display
    return render_template("game.html", players=player_names)


if __name__ == "__main__":
    app.run(debug=True)
