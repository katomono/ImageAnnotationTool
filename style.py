import functools
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QPixmapCache, QColor
import numpy as np
from colorsys import hsv_to_rgb
from functools import lru_cache
from typing import List, Optional, Tuple
import itertools

from data import BaseImageData, BaseBoxData

class ImageLayer:
    def __init__(self, image: Optional[BaseImageData]):
        self.axis0 = 0
        self.axis1 = 1
        assert image.data.shape[-1] == 1
        self.focus = list(image.data.shape[:1]) + [0] * len(image.data.shape[2:-1])
        self.image = image

        self.window_level = np.mean(image.data)
        self.window_width = np.std(image.data)
    
    def toPixmap(self)->QPixmap:
        # 2軸によって構成される２次元平面への写像処理
        slice_data = self.image.data
        for axis in range(self.data.ndim - 1):# channel
            if axis in [self.axis0, self.axis1]:
                continue            
            slice_data = np.take(slice_data, self.focus[axis], axis=axis)
        slice_data = slice_data[:,:,0]
        # 表示用のuint8型への変換
        slice_data = slice_data.astype(np.float32)
        w = 256 / self.window_width
        b = -self.window_level * w + 128
        slice_data *= w
        slice_data += b
        slice_data = np.clip(slice_data, 0, 255, out=slice_data).astype(np.uint8)
        view_data = np.empty([slice_data.shape[0], slice_data.shape[1], 4], dtype=np.uint8)
        np.stack([slice_data] * 3, axis=-1, out=view_data[:,:,0:3])
        view_data[:,:,3] = 255
        # QPixmapへの変換
        qimg = QImage(view_data, view_data.shape[1], view_data.shape[0], QImage.Format_ARGB32)
        pimg = QPixmap.fromImage(qimg)
        return pimg

class LabelMaskImageLayer:
    def __init__(self, image: Optional[BaseImageData]):
        self.axis0 = 0
        self.axis1 = 1
        assert image.data.shape[-1] == 1
        self.focus = list(image.data.shape[:1]) + [0] * len(image.data.shape[2:-1])
        self.image = image
        self.n_color = 10
        self.is_draw = [False] * [True] * 255

    def label_lut(self):
        n = self.n_color
        lut = [(self.is_draw[i], ) + hsv_to_rgb((i % n) / n, 0.9, 1.0) for i in range(256)]
        lut = np.asarray(lut, dtype=np.float32)
        lut *= 255
        return np.clip(lut, 0, 255, out=lut).astype(np.uint8)

    def toPixmap(self)->QPixmap:
        # 2軸によって構成される２次元平面への写像処理
        slice_data = self.image.data
        for axis in range(self.data.ndim - 1):
            if axis in [self.axis0, self.axis1]:
                continue            
            slice_data = np.take(slice_data, self.focus[axis], axis=axis)
        slice_data = slice_data[:,:,0]
        # 表示用のuint8型への変換
        view_data = self.lut[slice_data]
        
        qimg = QImage(view_data, view_data.shape[1], view_data.shape[0], QImage.Format_ARGB32)
        pimg = QPixmap.fromImage(qimg)
        return pimg

class BitMaskLayer:
    def __init__(self, image: Optional[BaseImageData]):
        self.axis0 = 0
        self.axis1 = 1
        assert image.data.shape[-1] == 1
        self.focus = list(image.data.shape[:1]) + [0] * len(image.data.shape[2:-1])
        self.image = image

        self.alpha = 0.5
        self.labels = np.unique(self.image.data)[1:] # 0を除外
        self.n_color = 10
        self.view_indice = [True] * (self.image.data.itemszie * 8)

    @property
    def lut(self):
        n_bit = self.image.data.itemsize * 8
        n = self.n_color
        n_mix_color = np.sum(tuple(itertools.product([0, 1], repeat=n_bit)), axis=1)
        lut = np.sum(tuple(itertools.product(
            [np.asarray((0, 0, 0)), 255 * self.view_indice[i] * np.asarray(hsv_to_rgb((i % n) / n, 0.9, 1.0)) for i in range(n_bit)])), axis=1)
        lut /= n_mix_color
        return np.clip(lut, 0, 255, out=lut).astype(np.uint8)

    def toPixmap(self)->QPixmap:
        # 2軸によって構成される２次元平面への写像処理
        slice_data = self.image.data
        for axis in range(self.image.data.ndim - 1):
            if axis in [self.axis0, self.axis1]:
                continue            
            slice_data = np.take(slice_data, self.focus[axis], axis=axis)
        slice_data = slice_data[:,:,0] # channel

        # 表示用のuint8型への変換
        view_data = self.lut[slice_data]
        
        qimg = QImage(view_data, view_data.shape[1], view_data.shape[0], QImage.Format_ARGB32)
        pimg = QPixmap.fromImage(qimg)
        return pimg
