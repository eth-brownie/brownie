import os
import time
import threading
from brownie import network
from queue import Queue, Empty
from brownie.network.rpc import hardhat
from brownie.network.rpc import ganache
import re
import psutil
import threading
from brownie.utils import color

def close_unused_file_descriptors(skip_fd=None):
    process = psutil.Process()
    for fd in process.open_files():
        try:
            if fd.fd != skip_fd:
                os.close(fd.fd)
        except OSError as e:
            print(f"Error closing file descriptor {fd.fd}: {e}")

class LogReader(threading.Thread):
    def __init__(self, process_stdout, nlines, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.process_stdout = process_stdout
        self.logs = []
        self.nlines = nlines
        self._stop_event = threading.Event()

    def enqueue_output(self, out, queue):
        try:
            for line in iter(out.readline, b''):
                queue.put(line)
        except OSError as e:
            print(f"Error reading from file descriptor: {e}")
        finally:
            try:
                out.close()
            except OSError as e:
                pass

    def run(self):
        q = Queue()
        t = threading.Thread(target=self.enqueue_output, args=(self.process_stdout, q))
        t.daemon = True
        t.start()

        if network.show_active() == 'mainnet-fork' or network.show_active() == 'development':
            pattern = re.compile(r"eth_call")
            pattern2 = re.compile(r"eth_sendTransaction")
        elif network.show_active() == 'hardhat-fork':
            pattern = re.compile(r"console\.log:")
            pattern2 = None

        print_next_lines = 0
        num_lines = self.nlines

        blacklist=['eth_call','eth_getBlockByNumber', 'Transaction:', 'eth_getTransactionCount', 
        'eth_getTransactionCount', 'eth_gasPrice', 'eth_chainId' , 'Block number', 
        'Gas usage:', 'Block time:', 'Contract created', 'eth_getTransactionByHash',
        'eth_getCode', 'eth_getTransactionReceipt', 'eth_sendTransaction', 'evm_snapshot',
        'Saved snapshot', 'eth_blockNumber', 'evm_increaseTime', 'eth_accounts', 'web3_clientVersion',
        'evm_addAccount', 'personal_unlockAccount','evm_setAccountBalance', 'Contract call:']

        print(color("yellow"),'\r',"Potential Console.log:",color("normal"))
        while not self._stop_event.is_set():
            try:
                line = q.get(timeout=0.3).strip().encode('utf-8').strip()
            except Empty:
                pass

            else:
                if print_next_lines > 0:
                    if any(re.search(pat, line.decode('utf-8')) for pat in blacklist):
                        pass
    
                    else:
                        if line.decode('utf-8').strip():
                            print(color("red"),'\r',line.decode('utf-8'),color("normal"))
                            print_next_lines -= 1

                elif pattern.search(line.decode('utf-8')):
                    print_next_lines = num_lines

                elif pattern2 != None:
                    if pattern2.search(line.decode('utf-8')):
                        print_next_lines = num_lines

    def stop(self):
        self._stop_event.set()

    def is_running(self):
        return not self._stop_event.is_set()

#getConsoleLog, accepts nlines to be prited and *kwargs {'duration': uint}
def getConsoleLog(*args, **kwargs):
    global log_reader    
    if args == ():
        nlines = 2
    else: 
        nlines = args[0]

    if kwargs == {}:
        duration=5
    else: 
        duration = kwargs['duration']
    
    # Create new process_stdout instance
    if network.show_active() == 'mainnet-fork' or network.show_active() == 'development':
        process_stdout = open(ganache.out_read, 'rt', buffering=1)
    elif network.show_active() == 'hardhat-fork':
        process_stdout = open(hardhat.out_read, 'rt', buffering=1)

    # Create and start new LogReader thread
    log_reader = LogReader(process_stdout, nlines)
    log_reader.start()

    time.sleep(duration)

    # Stop and join LogReader thread
    log_reader.stop()
    log_reader.join()

    print("Logs captured:")
    for log in log_reader.logs:
        print(log)

    close_unused_file_descriptors()
    # Set log_reader to None to enable re-calling this function
    log_reader = None

def log(*args, **kwargs):
    if args == () and kwargs == {}:
        logger_thread = threading.Thread(target=getConsoleLog, args=[5], kwargs={'duration':7},daemon=True)
    else:
        if args == ():
            nline = 5
        else:
            nline = args[0]

        if args  == {}:
            duration=5

        else:
            if 'duration' in kwargs:
                duration = kwargs['duration']

            else:
                kwargs = {'duration': 7}
                duration = kwargs['duration']

        logger_thread = threading.Thread(target=getConsoleLog, args=[nline], kwargs={'duration':duration},daemon=True)
        logger_thread.start()
    return logger_thread
