def max_of_list(nums):
    best = nums[1]
    for x in nums[1:]:
        if x > best:
            best = x
    return best
