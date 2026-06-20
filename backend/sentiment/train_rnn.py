import os
import re
import pickle
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
from sklearn.model_selection import train_test_split

# Set Kaggle Credentials
os.environ['KAGGLE_API_TOKEN'] = 'KGAT_c6b135f80dc02dd34e548279be758cb0'

# Clean text function matching ReviewSA.ipynb
def clean_text(text):
    if not isinstance(text, str):
        return ""
    # Remove HTML tags
    text = re.sub(r'<.*?>', '', text)
    # Remove punctuation and special characters, keep alphanumeric and spaces
    text = re.sub(r'[^a-zA-Z0-9 ]', '', text)
    # Convert to lowercase
    text = text.lower()
    return text

# A standard Keras-compatible tokenizer implemented in pure Python
class SimpleTokenizer:
    def __init__(self, num_words=None, oov_token='<unk>'):
        self.num_words = num_words
        self.oov_token = oov_token
        self.word_index = {}
        self.index_word = {}

    def fit_on_texts(self, texts):
        word_counts = {}
        for text in texts:
            for word in text.split():
                word_counts[word] = word_counts.get(word, 0) + 1
        
        # Sort words by frequency
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        
        self.word_index = {self.oov_token: 1}
        self.index_word = {1: self.oov_token}
        
        for idx, (word, _) in enumerate(sorted_words, start=2):
            if self.num_words and idx > self.num_words:
                break
            self.word_index[word] = idx
            self.index_word[idx] = word

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

# PyTorch Bidirectional LSTM Model with enhancements for accuracy (Batch Normalization and Dropout)
class SentimentRNN(nn.Module):
    def __init__(self, vocab_size, embedding_dim=128, hidden_dim=64):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.dropout1 = nn.Dropout(0.5)
        # Conv1d expects input (batch, channels, seq_len)
        self.conv = nn.Conv1d(in_channels=embedding_dim, out_channels=128, kernel_size=5)
        self.bn = nn.BatchNorm1d(128)  # Normalization to stabilize Conv1D outputs
        self.relu = nn.ReLU()
        self.pool = nn.MaxPool1d(kernel_size=4)
        self.dropout2 = nn.Dropout(0.5)
        # Bidirectional LSTM
        self.lstm = nn.LSTM(input_size=128, hidden_size=hidden_dim, batch_first=True, bidirectional=True)
        # Output layers
        self.fc = nn.Linear(hidden_dim * 2, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        # Embedding
        x = self.embedding(x)  # (batch, seq_len, embedding_dim)
        x = self.dropout1(x)
        
        # Conv1D and MaxPool
        x = x.transpose(1, 2)  # (batch, embedding_dim, seq_len)
        x = self.conv(x)
        x = self.bn(x)
        x = self.relu(x)
        x = self.pool(x)  # (batch, 128, pooled_seq_len)
        x = self.dropout2(x)
        
        # BiLSTM
        x = x.transpose(1, 2)  # (batch, pooled_seq_len, 128)
        lstm_out, (hn, cn) = self.lstm(x)
        
        # Concatenate forward and backward last hidden states
        out = torch.cat((hn[0], hn[1]), dim=1)  # (batch, 128)
        out = self.fc(out)
        out = self.sigmoid(out)
        return out

def main():
    print("Loading dataset using kagglehub...")
    import kagglehub
    path = kagglehub.dataset_download("lakshmi25npathi/imdb-dataset-of-50k-movie-reviews")
    file_path = os.path.join(path, "IMDB Dataset.csv")
    
    print(f"Reading dataset from: {file_path}")
    df = pd.read_csv(file_path)
    
    print("Cleaning reviews text...")
    df['cleaned_review'] = df['review'].apply(clean_text)
    df['sentiment_encoded'] = df['sentiment'].map({'positive': 1, 'negative': 0})
    
    print("Tokenizing text...")
    tokenizer = SimpleTokenizer(oov_token='<unk>')
    tokenizer.fit_on_texts(df['cleaned_review'])
    
    sequences = tokenizer.texts_to_sequences(df['cleaned_review'])
    max_length = 1500
    X = pad_sequences(sequences, maxlen=max_length, padding='post')
    y = df['sentiment_encoded'].values
    
    # Train / Val Split
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # PyTorch Datasets
    train_dataset = TensorDataset(torch.tensor(X_train), torch.tensor(y_train, dtype=torch.float32))
    val_dataset = TensorDataset(torch.tensor(X_val), torch.tensor(y_val, dtype=torch.float32))
    
    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False)
    
    vocab_size = len(tokenizer.word_index) + 1
    print(f"Vocabulary size: {vocab_size}")
    
    model = SentimentRNN(vocab_size=vocab_size, embedding_dim=128, hidden_dim=64)
    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    
    print("Training PyTorch RNN model...")
    epochs = 3  # 3 epochs is typically optimal and fast on CPU
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        correct = 0
        total = 0
        for batch_idx, (data, target) in enumerate(train_loader):
            optimizer.zero_grad()
            output = model(data).squeeze()
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            predictions = (output >= 0.5).float()
            correct += (predictions == target).sum().item()
            total += target.size(0)
            
            if (batch_idx + 1) % 100 == 0:
                print(f"Epoch {epoch+1}/{epochs} | Batch {batch_idx+1}/{len(train_loader)} | Train Loss: {total_loss / (batch_idx+1):.4f} | Train Acc: {correct/total:.4f}")
                
        # Validation epoch
        model.eval()
        val_loss = 0
        val_correct = 0
        val_total = 0
        with torch.no_grad():
            for data, target in val_loader:
                output = model(data).squeeze()
                loss = criterion(output, target)
                val_loss += loss.item()
                predictions = (output >= 0.5).float()
                val_correct += (predictions == target).sum().item()
                val_total += target.size(0)
        
        print(f"Epoch {epoch+1} Complete | Val Loss: {val_loss/len(val_loader):.4f} | Val Accuracy: {val_correct/val_total:.4f}\n")
        
    # Save the model and tokenizer
    models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Models")
    os.makedirs(models_dir, exist_ok=True)
    
    print("Saving tokenizer...")
    with open(os.path.join(models_dir, "tokenizer.pkl"), "wb") as f:
        pickle.dump(tokenizer, f)
        
    print("Saving PyTorch model weight state dict...")
    torch.save(model.state_dict(), os.path.join(models_dir, "ReviewSA_model.pth"))
    print("Model and Tokenizer successfully saved!")

if __name__ == "__main__":
    main()
