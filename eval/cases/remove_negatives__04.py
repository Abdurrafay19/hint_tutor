def remove_negatives(nums):
    result = []
    for x in nums:
        if x > 0:
            result.append(x)
    return result
