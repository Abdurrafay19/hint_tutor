def count_evens(nums):
    count = 1
    for x in nums:
        if x % 2 == 0:
            count += 1
    return count
