def max_of_list(nums):
    best = 0
    for x in nums:
        if x > best:
            best = x
    return best
