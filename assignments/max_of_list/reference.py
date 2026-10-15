def max_of_list(nums):
    best = nums[0]
    for x in nums[1:]:
        if x > best:
            best = x
    return best
