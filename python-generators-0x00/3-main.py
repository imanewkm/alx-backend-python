#!/usr/bin/python3
import sys
lazy_paginator = __import__('2-lazy_paginate')


try:
    for page in lazy_paginator.lazypaginate(100):
        for user in page:
            print(user)

except BrokenPipeError:
    sys.stderr.close()