import torch
import torch.nn as nn
import numpy as np

class XAUPredictorLSTM(nn.Module):
    def __init__(self, input_size=15, hidden_layer_size=64, num_layers=2, output_size=1, dropout=0.2):
        super().__init__()
        self.hidden_layer_size = hidden_layer_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(input_size, hidden_layer_size, num_layers, batch_first=True, dropout=dropout if num_layers > 1 else 0)
        self.linear = nn.Linear(hidden_layer_size, output_size)
        
    def forward(self, input_seq):
        lstm_out, _ = self.lstm(input_seq)
        # We want the prediction from the last time step
        predictions = self.linear(lstm_out[:, -1, :])
        return predictions

class ModelPipeline:
    def __init__(self, model_path=None):
        self.input_size = 15 # Features: OHLCV (5) + Indicators (10)
        self.model = XAUPredictorLSTM(input_size=self.input_size)
        
        # Use GPU if available
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        
        if model_path:
            self.load_model(model_path)
        else:
            # Random initialization for demo purposes
            self.model.eval()

    def load_model(self, path):
        try:
            self.model.load_state_dict(torch.load(path, map_location=self.device))
            self.model.eval()
        except Exception as e:
            print(f"Failed to load model: {e}")

    def predict(self, features: np.ndarray) -> float:
        """
        Expects features of shape (sequence_length, input_size)
        """
        if features.shape[-1] != self.input_size:
            # Handle feature mismatch if necessary
            pass
            
        with torch.no_grad():
            seq_tensor = torch.FloatTensor(features).unsqueeze(0).to(self.device)
            prediction = self.model(seq_tensor)
            return prediction.item()

    def batch_predict(self, features_batch: np.ndarray) -> np.ndarray:
        with torch.no_grad():
            seq_tensor = torch.FloatTensor(features_batch).to(self.device)
            predictions = self.model(seq_tensor)
            return predictions.cpu().numpy()
