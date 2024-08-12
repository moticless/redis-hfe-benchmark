# This script is used to run the HFE benchmark:
#
#    # Select SERVER: redis | keydb | tairhash | redis-expire
#    SERVER=redis
#    echo "1. Single hash, 10 million fields with distant expiry"
#    python3 ./benchmark.py 10000000 1 $SERVER 10000 0 0
#
#    echo "2. Single hash, 10 million fields with 3sec expiry"
#    python3 ./benchmark.py 10000000 1 $SERVER 3 0 0
#
#    echo "3. Single hash, 10 million fields with distant expiry (memtier: -t 2 -c 5)"
#    python3 ./benchmark.py 10000000 1 $SERVER 10000 1 0
#
#    echo "4. Single hash, 10 million fields. All expired at distant specific time"
#    python3 ./benchmark.py 10000000 1 $SERVER 10000 0 1
#
#    echo "5. 10 million hashes, single field with distant expiry"
#    python3 ./benchmark.py 10000000 0 $SERVER 10000 0 0
#
#    echo "6. 10 million hashes, single field with 3SEC expiry"
#    python3 ./benchmark.py 10000000 0 $SERVER 3 0 0
#
#    echo "7. 10 million hashes, all expired at distant specific time"
#    python3 ./benchmark.py 10000000 0 $SERVER 10000 0 1

PORT="6379"
HOST="127.0.0.1"
CLIENTS=1
THREADS=1

import os
import time
import subprocess
import sys
import random
import string

def print_usage():
    print("""
Usage: python3 benchmark2.py <NUM_ITEMS> <SINGLE_HASH> <redis|keydb|tairhash> <EXPIRE_SEC> <MULTI_CLIENTS> <ALL_SPECIFIC_TIME>

Arguments:
  <NUM_ITEMS>            : Number of keys/fields to be used in the benchmark
  <SINGLE_HASH>          : 1 to use a single hash with <NUM_ITEMS> fields, 0 to use <NUM_ITEMS> hashes with a single field each
  <redis|keydb|tairhash> : Tested server (another option is 'redis-expire' as a reference to the Redis EXPIRE command)
  <EXPIRE_SEC>           : Expiry time in seconds
  <MULTI_CLIENTS>        : 1 to use multiple clients, 0 to use a single client
  <ALL_SPECIFIC_TIME>    : 0 for regular expiry
                          1 for all keys to expire at the same specific time

 (Take care also to export env-var CLI to the path of the redis-cli or keydb-cli)
""")

def run_command(command):
    #print(command)
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    parse_output(result.stdout.strip())

def parse_output(output):
    lines = output.split('\n')
    separator = "----------------------------------------------------------------"
    capture = False
    capture_next_lines = 0
    for line in lines:
        if 'used_memory_human' in line:
            print(line.replace('used_memory_human', 'mem ').strip())
        if capture:
            if capture_next_lines > 0:
                if 'Totals' not in line:
                    words = line.strip().split()
                    second_word = int(float(words[1]))
                    print(words[0],":", second_word)
                capture_next_lines -= 1
        if separator in line:
            capture = True
            capture_next_lines = 2  # Capture the next two lines

if len(sys.argv) != 7:
    print_usage()
    sys.exit(1)
NUM_ITEMS = int(sys.argv[1])
SINGLE_HASH = int(sys.argv[2])
SELECTED_SERVER = sys.argv[3]
EXPIRE_SEC = int(sys.argv[4])
MULTI_CLIENTS = int(sys.argv[5])
ALL_SPECIFIC_TIME = int(sys.argv[6])

CLI = os.getenv('CLI')
if not CLI:
    print("Error: CLI environment variable is not defined.")
    sys.exit(1)
else:
    CLI = CLI.strip()

if ALL_SPECIFIC_TIME == 1:
    EXPIRE_SEC_AT = int(time.time()) + EXPIRE_SEC
    print(f">>> EXPIRE_SEC_AT={EXPIRE_SEC_AT}")

if MULTI_CLIENTS == 1:
    CLIENTS=5
    THREADS=2

if SINGLE_HASH == 1:
    KEY = "myhash"
    FIELD="__key__"
