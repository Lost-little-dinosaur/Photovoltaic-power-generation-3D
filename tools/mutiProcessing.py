import multiprocessing

cpuCount = multiprocessing.cpu_count()


def chunk_it(seq, num):
    avg, out, last = len(seq) / float(num), [], 0.0
    while last < len(seq):
        out.append(seq[int(last):int(last + avg)])
        last += avg
    return out
