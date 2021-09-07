#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Union, List

import decimal
import logging
import pprint
import requests
import urllib.parse

from chain.source import ChainSource
from chain.utxo import UTXO

log = logging.getLogger(__name__)


class ChainzExplorer(ChainSource):
    """chainz.cryptoid.info explorer API connector"""

    BASE_URL = "https://chainz.cryptoid.info/"

    def __init__(self, api_key: str = None):
        self.api_key = api_key

    def get_block_count(self, ticker: str) -> int:
        """Requests the current block height for a specific chain

        Example url:
            https://chainz.cryptoid.info/ltc/api.dws?q=getblockcount

        :param ticker: coin ticker symbol
        :return: block chain height
        """
        url = urllib.parse.urljoin(self.__class__.BASE_URL, f"{ticker.lower()}/api.dws")

        params = {
            "q": "getblockcount",
        }

        r = requests.get(url, params=params)
        r.raise_for_status()
        return int(r.json())

    def get_utxos(self, ticker: str, addresses: Union[set, list, tuple]) -> List[UTXO]:
        """Requests unspent outputs (UTXO) for a set of addresses

        Note: Requires an API key!

        Example url:
            https://chainz.cryptoid.info/ltc/api.dws?q=unspent&active=LLy8ng99pvzEFVR9EjukUfE7VcYwLN6thE&key=XXX

        :param ticker: coin ticker symbol
        :param addresses: set of wallet addresses
        :return: list of unspent outputs (UTXO)
        """
        url = urllib.parse.urljoin(self.__class__.BASE_URL, f"{ticker.lower()}/api.dws")

        assert self.api_key is not None

        active = ""
        for address in set(addresses):
            active += f"{address}|"
        active = active.rstrip("|")

        params = {
            "q": "unspent",
            "active": active,
            "key": self.api_key,
        }

        block_count = self.get_block_count(ticker)
        r = requests.get(url, params=params)
        r.raise_for_status()
        result = r.json()
        log.debug(pprint.pformat(result))

        utxos = list()
        for entry in result["unspent_outputs"]:
            utxos.append(UTXO(
                txid=entry["tx_hash"],
                vout=int(entry["tx_ouput_n"]),
                value=decimal.Decimal(entry["value"]) / decimal.Decimal("100000000"),
                address=entry["addr"],
                block=block_count - int(entry["confirmations"]),
            ))

        return utxos