else:
    KEY="__key__"
    FIELD= ''.join(random.choice(string.ascii_letters) for _ in range(8))

################ PREPARE COMMANDS FOR KEYDB
if SELECTED_SERVER == "keydb":
    HSET_CMD = f"HSET {KEY} {FIELD} __data__"
    if ALL_SPECIFIC_TIME == 1:
        EXPIRE_CMD = f"EXPIREMEMBERAT {KEY} {FIELD} {EXPIRE_SEC_AT}"
    else:
        EXPIRE_CMD = f"EXPIREMEMBER {KEY} {FIELD} {EXPIRE_SEC}"
    GET_TTL_CMD = f"TTL {KEY} {FIELD}"
    HDEL_CMD = f"HDEL {KEY} {FIELD}"

################ PREPARE COMMANDS FOR TAIRHASH
elif SELECTED_SERVER == "tairhash":
    HSET_CMD = f"EXHSET {KEY} {FIELD} __data__"
    if ALL_SPECIFIC_TIME == 1:
        EXPIRE_CMD = f"EXHPEXPIREAT {KEY} {FIELD} {EXPIRE_SEC_AT * 1000}"
    else:
        EXPIRE_CMD = f"EXHPEXPIRE {KEY} {FIELD} {EXPIRE_SEC * 1000}"
    GET_TTL_CMD = f"EXHTTL {KEY} {FIELD}"
    HDEL_CMD = f"EXHDEL {KEY} {FIELD}"

################ PREPARE COMMANDS FOR REDIS-EXPIRE
elif SELECTED_SERVER == "redis-expire":
    HSET_CMD = f"HSET {KEY} {FIELD} __data__"
    if ALL_SPECIFIC_TIME == 1:
        EXPIRE_CMD = f"EXPIREAT {KEY} {EXPIRE_SEC_AT}"
    else:
        EXPIRE_CMD = f"EXPIRE {KEY} {EXPIRE_SEC}"
    GET_TTL_CMD = f"TTL {KEY}"
    HDEL_CMD = f"HDEL {KEY} {FIELD}"

################ PREPARE COMMANDS FOR REDIS
else:
    HSET_CMD = f"HSET {KEY} {FIELD} __data__"
    if ALL_SPECIFIC_TIME == 1:
        EXPIRE_CMD = f"HEXPIREAT {KEY} {EXPIRE_SEC_AT} FIELDS 1 {FIELD}"
    else:
        EXPIRE_CMD = f"HEXPIRE {KEY} {EXPIRE_SEC} FIELDS 1 {FIELD}"
    GET_TTL_CMD = f"HTTL {KEY} FIELDS 1 {FIELD}"
    HDEL_CMD = f"HDEL {KEY} {FIELD}"

################ Start Benchmark ################
# Flush DB
run_command(f"{CLI} -p {PORT}  -h {HOST} FLUSHALL")
# Fillup DB with hash-fields
run_command(f"memtier_benchmark --port {PORT} --host {HOST} --data-size 1 --command='{HSET_CMD}' --command-key-pattern=P -c {CLIENTS} -t {THREADS} --pipeline 200 --hide-histogram --key-maximum {NUM_ITEMS} -n allkeys 2>&1")
# Check memory usage
run_command(f"{CLI} -p {PORT} -h {HOST} info | grep used_memory_human")
# Set expiration on hash-fields
run_command(f"memtier_benchmark --port {PORT} --host {HOST} --command='{EXPIRE_CMD}' --command-key-pattern=P -c {CLIENTS} -t {THREADS} --pipeline 200 --hide-histogram --key-maximum {NUM_ITEMS} -n allkeys 2>&1")
# Check memory usage again
run_command(f"{CLI} -p {PORT} -h {HOST} info | grep used_memory_human")
# If not going to expire soon, check TTL of hash-fields
if EXPIRE_SEC > 100:
    run_command(f"memtier_benchmark --port {PORT} --host {HOST} --command='{GET_TTL_CMD}' --command-key-pattern=P -c {CLIENTS} -t {THREADS} --pipeline 200 --hide-histogram --key-maximum {NUM_ITEMS} -n allkeys 2>&1")