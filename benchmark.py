import re
import timeit

def with_re_compile():
    time_regex = re.compile(r"time=(\d{2}:\d{2}:\d{2}\.\d+)")
    out_time_ms_regex = re.compile(r"out_time_ms=(\d+)")
    lines = [
        "frame= 1234 fps= 30 q=28.0 size= 2048kB time=00:00:41.13 bitrate= 408.0kbits/s speed=1.13x",
        "out_time_ms=41130000",
        "nothing to see here"
    ] * 1000
    for line in lines:
        match = time_regex.search(line) or out_time_ms_regex.search(line)

def without_re_compile():
    lines = [
        "frame= 1234 fps= 30 q=28.0 size= 2048kB time=00:00:41.13 bitrate= 408.0kbits/s speed=1.13x",
        "out_time_ms=41130000",
        "nothing to see here"
    ] * 1000
    for line in lines:
        match = re.search(r"time=(\d{2}:\d{2}:\d{2}\.\d+)", line) or re.search(r"out_time_ms=(\d+)", line)

t1 = timeit.timeit(without_re_compile, number=1000)
print(f"Without pre-compile: {t1:.4f} seconds")

t2 = timeit.timeit(with_re_compile, number=1000)
print(f"With pre-compile: {t2:.4f} seconds")
print(f"Improvement: {(t1-t2)/t1*100:.2f}%")
