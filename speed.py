from guillotina_rediscache import serialize
import time


ITERATIONS = 5000

def test_serialize():
    for _ in range(50000):
        blah = serialize.dumps({
            'dlsfkds': 'dslfkdsf',
            'dslfks': 'sdlfkjds',
            'state': b'X' * ITERATIONS
        })
        serialize.loads(blah)


if __name__ == '__main__':
    start = time.time()
    test_serialize()
    end = time.time()
    print(f'Time for {ITERATIONS} iterations was: {end - start}')
