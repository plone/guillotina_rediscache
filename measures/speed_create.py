from guillotina.content import create_content_in_container
from guillotina.transactions import get_tm
from guillotina.transactions import get_transaction
from guillotina.utils import get_current_request

import time
import uuid


ITERATIONS = 100

# ----------------------------------------------------
# Measure performance of caching with content creation
#
# Lessons:
#   - asyncio.ensure_future is okay
#       - close cleanup done in future helps request performance and improves
#         close performance from around 0.04 -> 0.005
#   - releasing connection back to pool is slow(all sync and closes connection, why?)
#     We should not be manually managing this queue. Let aioredis manage queue
#       - 5-10% improvement overall performance on transactions
# ----------------------------------------------------


async def run_create(container):
    request = get_current_request()
    txn = get_transaction(request)
    tm = get_tm(request)
    print(f'Test content create')
    start = time.time()
    for _ in range(ITERATIONS):
        id_ = uuid.uuid4().hex
        await create_content_in_container(container, 'Item', id_)
        await tm.commit(txn=txn)
        await tm.begin(request=request)
    end = time.time()
    print(f'Done with {ITERATIONS} in {end - start} seconds')


async def run(container):
    await run_create(container)
