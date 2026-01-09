import math
import os
from typing import Tuple, Optional

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor

from Codex.ai.dataset import CodeDataset


def get_device() -> torch.device:
    """Get the available device (GPU if available, else CPU)."""
    return torch.device('cuda' if torch.cuda.is_available() else 'cpu')


class PositionalEncoding(nn.Module):
    """Fixed sinusoidal positional encoding."""
    def __init__(self, d_model: int, max_len: int = 512):
        super().__init__()
        position = torch.arange(max_len).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2) * (-math.log(10000.0) / d_model))
        
        pe = torch.zeros(max_len, d_model)
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer('pe', pe.unsqueeze(0))
    
    def forward(self, x: Tensor) -> Tensor:
        """
        Args:
            x: Tensor, shape [batch_size, seq_len, embedding_dim]
        """
        x = x + self.pe[:, :x.size(1)]
        return x


class TransformerBlock(nn.Module):
    """Transformer encoder block with multi-head self-attention and feed-forward network."""
    def __init__(self, d_model: int, nhead: int, dim_feedforward: int, dropout: float = 0.1):
        super().__init__()
        self.self_attn = nn.MultiheadAttention(d_model, nhead, dropout=dropout, batch_first=True)
        self.linear1 = nn.Linear(d_model, dim_feedforward)
        self.linear2 = nn.Linear(dim_feedforward, d_model)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)
        self.activation = F.relu
    
    def forward(self, src: Tensor, src_mask: Optional[Tensor] = None) -> Tensor:
        # Self attention with residual connection
        src2 = self.self_attn(src, src, src, attn_mask=src_mask, need_weights=False)[0]
        src = src + self.dropout(src2)
        src = self.norm1(src)
        
        # Feed forward with residual connection
        src2 = self.linear2(self.dropout(self.activation(self.linear1(src))))
        src = src + self.dropout(src2)
        src = self.norm2(src)
        return src


class Transformer(nn.Module):
    """Transformer model for code generation."""
    def __init__(self, vocab_size: int, d_model: int = 256, nhead: int = 8, 
                 num_layers: int = 4, dim_feedforward: int = 512, max_len: int = 512, 
                 dropout: float = 0.1):
        super().__init__()
        self.token_embedding = nn.Embedding(vocab_size, d_model)
        self.pos_encoder = PositionalEncoding(d_model, max_len)
        
        # Stack of transformer blocks
        self.transformer_blocks = nn.ModuleList([
            TransformerBlock(d_model, nhead, dim_feedforward, dropout)
            for _ in range(num_layers)
        ])
        
        self.output_layer = nn.Linear(d_model, vocab_size)
        self.dropout = nn.Dropout(dropout)
        self.d_model = d_model
        self.max_len = max_len
    
    def forward(self, x: Tensor, mask: Optional[Tensor] = None) -> Tensor:
        # x: [batch_size, seq_len]
        seq_len = x.size(1)
        
        # Create mask for attention if not provided
        if mask is None:
            mask = torch.triu(torch.ones(seq_len, seq_len) * float('-inf'), diagonal=1).to(x.device)
        
        # Token embeddings + positional encoding
        x = self.token_embedding(x) * math.sqrt(self.d_model)
        x = self.pos_encoder(x)
        x = self.dropout(x)
        
        # Pass through transformer blocks
        for transformer in self.transformer_blocks:
            x = transformer(x, mask)
        
        # Output logits
        logits = self.output_layer(x)
        return logits


def train_transformer(
    model: Transformer,
    dataset: CodeDataset,
    num_epochs: int = 10,
    device: Optional[torch.device] = None,
    criterion: Optional[nn.Module] = None,
    optimizer: Optional[torch.optim.Optimizer] = None,
    on_epoch_end=None,
    on_batch_end=None,
) -> None:
    """Train the transformer model.

    Args:
        model: Transformer model to train
        dataset: CodeDataset instance
        num_epochs: Number of training epochs
        device: Device to run training on
        criterion: Loss function to use
        optimizer: Optimizer instance to use
        on_epoch_end: Optional callback for epoch completion
        on_batch_end: Optional callback for batch completion
    """
    if device is None:
        device = get_device()
    if criterion is None:
        criterion = nn.CrossEntropyLoss()
    if optimizer is None:
        optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

    model = model.to(device)
    model.train()

    for epoch in range(num_epochs):
        dataset.reset()
        batches = dataset.get_batches()
        total_batches = len(batches)
        epoch_loss = 0.0

        for batch_idx, (inputs, targets) in enumerate(batches, start=1):
            inputs_tensor = torch.tensor(inputs, device=device)
            targets_tensor = torch.tensor(targets, device=device)

            optimizer.zero_grad()
            outputs = model(inputs_tensor)
            logits = outputs[:, -1, :]
            loss = criterion(logits, targets_tensor)

            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()

            if on_batch_end is not None:
                on_batch_end(
                    epoch,
                    num_epochs,
                    batch_idx,
                    total_batches,
                    loss.item(),
                )

        avg_loss = epoch_loss / max(total_batches, 1)
        if on_epoch_end is not None:
            on_epoch_end(epoch, num_epochs, avg_loss, total_batches)


def save_model(model: Transformer, path: str) -> None:
    """Save the model to the specified path."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    torch.save(model.state_dict(), path)
    print(f"Model saved to {path}")


def load_model(path: str, model: Optional[Transformer] = None, **kwargs) -> Transformer:
    """Load a model from the specified path.
    
    Args:
        path: Path to the saved model
        model: Optional model instance to load weights into
        **kwargs: Arguments to create a new model if not provided
    
    Returns:
        Loaded model
    """
    if model is None:
        model = Transformer(**kwargs)
    
    device = get_device()
    model.load_state_dict(torch.load(path, map_location=device))
    model = model.to(device)
    print(f"Model loaded from {path}")
    return model


if __name__ == "__main__":
    # Example usage with dummy data
    vocab_size = 10000
    seq_len = 128
    batch_size = 4
    
    # Create dummy dataset
    class DummyDataset(CodeDataset):
        def __init__(self):
            self.data = torch.randint(0, vocab_size, (1000, seq_len))
            self.current_idx = 0
        
        def reset(self):
            self.current_idx = 0
        
        def get_batches(self):
            batches = []
            for i in range(0, len(self.data) - batch_size, batch_size):
                batch = self.data[i:i + batch_size]
                inputs = batch[:, :-1]
                targets = batch[:, -1]
                batches.append((inputs, targets))
            return batches
    
    # Initialize model and dataset
    model = Transformer(vocab_size=vocab_size)
    dataset = DummyDataset()
    
    # Train
    train_transformer(model, dataset, num_epochs=2)
    
    # Save and load example
    save_model(model, "model.pt")
    loaded_model = load_model("model.pt", vocab_size=vocab_size)
