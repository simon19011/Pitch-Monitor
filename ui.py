import sys
import time
from collections import deque
from data import start_microphone_recording, stop_microphone_recording, get_current_pitch, get_midi, get_exact_midi
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QScrollArea
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import Qt, QObject, Signal, Slot, QThread, QPointF

class PianoRoll(QWidget):
    NOTE_HEIGHT = 25
    NOTE_WIDTH = 60

    HISTORY_SECONDS = 5.0

    NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    MIN_MIDI = 21 # A0
    MAX_MIDI = 108 # C8

    WHITE_KEY_BACKDROP_COLOR = QColor(58, 66, 62)
    BLACK_KEY_BACKDROP_COLOR = QColor(44, 48, 46)
    WHITE_KEY_COLOR = QColor(235, 235, 235)
    BLACK_KEY_COLOR = QColor(40, 40, 40)
    WHITE_TEXT_COLOR = QColor(0, 0, 0)
    BLACK_TEXT_COLOR = QColor(255, 255, 255)
    CURRENT_PITCH_COLOR = QColor(230, 113, 46)
    CURRENT_PITCH_LINE_COLOR = QColor(255, 255, 255)

    def __init__(self):
        super().__init__()

        self.current_midi = 69 # A4, Temp variable

        self.pitch_history = deque()

        self.setMinimumHeight(
            (self.MAX_MIDI - self.MIN_MIDI + 1) * self.NOTE_HEIGHT
        )

    def set_pitch(self, frequency):
        now = time.monotonic()

        self.pitch_history.append((now, frequency))

        if frequency is not None:
            self.current_midi = get_midi(frequency)
        else:
            self.current_midi = None

        cutoff = now - self.HISTORY_SECONDS

        while self.pitch_history and self.pitch_history[0][0] < cutoff:
            self.pitch_history.popleft()

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)

        for midi in range(self.MAX_MIDI, self.MIN_MIDI - 1, -1):
            note_index = self.MAX_MIDI - midi
            y = note_index * self.NOTE_HEIGHT

            note_name = self.NOTES[midi % 12]
            octave = midi // 12 - 1
            note = f"{note_name}{octave}"

            is_sharp = note_name.endswith('#')

            if is_sharp:
                backdrop_color = self.BLACK_KEY_BACKDROP_COLOR
                key_color = self.BLACK_KEY_COLOR
                text_color = self.BLACK_TEXT_COLOR

            else:
                backdrop_color = self.WHITE_KEY_BACKDROP_COLOR
                key_color = self.WHITE_KEY_COLOR
                text_color = self.WHITE_TEXT_COLOR

            painter.fillRect(
                0,
                y,
                self.width(),
                self.NOTE_HEIGHT,
                backdrop_color
            )

            if midi == self.current_midi:
                painter.fillRect(
                    0,
                    y,
                    self.width(),
                    self.NOTE_HEIGHT,
                    self.CURRENT_PITCH_COLOR
                )

            painter.fillRect(
                0,
                y,
                self.NOTE_WIDTH,
                self.NOTE_HEIGHT,
                key_color 
            )
            
            painter.drawLine(
                0,
                y,
                self.width(),
                y
            )

            painter.save()
            painter.setPen(text_color)
            painter.drawText(
                self.NOTE_WIDTH / 3,
                y + self.NOTE_HEIGHT / 1.5,
                note
            )
            painter.restore()

            if len(self.pitch_history) > 1:
                now = time.monotonic()

                painter.save()
                pen = QPen(self.CURRENT_PITCH_LINE_COLOR)
                pen.setWidth(2)
                painter.setPen(pen)

                left_x_bound = self.NOTE_WIDTH
                right_x_bound = self.width() * 0.75
                graph_width = right_x_bound - left_x_bound

                previous_point = None

                for timestamp, frequency in self.pitch_history:
                    age = now - timestamp
                    
                    x = right_x_bound - (age / self.HISTORY_SECONDS) * graph_width

                    if frequency is None:
                        previous_point = None
                        continue

                    y = (self.MAX_MIDI - get_exact_midi(frequency)) * self.NOTE_HEIGHT + self.NOTE_HEIGHT / 2

                    point = QPointF(x, y)

                    if previous_point is not None:
                        painter.drawLine(previous_point, point)

                    previous_point = point

                painter.restore()


class Controls(QWidget):
    def __init__(self):
        super().__init__()


class AudioWorker(QObject):
    pitch_detected = Signal(object)
    finished = Signal()

    def __init__(self):
        super().__init__()
        self.running = True

    @Slot()
    def run(self):
        start_microphone_recording()

        while self.running:
            frequency = get_current_pitch()
            self.pitch_detected.emit(frequency)

        stop_microphone_recording()
        self.finished.emit()

    def stop(self):
        self.running = False

app = QApplication(sys.argv)
window = QWidget()
window.setWindowTitle("Pitch Monitor")
window.resize(350, 600)


layout = QVBoxLayout()
layout.setContentsMargins(0, 0, 0, 0)
layout.setSpacing(0)


piano_roll = PianoRoll()

scroll_area = QScrollArea()
scroll_area.setWidget(piano_roll)
scroll_area.setWidgetResizable(True)
scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

layout.addWidget(scroll_area, 6)
layout.addWidget(Controls(), 1)

window.setLayout(layout)

thread = QThread()
worker = AudioWorker()

worker.moveToThread(thread)

thread.started.connect(worker.run)
worker.finished.connect(thread.quit)
worker.finished.connect(worker.deleteLater)
thread.finished.connect(thread.deleteLater)

worker.pitch_detected.connect(piano_roll.set_pitch)

thread.start()

window.show()
app.exec()
