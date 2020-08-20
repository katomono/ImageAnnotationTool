from typing import Tuple
import numpy as np


def _load_hdr(filepath)->Tuple[Tuple[int], int, Tuple[float]]:
    hdr = np.loadtxt(str(filepath))
    shape = tuple(map(int, hdr[0:3][::-1]))
    itemsize = int(hdr[3].astype(np.int))
    spacing = tuple(map(float, hdr[4:7][::-1]))
    return shape, itemsize, spacing

def _load_raw(filepath, dtype, shape: Tuple[int])->np.ndarray:
    flat_raw = np.fromfile(str(filepath), dtype=dtype)
    raw = np.reshape(flat_raw, shape + (1,))
    return raw

class BaseImageData:
    def __init__(self, data, spacing):
        self.data = data
        self.spacing = spacing


class Image(BaseImageData):
    @classmethod
    def load(cls, filepath)->"Image":
        shape, itemsize, spacing, *other = _load_hdr(filepath.with_suffix(".hdr"))
        dtype = np.dtype("i%d" % itemsize)
        data = _load_raw(filepath, dtype, shape)
        return Image(data, spacing)

class BitMask(object):
    @classmethod
    def load(self, filepath)->"BitMask":
        shape, itemsize, spacing, *other = _load_hdr(filepath.with_suffix(".hdr"))
        dtype = np.dtype("u%d" % itemsize)
        data = _load_raw(filepath, dtype, shape)
        return BitMask(data, spacing)
