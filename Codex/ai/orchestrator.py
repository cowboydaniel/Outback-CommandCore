"""
Orchestrator module for the CommandCoreCodex project.

This module coordinates the code generation and validation pipeline,
handling tokenization, model training, code generation, and validation.
"""

import os
import logging
from typing import List, Tuple, Dict, Optional, Any
import torch
from torch import nn, optim

from Codex.ai.tokenizer import Tokenizer
from Codex.ai.dataset import CodeDataset
from Codex.ai.codegen import Transformer, train_transformer
from Codex.ai.checker import CodeChecker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Orchestrator:
    """
    Orchestrates the code generation and validation pipeline.
    
    This class manages the entire workflow from tokenization to code generation,
    including model training and code validation.
    """
    
    def __init__(
        self,
        batch_size: int = 32,
        num_epochs: int = 10,
        embedding_size: int = 256,
        num_heads: int = 8,
        num_layers: int = 6,
        learning_rate: float = 0.001,
        max_sequence_length: int = 1024,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ) -> None:
        """
        Initialize the orchestrator with the given configuration.
        
        Args:
            batch_size: Size of training batches
            num_epochs: Number of training epochs
            embedding_size: Size of token embeddings
            num_heads: Number of attention heads in the transformer
            num_layers: Number of transformer layers
            learning_rate: Learning rate for the optimizer
            max_sequence_length: Maximum sequence length for the model
            device: Device to run the model on ('cuda' or 'cpu')
        """
        self.batch_size = batch_size
        self.num_epochs = num_epochs
        self.learning_rate = learning_rate
        self.max_sequence_length = max_sequence_length
        self.device = device
        
        # Initialize components
        self.tokenizer = Tokenizer()
        self.dataset: Optional[CodeDataset] = None
        self.checker = CodeChecker()
        
        # Model will be initialized when data is prepared
        self.model: Optional[Transformer] = None
        self.vocab_size: int = 0
        self.pad_token_id: int = 0
        
        logger.info(f"Orchestrator initialized with device: {device}")
    
    def prepare_data(self, source_code: str) -> None:
        """
        Prepare training data from source code.
        
        Args:
            source_code: Input source code as a string
        """
        try:
            # Tokenize the source code
            tokens = self.tokenizer.tokenize(source_code)
            
            # Initialize dataset with tokenized data
            self.dataset = CodeDataset(
                tokens=tokens,
                max_sequence_length=self.max_sequence_length,
                batch_size=self.batch_size
            )
            
            # Initialize model with the correct vocab size
            self.vocab_size = len(self.tokenizer.vocab)
            self.pad_token_id = self.tokenizer.pad_token_id
            
            self.model = Transformer(
                vocab_size=self.vocab_size,
                embedding_size=256,
                num_heads=8,
                num_layers=6,
                max_sequence_length=self.max_sequence_length,
                pad_token_id=self.pad_token_id
            ).to(self.device)
            
            logger.info(f"Prepared data with {len(tokens)} tokens and vocab size {self.vocab_size}")
            
        except Exception as e:
            logger.error(f"Error preparing data: {str(e)}")
            raise
    
    def train_model(self) -> None:
        """Train the transformer model on the prepared dataset."""
        if self.model is None or self.dataset is None:
            raise ValueError("Data must be prepared before training")
        
        try:
            # Initialize optimizer and loss function
            optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
            criterion = nn.CrossEntropyLoss(ignore_index=self.pad_token_id)
            
            # Train the model
            train_transformer(
                model=self.model,
                dataset=self.dataset,
                criterion=criterion,
                optimizer=optimizer,
                num_epochs=self.num_epochs,
                device=self.device
            )
            
            logger.info("Model training completed successfully")
            
        except Exception as e:
            logger.error(f"Error during model training: {str(e)}")
            raise
    
    def lint_code(self, source_code: str) -> List[str]:
        """
        Lint the given source code.
        
        Args:
            source_code: Source code to lint
            
        Returns:
            List of lint warning messages
        """
        try:
            return self.checker.lint_code(source_code)
        except Exception as e:
            logger.error(f"Error during linting: {str(e)}")
            return [f"Error during linting: {str(e)}"]
    
    def run_sandboxed(self, source_code: str) -> Tuple[str, str]:
        """
        Run the given source code in a sandboxed environment.
        
        Args:
            source_code: Source code to execute
            
        Returns:
            Tuple of (stdout, stderr)
        """
        try:
            return self.checker.run_sandboxed(source_code)
        except Exception as e:
            error_msg = f"Error in sandboxed execution: {str(e)}"
            logger.error(error_msg)
            return "", error_msg
    
    def generate_code(self, prompt: str, max_tokens: int = 100) -> str:
        """
        Generate code from a given prompt.
        
        Args:
            prompt: Input prompt for code generation
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Generated code as a string
        """
        if self.model is None:
            raise ValueError("Model must be trained before generation")
        
        self.model.eval()
        input_tokens = self.tokenizer.tokenize(prompt)
        generated_tokens = input_tokens.copy()
        
        with torch.no_grad():
            for _ in range(max_tokens):
                # Prepare input tensor
                input_tensor = torch.tensor(
                    [generated_tokens[-self.max_sequence_length:]],
                    device=self.device
                )
                
                # Get model predictions
                logits = self.model(input_tensor)
                next_token = torch.argmax(logits[0, -1, :], dim=-1).item()
                
                # Stop if we hit the end token or max length
                if next_token == self.tokenizer.eos_token_id:
                    break
                    
                generated_tokens.append(next_token)
        
        return self.tokenizer.detokenize(generated_tokens[len(input_tokens):])

def main() -> None:
    """Example usage of the Orchestrator class."""
    try:
        # Sample source code for demonstration
        sample_code = """
def hello_world():
    print("Hello, World!")
    return 42
"""
        # Initialize orchestrator
        orchestrator = Orchestrator(
            batch_size=4,
            num_epochs=2,
            embedding_size=128,
            num_heads=4,
            num_layers=2,
            max_sequence_length=64
        )
        
        # Run linting
        print("Running lint checks...")
        warnings = orchestrator.lint_code(sample_code)
        for warning in warnings:
            print(f"Lint warning: {warning}")
        
        # Prepare data and train model
        print("\nPreparing data and training model...")
        orchestrator.prepare_data(sample_code)
        orchestrator.train_model()
        
        # Generate code
        print("\nGenerating code...")
        prompt = "def add(a, b):"
        generated = orchestrator.generate_code(prompt, max_tokens=20)
        print(f"Generated code:\n{prompt}{generated}")
        
        # Run generated code in sandbox
        print("\nRunning generated code in sandbox...")
        stdout, stderr = orchestrator.run_sandboxed(f"{prompt}{generated}")
        if stdout:
            print(f"Output: {stdout}")
        if stderr:
            print(f"Errors: {stderr}")
            
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise

if __name__ == "__main__":
    main()
