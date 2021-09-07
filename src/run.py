    #!/usr/bin/env python3
# -*- coding: utf-8 -*-

import decimal
import json
import logging
import pprint
import requests
import operator

import chain
import chain.utxo

log = logging.getLogger("CCAPICheck")


def main() -> None:
    """Compare block height and utxos for a set of addresses against different chain sources"""

    logging.basicConfig(level=logging.INFO)
    decimal.getcontext().rounding = decimal.ROUND_DOWN

    ticker = "SYS"
    addresses = ["Sg8iK3iRB5m8x4uzY7JinoKKvcRwTXidop", "SNydEuejwkVy8WRCaQgqrvXZw4bA1hVYHg", "ScGBGjpAoFKdDBkq8efWSMz7LapJqqQM8Y"]

    # configure sources
    sources = list()
    sources.append(chain.CloudChains())
    sources.append(chain.ChainzExplorer(api_key="XXX"))
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
            raise
        except json.decoder.JSONDecodeError as e:
            raise
        except KeyError as e:
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

    # compare sets
    if sum([len(d) for d in diffs]) > 0:
        log.warning("Found differences!")
        for i in range(len(diffs)):
            log.warning(f"source='{sources[i]}' diffs='{pprint.pformat(diffs[i])}'\n")
    else:
        log.info("All utxos match!")


if __name__ == "__main__":
    main()

