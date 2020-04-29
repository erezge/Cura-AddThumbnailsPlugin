# Copyright (c) 2020 GimboGandalf
# This file is released under the terms of the AGPLv3 or higher.

from ..Script import Script

from UM.Application import Application #To get the current printer's settings.
from UM.Logger import Logger
from cura.Snapshot import Snapshot
from PyQt5.QtCore import Qt, QByteArray, QBuffer, QIODevice
from PyQt5.QtGui import QImage
from typing import List
import textwrap

class AddThumbnails(Script):

    GCODE_LINE_PREFIX = "; "
    GCODE_LINE_WIDTH = 80

    def __init__(self) -> None:
        super().__init__()

    def _image_to_byte_array(self, image) -> QByteArray:
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.WriteOnly)
        image.save(buffer, 'png')
        buffer.close()
        return byte_array 

    def _image_to_base64(self, image) -> QByteArray:
        ba = self._image_to_byte_array(image)
        ba64 = ba.toBase64()
        return ba64

    def _txt_to_gcode(self, txt) -> str:
        wrapper = textwrap.TextWrapper(initial_indent=self.GCODE_LINE_PREFIX, width=self.GCODE_LINE_WIDTH,
                                    subsequent_indent=self.GCODE_LINE_PREFIX)
        return wrapper.fill(txt)

    def _create_snapshot(self, width, height):
        # must be called from the main thread because of OpenGL
        Logger.log("d", "Creating thumbnail image...")
        try:
            snapshot = Snapshot.snapshot(width = width, height = height)
            return snapshot
        except Exception:
            Logger.logException("w", "Failed to create snapshot image")
            return None

    def _create_thumbnail_gcode(self, width, height) -> str:
        min_size = min(width,height)
        tmp_snapshot = self._create_snapshot(min_size, min_size)
         # Scale it to the correct size
        if (width != height):
            snapshot = tmp_snapshot.copy(int((min_size-width)/2), int((min_size-height)/2), width, height)
        else:
            snapshot = tmp_snapshot

        ba64 = self._image_to_base64(snapshot)
        b64str = str(ba64, 'utf-8')
        b64gcode = self._txt_to_gcode(b64str)
        gcode = self.GCODE_LINE_PREFIX + "\n" + self.GCODE_LINE_PREFIX + "thumbnail begin " + str(width) + "x" + str(height) + " " + str(len(b64str)) + "\n" + \
            b64gcode + "\n" + \
            self.GCODE_LINE_PREFIX + "thumbnail end\n" + self.GCODE_LINE_PREFIX + "\n"
        return gcode


    def getSettingDataString(self) -> str:
        return """{
            "name":"Add Thumbnails",
            "key":"AddThumbnails",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "turn_on":
                {
                    "label": "Enable",
                    "description": "When enabled, Thumbnail will be added to the gcode file.",
                    "type": "bool",
                    "default_value": true
                },
                "thumbnail_width":
                {
                    "label": "Thumbnail Width",
                    "description": "Width of the thumbnail",
                    "unit": "pixels",
                    "type": "int",
                    "default_value": 220,
                    "minimum_value": "16",
                    "minimum_value_warning": "16"
                },
                "thumbnail_height":
                {
                    "label": "Thumbnail Height",
                    "description": "Height of the thumbnail",
                    "unit": "pixels",
                    "type": "int",
                    "default_value": 220,
                    "minimum_value": "16",
                    "minimum_value_warning": "16"
                }
            }
        }"""

    ##  Inserts the thumbnail.
    #   \param data: List of layers.
    #   \return New list of layers.
    def execute(self, data: List[str]) -> List[str]:
        turn_on = self.getSettingValueByKey("turn_on")
        thumbnail_width = self.getSettingValueByKey("thumbnail_width")
        thumbnail_height = self.getSettingValueByKey("thumbnail_height")
        Logger.log("d", "Adding thumbnail image enabled=" + str(turn_on) + " resolution=" + str(thumbnail_width) + "x" + str(thumbnail_height))

        if turn_on :
            thumbnail_gcode = self._create_thumbnail_gcode(thumbnail_width, thumbnail_height)
            data[0] = data[0] + thumbnail_gcode

        return data
