#!/usr/bin/env python
from stat import S_ISREG, ST_CTIME, ST_MODE, ST_SIZE
import os
import time
import bisect
import logging
import config

fileutil_logger = logging.getLogger('FileUtilities')


def list_files(dir_path):
    # get all entries in the directory w/ stats
    entries = (os.path.join(dir_path, fn) for fn in os.listdir(dir_path))
    entries = ((os.stat(path), path) for path in entries)

    # leave only regular files, insert creation date
    entries = ({'ctime': stat[ST_CTIME], 'path': path, 'size': stat[ST_SIZE]} for stat, path in entries if S_ISREG(stat[ST_MODE]))

    return sorted(entries)


def remove_oldest_files(dir_path, size_limit, size_after):
    def partial_sums(iterable):
        total = 0
        for i in iterable:
            total += i
            yield total

    files = list_files(dir_path)
    if len(files):
        cumulative_size = list(partial_sums((f['size'] for f in files)))
        if cumulative_size[-1] > size_limit > size_after:
            overflow_bytes = cumulative_size[-1] - size_after
            fileutil_logger.info('overflowing by %u b' % overflow_bytes)
            file_ind = bisect.bisect_left(cumulative_size, overflow_bytes)
            if file_ind < len(files):
                fileutil_logger.info('partial sum found at index %u value %u' % (file_ind, cumulative_size[file_ind]))
                for f in files[:file_ind+1]:
                    fileutil_logger.info('deleting %s' % f['path'])
                    try:
                        os.remove(f['path'])
                    except OSError:
                        fileutil_logger.error('failed to delete %s' % (f['path']))
                        pass
        else:
            fileutil_logger.error('dir %s not overflowing, current size %u kB, limit %u kB' % (dir_path, cumulative_size[-1] / 1024, size_limit / 1024))


if __name__ == "__main__":
    target_path = os.path.join('..', 'testing', 'test_data2')
    files = list_files(target_path)

    for f in files:
        fileutil_logger.info('%20s %10s %20s' % (time.ctime(f['ctime']), f['size'], os.path.basename((f['path']))))

    remove_oldest_files(target_path, 60*1024*1024, 50*1024*1024)
