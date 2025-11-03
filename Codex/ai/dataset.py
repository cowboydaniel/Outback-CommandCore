from typing import List, Tuple

class CodeDataset:
    def __init__(self, sequences: List[Tuple[List[int], int]], batch_size: int = 32, shuffle: bool = True):
        """
        Initialize the dataset with sequences of (input_ids, target_id) pairs.
        
        Args:
            sequences: List of (input_ids, target_id) pairs
            batch_size: Number of samples per batch
            shuffle: Whether to shuffle the dataset
        """
        self.sequences = sequences
        self.batch_size = batch_size
        self.shuffle = shuffle
        
        if self.shuffle:
            self._fisher_yates_shuffle()
    
    def _fisher_yates_shuffle(self) -> None:
        """Shuffle the sequences in-place using Fisher-Yates algorithm."""
        n = len(self.sequences)
        for i in range(n - 1, 0, -1):
            # Generate a random index between 0 and i (inclusive)
            j = int(i * (self._random_float() * 1000 % 1000) / 1000)
            # Swap elements at i and j
            self.sequences[i], self.sequences[j] = self.sequences[j], self.sequences[i]
    
    def _random_float(self) -> float:
        """Generate a pseudo-random float between 0 and 1."""
        import time
        return (time.time() * 1000) % 1
    
    def get_batches(self) -> List[Tuple[List[List[int]], List[int]]]:
        """
        Split the dataset into batches.
        
        Returns:
            List of (inputs, targets) batches where:
            - inputs: list of input ID sequences
            - targets: list of target IDs
        """
        batches = []
        n = len(self.sequences)
        
        for i in range(0, n, self.batch_size):
            batch = self.sequences[i:i + self.batch_size]
            inputs = [seq for seq, _ in batch]
            targets = [target for _, target in batch]
            batches.append((inputs, targets))
            
        return batches
    
    def reset(self) -> None:
        """Reset the dataset by reshuffling if shuffle is enabled."""
        if self.shuffle:
            self._fisher_yates_shuffle()


def prepare_training_sequences(encoded_tokens: List[int], context_window: int = 8) -> List[Tuple[List[int], int]]:
    """
    Prepare training sequences from encoded tokens.
    
    Args:
        encoded_tokens: List of token IDs
        context_window: Size of the context window
        
    Returns:
        List of (input_sequence, target) pairs
    """
    sequences = []
    for i in range(len(encoded_tokens) - context_window):
        input_seq = encoded_tokens[i:i + context_window]
        target = encoded_tokens[i + context_window]
        sequences.append((input_seq, target))
    return sequences


if __name__ == "__main__":
    # Test the CodeDataset with a simple example
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from tokenizer import Tokenizer
    
    # Initialize tokenizer and build vocab
    tokenizer = Tokenizer()
    test_code = "x = y + 2"
    
    # Tokenize the code
    tokens = tokenizer.tokenize(test_code)
    
    # Build vocabulary
    tokenizer.build_vocab(tokens)
    
    # Encode tokens
    encoded = tokenizer.encode(tokens)
    
    # Prepare training sequences
    training_data = prepare_training_sequences(encoded)
    
    # Create dataset
    dataset = CodeDataset(training_data, batch_size=2, shuffle=True)
    
    # Get and print batches
    batches = dataset.get_batches()
    for i, (inputs, targets) in enumerate(batches):
        print(f"Batch {i+1}:")
        print(f"  Inputs: {inputs}")
        print(f"  Targets: {targets}")
    
    # Test reset
    print("\nResetting dataset...")
    dataset.reset()
    
    # Get and print batches after reset
    batches_after_reset = dataset.get_batches()
    for i, (inputs, targets) in enumerate(batches_after_reset):
        print(f"Batch {i+1} after reset:")
        print(f"  Inputs: {inputs}")
        print(f"  Targets: {targets}")
