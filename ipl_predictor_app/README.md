# BoundaryIQ — IPL Chase Predictor

A Django website using the supplied scikit-learn pipeline (`ipl_model.pkl`). The interface lets a user select batting and bowling teams, venue, target, current score, balls bowled, and wickets lost.

## Run on Windows (PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py runserver
```

Open http://127.0.0.1:8000/.

## Model inputs

The model's stored `feature_names_in_` contains these nine fields, in this order:

1. `batting_team`
2. `bowling_team`
3. `city`
4. `runs_left`
5. `ball_left`
6. `wickets`
7. `total_runs_x`
8. `crr`
9. `rrr`

The app derives runs left, balls left, wickets remaining, current run rate (CRR), and required run rate (RRR) from the form inputs.

## Important model limitations

- The model uses `OneHotEncoder(handle_unknown="error")`; team and city choices are restricted to categories found in the uploaded model. Newer IPL franchise names are not automatically mapped to historical names.
- The model's classes are `0` and `1`. This app assumes class `1` means the chasing/batting team wins. Verify that mapping against the original training labels before relying on the displayed probabilities. Change `BATTING_WIN_CLASS` in `ipl_site/settings.py` if the training labels use the opposite convention.
- This is a model estimate, not a guarantee. It predicts a chase situation, not the winner before the toss.
- Pickle files can execute code when loaded. Only run this app with a model file you trust.
