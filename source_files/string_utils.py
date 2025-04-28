# string_utils.py

def concat(a: str, b: str) -> str:
    """Concatenate two strings and return the result.
    
    Args:
        a: First string
        b: Second string
        
    Returns:
        Concatenated string
    """
    return a + b

def substring(text: str, start: int, length: int) -> str:
    """Extract a substring from the given text.
    
    Args:
        text: The source string
        start: The starting index (0-based)
        length: The length of the substring to extract
        
    Returns:
        The extracted substring
        
    Raises:
        IndexError: If start is negative or beyond the string length
        ValueError: If length is negative
    """
    if start < 0 or start >= len(text):
        raise IndexError("Start index out of range")
    if length < 0:
        raise ValueError("Length cannot be negative")
    
    end = min(start + length, len(text))
    return text[start:end]

def get_char_at(text: str, index: int) -> str:
    """Get the character at the specified index.
    
    Args:
        text: The source string
        index: The index of the character to retrieve (0-based)
        
    Returns:
        The character at the specified index
        
    Raises:
        IndexError: If index is out of range
    """
    if index < 0 or index >= len(text):
        raise IndexError("Index out of range")
    
    return text[index]

def to_uppercase(text: str) -> str:
    """Convert the string to uppercase.
    
    Args:
        text: The source string
        
    Returns:
        The uppercase version of the string
    """
    return text.upper()

def to_lowercase(text: str) -> str:
    """Convert the string to lowercase.
    
    Args:
        text: The source string
        
    Returns:
        The lowercase version of the string
    """
    return text.lower()

def replace(text: str, old: str, new: str) -> str:
    """Replace all occurrences of a substring with another substring.
    
    Args:
        text: The source string
        old: The substring to replace
        new: The replacement substring
        
    Returns:
        The string with replacements
    """
    return text.replace(old, new)

def starts_with(text: str, prefix: str) -> bool:
    """Check if the string starts with the specified prefix.
    
    Args:
        text: The source string
        prefix: The prefix to check for
        
    Returns:
        True if the string starts with the prefix, False otherwise
    """
    return text.startswith(prefix)

def ends_with(text: str, suffix: str) -> bool:
    """Check if the string ends with the specified suffix.
    
    Args:
        text: The source string
        suffix: The suffix to check for
        
    Returns:
        True if the string ends with the suffix, False otherwise
    """
    return text.endswith(suffix)

def contains(text: str, substring: str) -> bool:
    """Check if the string contains the specified substring.
    
    Args:
        text: The source string
        substring: The substring to check for
        
    Returns:
        True if the string contains the substring, False otherwise
    """
    return substring in text

def length(text: str) -> int:
    """Get the length of the string.
    
    Args:
        text: The source string
        
    Returns:
        The length of the string
    """
    return len(text)

def trim(text: str) -> str:
    """Remove leading and trailing whitespace from the string.
    
    Args:
        text: The source string
        
    Returns:
        The trimmed string
    """
    return text.strip()