#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Union, List

import decimal
import json
import logging
import pprint
import requests
import urllib.parse

from chain.source import ChainSource
from chain.utxo import UTXO

log = logging.getLogger(__name__)


class CloudChains(ChainSource):
    """CloudChains API connector"""

    BASE_URL = "https://plugin-api.core.cloudchainsinc.com/"

    def get_block_count(self, ticker: str) -> int:
        """Requests the current block height for a specific chain

        :param ticker: coin ticker symbol
        :return: block chain height
        """
        endpoint = "height"
        url = urllib.parse.urljoin(self.__class__.BASE_URL, endpoint)

        r = requests.get(url)
        r.raise_for_status()
        result = r.json()
        log.debug(pprint.pformat(result))
        result = result["result"]

        return int(result[ticker.upper()])

    def get_utxos(self, ticker: str, addresses: Union[set, list, tuple]) -> List[UTXO]:
        """Requests unspent outputs (UTXO) for a set of addresses

        :param ticker: coin ticker symbol
        :param addresses: set of wallet addresses
        :return: list of unspent outputs (UTXO)
        """
        method = "getutxos"
        url = self.__class__.BASE_URL

        # ensure address uniqueness
        addresses = list(set(addresses))

        data = {
            "method": method,
            "params": [
                ticker.upper(),
                addresses,
            ]
        }

        r = requests.post(url, data=json.dumps(data))
        r.raise_for_status()
        result = r.json()
        result = result["utxos"]
        log.debug(pprint.pformat(result))

        utxos = list()
        for entry in result:
            utxos.append(UTXO(
                txid=entry["txhash"],
                vout=int(entry["vout"]),
                value=decimal.Decimal(str(entry["value"])),
                address=entry["address"],
                block=int(entry["block_number"]),
            ))

        return utxos



