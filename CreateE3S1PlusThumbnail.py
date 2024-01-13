# Cura CreateE3S1Plus Thumbnail creator
# Abonent0007 (yurentiy.avd@gmail.com)
#
# This only works with Cura 5.6.0 or later
# Based on:
# https://github.com/Ultimaker/Cura/blob/master/plugins/PostProcessingPlugin/scripts/CreateThumbnail.py

import base64

from UM.Logger import Logger
from cura.Snapshot import Snapshot
from PyQt6.QtCore import QByteArray, QIODevice, QBuffer

from ..Script import Script


class CreateE3S1PlusThumbnail(Script):
    def __init__(self):
        super().__init__()

    def _createSnapshot(self, width, height):
        Logger.log("d", "Creating thumbnail image...")
        try:
            return Snapshot.snapshot(width, height)
        except Exception:
            Logger.logException("w", "Failed to create snapshot image")

    def _encodeSnapshot(self, snapshot):
        Logger.log("d", "Encoding thumbnail image...")
        try:
            thumbnail_buffer = QBuffer()
            thumbnail_buffer.open(QBuffer.OpenModeFlag.ReadWrite)
            thumbnail_image = snapshot
            thumbnail_image.save(thumbnail_buffer, "JPEG") # edit line
            thumbnail_data = thumbnail_buffer.data()
            thumbnail_length = thumbnail_data.length()
            base64_bytes = base64.b64encode(thumbnail_data)
            base64_message = base64_bytes.decode('ascii')
            thumbnail_buffer.close()
            Logger.log("d", "Snapshot thumbnail_length={}".format(thumbnail_length))
            return (base64_message, thumbnail_length)
        except Exception:
            Logger.logException("w", "Failed to encode snapshot image")

    def _convertSnapshotToGcode(self, thumbnail_length, encoded_snapshot, width, height, chunk_size=76):
        Logger.log("d", "Converting snapshot into gcode...")
        gcode = []

        # these numbers appear to be related to image size, guessing here
        x1 = (int)(width/80) + 24 #edit line
        x2 = (width - x1) - 1 #edit line
        x3 = thumbnail_length + 175 #edit line
        x4 = round(x3 / 115) #edit
        header = "; jpg begin {}*{} {} {} {} {}".format(
            width, height, x3, x1, x2, x4)  #edit line
        Logger.log("d", "Gcode header={}".format(header))
        gcode.append(header)

        chunks = ["; {}".format(encoded_snapshot[i:i+chunk_size])
                  for i in range(0, len(encoded_snapshot), chunk_size)]
        gcode.extend(chunks)

        gcode.append("; jpg end")
        gcode.append(";")
        gcode.append("")

        return gcode

    def getSettingDataString(self):
        return """{
            "name": "Create Thumbnail (CreateE3S1PlusThumbnail)",
            "key": "CreateE3S1PlusThumbnail",
            "metadata": {},
            "version": 2,
            "settings":
            {}
        }"""

    def execute(self, data):
        width = 300 #edit
        height = 300 #edit
        Logger.log("d", "CreateE3S1PlusThumbnail Plugin start with width={}, height={}...".format(width, height))

        snapshot = self._createSnapshot(width, height)
        if snapshot:
            Logger.log("d", "Snapshot created")
            (encoded_snapshot, thumbnail_length) = self._encodeSnapshot(snapshot)
            snapshot_gcode = self._convertSnapshotToGcode(
                thumbnail_length, encoded_snapshot, width, height)

            Logger.log("d", "Layer count={}".format(len(data)))
            if len(data) > 0:
                # The Ender-3 S1 Plus really wants this at the top of the file
                layer_index = 0
                lines = data[layer_index].split("\n")
                Logger.log("d", "Adding snapshot gcode lines (len={}) before '{}'".format(len(snapshot_gcode), lines[0]))
                lines[0:0] = snapshot_gcode
                final_lines = "\n".join(lines)
                data[layer_index] = final_lines

        Logger.log("d", "CreateE3S1PlusThumbnail Plugin end")
        return data
