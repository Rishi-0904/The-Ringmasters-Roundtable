import sys
import os
import json
import argparse
import re
import pickle
import numpy as np
import torch
import torch.nn as nn

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Tokenizer definition for unpickling
class SimpleTokenizer:
    def __init__(self, num_words=None, oov_token='<unk>'):
        self.num_words = num_words
        self.oov_token = oov_token
        self.word_index = {}
        self.index_word = {}

    def texts_to_sequences(self, texts):
        sequences = []
        for text in texts:
            seq = []
            for word in text.split():
                seq.append(self.word_index.get(word, self.word_index[self.oov_token]))
            sequences.append(seq)
        return sequences

def pad_sequences(sequences, maxlen, padding='post'):
    padded = np.zeros((len(sequences), maxlen), dtype=np.int64)
    for i, seq in enumerate(sequences):
        if len(seq) == 0:
            continue
        if len(seq) > maxlen:
            if padding == 'post':
                padded[i, :] = seq[:maxlen]
            else:
                padded[i, :] = seq[-maxlen:]
        else:
            if padding == 'post':
                padded[i, :len(seq)] = seq
            else:
                padded[i, -len(seq):] = seq
    return padded

# PyTorch Model matching the train script
class SentimentRNN(nn.Module):
    def __init__(self, vocab_size, embedding_dim=128, hidden_dim=64):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.dropout1 = nn.Dropout(0.5)
        self.conv = nn.Conv1d(in_channels=embedding_dim, out_channels=128, kernel_size=5)
        self.bn = nn.BatchNorm1d(128)
        self.relu = nn.ReLU()
        self.pool = nn.MaxPool1d(kernel_size=4)
        self.dropout2 = nn.Dropout(0.5)
        self.lstm = nn.LSTM(input_size=128, hidden_size=hidden_dim, batch_first=True, bidirectional=True)
        self.fc = nn.Linear(hidden_dim * 2, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        x = self.embedding(x)
        x = self.dropout1(x)
        x = x.transpose(1, 2)
        x = self.conv(x)
        x = self.bn(x)
        x = self.relu(x)
        x = self.pool(x)
        x = self.dropout2(x)
        x = x.transpose(1, 2)
        lstm_out, (hn, cn) = self.lstm(x)
        out = torch.cat((hn[0], hn[1]), dim=1)
        out = self.fc(out)
        out = self.sigmoid(out)
        return out

# Load model and preprocessors
model = None
tokenizer = None
max_length = 1500

try:
    with open(os.path.join(script_dir, 'Models/tokenizer.pkl'), 'rb') as f:
        tokenizer = pickle.load(f)
        
    vocab_size = len(tokenizer.word_index) + 1
    model = SentimentRNN(vocab_size=vocab_size, embedding_dim=128, hidden_dim=64)
    model.load_state_dict(torch.load(os.path.join(script_dir, 'Models/ReviewSA_model.pth'), map_location=torch.device('cpu')))
    model.eval()
    print("RNN Model loaded successfully", file=sys.stderr)
except Exception as e:
    print(f"Warning: Could not load RNN models ({e}). Simple fallback will be used.", file=sys.stderr)
    model = None

def preprocess_text(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'[^a-zA-Z0-9 ]', '', text)
    text = text.lower()
    return text

def simple_sentiment_analysis(text):
    """
    Simple rule-based sentiment analysis as fallback
    """
    positive_words = ['love', 'amazing', 'great', 'awesome', 'fantastic', 'wonderful', 'excellent', 'good', 'best', 'beautiful', 'perfect', 'incredible', 'outstanding', 'brilliant', 'superb', 'magnificent', 'marvelous', 'terrific', 'fabulous', 'delightful']
    negative_words = ['hate', 'terrible', 'awful', 'bad', 'worst', 'horrible', 'disgusting', 'pathetic', 'useless', 'disappointing', 'annoying', 'frustrating', 'boring', 'stupid', 'ridiculous', 'waste', 'regret', 'poor', 'cheap', 'fake']
    
    text_lower = text.lower()
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    if positive_count > negative_count:
        return 1, 0.7  # positive
    elif negative_count > positive_count:
        return -1, 0.7  # negative
    else:
        return 0, 0.5  # neutral

def predict_sentiment(text):
    """
    Predict sentiment for a single text
    """
    processed_text = preprocess_text(text)
    
    if processed_text == '':
        return {'prediction': 0, 'confidence': 0.5}
    
    # Use PyTorch RNN model if loaded successfully
    if model is not None and tokenizer is not None:
        try:
            # Tokenize & pad
            seqs = tokenizer.texts_to_sequences([processed_text])
            padded = pad_sequences(seqs, maxlen=max_length, padding='post')
            tensor_input = torch.tensor(padded)
            
            with torch.no_grad():
                output = model(tensor_input).item()
            
            # Map probability output (0.0 to 1.0) to class labels (1: positive, -1: negative, 0: neutral)
            if output > 0.6:
                return {'prediction': 1, 'confidence': float(output)}
            elif output < 0.4:
                return {'prediction': -1, 'confidence': float(1.0 - output)}
            else:
                # Neutral sentiment in the margin
                confidence = float(1.0 - abs(output - 0.5) * 2)
                return {'prediction': 0, 'confidence': confidence}
        except Exception as e:
            print(f"RNN model prediction failed: {e}", file=sys.stderr)
            pass
            
    # Fallback
    prediction, confidence = simple_sentiment_analysis(text)
    return {'prediction': prediction, 'confidence': confidence}

def predict_batch(texts):
    results = []
    for text in texts:
        result = predict_sentiment(text)
        results.append(result)
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Sentiment Analysis using PyTorch RNN')
    parser.add_argument('--text', type=str, help='Text to analyze')
    parser.add_argument('--batch', type=str, help='JSON array of texts to analyze')
    
    args = parser.parse_args()
    
    if args.text:
        result = predict_sentiment(args.text)
        print(json.dumps(result))
    elif args.batch:
        try:
            texts = json.loads(args.batch)
            results = predict_batch(texts)
            print(json.dumps(results))
        except json.JSONDecodeError:
            print(json.dumps({'error': 'Invalid JSON format'}))
    else:
        print(json.dumps({'error': 'No text provided'}))
