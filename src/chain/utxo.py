#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List, Set

import decimal
import collections


class UTXO(object):
    def __init__(self, txid: str, vout: int, value: decimal.Decimal, address: str, block: int) -> None:
        self.txid = txid
        self.vout = vout
        self.value = value
        self.address = address
        self.block = block

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return str(dict(collections.OrderedDict([
            ("address", self.address),
            ("txid", self.txid),
            ("vout", self.vout),
            ("value", self.value),
            ("block", self.block),
        ])))

    def __hash__(self) -> int:
        return hash((self.txid, self.vout, self.value, self.address, self.block))

    def __eq__(self, other) -> bool:
        if not isinstance(other, UTXO):
            return NotImplemented

        return (
            self.txid == other.txid and
            self.vout == other.vout and
            self.value == other.value and
            self.address == other.address and
            self.block == other.block
        )


def diff(utxo_sets: List[Set[UTXO]]):
    """Computes the
    - intersection: elements that are common to all sets
    - diffs: list of differences for each set, remainder elements not in 'intersection'

    :param utxo_sets: list of utxo sets returned by chain sources
    :return: intersection, diffs
    """
    intersection = utxo_sets[0].intersection(*utxo_sets[1:]) if len(utxo_sets) > 0 else set()

    diffs = list()
    for s in utxo_sets:
        diffs.append(s - intersection)

    return intersection, diffs
