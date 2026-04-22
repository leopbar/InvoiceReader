import re
import logging
import tiktoken

logger = logging.getLogger(__name__)

def clean_text(text: str) -> str:
    """
    Cleans and optimizes text before sending to AI.
    - Remove excessive whitespace (multiple spaces, blank lines)
    - Remove common boilerplate (page numbers, "Page X of Y", headers/footers)
    - Remove non-printable characters
    - Collapse repeated separators (----, ====, etc.)
    - Strip leading/trailing whitespace from each line
    - Remove empty lines
    - Return cleaned text
    """
    if not text:
        return ""

    # Remove non-printable characters
    text = "".join(char for char in text if char.isprintable() or char in "\n\r\t")

    # Strip leading/trailing whitespace from each line
    lines = [line.strip() for line in text.splitlines()]

    # Remove common boilerplate like "Page X of Y"
    cleaned_lines = []
    for line in lines:
        # Match "Page 1", "Page 1 of 2", "Página 1", etc.
        if re.match(r"^(Page|Página)\s+\d+(\s+of\s+\d+)?$", line, re.IGNORECASE):
            continue
        cleaned_lines.append(line)
    
    # Remove empty lines
    cleaned_lines = [line for line in cleaned_lines if line]

    # Join back to text
    text = "\n".join(cleaned_lines)

    # Collapse repeated separators (----, ====, etc.)
    text = re.sub(r"[-=]{3,}", "---", text)

    # Remove excessive whitespace (multiple spaces)
    text = re.sub(r" {2,}", " ", text)

    return text.strip()

def estimate_tokens(text: str) -> int:
    """
    Rough estimate of token count (approximately len(text) / 4)
    Also uses tiktoken for a more accurate count.
    Logs the estimated token count.
    """
    if not text:
        return 0
    
    # Rough estimate
    rough_count = len(text) // 4
    
    # More accurate estimate using tiktoken (cl100k_base used by GPT-4 and Gemini-like models)
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        accurate_count = len(encoding.encode(text))
    except Exception:
        accurate_count = rough_count

    logger.info(f"Estimated tokens: {accurate_count} (Rough: {rough_count})")
    return accurate_count

def truncate_if_needed(text: str, max_tokens: int = 4000) -> str:
    """
    If text exceeds max_tokens, intelligently truncate.
    Keep the first part (header info) and last part (totals).
    Remove middle content if too long.
    """
    current_tokens = estimate_tokens(text)
    if current_tokens <= max_tokens:
        return text

    logger.warning(f"Text exceeds max tokens ({current_tokens} > {max_tokens}). Truncating...")
    
    # Simple truncation: keep 40% from start, 40% from end
    lines = text.splitlines()
    if len(lines) < 10:
        return text[:max_tokens * 4] # Fallback to character limit

    num_lines = len(lines)
    keep_lines = int(num_lines * 0.4)
    
    truncated_text = "\n".join(lines[:keep_lines]) + "\n\n... [TRUNCATED] ...\n\n" + "\n".join(lines[-keep_lines:])
    
    return truncated_text
