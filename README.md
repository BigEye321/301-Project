# Blackjack AI Coach MVP

This folder contains the completed MVP deliverable for Project 301.

## Files

| File | Purpose |
| --- | --- |
| `app.py` | Streamlit demo entrypoint |
| `blackjack_engine.py` | Rules engine for blackjack recommendations |
| `build_blackjack_dataset.py` | Creates synthetic training data |
| `model.py` | nanoGPT-style model |
| `train.py` | Training script |
| `sample.py` | Inference script |
| `requirements.txt` | Python dependencies |
| `report.md` | Project report |

## Setup

```bash
pip install -r requirements.txt
```

## Run Demo

```bash
streamlit run app.py
```

## Train Model

```bash
python build_blackjack_dataset.py
python train.py
```

## Run Inference

```bash
python sample.py
```

## Checklist

- [x] Working `mvp/` directory exists
- [x] Training code included
- [x] Inference code included
- [x] Demo entrypoint included
- [x] `README.md` completed
- [x] `report.md` completed

