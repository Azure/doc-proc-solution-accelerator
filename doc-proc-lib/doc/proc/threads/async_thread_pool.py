from __future__ import annotations
from threading import Thread
import asyncio, time, typing
if typing.TYPE_CHECKING:
    from concurrent.futures import Future
    from asyncio import AbstractEventLoop

class AsyncThreadPool:
    """ Thread pool for running async future/coroutines """
    def __init__(self, workers:int=1):
        self.workers: int = workers
        """ Number of worker threads in the pool """
        self.threads: list[Thread] = []
        """ Running threads in the pool """
        self.loops: list[AbstractEventLoop] = []
        """ Event loops for each thread """
        self.roundrobin: int = 0
        """ Next thread to run something in, for round-robin scheduling """

        # initialize threads
        for i in range(workers):
            loop = asyncio.new_event_loop()
            self.loops.append(loop)
            thread = Thread(target=loop.run_forever)
            thread.start()
            self.threads.append(thread)

    def run(self, target: typing.Coroutine | typing.Future, worker: int|None=None) -> Future:
        """ Run async future/coroutine in the thread pool
        
            :param target: the future/coroutine to execute
            :param worker: worker thread you want to run the callable; None for round-robin
                selection of worker thread
            :return: future with result
        """
        if worker is None:
            worker = self.roundrobin
            self.roundrobin = (worker + 1) % self.workers
        return asyncio.run_coroutine_threadsafe(target, self.loops[worker])
    
    def join(self, timeout:float=.1):
        """ Blocking call to close the thread pool
        
            :param timeout: timeout for polling a thread to check if its async tasks are all finished
        """
        for i in range(self.workers):
            # wait for completion of pending tasks before stopping;
            # stop only waits for current batch of callbacks to complete
            loop = self.loops[i]
            while len(asyncio.all_tasks(loop)):
                time.sleep(timeout)
            loop.call_soon_threadsafe(loop.stop)
            self.threads[i].join()