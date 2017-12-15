from guillotina_rediscache import serialize

import time


ITERATIONS = 100000

# ----------------------------------------------------
# Measure performance of serializing data
#
# Lessons:
#   - pickle is MUCH faster than json
# ----------------------------------------------------


async def runit():
    print(f'Test content serialization')
    start = time.time()
    for _ in range(ITERATIONS):
        blah = serialize.dumps({
            'dlsfkds': 'dslfkdsf',
            'dslfks': 'sdlfkjds',
            'state': b'X' * ITERATIONS
        })
        serialize.loads(blah)
    end = time.time()
    print(f'Done with {ITERATIONS} in {end - start} seconds')


async def run():
    await runit()
