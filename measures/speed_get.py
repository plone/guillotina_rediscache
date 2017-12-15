from guillotina.content import create_content_in_container
from guillotina.transactions import get_tm
from guillotina.transactions import get_transaction
from guillotina.utils import get_current_request

import time
import uuid


ITERATIONS = 100

# ----------------------------------------------------
# Measure performance of retrieval from cache
#
# Lessons:
# ----------------------------------------------------


async def run_get(container):
    request = get_current_request()
    txn = get_transaction(request)
    tm = get_tm(request)
    id_ = uuid.uuid4().hex
    await create_content_in_container(container, 'Item', id_)
    await tm.commit(txn=txn)
    await tm.begin(request=request)
    print(f'Test content get')
    start = time.time()
    for _ in range(ITERATIONS):
        await container.async_get(id_)
    end = time.time()
    print(f'Done with {ITERATIONS} in {end - start} seconds')


async def run(container):
    await run_get(container)
