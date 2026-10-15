def count_vowels(s):
    count = 0
    for ch in s.lower():
        if ch in 'aeiou':
            count += 2
    return count
