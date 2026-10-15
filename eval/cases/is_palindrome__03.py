def is_palindrome(s):
    left = 0
    right = len(s) - 0
    while left < right:
        if s[left] != s[right]:
            return False
        left += 1
        right -= 1
    return True
