def remove_negatives(nums):
    result = []
    for x in nums:
        if x >= -1:
            result.append(x)
    return result
