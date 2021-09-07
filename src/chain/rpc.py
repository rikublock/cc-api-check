#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Union, List

import decimal
import logging
import pprint

from chain.source import ChainSource
from chain.source import UTXO
from util.authproxy import AuthServiceProxy

log = logging.getLogger(__name__)


class BitcoinRPC(ChainSource):
    """local RPC connector for core wallets forked from bitcoin"""

    def __init__(self, creds: dict) -> None:
        self._creds = dict(creds)
        self._service_url = "http://{user}:{password}@{host}:{port}".format(**self._creds)
        self._proxy = AuthServiceProxy(self._service_url)

    def _call_command(self, cmd: list):
        return self._proxy.__getattr__(cmd[0])(*cmd[1:])

    def rpc_help(self, cmd: str = None) -> str:
        """List all commands, or get help for a specified command

        :return: rpc output
        """
        if cmd:
            return self._call_command(["help", cmd])
        return self._call_command(["help"])

    def rpc_getblockchaininfo(self) -> dict:
        """Returns an object containing various state info regarding blockchain processing

        :return: rpc output
        """
        return self._call_command(["getblockchaininfo"])

    def rpc_getblockcount(self) -> int:
        """Returns the height of the most-work fully-validated chain

        :return: rpc output
        """
        return self._call_command(["getblockcount"])

    def rpc_getaddressinfo(self, address: str) -> dict:
        """Return information about the given address

        :return: rpc output
        """
        return self._call_command(["getaddressinfo", address])

    def rpc_listunspent(self, min_conf: int = 1, max_conf: int = 99999999, addresses: list = []) -> list:
        """Returns array of unspent transaction outputs

        :param min_conf: minimum confirmations to filter
        :param max_conf: maximum confirmations to filter
        :param addresses: array of blocknet addresses to filter
        :return: rpc output
        """
        return self._call_command(["listunspent", min_conf, max_conf, addresses])

    def get_block_count(self, ticker: str) -> int:
        """Requests the current block height

        :param ticker: coin ticker symbol (ignored)
        :return: block chain height
        """
        result = self.rpc_getblockcount()
        return int(result)

    def get_utxos(self, ticker: str, addresses: Union[set, list, tuple]) -> List[UTXO]:
        """Requests unspent outputs (UTXO) for a set of addresses

        Based on the 'listunspent' rpc call (has limitations).

        Known limitations:
        - Only works with wallet addresses. Use the 'importaddress' or 'importmulti' command to add
        a new address to the wallet (watch-only).
        - Does NOT return/include immature coinbase outputs (staked or minted coins that have not yet reached maturity).
        - Further limitations might apply depending on the specific bitcoin fork.

        :param ticker: coin ticker symbol (ignored)
        :param addresses: set of wallet addresses
        :return: list of unspent outputs (UTXO)
        """

        # TODO make call as batch
        # sanity check: only wallet address are supported
        for address in addresses:
            info = self.rpc_getaddressinfo(address)
            if not (info["ismine"] or info["iswatchonly"]):
                log.warning(f"Non wallet address '{address}' detected! "
                            f"This can lead to wrong results. Import the address first with rescan enabled!")

        block_count = self.rpc_getblockcount()
        result = self.rpc_listunspent(addresses=list(set(addresses)))
        log.debug(pprint.pformat(result))

        utxos = list()
        for entry in result:
            utxos.append(UTXO(
                txid=entry["txid"],
                vout=int(entry["vout"]),
                value=entry["amount"],
                address=entry["address"],
                block=block_count - int(entry["confirmations"] - 1),
            ))

        return utxos


class DashRPC(BitcoinRPC):

    def rpc_getaddressutxos(self, addresses: list) -> list:
        """Returns all unspent outputs for an address (requires addressindex to be enabled)

        :return: rpc output
        """
        return self._call_command(["getaddressutxos", {"addresses": addresses}])

    def get_utxos(self, ticker: str, addresses: Union[set, list, tuple]) -> List[UTXO]:
        """Requests unspent outputs (UTXO) for a set of addresses

        Based on the 'getaddressutxos' rpc call.

        :param ticker: coin ticker symbol (ignored)
        :param addresses: set of wallet addresses
        :return: list of unspent outputs (UTXO)
        """
        result = self.rpc_getaddressutxos(addresses=list(set(addresses)))
        log.debug(pprint.pformat(result))

        utxos = list()
        for entry in result:
            utxos.append(UTXO(
                txid=entry["txid"],
                vout=int(entry["outputIndex"]),
                value=decimal.Decimal(entry["satoshis"]) / decimal.Decimal("100000000"),
                address=entry["address"],
                block=int(entry["height"]),
            ))

        return utxos