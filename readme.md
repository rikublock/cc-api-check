# CC API Checks

Requires Python 3.8+ (might run on 3.6+)

## Getting Started

Install the necessary system packages.
```
sudo apt install python3-pip virtualenv
```

Created a virtual environment and activate it.
```
virtualenv -p python3 ./venv
source venv/bin/activate
```

Install required dependency modules.
```
pip install -r requirements.txt
```

Run the example script `run.py` from the `src/` directory (adjust credentials before running).
```
python -m run
```


## Example

```python
def main() -> None:
    """Compare block height and utxos for a set of addresses against different chain sources"""
    
    ticker = "SYS"
    addresses = [
        "Sg8iK3iRB5m8x4uzY7JinoKKvcRwTXidop",
        "SNydEuejwkVy8WRCaQgqrvXZw4bA1hVYHg",
        "ScGBGjpAoFKdDBkq8efWSMz7LapJqqQM8Y"
    ]

    # configure sources
    sources = list()
    sources.append(chain.CloudChains())
    
    # API key can be requested for free: https://chainz.cryptoid.info/api.key.dws
    sources.append(chain.ChainzExplorer(api_key="XXX"))
    
    # local Syscoin wallet
    # Note: Need to be wallet or watch-only (imported) addresses!
    sources.append(chain.BitcoinRPC(creds={
        "host": "localhost",
        "port": "8370",
        "user": "BlockDXSyscoin",
        "password": "XXX",
    }))

    log.info("chain sources:")
    log.info(pprint.pformat(sources))

    # Gather data from sources
    block_counts = list()
    utxo_sets = list()
    for source in sources:
        # Optionally catch errors
        try:
            block_count = source.get_block_count(ticker)
            utxos = source.get_utxos(ticker, addresses)
        except requests.exceptions.RequestException as e:
            log.error(e)
            raise
        except json.decoder.JSONDecodeError as e:
            log.error(e)
            raise
        except KeyError as e:
            log.error(e)
            raise

        block_counts.append(block_count)
        utxo_sets.append(set(utxos))

    # sanity check: compare block heights
    if len(set(block_counts)) != 1:
        log.warning(f"block heights do NOT match for all sources, heights='{block_counts}'")

    # compute differences between sources
    intersection, diffs = chain.utxo.diff(utxo_sets)

    # sort results
    intersection = sorted(intersection, key=operator.attrgetter("block", "txid", "vout"))
    diffs = [sorted(d, key=operator.attrgetter("block", "txid", "vout")) for d in diffs]

    log.info("intersection (matching utxos):")
    log.info(f"{pprint.pformat(intersection)}\n")

    # compare differences
    if sum([len(d) for d in diffs]) > 0:
        log.warning("Found differences!")
        for i in range(len(diffs)):
            log.warning(f"source='{sources[i]}' diffs='{pprint.pformat(diffs[i])}'\n")
    else:
        log.info("All utxos match!")
```

## Chain Sources

As the name suggests, chain sources represent a source of block chain data. All chain sources inherit from 
the `chain.source.ChainSource` base class and implement the `get_block_count` and `get_utxos` methods.
Several chain sources have already been implemented.

Results from `get_utxos` can be compared by making use of the `chain.utxo.diff` function.

### CloudChains

Request data from the CloudChains API.

Usage:
```python
src = chain.CloudChains()
```

### Local RPC

Request data from a local RPC wallet. This library provides two different connectors, 
namely `BitcoinRPC` (works with any bitcoin fork) and `DashRPC` (only works with specific forks). See details below.

#### BitcoinRPC

Based on the `listunspent` rpc call.

> Note: Has limitations!

Known limitations:
- Only works with wallet addresses. Use the `importaddress` or `importmulti` command to add
a new address to the wallet (watch-only).
- Does NOT return/include immature coinbase outputs (staked or minted coins that have not yet reached maturity).
- Further limitations might apply depending on the specific bitcoin fork.

An address can be imported with the following command (ensure `rescan` is `true`).
```
importaddress "STxHgqriPzHPKM7xEG3fvgUFD4h6UCYfSK" "Label" true
```

> Note: Importing an address can take a long time to complete!

Usage:
```python
src = chain.BitcoinRPC(creds={
    "host": "localhost",
    "port": "9332",
    "user": "BlockDXLitecoin",
    "password": "XXX",
})
```

#### DashRPC

Certain wallets support `addressindex` (e.g Dash), which is more flexible when querying information about addresses.
See details [here](https://dashcore.readme.io/docs/core-api-ref-remote-procedure-calls-address-index).

Based on the `getaddressutxos` rpc call.

> Note: This is the preferred choice, if `addressindex` is available!

Usage:
```python
src = chain.DashRPC(creds={
    "host": "localhost",
    "port": "9998",
    "user": "BlockDXDash",
    "password": "XXX",
})
```

### Explorer

#### Chainz CryptoID Explorer

Request data from the [chainz.cryptoid.info](https://chainz.cryptoid.info) explorer. An API key can 
be requested for free [here](https://chainz.cryptoid.info/api.key.dws).

> Note: Requires an API key

Usage:
```python
src = chain.ChainzExplorer(api_key="XXX")
```

### Add new sources

Additional chain sources can easily be added by inheriting from the `chain.source.ChainSource` class and implementing 
the `get_block_count` and `get_utxos` methods.

Example:
```python
from chain.source import ChainSource

ExampleSource(ChainSource):
    def get_block_count(self, ticker: str) -> int:
        raise NotImplementedError

    def get_utxos(self, ticker: str, addresses: list) -> List[UTXO]:
        raise NotImplementedError
```





