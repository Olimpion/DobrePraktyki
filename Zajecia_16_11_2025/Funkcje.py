#PALINDROM
def is_palindrome(text: str) -> bool:
    text = text.replace(" ", "").lower()
    return text == text[::-1]

#FIBONACCI
def fibonacci(n: int) -> int:
    if n == 0:
        return 0
    elif n == 1:
        return 1
    else:
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b


#SAMOGŁOSKI
def count_vowels(text: str) -> int:
    vowels = "aeiouyAEIOUY"
    return sum(1 for char in text if char in vowels)

#ZNIŻKA
def calculate_discount(price: float, discount: float) -> float:
    if not (0 <= discount <= 1):
        raise ValueError("Discount must be between 0 and 1.")
    return price * (1 - discount)

#SPŁASZCZANA LISTA
def flatten_list(nested_list: list) -> list:
    flat_list = []
    for item in nested_list:
        if isinstance(item, list):
            flat_list.extend(flatten_list(item))
        else:
            flat_list.append(item)
    return flat_list


#SŁOWNIK WYSTĄPIEŃ
import string

def word_frequencies(text: str) -> dict:
    text = text.translate(str.maketrans("", "", string.punctuation)).lower()
    words = text.split()
    frequencies = {}
    for word in words:
        frequencies[word] = frequencies.get(word, 0) + 1
    return frequencies

#LICZBA PIERWSZA
def is_prime(n: int) -> bool:
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

