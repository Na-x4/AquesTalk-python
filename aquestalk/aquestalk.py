#
#  AquesTalk-python - Python Wrapper for AquesTalk (Old License)
#  Copyright (C) 2018 Na-x4
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#


# -*- coding: utf-8 -*-

import ctypes
import io
import wave
import enum
import hashlib
import os

__all__ = ['VOICE_TYPES', 'VoiceType', 'AquesTalk', 'AquesTalkError', 'load', 'load_from_path']

VOICE_TYPES = ('f1', 'f2', 'm1', 'm2', 'r1', 'dvd', 'jgr', 'imd1')
VoiceType = enum.Enum('VoiceType', VOICE_TYPES, module=__name__)


class AquesTalk:
    """
    AquesTalk Wrapper

    Parameters
    ----------
    name : str
        AquesTalk.dllのパス
    voice_type : VoiceType
        声種

    Attributes
    ----------
    voice_type : VoiceType
        声種
    """

    def __init__(self, name, voice_type=None):
        self._dll = ctypes.windll.LoadLibrary(name)
        self._voice_type = voice_type

        self._dll.AquesTalk_Synthe.argtypes = (ctypes.POINTER(ctypes.c_char),
                                               ctypes.c_int,
                                               ctypes.POINTER(ctypes.c_int))
        self._dll.AquesTalk_Synthe.restype = ctypes.POINTER(ctypes.c_char)

        self._dll.AquesTalk_FreeWave.argtypes = (ctypes.POINTER(ctypes.c_char),)
        self._dll.AquesTalk_FreeWave.restype = None

    def synthe(self, koe, speed=100):
        """
        音声記号列から音声波形を生成します。

        Parameters
        ----------
        koe : str
            音声記号列
        speed : int
            発話速度[%]

            - 50-300の間で指定
            - デフォルト：100
            - 値を大きく設定するほど、速くなる

        Returns
        -------
        wave.Wave_read
            生成した音声

        Raises
        ------
        AquesTalkError
            音声波形の生成時にエラーが発生した場合
        """
        wav = wave.open(io.BytesIO(self.synthe_raw(koe, speed)), 'rb')
        return wav

    def synthe_raw(self, koe, speed=100):
        """
        音声記号列から音声波形を生成します。

        Parameters
        ----------
        koe : str
            音声記号列
        speed : int
            発話速度[%]

            - 50-300の間で指定
            - デフォルト：100
            - 値を大きく設定するほど、速くなる

        Returns
        -------
        bytes
            WAVフォーマットのデータ

        Raises
        ------
        AquesTalkError
            音声波形の生成時にエラーが発生した場合
        """
        c_wav, size = self._synthe(koe, speed)
        if not c_wav:
            raise AquesTalkError(size)

        wav_raw = c_wav[:size]
        self._freewave(c_wav)

        return wav_raw

    @property
    def voice_type(self):
        """
        声種
        """
        return self._voice_type

    def _synthe(self, koe, speed):
        """
        音声記号列から音声波形を生成します
        生成した音声データ領域は、使用後、呼び出し側でAquesTalk_FreeWave()で解放してください。

        Parameters
        ----------
        koe : str
            音声記号列
        speed : int
            発話速度[%] 50-300の間で指定 デフォルト：100 値を大きく設定するほど、速くなる

        Returns
        -------
        ctypes.POINTER(ctypes.c_char)
            WAVフォーマットのデータ(内部で領域確保、解放は呼び出し側でAquesTalk_FreeWave()で行う)の先頭アドレスを返す。
            エラー時は、Noneを返す。このときsizeにエラーコードが設定される。
        int
            生成した音声データのサイズが返る[byte](エラーの場合はエラーコードが返る)
        """
        c_size = ctypes.c_int()
        c_wav = self._dll.AquesTalk_Synthe(koe.encode('sjis'), speed, ctypes.byref(c_size))
        return c_wav if c_wav else None, c_size.value

    def _freewave(self, c_wav):
        """
        音声データの領域を開放

        Parameters
        ----------
        c_wav : ctypes.POINTER(ctypes.c_char)
            WAVフォーマットのデータ(AquesTalk_Synthe()で生成した音声データ)
        """
        self._dll.AquesTalk_FreeWave(c_wav)


