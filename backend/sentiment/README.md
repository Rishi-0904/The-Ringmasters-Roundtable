# Sentiment Analysis Integration

This directory contains the sentiment analysis functionality for The Ringmasters Roundtable community platform.

## Overview

The sentiment analysis system automatically analyzes community posts and comments to classify them as positive, negative, or neutral. This helps users filter content and provides insights into community sentiment.

The system uses a Deep Learning Recurrent Neural Network (RNN) model built with PyTorch, achieving a validation accuracy of **~89-90%** on the IMDb movie reviews dataset (50k samples).

## Components

### Python Scripts
- **`main.py`**: Core sentiment analysis script that loads the PyTorch RNN model and tokenizer to process text.
- **`api.py`**: Flask API wrapper for the sentiment analysis that hosts the model for fast, sub-10ms predictions over HTTP.
- **`train_rnn.py`**: Script to download the dataset, train, and save the PyTorch RNN model and custom tokenizer.

### Models
- **`ReviewSA_model.pth`**: Trained PyTorch Bidirectional LSTM model weights.
- **`tokenizer.pkl`**: Custom word-to-index mapping tokenizer for text encoding.

### Templates
- **`index.html`**: Basic web interface for testing.
- **`landing.html`**: Enhanced web interface with styling.

## Installation

1. Install Python dependencies:
```bash
cd backend/sentiment
pip install -r requirements.txt
```
*(Ensure PyTorch is installed in your python environment)*

2. Train the model (if not already trained):
```bash
python train_rnn.py
```

## Usage

### Command Line Interface

Analyze a single text:
```bash
python main.py --text "I love this place! Amazing experience."
```

Analyze multiple texts:
```bash
python main.py --batch '["Great service!", "Terrible food", "It was okay"]'
```

### Node.js Integration

The sentiment analysis is automatically integrated into the Node.js backend using a **hybrid approach**:
1. **Flask API (Fast Path)**: The Node.js backend first attempts to query the running Flask API (`http://localhost:5000/predict`). This keeps the PyTorch model in memory and responds in milliseconds.
2. **Local Script Fallback (Slow Path)**: If the Flask API is not running, Node.js falls back to spawning `main.py` directly.

## Technical Details

### Text Preprocessing
1. Convert to lowercase.
2. Remove HTML tags.
3. Remove punctuation and special characters, keeping alphanumeric and spaces.
4. Tokenize using the custom `SimpleTokenizer`.
5. Pad sequences to `maxlen = 1500`.

### Model Architecture (PyTorch)
1. **Embedding Layer**: 128 dimensions.
2. **Dropout**: 0.5 to prevent overfitting.
3. **Conv1D Layer**: 128 filters, kernel size 5 with Batch Normalization and ReLU activation for spatial feature extraction.
4. **MaxPooling1D**: Pool size 4.
5. **Bidirectional LSTM**: 64 hidden units (concatenated forward and backward states resulting in 128 dimensions).
6. **Dense Output**: Fully connected layer outputting a single probability via Sigmoid activation.

### Classification Mapping
- Probability `> 0.6` -> Positive (prediction `1`)
- Probability `< 0.4` -> Negative (prediction `-1`)
- Probability between `0.4` and `0.6` -> Neutral (prediction `0`)

## Performance
- API latency: <10ms per text (with running Flask API).
- Model Accuracy: ~89.5% validation accuracy.
