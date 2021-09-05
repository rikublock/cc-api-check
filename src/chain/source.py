#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Union, List

from chain.utxo import UTXO


class ChainSource(object):
    def get_block_count(self, ticker: str) -> int:
        """Requests the current block height for a specific chain

        :param ticker: coin ticker symbol
        :return: block chain height
        """
        raise NotImplementedError

    def get_utxos(self, ticker: str, addresses: Union[set, list, tuple]) -> List[UTXO]:
        """Requests unspent outputs (UTXO) for a set of addresses

        :param ticker: coin ticker symbol
        :param addresses: set of wallet addresses
        :return: list of unspent outputs (UTXO)
        """
        raise NotImplementedError



