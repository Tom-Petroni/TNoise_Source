"""Python color ramp editor for TNoise.

This provides a Blender-like stop editor (gradient bar + draggable points)
and writes the result into the `color_ramp_stops` table knob.
"""

from __future__ import annotations

import json
import os
from typing import Dict, List, Optional, Sequence, Tuple

import nuke  # ty:ignore[unresolved-import]

from _consts import NODE_CLASS_NAME

try:
    from PySide2 import QtCore, QtGui, QtWidgets  # ty:ignore[import-not-found]
except Exception:  # pragma: no cover - Nuke runtime dependency
    try:
        from PySide6 import QtCore, QtGui, QtWidgets  # ty:ignore[import-not-found]
    except Exception:  # pragma: no cover - Nuke runtime dependency
        QtCore = None
        QtGui = None
        QtWidgets = None

_SERIALIZED_KNOB = "color_ramp_serialized"

_RAMP_PRESETS: Dict[str, Sequence[Tuple[float, Tuple[float, float, float]]]] = {
    "Grayscale": (
        (0.0, (0.0, 0.0, 0.0)),
        (1.0, (1.0, 1.0, 1.0)),
    ),
    "Heat": (
        (0.0, (0.02, 0.02, 0.02)),
        (0.28, (0.72, 0.05, 0.0)),
        (0.62, (0.95, 0.45, 0.0)),
        (1.0, (1.0, 0.92, 0.5)),
    ),
    "Ocean": (
        (0.0, (0.02, 0.09, 0.18)),
        (0.35, (0.0, 0.36, 0.7)),
        (0.7, (0.0, 0.72, 0.82)),
        (1.0, (0.75, 0.95, 1.0)),
    ),
    "Toxic": (
        (0.0, (0.03, 0.03, 0.03)),
        (0.35, (0.08, 0.65, 0.08)),
        (0.7, (0.55, 0.95, 0.1)),
        (1.0, (0.95, 1.0, 0.45)),
    ),
    "Sunset": (
        (0.0, (0.12, 0.03, 0.22)),
        (0.35, (0.62, 0.12, 0.44)),
        (0.72, (0.95, 0.42, 0.2)),
        (1.0, (1.0, 0.86, 0.45)),
    ),
}

_CUSTOM_PRESET_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "_color_ramp_presets.json",
)


