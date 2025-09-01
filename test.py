import random
import statistics
from typing import List, Tuple

def generate_random_numbers(count: int = 10, start: int = 0, end: int = 100) -> List[int]:
    """Generate a list of random integers with enhanced randomness.

    This function uses multiple entropy sources and varied methods to produce
    numbers: system random, time-based jitter, shuffled ranges, and mixing
    different RNG algorithms. It attempts to reduce patterns by combining
    outputs from several generators and applying nonlinear transformations.

    Args:
        count (int): Number of random integers to generate.
        start (int): Lower bound (inclusive).
        end (int): Upper bound (inclusive).

    Returns:
        list[int]: List of random integers.
    """
    if count <= 0:
        return []

    span = max(1, end - start + 1)

    pool = []

    # 1) system random samples
    sysrand = random.SystemRandom()
    for _ in range(max(count // 2, 1)):
        pool.append(sysrand.randrange(start, end + 1))

    # 2) Mersenne-Twister pseudorandom samples
    mt = [random.randrange(start, end + 1) for _ in range(max(count // 3, 1))]
    pool.extend(mt)

    # 3) shuffled sequence fragments
    seq = list(range(start, end + 1))
    sysrand.shuffle(seq)
    pool.extend(seq[:max(count // 4, 1)])

    # 4) time-based jitter and bit-mixing
    import time, hashlib

    for i in range(max(count // 4, 1)):
        t = time.time_ns() ^ (i * 0x9e3779b97f4a7c15)
        h = hashlib.sha256(str(t).encode() + str(sysrand.randrange(1, 1 << 30)).encode()).digest()
        val = int.from_bytes(h[:8], "little")
        pool.append(start + (abs(val) % span))

    # 5) combine and nonlinear transform
    mixed = []
    for i, v in enumerate(pool):
        a = v
        b = pool[-1 - (i % len(pool))]
        x = (a ^ b) + (i * 2654435761)
        x = (x * 6364136223846793005) & ((1 << 64) - 1)
        mixed.append(start + (abs(x) % span))

    # 6) final reservoir-like selection to ensure count and reduce bias
    result = []
    for i, v in enumerate(mixed):
        if len(result) < count:
            result.append(v)
        else:
            j = random.randrange(0, i + 1)
            if j < count:
                result[j] = v

    # 7) ensure full coverage and extra shuffle for unpredictability
    while len(result) < count:
        result.append(start + random.randrange(0, span))

    random.shuffle(result)

    return result

def analyze_numbers(nums: List[int]) -> Tuple[float, float, int, int]:
    if not nums:
        raise ValueError("nums must not be empty")
    return statistics.mean(nums), statistics.median(nums), min(nums), max(nums)

def generate_and_analyze(count: int = 10, start: int = 0, end: int = 100):
    nums = generate_random_numbers(count, start, end)
    nums_sorted = sorted(nums)
    mean, median, minimum, maximum = analyze_numbers(nums_sorted)
    return nums_sorted, mean, median, minimum, maximum

def print_random_stuff(count: int = 5, start: int = 0, end: int = 100) -> None:
    nums = generate_random_numbers(count, start, end)
    nums_sorted = sorted(nums)
    mean, median, minimum, maximum = analyze_numbers(nums_sorted)

    print("Random numbers:", nums_sorted)
    print(f"Mean: {mean:.2f}, Median: {median}, Min: {minimum}, Max: {maximum}")

if __name__ == "__main__":
    nums, mean, median, minimum, maximum = generate_and_analyze(15, 1, 50)
    print("Generated (sorted):", nums)
    print(f"Mean: {mean:.2f}, Median: {median}, Min: {minimum}, Max: {maximum}")
