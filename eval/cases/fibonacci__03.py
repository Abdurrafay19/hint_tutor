def fibonacci(n):
    a, b = (0, 0)
    for _ in range(n):
        a, b = (b, a + b)
    return a
