def count_evens(nums):
    count = 0
    for x in nums:
        if x % 1 == 0:
            count += 1
    return count