class AquesTalkError(Exception):
    """
    AquesTalk関数が返すエラー
    """
    messages = {100: 'その他のエラー',
                101: 'メモリ不足',
                102: '音声記号列に未定義の読み記号が指定された',
                103: '韻律データの時間長がマイナスなっている',
                104: '内部エラー(未定義の区切りコード検出）',
                105: '音声記号列に未定義の読み記号が指定された',
                106: '音声記号列のタグの指定が正しくない',
                107: 'タグの長さが制限を越えている（または[>]がみつからない）',
                108: 'タグ内の値の指定が正しくない',
                109: 'WAVE再生ができない（サウンドドライバ関連の問題）',
                110: 'WAVE再生ができない（サウンドドライバ関連の問題非同期再生）',
                111: '発声すべきデータがない',
                200: '音声記号列が長すぎる',
                201: '１つのフレーズ中の読み記号が多すぎる',
                202: '音声記号列が長い（内部バッファオーバー1）',
                203: 'ヒープメモリ不足',
                204: '音声記号列が長い（内部バッファオーバー1）'}

    def __init__(self, err):
        self.err = err
        self.message = AquesTalkError.messages[err] if err in AquesTalkError.messages else '不明なエラー'
        super().__init__('{}({})'.format(self.message, self.err))


def _get_md5_from_file(name, chunk_size=4096):
    md5 = hashlib.md5()
    with open(name, 'rb') as file:
        for chunk in iter(lambda: file.read(chunk_size), b''):
            md5.update(chunk)
    return md5.hexdigest()


# http://blog-yama.a-quest.com/?eid=970181
_DLL_MD5_DICT = {'d09ba89e04fc6a848377cb695b7c227a': VoiceType.f1,
                 '23bd3bbfe89e7bb0f92e5e3ed841cec4': VoiceType.f1,
                 'f97a031451220238b21ada12dd2ba6b7': VoiceType.f1,
                 '8bfacc9e1c9d6f1a1f6803739a9ed7d6': VoiceType.f2,
                 '950cb2c4a9493ff3af7906fdb02b523b': VoiceType.m1,
                 'd4491b6ff6aab7e6f3a19dad369d0432': VoiceType.m2,
                 '1a69c64175f46271f9f491890b265762': VoiceType.r1,
                 'cd431c8c86c1566e73cbbb166047b8a9': VoiceType.dvd,
                 '54f15b467cbf215884d29a0ad39a9df3': VoiceType.jgr,
                 'e352165e9da54e255c3c25a33cb85aaa': VoiceType.imd1}


def load(voice_type, check_voice_type=False):
    """
    指定された声種のAquesTalkライブラリを読み込みます

    Parameters
    ----------
    voice_type : VoiceType
        声種
    check_voice_type : bool
        声種が一致しているか確認するかどうか (デフォルト : False)

    Returns
    -------
    AquesTalk
        読み込んだAquesTalkライブラリのインスタンス
    """
    if not isinstance(voice_type, VoiceType):
        voice_type = VoiceType[voice_type]
    path = os.path.join(os.path.dirname(__file__), voice_type.name, "AquesTalk.dll")
    return load_from_path(path, voice_type, check_voice_type)


def load_from_path(path, voice_type, check_voice_type=False):
    """
    指定されたパスからAquesTalkライブラリを読み込みます

    Parameters
    ----------
    path : str
        dllファイルのパス
    voice_type : VoiceType
        声種
    check_voice_type : bool
        声種が一致しているか確認するかどうか (デフォルト : False)

    Returns
    -------
    AquesTalk
        読み込んだAquesTalkライブラリのインスタンス
    """
    if not check_voice_type:
        md5 = _get_md5_from_file(path)
        if _DLL_MD5_DICT[md5] != voice_type:
            voice_type = _DLL_MD5_DICT[md5]
    return AquesTalk(path, voice_type)
