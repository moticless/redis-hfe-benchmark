# Redis HFE Benchmark

This repository contains the benchmark code used to evaluate the new Hash Field Expiration (HFE) feature introduced in 
Redis Community Edition and Stack 7.4. This benchmark compares Redis with KeyDB by Alibaba and TairHash by Snap, 
focusing on memory usage and performance in various scenarios.

## Overview

The HFE feature in Redis allows for efficient expiration management at the field level within a hash, optimizing 
performance and minimizing memory usage. The blog post associated with this repository delves into the technical 
implementation of HFE and presents benchmark results demonstrating Redis's superior performance and lower memory 
consumption compared to KeyDB of Snap and TairHash of Alibaba.

## Blog Post
For a detailed explanation of the HFE feature and benchmark results, please refer to the 
[accompanying blog post](https://redis.io/blog/hash-field-expiration-architecture-and-benchmarks/).

## Usage

To run the benchmark, use the following command structure:

```bash
# Select SERVER: redis | keydb | tairhash | redis-expire
export CLI=/path/to/cli-of-server
SERVER=redis
python3 benchmark.py <NUM_ITEMS> <SINGLE_HASH> $SERVER <EXPIRE_SEC> <MULTI_CLIENTS> <ALL_SPECIFIC_TIME>
```
Arguments:
- `<NUM_ITEMS>`: Number of keys/fields to be used in the benchmark.
- `<SINGLE_HASH>`: 
  - `0`: Use `<NUM_ITEMS>` hashes, each with a single field.
  - `1`: Use a single hash containing `<NUM_ITEMS>` fields.
- `<redis|keydb|tairhash>`: Server to test
- `<EXPIRE_SEC>`: Expiry time in seconds.
- `<MULTI_CLIENTS>`: 
  - `0`: Use a single client.
  - `1`: Use multiple clients.
- `<ALL_SPECIFIC_TIME>`: 
  - `0`: Expire keys/fields after a relative time interval (delta expiry)
  - `1`: All keys/fields expire at a specific fixed time (absolute time)


## Benchmark Scenarios

This script runs multiple benchmark scenarios, including:

1. **Single hash, 10 million fields with distant expiry**
2. **Single hash, 10 million fields with 3-second expiry**
3. **Single hash, 10 million fields with distant expiry using memtier with multiple threads and clients**
4. **Single hash, 10 million fields all expiring at a specific distant time**
5. **10 million hashes, each with a single field and distant expiry**
6. **10 million hashes, each with a single field and 3-second expiry**
7. **10 million hashes all expiring at a specific distant time**

```bash
# Select SERVER: redis | keydb | tairhash | redis-expire
SERVER=redis
echo "1. Single hash, 10 million fields with distant expiry"
python3 ./benchmark.py 10000000 1 $SERVER 10000 0 0
echo "2. Single hash, 10 million fields with 3sec expiry"
python3 ./benchmark.py 10000000 1 $SERVER 3 0 0
echo "3. Single hash, 10 million fields with distant expiry (memtier: -t 2 -c 5)"
python3 ./benchmark.py 10000000 1 $SERVER 10000 1 0
echo "4. Single hash, 10 million fields. All expired at distant specific time"
python3 ./benchmark.py 10000000 1 $SERVER 10000 0 1
echo "5. 10 million hashes, single field with distant expiry"
python3 ./benchmark.py 10000000 0 $SERVER 10000 0 0
echo "6. 10 million hashes, single field with 3SEC expiry"
python3 ./benchmark.py 10000000 0 $SERVER 3 0 0
echo "7. 10 million hashes, all expired at distant specific time"
python3 ./benchmark.py 10000000 0 $SERVER 10000 0 1
```

Output is in the form:
```bash
1. Single hash, 10 million fields with distant expiry
Hsets : 664589
mem :719.52M
Hexpires : 512863
mem :830.49M
Httls : 791543
2. Single hash, 10 million fields with 3sec expiry
Hsets : 665694
mem :719.52M
Hexpires : 516114
...
```
