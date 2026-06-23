"""
DROIDCOM - Native Andriller Integration
Drives andriller's own ChainExecution/decoder/cracking classes directly and
renders the results inside DROIDCOM's UI, instead of launching andriller's
separate `python -m andriller` Tk GUI.
"""

import importlib.util
import os
from pathlib import Path

from PySide6 import QtWidgets

from ..utils.qt_dispatcher import emit_ui


class _AndrillerLogAdapter:
    """Adapts andriller's expected logger interface onto a sink callback."""

    def __init__(self, sink):
        self.sink = sink

    def _emit(self, msg, *args, **kwargs):
        self.sink(str(msg))

    info = debug = warning = error = exception = _emit

    def setLevel(self, *args, **kwargs):
        pass


class AndrillerResultsDialog(QtWidgets.QDialog):
    """Runs andriller's extraction/decoding pipeline and displays the
    decoded artifacts natively, without opening andriller's own GUI."""

    EXTRACTIONS_DIR = Path.home() / "Andriller-Extractions"

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.setWindowTitle("Andriller - Android Forensics")
        self.resize(900, 650)
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        top = QtWidgets.QHBoxLayout()
        self.start_btn = QtWidgets.QPushButton("Start Extraction")
        self.start_btn.clicked.connect(self._start_extraction)
        self.crack_btn = QtWidgets.QPushButton("Lockscreen Hash Cracker...")
        self.crack_btn.clicked.connect(self._open_cracker)
        top.addWidget(self.start_btn)
        top.addWidget(self.crack_btn)
        top.addStretch()
        layout.addLayout(top)

        self.status_label = QtWidgets.QLabel(
            "Ready. Connect a device, then click Start Extraction.\n"
            "If your device isn't rooted, confirm the on-screen backup prompt "
            "without setting a password when it appears."
        )
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.tabs = QtWidgets.QTabWidget()
        layout.addWidget(self.tabs, 1)

        self.log_view = QtWidgets.QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumHeight(140)
        layout.addWidget(self.log_view)

    def _log(self, msg):
        emit_ui(self.owner, lambda: self._append_log(msg))

    def _append_log(self, msg):
        self.log_view.append(msg)
        self.owner.log_message(f"[Andriller] {msg}")

    def _set_status(self, msg):
        emit_ui(self.owner, lambda: self.status_label.setText(msg))

    def _start_extraction(self):
        if not getattr(self.owner, "device_connected", False):
            QtWidgets.QMessageBox.information(
                self, "Not Connected", "Please connect to a device first."
            )
            return
        self.start_btn.setEnabled(False)
        self.tabs.clear()
        self.log_view.clear()
        self.owner._run_in_thread(self._run_extraction_task)

    def _run_extraction_task(self):
        from andriller import driller

        try:
            self.EXTRACTIONS_DIR.mkdir(parents=True, exist_ok=True)
            logger_adapter = _AndrillerLogAdapter(self._log)

            self._set_status("Reading device information...")
            dr = driller.ChainExecution(str(self.EXTRACTIONS_DIR), use_adb=True, logger=logger_adapter)
            dr.InitialAdbRead()
            dr.CreateWorkDir()

            self._set_status("Acquiring data from device...")
            dr.DataAcquisition()

            self._set_status("Extracting acquired data...")
            dr.DataExtraction()

            self._set_status("Decoding extracted artifacts...")
            decoders = self._decode_native(dr)

            dr.CleanUp()

            if decoders:
                emit_ui(self.owner, lambda: self._populate_tabs(dr, decoders))
                self._set_status(
                    f"Done. {len(decoders)} artifact type(s) decoded. Saved to: {dr.work_dir}"
                )
            else:
                emit_ui(self.owner, lambda: self._populate_tabs(dr, decoders))
                self._set_status(
                    "Extraction finished but no decodable artifacts were found. "
                    "If the device isn't rooted, make sure you confirmed the backup "
                    "prompt on the device screen."
                )
        except Exception as e:
            self._log(f"Extraction failed: {e}")
            self._set_status("Extraction failed")
            emit_ui(self.owner, lambda: QtWidgets.QMessageBox.critical(
                self, "Andriller Error", str(e)
            ))
        finally:
            emit_ui(self.owner, lambda: self.start_btn.setEnabled(True))

    def _decode_native(self, dr):
        """Mirrors andriller's own ChainExecution.DataDecoding(), but keeps the
        decoder objects (and their DATA) for in-app display instead of writing
        HTML/XLSX report files."""
        results = []
        for file_name in filter(None, dr.DOWNLOADS):
            if not dr.registry.has_target(file_name):
                continue
            for deco_class in dr.registry.decoders_target(file_name):
                file_path = os.path.join(dr.output_dir, file_name)
                try:
                    deco = deco_class(dr.work_dir, file_path)
                except Exception as e:
                    self._log(f"Decode error ({deco_class.__name__}): {e}")
                    continue
                if not deco.template_name or not deco.DATA:
                    continue
                self._log(f"Decoded {deco.title}: {len(deco.DATA)} record(s)")
                results.append(deco)
        return results

    def _populate_tabs(self, dr, decoders):
        info_table = QtWidgets.QTableWidget(len(dr.REPORT), 2)
        info_table.setHorizontalHeaderLabels(["Field", "Value"])
        info_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        for row, (k, v) in enumerate(dr.REPORT.items()):
            info_table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(k)))
            info_table.setItem(row, 1, QtWidgets.QTableWidgetItem("" if v is None else str(v)))
        info_table.resizeColumnsToContents()
        self.tabs.addTab(info_table, "Device Info")

        for deco in decoders:
            self.tabs.addTab(self._make_table(deco), f"{deco.title} ({len(deco.DATA)})")

    @staticmethod
    def _make_table(deco):
        cols = list(deco.headers.items())
        table = QtWidgets.QTableWidget(len(deco.DATA), len(cols))
        table.setHorizontalHeaderLabels([label for _, label in cols])
        table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        for row, item in enumerate(deco.DATA):
            for col, (key, _label) in enumerate(cols):
                val = item.get(key, "")
                table.setItem(row, col, QtWidgets.QTableWidgetItem("" if val is None else str(val)))
        table.resizeColumnsToContents()
        table.setSortingEnabled(True)
        return table

    def _open_cracker(self):
        LockscreenCrackerDialog(self).exec()


