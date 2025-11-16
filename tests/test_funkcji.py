import pytest

from Zajecia_16_11_2025.Funkcje import is_palindrome, fibonacci, count_vowels, calculate_discount, flatten_list, word_frequencies, is_prime

# 1. Testy dla funkcji is_palindrome
def test_is_palindrome():
    assert is_palindrome("kajak") == True
    assert is_palindrome("Kobyła ma mały bok") == True
    assert is_palindrome("python") == False
    assert is_palindrome("") == True
    assert is_palindrome("A") == True

# 2. Testy dla funkcji fibonacci
def test_fibonacci():
    assert fibonacci(0) == 0
    assert fibonacci(1) == 1
    assert fibonacci(5) == 5
    assert fibonacci(10) == 55
    with pytest.raises(ValueError): fibonacci(-1)

# 3. Testy dla funkcji count_vowels
def test_count_vowels():
    assert count_vowels("Python") == 2
    assert count_vowels("AEIOUY") == 6
    assert count_vowels("bcd") == 0
    assert count_vowels("") == 0
    assert count_vowels("Próba żółwia") == 5