def remove_negatives(nums):
    for x in nums:
        if x < 0:
            nums.remove(x)
    return nums