class LockscreenCrackerDialog(QtWidgets.QDialog):
    """Manual front-end for andriller's cracking.py (PIN/pattern/dictionary
    brute-forcer), driven directly without andriller's own GUI."""

    def __init__(self, results_dialog):
        super().__init__(results_dialog)
        self.owner = results_dialog.owner
        self.setWindowTitle("Lockscreen Hash Cracker")
        self.resize(480, 380)
        self.dict_path = None
        self._build_ui()

    def _build_ui(self):
        form = QtWidgets.QFormLayout()

        self.hash_edit = QtWidgets.QLineEdit()
        self.hash_edit.setPlaceholderText("SHA1 hash (hex), e.g. from gesture.key/password.key")
        self.salt_edit = QtWidgets.QLineEdit()
        self.salt_edit.setPlaceholderText("Integer salt (from settings/locksettings data)")

        self.mode_combo = QtWidgets.QComboBox()
        self.mode_combo.addItems(["PIN (numeric)", "Pattern (gesture)", "Alphanumeric range", "Dictionary file"])
        self.mode_combo.currentIndexChanged.connect(self._mode_changed)

        self.range_edit = QtWidgets.QLineEdit()
        self.range_edit.setPlaceholderText("e.g. abcdefghijklmnopqrstuvwxyz0123456789")
        self.min_len_spin = QtWidgets.QSpinBox()
        self.min_len_spin.setRange(1, 16)
        self.min_len_spin.setValue(4)
        self.max_len_spin = QtWidgets.QSpinBox()
        self.max_len_spin.setRange(1, 16)
        self.max_len_spin.setValue(6)
        self.dict_btn = QtWidgets.QPushButton("Choose dictionary file...")
        self.dict_btn.clicked.connect(self._choose_dict)
        self.samsung_check = QtWidgets.QCheckBox("Samsung device (iterative SHA1 algorithm)")

        form.addRow("Hash:", self.hash_edit)
        form.addRow("Salt:", self.salt_edit)
        form.addRow("Mode:", self.mode_combo)
        form.addRow("Char range:", self.range_edit)
        form.addRow("Min length:", self.min_len_spin)
        form.addRow("Max length:", self.max_len_spin)
        form.addRow(self.dict_btn)
        form.addRow(self.samsung_check)

        self.start_btn = QtWidgets.QPushButton("Start Cracking")
        self.start_btn.clicked.connect(self._start)
        self.result_label = QtWidgets.QLabel("")
        self.result_label.setWordWrap(True)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.start_btn)
        layout.addWidget(self.result_label)

        self._mode_changed(0)

    def _mode_changed(self, idx):
        is_pattern = idx == 1
        is_alpha = idx == 2
        is_dict = idx == 3
        self.salt_edit.setEnabled(not is_pattern)
        self.range_edit.setEnabled(is_alpha)
        self.min_len_spin.setEnabled(is_alpha)
        self.max_len_spin.setEnabled(is_alpha)
        self.dict_btn.setEnabled(is_dict)
        self.samsung_check.setEnabled(not is_pattern)

    def _choose_dict(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select Dictionary File")
        if path:
            self.dict_path = path
            self.dict_btn.setText(os.path.basename(path))

    def _start(self):
        mode = self.mode_combo.currentIndex()
        hash_val = self.hash_edit.text().strip()
        if not hash_val:
            QtWidgets.QMessageBox.warning(self, "Missing Hash", "Enter the hash to crack.")
            return

        if mode == 1:
            self.start_btn.setEnabled(False)
            self.result_label.setText("Cracking pattern...")
            self.owner._run_in_thread(lambda: self._run_pattern(hash_val))
            return

        try:
            salt = int(self.salt_edit.text().strip())
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Invalid Salt", "Salt must be an integer.")
            return

        kwargs = dict(key=hash_val, salt=salt, samsung=self.samsung_check.isChecked())
        if mode == 0:
            kwargs["alpha"] = False
        elif mode == 2:
            rng = self.range_edit.text()
            if not rng:
                QtWidgets.QMessageBox.warning(self, "Missing Range", "Enter a character range.")
                return
            kwargs.update(alpha=True, alpha_range=rng,
                           min_len=self.min_len_spin.value(), max_len=self.max_len_spin.value())
        elif mode == 3:
            if not self.dict_path:
                QtWidgets.QMessageBox.warning(self, "Missing Dictionary", "Choose a dictionary file.")
                return
            kwargs.update(alpha=True, dict_file=self.dict_path)

        self.start_btn.setEnabled(False)
        self.result_label.setText("Cracking... this may take a while.")
        self.owner._run_in_thread(lambda: self._run_password(kwargs))

    def _run_pattern(self, hash_val):
        from andriller import cracking
        try:
            result, err = cracking.crack_pattern(hash_val), None
        except Exception as e:
            result, err = None, str(e)
        emit_ui(self.owner, lambda: self._show_result(result, err))

    def _run_password(self, kwargs):
        from andriller import cracking
        try:
            result, err = cracking.PasswordCrack(**kwargs).crack_password(), None
        except Exception as e:
            result, err = None, str(e)
        emit_ui(self.owner, lambda: self._show_result(result, err))

    def _show_result(self, result, err):
        self.start_btn.setEnabled(True)
        if err:
            self.result_label.setText(f"Error: {err}")
        elif result:
            self.result_label.setText(f"Found: {result}")
        else:
            self.result_label.setText("Not found in the given search space.")


class AndrillerNativeMixin:
    """Mixin exposing Andriller's functionality natively in DROIDCOM, with
    no separate andriller GUI process."""

    def run_andriller(self):
        if importlib.util.find_spec("andriller") is None:
            self._offer_pip_install("andriller", "Andriller")
            return
        AndrillerResultsDialog(self).exec()
