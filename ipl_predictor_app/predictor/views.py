from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd
from django.conf import settings
from django.shortcuts import render

BASE_DIR = Path(settings.BASE_DIR)
MODEL_PATH = BASE_DIR / "ipl_model.pkl"

# These choices are the teams represented in BOTH categorical columns of
# the uploaded model. Modern names/new franchises are not silently substituted.
TEAMS = [
    "Chennai Super Kings",
    "Deccan Chargers",
    "Kings XI Punjab",
    "Kolkata Knight Riders",
    "Mumbai Indians",
    "Rajasthan Royals",
    "Royal Challengers Bangalore",
    "Sunrisers Hyderabad",
    "Delhi Capitals",
]
CITIES = [
    "Abu Dhabi", "Ahmedabad", "Bangalore", "Bengaluru", "Cape Town",
    "Centurion", "Chandigarh", "Chennai", "Cuttack", "Delhi",
    "Dharamsala", "Durban", "East London", "Hyderabad", "Indore",
    "Jaipur", "Johannesburg", "Kanpur", "Kimberley", "Kochi",
    "Kolkata", "Mohali", "Mumbai", "Nagpur", "Port Elizabeth",
    "Pune", "Raipur", "Rajkot", "Ranchi", "Sharjah", "Visakhapatnam",
]

@lru_cache(maxsize=1)
def get_model():
    # Only load pickle files you trust. The supplied model is loaded locally.
    return joblib.load(MODEL_PATH)


def home(request):
    context = {"teams": TEAMS, "cities": CITIES}
    if request.method == "POST":
        try:
            batting_team = request.POST.get("batting_team", "")
            bowling_team = request.POST.get("bowling_team", "")
            city = request.POST.get("city", "")
            target = int(request.POST.get("target", "0"))
            score = int(request.POST.get("score", "0"))
            balls_bowled = int(request.POST.get("balls_bowled", "0"))
            wickets_lost = int(request.POST.get("wickets_lost", "0"))

            if batting_team not in TEAMS or bowling_team not in TEAMS:
                raise ValueError("Choose both teams from the available list.")
            if batting_team == bowling_team:
                raise ValueError("Batting and bowling teams must be different.")
            if city not in CITIES:
                raise ValueError("Choose a venue from the available list.")
            if not (1 <= target <= 400):
                raise ValueError("Target must be between 1 and 400 runs.")
            if not (0 <= score < target):
                raise ValueError("Current score must be at least 0 and below the target.")
            if not (0 <= balls_bowled < 120):
                raise ValueError("Balls bowled must be between 0 and 119 for a regular 20-over chase.")
            if not (0 <= wickets_lost <= 9):
                raise ValueError("Wickets lost must be between 0 and 9. A completed innings cannot be predicted.")

            runs_left = target - score
            balls_left = 120 - balls_bowled
            wickets_remaining = 10 - wickets_lost
            overs_completed = balls_bowled / 6
            crr = (score / overs_completed) if overs_completed else 0.0
            rrr = (runs_left * 6 / balls_left) if balls_left else 0.0

            # Exact feature order recovered from model.feature_names_in_.
            features = pd.DataFrame([{
                "batting_team": batting_team,
                "bowling_team": bowling_team,
                "city": city,
                "runs_left": runs_left,
                "ball_left": balls_left,
                "wickets": wickets_remaining,
                "total_runs_x": target,
                "crr": crr,
                "rrr": rrr,
            }], columns=[
                "batting_team", "bowling_team", "city", "runs_left",
                "ball_left", "wickets", "total_runs_x", "crr", "rrr",
            ])

            model = get_model()
            prediction = int(model.predict(features)[0])
            probabilities = model.predict_proba(features)[0]
            classes = list(model.classes_)
            batting_win_class = settings.BATTING_WIN_CLASS
            if batting_win_class not in classes:
                raise ValueError("The configured batting-win class is not present in this model.")
            batting_probability = float(probabilities[classes.index(batting_win_class)])
            bowling_probability = 1.0 - batting_probability

            context["result"] = {
                "batting_team": batting_team,
                "bowling_team": bowling_team,
                "batting_probability": round(batting_probability * 100, 1),
                "bowling_probability": round(bowling_probability * 100, 1),
                "prediction": prediction,
                "score": score,
                "target": target,
                "runs_left": runs_left,
                "balls_left": balls_left,
                "wickets_left": wickets_remaining,
                "crr": round(crr, 2),
                "rrr": round(rrr, 2),
            }
            context["form_values"] = request.POST
        except (ValueError, TypeError) as exc:
            context["error"] = str(exc)
            context["form_values"] = request.POST
        except Exception:
            context["error"] = "The model could not make a prediction. Check that the model file and scikit-learn version are correct."
            context["form_values"] = request.POST
    return render(request, "predictor/home.html", context)
