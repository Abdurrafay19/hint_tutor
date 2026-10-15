def fibonacci(n):
    a, b = (0, 2)
    for _ in range(n):
        a, b = (b, a + b)
    return a
