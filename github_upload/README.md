# Blackjack AI Coach MVP

This project is a Blackjack AI Coach MVP for Project 301. The app recommends a statistically reasonable blackjack action and explains the decision in coaching language.

The system uses a hybrid design:

- `blackjack_engine.py` makes the actual recommendation using deterministic blackjack strategy logic.
- `model.py`, `train.py`, and `sample.py` provide a small nanoGPT-style language model workflow.
- `app.py` is the Streamlit demo entrypoint.
- `build_blackjack_dataset.py` creates synthetic blackjack training examples for the language model.

## MVP Directory

The completed MVP deliverable is in:

```text
mvp/
```

Key files:

```text
mvp/app.py
mvp/blackjack_engine.py
mvp/build_blackjack_dataset.py
mvp/model.py
mvp/train.py
mvp/sample.py
mvp/requirements.txt
mvp/README.md
mvp/report.md
```

## Setup

From the `mvp` directory:

```bash
pip install -r requirements.txt
```

## Run The Demo

From the `mvp` directory:

```bash
streamlit run app.py
```

The demo lets a user enter:

- Player card 1
- Player card 2
- Dealer upcard
- Optional additional player cards
- Rule settings for double, split, and dealer soft 17

The app outputs:

- Recommended action
- Confidence score
- Player total
- Coaching explanation
- Rules engine details
- Optional nanoGPT explanation if a trained checkpoint exists

## Train The nanoGPT-Style Model

From the `mvp` directory, first build the training dataset:

```bash
python build_blackjack_dataset.py
```

Then train the model:

```bash
python train.py
```

Training creates:

```text
out/best_model.pt
out/meta.json
out/loss_curve.png
```

## Run Inference

After training, run:

```bash
python sample.py
```

This loads `out/best_model.pt` and `out/meta.json`, then generates a blackjack explanation from a sample prompt.

## Deliverable Checklist

- [x] Working `mvp/` directory exists
- [x] Training code included
- [x] Inference code included
- [x] Demo entrypoint included
- [x] `README.md` completed
- [x] `report.md` completed

