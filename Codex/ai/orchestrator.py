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
        self.embedding_size = embedding_size
        self.num_heads = num_heads
        self.num_layers = num_layers
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
    
    def _prepare_from_source(self, source_code: str) -> Dict[str, int]:
        tokens = self.tokenizer.tokenize(source_code)
        if not tokens:
            raise ValueError("No tokens were generated from the provided source code.")

        context_size = min(self.max_sequence_length, len(tokens) - 1)
        if context_size <= 0:
            raise ValueError("Not enough tokens to build training sequences.")

        sequences = self.tokenizer.prepare_training_sequences(
            tokens,
            context_size=context_size
        )
        if not sequences:
            raise ValueError("Not enough tokens to build training sequences.")

        self.dataset = CodeDataset(
            sequences=sequences,
            batch_size=self.batch_size
        )

        self.vocab_size = self.tokenizer.vocab_size
        self.pad_token_id = 0

        self.model = Transformer(
            vocab_size=self.vocab_size,
            d_model=self.embedding_size,
            nhead=self.num_heads,
            num_layers=self.num_layers,
            max_len=self.max_sequence_length
        ).to(self.device)

        return {
            "token_count": len(tokens),
            "sequence_count": len(sequences),
        }

    def prepare_data(self, source_code: str) -> None:
        """
        Prepare training data from source code.

        Args:
            source_code: Input source code as a string
        """
        try:
            stats = self._prepare_from_source(source_code)
            logger.info(
                "Prepared data with %s tokens and %s sequences",
                stats["token_count"],
                stats["sequence_count"]
            )
        except Exception as e:
            logger.error(f"Error preparing data: {str(e)}")
            raise

    def prepare_data_from_path(self, path: str) -> Dict[str, int]:
        """
        Prepare training data from a directory of Python files.

        Args:
            path: Path to the dataset directory.

        Returns:
            Dict with counts for loaded files, tokens, and sequences.
        """
        if not os.path.isdir(path):
            raise ValueError(f"Dataset path does not exist or is not a directory: {path}")

        python_files = []
        for root, _, files in os.walk(path):
            for filename in files:
                if filename.endswith(".py"):
                    python_files.append(os.path.join(root, filename))

        if not python_files:
            raise ValueError(f"No .py files found in directory: {path}")

        python_files.sort()
        sources = []
        for file_path in python_files:
            try:
                with open(file_path, "r", encoding="utf-8") as file_handle:
                    content = file_handle.read()
            except UnicodeDecodeError as exc:
                raise ValueError(
                    f"File is not valid UTF-8 text: {file_path}"
                ) from exc

            sources.append(content)

        combined_source = "\n\n".join(sources).strip()
        if not combined_source:
            raise ValueError("No readable Python source found in the selected directory.")

        stats = self._prepare_from_source(combined_source)
        stats["file_count"] = len(python_files)

        logger.info(
            "Prepared data from %s files with %s tokens and %s sequences",
            stats["file_count"],
            stats["token_count"],
            stats["sequence_count"]
        )
        return stats
    
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
