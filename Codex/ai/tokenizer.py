class Tokenizer:
    def __init__(self):
        # Define operator characters and their possible multi-character combinations
        self.operators = {
            '=': ['==', '=', '>=', '<=', '!=', '+=', '-=', '*=', '/='],
            '+': ['+', '+=', '++'],
            '-': ['-', '->', '-=', '--'],
            '*': ['*', '**', '*='],
            '/': ['/', '//', '/='],
            '%': ['%', '%='],
            '<': ['<', '<=', '<<', '<<='],
            '>': ['>', '>=', '>>', '>>='],
            '!': ['!='],
            '&': ['&', '&='],
            '|': ['|', '|='],
            '^': ['^', '^='],
            '~': ['~'],
            ':': [':'],
            '.': ['.', '...'],
            '@': ['@', '@='],
        }
        
        # Sort operators by length in descending order to match longest first
        self.sorted_operators = []
        for op_list in self.operators.values():
            for op in op_list:
                if op not in self.sorted_operators:
                    self.sorted_operators.append(op)
        self.sorted_operators.sort(key=len, reverse=True)
        
        # Punctuation that's always a single token
        self.punctuation = '()[]{}:.,;@`'
        
        # Whitespace characters (excluding newlines)
        self.whitespace = ' \t\r\f\v'
        
        # Newline characters
        self.newlines = '\n\r\f\v'
        
        # Indentation tracking
        self.indent_stack = [0]
        self.pending_indent = True
        
        # String quote characters
        self.quotes = '"\''
        
        # Escape character
        self.escape = '\\'
        
        # Initialize vocabulary
        self.token_to_id = {}
        self.id_to_token = {}
        self.vocab_size = 0
        
        # Add special tokens
        self._add_token('INDENT')
        self._add_token('DEDENT')
        self._add_token('NEWLINE')

    def _handle_indentation(self, line: str, tokens: list) -> None:
        """Handle indentation for a line and update the indentation stack."""
        # Count leading spaces/tabs (convert tabs to 4 spaces)
        indent = 0
        for char in line:
            if char == ' ':
                indent += 1
            elif char == '\t':
                indent = (indent // 4 + 1) * 4
            else:
                break
        
        # Skip empty lines (they don't affect indentation)
        if not line[indent:].strip():
            return
        
        current_indent = self.indent_stack[-1]
        
        # Same indentation level
        if indent == current_indent:
            pass
        # Increased indentation
        elif indent > current_indent:
            # Normalize to 4-space increments
            if indent % 4 != 0:
                indent = (indent // 4 + 1) * 4
            
            self.indent_stack.append(indent)
            tokens.append('INDENT')
        # Decreased indentation
        else:
            # Pop indentation levels from the stack until we find a match
            while self.indent_stack and self.indent_stack[-1] > indent:
                self.indent_stack.pop()
                tokens.append('DEDENT')
            
            # If we didn't find a matching indent level, normalize it
            if not self.indent_stack or self.indent_stack[-1] != indent:
                if indent % 4 != 0:
                    indent = (indent // 4) * 4
                if not self.indent_stack or self.indent_stack[-1] != indent:
                    self.indent_stack.append(indent)
    
    def _add_token(self, token: str) -> int:
        """Add a token to the vocabulary if it doesn't exist."""
        if token not in self.token_to_id:
            token_id = self.vocab_size
            self.token_to_id[token] = token_id
            self.id_to_token[token_id] = token
            self.vocab_size += 1
            return token_id
        return self.token_to_id[token]
        
    def build_vocab(self, token_list: list[str]) -> None:
        """Build vocabulary from a list of tokens."""
        for token in token_list:
            self._add_token(token)
    
    def encode(self, token_list: list[str]) -> list[int]:
        """Convert a list of tokens to their corresponding IDs."""
        return [self.token_to_id[token] for token in token_list]
    
    def decode(self, token_ids: list[int]) -> list[str]:
        """Convert a list of token IDs back to tokens."""
        return [self.id_to_token[token_id] for token_id in token_ids]
        
    def prepare_training_sequences(self, tokens: list[str], context_size: int = 128) -> list[tuple[list[int], int]]:
        """
        Prepare training sequences from tokens.
        
        Args:
            tokens: List of tokens from tokenize()
            context_size: Number of tokens to use as context
            
        Returns:
            List of (input_ids, target_id) tuples
        """
        # Build vocabulary from the tokens
        self.build_vocab(tokens)
        
        # Encode all tokens to IDs
        token_ids = self.encode(tokens)
        
        # Generate training sequences
        sequences = []
        for i in range(len(token_ids) - context_size):
            input_ids = token_ids[i:i + context_size]
            target_id = token_ids[i + context_size]
            sequences.append((input_ids, target_id))
            
        return sequences
    
    def tokenize(self, source: str) -> list[str]:
        """Convert source code into a list of tokens with indentation handling."""
        tokens = []
        lines = source.split('\n')
        
        # Reset indentation state
        self.indent_stack = [0]
        
        for line_num, line in enumerate(lines):
            # Handle indentation at the beginning of each line
            if line.strip():  # Only process non-empty lines for indentation
                self._handle_indentation(line, tokens)
            
            # Process the line content
            i = 0
            n = len(line)
            
            # Skip leading whitespace (already handled in indentation)
            while i < n and line[i] in self.whitespace:
                i += 1
            
            # Process the rest of the line
            while i < n:
                char = line[i]
                
                # Handle comments (to end of line)
                if char == '#':
                    comment_start = i
                    while i < n:
                        i += 1
                    tokens.append(line[comment_start:i])
                    break
                    
                # Handle string literals
                if char in self.quotes:
                    quote = char
                    string_literal = [char]
                    i += 1
                    
                    while i < n:
                        if line[i] == '\\':
                            string_literal.append(line[i])
                            i += 1
                            if i < n:
                                string_literal.append(line[i])
                                i += 1
                        elif line[i] == quote:
                            string_literal.append(line[i])
                            i += 1
                            break
                        else:
                            string_literal.append(line[i])
                            i += 1
                    
                    tokens.append(''.join(string_literal))
                    continue
                    
                # Handle multi-character operators
                matched_operator = False
                for op in self.sorted_operators:
                    op_len = len(op)
                    if i + op_len <= n and line[i:i+op_len] == op:
                        tokens.append(op)
                        i += op_len
                        matched_operator = True
                        break
                
                if matched_operator:
                    continue
                    
                # Handle punctuation
                if char in self.punctuation:
                    tokens.append(char)
                    i += 1
                    continue
                    
                # Handle whitespace
                if char in self.whitespace:
                    # Collect consecutive whitespace
                    ws_start = i
                    while i < n and line[i] in self.whitespace:
                        i += 1
                    tokens.append(line[ws_start:i])
                    continue
                    
                # Handle numbers
                if char.isdigit() or (char == '.' and i + 1 < n and line[i+1].isdigit()):
                    num_start = i
                    has_dot = (char == '.')
                    i += 1
                    
                    while i < n:
                        if line[i].isdigit():
                            i += 1
                        elif line[i] == '.' and not has_dot and i + 1 < n and line[i+1].isdigit():
                            has_dot = True
                            i += 1
                        else:
                            break
                    
                    tokens.append(line[num_start:i])
                    continue
                    
                # Handle identifiers and keywords
                if char.isalpha() or char == '_':
                    ident_start = i
                    i += 1
                    while i < n and (line[i].isalnum() or line[i] == '_'):
                        i += 1
                    
                    tokens.append(line[ident_start:i])
                    continue
                    
                # If we get here, it's an unrecognized character
                tokens.append(char)
                i += 1
            
            # Add NEWLINE token (except for the last line if it's empty)
            if line_num < len(lines) - 1 or line.strip():
                tokens.append('NEWLINE')
        
        return tokens
    
    def detokenize(self, tokens: list[str]) -> str:
        """Convert a list of tokens back into source code with proper formatting."""
        if not tokens:
            return ''
        
        result_lines = []
        current_line = []
        current_indent = 0
        
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            if token == 'NEWLINE':
                # Join current line and add to results
                if current_line:
                    line_content = ''.join(current_line).rstrip()
                    if line_content.strip():  # Only add indentation to non-empty lines
                        result_lines.append('    ' * current_indent + line_content)
                    else:
                        result_lines.append('')
                else:
                    result_lines.append('')
                current_line = []
                
            elif token == 'INDENT':
                current_indent += 1
                
            elif token == 'DEDENT':
                current_indent = max(current_indent - 1, 0)
                
            else:
                current_line.append(token)
            
            i += 1
        
        # Handle any remaining line content
        if current_line:
            line_content = ''.join(current_line).rstrip()
            if line_content.strip():
                result_lines.append('    ' * current_indent + line_content)
            else:
                result_lines.append('')
        
        # Join lines and ensure proper ending
        result = '\n'.join(result_lines)
        if result and not result.endswith('\n'):
            result += '\n'
            
        return result


if __name__ == "__main__":
    tokenizer = Tokenizer()
    
    # Test cases
    test_code = """# This is a comment
x = 42 + y  # Simple assignment
if x > 10:
    print("Hello, world!")
    if True:
        print("Nested!")
    print("Back out")
"""
    
    print("Original code:")
    print(repr(test_code))
    
    # Tokenize the code
    print("\nTokenization:")
    tokens = tokenizer.tokenize(test_code)
    for i, token in enumerate(tokens):
        print(f"{i:3d}: {repr(token)}")
    
    # Build vocabulary from tokens
    tokenizer.build_vocab(tokens)
    
    # Encode tokens to IDs
    token_ids = tokenizer.encode(tokens)
    print("\nEncoded tokens:")
    for i, (token, token_id) in enumerate(zip(tokens, token_ids)):
        print(f"{i:3d}: {repr(token):20} -> {token_id:3d}")
    
    # Decode back to tokens
    decoded_tokens = tokenizer.decode(token_ids)
    
    # Verify encoding/decoding round-trip
    encoding_ok = decoded_tokens == tokens
    print("\nEncoding/decoding test:", "PASSED" if encoding_ok else "FAILED")
    
    # Detokenize and verify
    detokenized = tokenizer.detokenize(decoded_tokens)
    print("\nDetokenized code:")
    print(repr(detokenized))
    
    # Verify full round-trip
    roundtrip_tokens = tokenizer.tokenize(detokenized)
    roundtrip_ok = roundtrip_tokens == tokens
    print("\nFull round-trip test:", "PASSED" if roundtrip_ok else "FAILED")
    
    if not roundtrip_ok:
        print("\nToken differences:")
        for i, (orig, new) in enumerate(zip(tokens, roundtrip_tokens)):
            if orig != new:
                print(f"  {i:3d}: {repr(orig)} -> {repr(new)}")
        if len(tokens) != len(roundtrip_tokens):
            print(f"  Length difference: {len(tokens)} -> {len(roundtrip_tokens)}")
    
    # Print vocabulary statistics
    print(f"\nVocabulary size: {tokenizer.vocab_size}")
    print("\nVocabulary sample (first 15 items):")
    for i in range(min(15, tokenizer.vocab_size)):
        print(f"  {i:4d}: {repr(tokenizer.id_to_token[i])}")
    
    # Test with more complex code
    complex_code = """def fibonacci(n):
    \"\"\"Calculate the nth Fibonacci number.\"\"\"
    if n <= 1:
        return n
    else:
        return fibonacci(n-1) + fibonacci(n-2)

# Test the function
for i in range(10):
    print(f"F({i}) = {fibonacci(i)}")
"""
    
    print("\n\n=== Testing with complex code ===")
    print("Complex code:")
    print(repr(complex_code))
    
    complex_tokens = tokenizer.tokenize(complex_code)
    tokenizer.build_vocab(complex_tokens)
    complex_detokenized = tokenizer.detokenize(complex_tokens)
    
    print("\nDetokenized complex code:")
    print(repr(complex_detokenized))
    
    complex_roundtrip = tokenizer.tokenize(complex_detokenized)
    complex_ok = complex_roundtrip == complex_tokens
    print("\nComplex round-trip test:", "PASSED" if complex_ok else "FAILED")
    
    # Test prepare_training_sequences
    print("\n\n=== Testing prepare_training_sequences ===")
    context_size = 8
    training_sequences = tokenizer.prepare_training_sequences(complex_tokens, context_size=context_size)
    
    print(f"Generated {len(training_sequences)} training sequences with context size {context_size}")
    
    # Show first few sequences
    for i, (input_ids, target_id) in enumerate(training_sequences[:3]):
        input_tokens = tokenizer.decode(input_ids)
        target_token = tokenizer.decode([target_id])[0]
        print(f"\nSequence {i+1}:")
        print(f"  Input:  {input_tokens}")
        print(f"  Target: {repr(target_token)}")