def _load_custom_presets() -> Dict[str, List[Dict[str, object]]]:
    if not os.path.isfile(_CUSTOM_PRESET_FILE):
        return {}
    try:
        with open(_CUSTOM_PRESET_FILE, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except Exception:
        return {}
    if not isinstance(payload, dict):
        return {}

    result: Dict[str, List[Dict[str, object]]] = {}
    for name, stops in payload.items():
        if not isinstance(name, str) or not isinstance(stops, list):
            continue
        safe_stops: List[Dict[str, object]] = []
        for stop in stops:
            if not isinstance(stop, dict):
                continue
            safe_stops.append(
                {
                    "pos": float(stop.get("pos", 0.0)),
                    "color": tuple(stop.get("color", (0.0, 0.0, 0.0))),
                },
            )
        if safe_stops:
            result[name] = safe_stops
    return result


_CUSTOM_PRESETS: Dict[str, List[Dict[str, object]]] = _load_custom_presets()


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


def _preset_names() -> List[str]:
    names = list(_RAMP_PRESETS.keys())
    for custom_name in sorted(_CUSTOM_PRESETS.keys()):
        if custom_name not in names:
            names.append(custom_name)
    return names


def _preset_stops(name: str) -> List[Dict[str, object]]:
    custom = _CUSTOM_PRESETS.get(name)
    if custom:
        return _normalize_stops(custom)
    raw = _RAMP_PRESETS.get(name)
    if not raw:
        return _normalize_stops([])
    return _normalize_stops([{"pos": pos, "color": color} for pos, color in raw])


def _save_custom_preset(name: str, stops: Sequence[Dict[str, object]]) -> bool:
    preset_name = str(name).strip()
    if not preset_name:
        return False

    _CUSTOM_PRESETS[preset_name] = _normalize_stops(stops)
    try:
        with open(_CUSTOM_PRESET_FILE, "w", encoding="utf-8") as handle:
            json.dump(_CUSTOM_PRESETS, handle, indent=2)
    except Exception:
        return False
    return True


def _pack_rgb8(color: Tuple[float, float, float]) -> int:
    r = int(round(_clamp01(color[0]) * 255.0))
    g = int(round(_clamp01(color[1]) * 255.0))
    b = int(round(_clamp01(color[2]) * 255.0))
    return (r << 16) | (g << 8) | b


def _unpack_rgb8(value: int) -> Tuple[float, float, float]:
    value = int(value)
    r = ((value >> 16) & 0xFF) / 255.0
    g = ((value >> 8) & 0xFF) / 255.0
    b = (value & 0xFF) / 255.0
    return (r, g, b)


def _normalize_stops(stops: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    out: List[Dict[str, object]] = []
    for stop in stops:
        pos = _clamp01(float(stop.get("pos", 0.0)))
        color = stop.get("color", (0.0, 0.0, 0.0))
        if not isinstance(color, (tuple, list)) or len(color) != 3:
            color = (0.0, 0.0, 0.0)
        c = (_clamp01(float(color[0])), _clamp01(float(color[1])), _clamp01(float(color[2])))
        out.append({"pos": pos, "color": c})

    if len(out) < 2:
        out = [
            {"pos": 0.0, "color": (0.0, 0.0, 0.0)},
            {"pos": 1.0, "color": (1.0, 1.0, 1.0)},
        ]

    out.sort(key=lambda s: float(s["pos"]))
    return out


def _serialize_stops(stops: Sequence[Dict[str, object]]) -> str:
    safe_stops = _normalize_stops(stops)
    return ";".join(
        "{:.6f}|{:.6f}|{:.6f}|{:.6f}".format(
            float(stop["pos"]),
            float(stop["color"][0]),  # type:ignore[index]
            float(stop["color"][1]),  # type:ignore[index]
            float(stop["color"][2]),  # type:ignore[index]
        )
        for stop in safe_stops
    )


def _deserialize_stops(payload: str) -> List[Dict[str, object]]:
    if not payload:
        return _normalize_stops([])

    parsed: List[Dict[str, object]] = []
    for token in str(payload).split(";"):
        token = token.strip()
        if not token:
            continue
        parts = [p.strip() for p in token.split("|")]
        if len(parts) != 4:
            continue
        try:
            pos = float(parts[0])
            r = float(parts[1])
            g = float(parts[2])
            b = float(parts[3])
        except Exception:
            continue
        parsed.append({"pos": pos, "color": (_clamp01(r), _clamp01(g), _clamp01(b))})
    return _normalize_stops(parsed)


def _table_iface(node) -> Optional[object]:
    knob = node.knob("color_ramp_stops")
    if knob is None:
        return None

    candidates = [knob]
    for accessor in ("tableKnob", "table"):
        fn = getattr(knob, accessor, None)
        if callable(fn):
            try:
                obj = fn()
            except Exception:
                obj = None
            if obj is not None:
                candidates.append(obj)

    required = ("getRowCount", "getColumnIndex", "addRow", "setCellFloat", "setCellColor")
    for candidate in candidates:
        if all(hasattr(candidate, name) for name in required):
            return candidate
    return None


def _read_stops_from_node(node) -> List[Dict[str, object]]:
    serialized_knob = node.knob(_SERIALIZED_KNOB)
    if serialized_knob is not None:
        try:
            payload = str(serialized_knob.value())
        except Exception:
            payload = ""
        if payload:
            return _deserialize_stops(payload)

    iface = _table_iface(node)
    if iface is None:
        return _normalize_stops([])

    try:
        row_count = int(iface.getRowCount())
        pos_col = int(iface.getColumnIndex("pos"))
        color_col = int(iface.getColumnIndex("color"))
    except Exception:
        return _normalize_stops([])

    if row_count <= 0 or pos_col < 0 or color_col < 0:
        return _normalize_stops([])

    stops: List[Dict[str, object]] = []
    for row in range(row_count):
        try:
            pos = float(iface.getCellFloat(row, pos_col))
            color = _unpack_rgb8(int(iface.getCellColor(row, color_col)))
        except Exception:
            continue
        stops.append({"pos": pos, "color": color})
    return _normalize_stops(stops)


def _clear_table_rows(iface) -> None:
    if hasattr(iface, "deleteAllItems"):
        iface.deleteAllItems()
        return

    if hasattr(iface, "deleteRow") and hasattr(iface, "getRowCount"):
        for row in reversed(range(int(iface.getRowCount()))):
            iface.deleteRow(row)


def _write_stops_to_node(node, stops: Sequence[Dict[str, object]]) -> bool:
    safe_stops = _normalize_stops(stops)
    wrote = False

    serialized_knob = node.knob(_SERIALIZED_KNOB)
    if serialized_knob is not None:
        try:
            serialized_knob.setValue(_serialize_stops(safe_stops))
            wrote = True
        except Exception:
            pass

    iface = _table_iface(node)
    if iface is not None:
        try:
            pos_col = int(iface.getColumnIndex("pos"))
            color_col = int(iface.getColumnIndex("color"))
            if pos_col >= 0 and color_col >= 0:
                _clear_table_rows(iface)
                for stop in safe_stops:
                    row = int(iface.addRow())
                    iface.setCellFloat(row, pos_col, float(stop["pos"]))
                    iface.setCellColor(row, color_col, _pack_rgb8(stop["color"]))  # type:ignore[arg-type]
                wrote = True
        except Exception:
            pass

    enable_knob = node.knob("color_ramp_enable")
    if enable_knob is not None:
        try:
            enable_knob.setValue(True)
        except Exception:
            pass

    try:
        node.forceValidate()
    except Exception:
        pass
    return wrote


if QtWidgets is not None:

    class _RampWidget(QtWidgets.QWidget):
        stopsChanged = QtCore.Signal()
        selectionChanged = QtCore.Signal(int)

        def __init__(self, stops: Sequence[Dict[str, object]], parent=None):
            super().__init__(parent)
            self.setMinimumHeight(92)
            self.setMaximumHeight(92)
            self.setSizePolicy(
                QtWidgets.QSizePolicy(
                    QtWidgets.QSizePolicy.Expanding,
                    QtWidgets.QSizePolicy.Fixed,
                ),
            )
            self._stops = _normalize_stops(stops)
            self._selected = 0
            self._dragging = False

        def _bar_rect(self):
            return QtCore.QRectF(14.0, 14.0, max(10.0, self.width() - 28.0), 26.0)

        def _x_from_pos(self, pos: float, rect: QtCore.QRectF) -> float:
            return rect.left() + _clamp01(pos) * rect.width()

        def _pos_from_x(self, x: float, rect: QtCore.QRectF) -> float:
            return _clamp01((x - rect.left()) / max(1.0, rect.width()))

        def _qcolor(self, c: Tuple[float, float, float]):
            return QtGui.QColor.fromRgbF(c[0], c[1], c[2], 1.0)

        def _event_xy(self, event) -> Tuple[float, float]:
            x = float(event.position().x()) if hasattr(event, "position") else float(event.x())
            y = float(event.position().y()) if hasattr(event, "position") else float(event.y())
            return (x, y)

        def _is_outside_delete_zone(self, x: float, y: float, rect: QtCore.QRectF) -> bool:
            # Larger keep-area so users need to drag farther before deleting a stop.
            return (
                x < (rect.left() - 34.0)
                or x > (rect.right() + 34.0)
                or y < (rect.top() - 26.0)
                or y > (rect.bottom() + 54.0)
            )

        def _open_color_picker_for_selected(self) -> None:
            stop = self._stops[self._selected]
            c = stop["color"]  # type:ignore[assignment]
            initial = QtGui.QColor.fromRgbF(c[0], c[1], c[2], 1.0)
            chosen = QtWidgets.QColorDialog.getColor(initial, self, "Pick Ramp Color")
            if not chosen.isValid():
                return
            self.set_selected_color((chosen.redF(), chosen.greenF(), chosen.blueF()))

        def _sample_color(self, pos: float) -> Tuple[float, float, float]:
            p = _clamp01(pos)
            if p <= float(self._stops[0]["pos"]):
                return self._stops[0]["color"]  # type:ignore[return-value]
            if p >= float(self._stops[-1]["pos"]):
                return self._stops[-1]["color"]  # type:ignore[return-value]
            for i in range(1, len(self._stops)):
                l = self._stops[i - 1]
                r = self._stops[i]
                lp = float(l["pos"])
                rp = float(r["pos"])
                if p <= rp:
                    t = 0.0 if rp <= lp else (p - lp) / (rp - lp)
                    lc = l["color"]  # type:ignore[assignment]
                    rc = r["color"]  # type:ignore[assignment]
                    return (
                        lc[0] + (rc[0] - lc[0]) * t,
                        lc[1] + (rc[1] - lc[1]) * t,
                        lc[2] + (rc[2] - lc[2]) * t,
                    )
            return (0.0, 0.0, 0.0)

        def stops(self) -> List[Dict[str, object]]:
            return _normalize_stops(self._stops)

        def selected_index(self) -> int:
            return int(self._selected)

        def set_selected_index(self, idx: int) -> None:
            idx = max(0, min(int(idx), len(self._stops) - 1))
            if idx != self._selected:
                self._selected = idx
                self.selectionChanged.emit(self._selected)
                self.update()

        def set_stops(self, stops: Sequence[Dict[str, object]]) -> None:
            self._stops = _normalize_stops(stops)
            self._selected = max(0, min(self._selected, len(self._stops) - 1))
            self.stopsChanged.emit()
            self.selectionChanged.emit(self._selected)
            self.update()

        def add_stop(self, pos: float) -> None:
            p = _clamp01(pos)
            c = self._sample_color(p)
            stop = {"pos": p, "color": c}
            self._stops.append(stop)
            self._stops.sort(key=lambda s: float(s["pos"]))
            self._selected = self._stops.index(stop)
            self.stopsChanged.emit()
            self.selectionChanged.emit(self._selected)
            self.update()

        def remove_selected(self) -> None:
            if len(self._stops) <= 2:
                return
            del self._stops[self._selected]
            self._selected = max(0, min(self._selected, len(self._stops) - 1))
            self.stopsChanged.emit()
            self.selectionChanged.emit(self._selected)
            self.update()

        def set_selected_color(self, color: Tuple[float, float, float]) -> None:
            self._stops[self._selected]["color"] = (
                _clamp01(color[0]),
                _clamp01(color[1]),
                _clamp01(color[2]),
            )
            self.stopsChanged.emit()
            self.update()

        def set_selected_pos(self, pos: float) -> None:
            stop = self._stops[self._selected]
            stop["pos"] = _clamp01(pos)
            self._stops.sort(key=lambda s: float(s["pos"]))
            self._selected = self._stops.index(stop)
            self.stopsChanged.emit()
            self.selectionChanged.emit(self._selected)
            self.update()

        def paintEvent(self, _event):
            p = QtGui.QPainter(self)
            p.setRenderHint(QtGui.QPainter.Antialiasing, True)
            rect = self._bar_rect()

            gradient = QtGui.QLinearGradient(rect.left(), rect.top(), rect.right(), rect.top())
            for stop in self._stops:
                gradient.setColorAt(float(stop["pos"]), self._qcolor(stop["color"]))  # type:ignore[arg-type]

            p.setPen(QtGui.QPen(QtGui.QColor(40, 40, 40), 1.0))
            p.setBrush(QtGui.QBrush(gradient))
            p.drawRoundedRect(rect, 4.0, 4.0)

            for i, stop in enumerate(self._stops):
                x = self._x_from_pos(float(stop["pos"]), rect)
                top = rect.bottom() + 4.0
                poly = QtGui.QPolygonF(
                    [
                        QtCore.QPointF(x, top),
                        QtCore.QPointF(x - 6.0, top + 10.0),
                        QtCore.QPointF(x + 6.0, top + 10.0),
                    ],
                )
                p.setBrush(self._qcolor(stop["color"]))  # type:ignore[arg-type]
                border = QtGui.QColor(255, 255, 255) if i == self._selected else QtGui.QColor(20, 20, 20)
                p.setPen(QtGui.QPen(border, 1.3))
                p.drawPolygon(poly)
                square_size = 9.0
                square_rect = QtCore.QRectF(
                    x - (square_size * 0.5),
                    top + 12.0,
                    square_size,
                    square_size,
                )
                p.setBrush(self._qcolor(stop["color"]))  # type:ignore[arg-type]
                p.setPen(QtGui.QPen(border, 1.1))
                p.drawRect(square_rect)

        def _pick_handle(self, x: float, y: float) -> int:
            rect = self._bar_rect()
            hy0 = rect.bottom() + 2.0
            hy1 = rect.bottom() + 28.0
            if y < hy0 or y > hy1:
                return -1
            best = -1
            best_d = 1e9
            for i, stop in enumerate(self._stops):
                sx = self._x_from_pos(float(stop["pos"]), rect)
                d = abs(sx - x)
                if d < best_d and d <= 9.0:
                    best = i
                    best_d = d
            return best

        def mousePressEvent(self, event):
            if event.button() != QtCore.Qt.LeftButton:
                return
            rect = self._bar_rect()
            x, y = self._event_xy(event)

            handle = self._pick_handle(x, y)
            if handle >= 0:
                self.set_selected_index(handle)
                self._dragging = True
                return

            if rect.contains(QtCore.QPointF(x, y)):
                self.add_stop(self._pos_from_x(x, rect))
                self._dragging = True

        def mouseMoveEvent(self, event):
            if not self._dragging:
                return
            rect = self._bar_rect()
            x, y = self._event_xy(event)
            if self._is_outside_delete_zone(x, y, rect):
                if len(self._stops) > 2:
                    self.remove_selected()
                self._dragging = False
                return
            self.set_selected_pos(self._pos_from_x(x, rect))

        def mouseReleaseEvent(self, _event):
            self._dragging = False

        def mouseDoubleClickEvent(self, event):
            if event.button() != QtCore.Qt.LeftButton:
                return
            x, y = self._event_xy(event)
            handle = self._pick_handle(x, y)
            if handle < 0:
                return
            self.set_selected_index(handle)
            self._open_color_picker_for_selected()


    class _RampEditorDialog(QtWidgets.QDialog):
        def __init__(self, stops: Sequence[Dict[str, object]], parent=None):
            super().__init__(parent)
            self.setWindowTitle("TNoise Python Color Ramp")
            self.resize(520, 210)

            root = QtWidgets.QVBoxLayout(self)
            self._ramp = _RampWidget(stops, self)
            root.addWidget(self._ramp)

            controls = QtWidgets.QHBoxLayout()
            controls.addWidget(QtWidgets.QLabel("Pos"))
            self._pos = QtWidgets.QDoubleSpinBox()
            self._pos.setRange(0.0, 1.0)
            self._pos.setDecimals(4)
            self._pos.setSingleStep(0.01)
            self._pos.setFixedWidth(90)
            controls.addWidget(self._pos)

            self._color_btn = QtWidgets.QPushButton("Color")
            self._color_btn.setFixedWidth(96)
            controls.addWidget(self._color_btn)

            self._add_btn = QtWidgets.QPushButton("Add")
            self._remove_btn = QtWidgets.QPushButton("Remove")
            controls.addWidget(self._add_btn)
            controls.addWidget(self._remove_btn)
            controls.addStretch(1)
            root.addLayout(controls)

            presets = QtWidgets.QHBoxLayout()
            presets.addWidget(QtWidgets.QLabel("Preset"))
            self._preset_combo = QtWidgets.QComboBox()
            self._preset_combo.addItems(_preset_names())
            self._preset_combo.setFixedWidth(124)
            presets.addWidget(self._preset_combo)
            self._preset_save_btn = QtWidgets.QPushButton("Save")
            self._preset_save_btn.setFixedWidth(72)
            presets.addWidget(self._preset_save_btn)
            presets.addStretch(1)
            root.addLayout(presets)

            buttons = QtWidgets.QDialogButtonBox(
                QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            )
            root.addWidget(buttons)

            self._ramp.selectionChanged.connect(self._sync_controls_from_selection)
            self._ramp.stopsChanged.connect(self._sync_controls_from_selection)
            self._pos.valueChanged.connect(self._on_pos_changed)
            self._color_btn.clicked.connect(self._on_pick_color)
            self._add_btn.clicked.connect(lambda: self._ramp.add_stop(0.5))
            self._remove_btn.clicked.connect(self._ramp.remove_selected)
            self._preset_combo.currentIndexChanged.connect(self._on_preset_selected)
            self._preset_save_btn.clicked.connect(self._on_save_preset)
            buttons.accepted.connect(self.accept)
            buttons.rejected.connect(self.reject)

            self._sync_controls_from_selection()

        def _selected_stop(self) -> Dict[str, object]:
            return self._ramp.stops()[self._ramp.selected_index()]

        def _set_color_button(self, color: Tuple[float, float, float]) -> None:
            q = QtGui.QColor.fromRgbF(color[0], color[1], color[2], 1.0)
            self._color_btn.setStyleSheet(
                "QPushButton{background-color:%s;}" % q.name(),
            )

        def _sync_controls_from_selection(self, *_args) -> None:
            stop = self._selected_stop()
            self._pos.blockSignals(True)
            self._pos.setValue(float(stop["pos"]))
            self._pos.blockSignals(False)
            self._set_color_button(stop["color"])  # type:ignore[arg-type]
            self._remove_btn.setEnabled(len(self._ramp.stops()) > 2)

        def _on_pos_changed(self, value: float) -> None:
            self._ramp.set_selected_pos(value)

        def _on_pick_color(self) -> None:
            stop = self._selected_stop()
            c = stop["color"]  # type:ignore[assignment]
            initial = QtGui.QColor.fromRgbF(c[0], c[1], c[2], 1.0)
            chosen = QtWidgets.QColorDialog.getColor(initial, self, "Pick Ramp Color")
            if not chosen.isValid():
                return
            self._ramp.set_selected_color((chosen.redF(), chosen.greenF(), chosen.blueF()))
            self._sync_controls_from_selection()

        def _on_preset_selected(self, _index: int) -> None:
            self._ramp.set_stops(_preset_stops(str(self._preset_combo.currentText())))

        def _refresh_preset_combo(self, selected_name: str) -> None:
            current = str(selected_name).strip()
            self._preset_combo.blockSignals(True)
            self._preset_combo.clear()
            self._preset_combo.addItems(_preset_names())
            if current:
                idx = self._preset_combo.findText(current)
                if idx >= 0:
                    self._preset_combo.setCurrentIndex(idx)
            self._preset_combo.blockSignals(False)

        def _on_save_preset(self) -> None:
            name, ok = QtWidgets.QInputDialog.getText(
                self,
                "Save Ramp Preset",
                "Preset name:",
            )
            if not ok:
                return
            if not _save_custom_preset(str(name), self._ramp.stops()):
                nuke.message("Unable to save preset.")
                return
            self._refresh_preset_combo(str(name))

        def result_stops(self) -> List[Dict[str, object]]:
            return self._ramp.stops()


    class _InlineRampEditorWidget(QtWidgets.QWidget):
        def __init__(self, node, parent=None):
            super().__init__(parent)
            self._node = node
            self._suspend_write = False
            self.setSizePolicy(
                QtWidgets.QSizePolicy(
                    QtWidgets.QSizePolicy.Preferred,
                    QtWidgets.QSizePolicy.Fixed,
                ),
            )

            root = QtWidgets.QVBoxLayout(self)
            root.setContentsMargins(0, 0, 0, 0)
            root.setSpacing(6)

            self._ramp = _RampWidget(_read_stops_from_node(node), self)
            root.addWidget(self._ramp)

            controls = QtWidgets.QHBoxLayout()
            controls.addWidget(QtWidgets.QLabel("Pos"))
            self._pos = QtWidgets.QDoubleSpinBox()
            self._pos.setRange(0.0, 1.0)
            self._pos.setDecimals(4)
            self._pos.setSingleStep(0.01)
            self._pos.setFixedWidth(90)
            controls.addWidget(self._pos)

            self._color_btn = QtWidgets.QPushButton("Color")
            self._color_btn.setFixedWidth(96)
            controls.addWidget(self._color_btn)

            self._add_btn = QtWidgets.QPushButton("Add")
            self._remove_btn = QtWidgets.QPushButton("Remove")
            controls.addWidget(self._add_btn)
            controls.addWidget(self._remove_btn)
            controls.addStretch(1)
            root.addLayout(controls)

            presets = QtWidgets.QHBoxLayout()
            presets.addWidget(QtWidgets.QLabel("Preset"))
            self._preset_combo = QtWidgets.QComboBox()
            self._preset_combo.addItems(_preset_names())
            self._preset_combo.setFixedWidth(124)
            presets.addWidget(self._preset_combo)
            self._preset_save_btn = QtWidgets.QPushButton("Save")
            self._preset_save_btn.setFixedWidth(72)
            presets.addWidget(self._preset_save_btn)
            presets.addStretch(1)
            root.addLayout(presets)

            self._ramp.selectionChanged.connect(self._sync_controls_from_selection)
            self._ramp.stopsChanged.connect(self._on_stops_changed)
            self._pos.valueChanged.connect(self._on_pos_changed)
            self._color_btn.clicked.connect(self._on_pick_color)
            self._add_btn.clicked.connect(lambda: self._ramp.add_stop(0.5))
            self._remove_btn.clicked.connect(self._ramp.remove_selected)
            self._preset_combo.currentIndexChanged.connect(self._on_preset_selected)
            self._preset_save_btn.clicked.connect(self._on_save_preset)

            self._sync_controls_from_selection()
            fixed_h = int(self.sizeHint().height())
            self.setMinimumHeight(fixed_h)
            self.setMaximumHeight(fixed_h)

        def _selected_stop(self) -> Dict[str, object]:
            return self._ramp.stops()[self._ramp.selected_index()]

        def _set_color_button(self, color: Tuple[float, float, float]) -> None:
            q = QtGui.QColor.fromRgbF(color[0], color[1], color[2], 1.0)
            self._color_btn.setStyleSheet(
                "QPushButton{background-color:%s;}" % q.name(),
            )

        def _sync_controls_from_selection(self, *_args) -> None:
            stop = self._selected_stop()
            self._suspend_write = True
            self._pos.blockSignals(True)
            self._pos.setValue(float(stop["pos"]))
            self._pos.blockSignals(False)
            self._suspend_write = False
            self._set_color_button(stop["color"])  # type:ignore[arg-type]
            self._remove_btn.setEnabled(len(self._ramp.stops()) > 2)

        def _commit(self) -> None:
            if self._suspend_write:
                return
            _write_stops_to_node(self._node, self._ramp.stops())

        def _on_stops_changed(self, *_args) -> None:
            self._sync_controls_from_selection()
            self._commit()

        def _on_pos_changed(self, value: float) -> None:
            self._ramp.set_selected_pos(value)

        def _on_pick_color(self) -> None:
            stop = self._selected_stop()
            c = stop["color"]  # type:ignore[assignment]
            initial = QtGui.QColor.fromRgbF(c[0], c[1], c[2], 1.0)
            chosen = QtWidgets.QColorDialog.getColor(initial, self, "Pick Ramp Color")
            if not chosen.isValid():
                return
            self._ramp.set_selected_color((chosen.redF(), chosen.greenF(), chosen.blueF()))
            self._sync_controls_from_selection()
            self._commit()

        def _on_preset_selected(self, _index: int) -> None:
            self._ramp.set_stops(_preset_stops(str(self._preset_combo.currentText())))
            self._sync_controls_from_selection()
            self._commit()

        def _refresh_preset_combo(self, selected_name: str) -> None:
            current = str(selected_name).strip()
            self._preset_combo.blockSignals(True)
            self._preset_combo.clear()
            self._preset_combo.addItems(_preset_names())
            if current:
                idx = self._preset_combo.findText(current)
                if idx >= 0:
                    self._preset_combo.setCurrentIndex(idx)
            self._preset_combo.blockSignals(False)

        def _on_save_preset(self) -> None:
            name, ok = QtWidgets.QInputDialog.getText(
                self,
                "Save Ramp Preset",
                "Preset name:",
            )
            if not ok:
                return
            if not _save_custom_preset(str(name), self._ramp.stops()):
                nuke.message("Unable to save preset.")
                return
            self._refresh_preset_combo(str(name))


def _context_node():
    try:
        node = nuke.thisNode()
        if node is not None:
            return node
    except Exception:
        pass
    try:
        knob = nuke.thisKnob()
        if knob is not None and hasattr(knob, "node"):
            return knob.node()
    except Exception:
        pass
    return None


class TNoiseInlineRampKnob:
    """Bridge object used by Nuke PythonKnob/PyCustom to create inline UI."""

    def makeUI(self):
        if QtWidgets is None:
            return None
        node = _context_node()
        if node is None or node.Class() != NODE_CLASS_NAME:
            return QtWidgets.QLabel("TNoise node context not available.")
        return _InlineRampEditorWidget(node)


def _main_window():
    if QtWidgets is None:
        return None
    app = QtWidgets.QApplication.instance()
    if app is None:
        return None
    for widget in app.topLevelWidgets():
        if widget.inherits("QMainWindow"):
            return widget
    return None


def _exec_dialog(dialog) -> int:
    if hasattr(dialog, "exec_"):
        return int(dialog.exec_())
    return int(dialog.exec())


def open_python_ramp_editor(node=None):
    """Open the Python color ramp editor for a TNoise node."""
    if node is None:
        try:
            node = nuke.thisNode()
        except Exception:
            node = None

    if node is None or node.Class() != NODE_CLASS_NAME:
        nuke.message("Select a TNoise node first.")
        return

    if QtWidgets is None:
        nuke.message("PySide is not available in this Nuke session.")
        return

    stops = _read_stops_from_node(node)
    dialog = _RampEditorDialog(stops, _main_window())
    if _exec_dialog(dialog) != 1:
        return

    if not _write_stops_to_node(node, dialog.result_stops()):
        nuke.message(
            "Unable to write the Python ramp into color_ramp_stops.",
        )


def open_python_ramp_editor_for_selected():
    """Open editor for currently selected TNoise node."""
    try:
        node = nuke.selectedNode()
    except Exception:
        node = None
    open_python_ramp_editor(node)
