from __future__ import annotations

import hashlib
import json
import shutil
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QFormLayout,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMainWindow, QMessageBox, QPushButton, QSplitter, QTextEdit,
    QVBoxLayout, QWidget
)

APP_NAME = "Live ISO Driver Injector"
PROJECT_VERSION = "0.1.0"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass
class DriverRecord:
    path: str
    filename: str
    sha256: str
    keep_manual: bool = True
    keep_network: bool = True
    strategy: str = "Preserve and reapply"
    source_type: str = "Local file"
    source_location: str = ""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} — {PROJECT_VERSION}")
        self.resize(1120, 760)
        self.image_path: Path | None = None
        self.drivers: list[DriverRecord] = []
        self.project_path: Path | None = None
        self._build_ui()
        self._log("Ready. This phase stages and audits files; it does not modify an ISO or USB.")

    def _build_ui(self):
        root = QWidget()
        outer = QVBoxLayout(root)

        banner = QLabel(
            "PRESERVATION-FIRST PROTOTYPE — No image is modified in this release."
        )
        banner.setWordWrap(True)
        banner.setStyleSheet(
            "background:#fff2cc;color:#594300;padding:10px;border:1px solid #e0c76b;"
            "border-radius:6px;font-weight:600;"
        )
        outer.addWidget(banner)

        image_row = QHBoxLayout()
        self.image_label = QLabel("No ISO / disk image selected")
        self.image_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        choose_image = QPushButton("Choose image…")
        choose_image.clicked.connect(self.choose_image)
        image_row.addWidget(QLabel("Source image:"))
        image_row.addWidget(self.image_label, 1)
        image_row.addWidget(choose_image)
        outer.addLayout(image_row)

        splitter = QSplitter(Qt.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(QLabel("Imported drivers"))
        self.driver_list = QListWidget()
        self.driver_list.currentRowChanged.connect(self.load_selected_driver)
        left_layout.addWidget(self.driver_list, 1)
        add_btn = QPushButton("Add driver files…")
        add_btn.clicked.connect(self.add_drivers)
        remove_btn = QPushButton("Remove selected driver")
        remove_btn.clicked.connect(self.remove_driver)
        left_layout.addWidget(add_btn)
        left_layout.addWidget(remove_btn)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.addWidget(QLabel("Selected driver settings"))
        form = QFormLayout()
        self.filename_label = QLabel("—")
        self.hash_label = QLabel("—")
        self.manual_check = QCheckBox("Keep during manual updates")
        self.network_check = QCheckBox("Keep during network updates")
        self.manual_check.setChecked(True)
        self.network_check.setChecked(True)
        self.strategy = QComboBox()
        self.strategy.addItems([
            "Preserve and reapply",
            "Download again if missing",
            "Preserve first; download if missing",
        ])
        self.source_type = QComboBox()
        self.source_type.addItems(["Local file", "Git repository", "Direct HTTPS download", "Onion service"])
        self.source_location = QLineEdit()
        self.source_location.setPlaceholderText("Optional URL / repository / release reference")
        form.addRow("Filename:", self.filename_label)
        form.addRow("SHA-256:", self.hash_label)
        form.addRow("", self.manual_check)
        form.addRow("", self.network_check)
        form.addRow("Update strategy:", self.strategy)
        form.addRow("Source type:", self.source_type)
        form.addRow("Source location:", self.source_location)
        right_layout.addLayout(form)

        save_settings = QPushButton("Apply settings to selected driver")
        save_settings.clicked.connect(self.apply_driver_settings)
        right_layout.addWidget(save_settings)
        right_layout.addStretch(1)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([430, 650])
        outer.addWidget(splitter, 1)

        actions = QHBoxLayout()
        analyze = QPushButton("Analyze conflicts")
        analyze.clicked.connect(self.analyze_conflicts)
        save = QPushButton("Save project…")
        save.clicked.connect(self.save_project)
        actions.addWidget(analyze)
        actions.addWidget(save)
        actions.addStretch(1)
        outer.addLayout(actions)

        outer.addWidget(QLabel("Activity and conflict report"))
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        outer.addWidget(self.log_view, 1)

        self.setCentralWidget(root)

    def _log(self, message: str):
        stamp = datetime.now().strftime("%H:%M:%S")
        self.log_view.append(f"[{stamp}] {message}")

    def choose_image(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Choose Linux image", "",
            "Linux images (*.iso *.img *.raw *.bin);;All files (*.*)"
        )
        if filename:
            self.image_path = Path(filename)
            self.image_label.setText(str(self.image_path))
            self._log(f"Selected source image: {self.image_path}")
            self._log("Image inspection is not implemented yet; source remains untouched.")

    def add_drivers(self):
        filenames, _ = QFileDialog.getOpenFileNames(
            self, "Choose driver files", "",
            "Driver/package files (*.deb *.ko *.xz *.zst *.gz *.zip *.tar *.tgz *.bin *.fw);;All files (*.*)"
        )
        added = 0
        for name in filenames:
            path = Path(name)
            try:
                digest = sha256_file(path)
            except OSError as exc:
                self._log(f"Could not read {path}: {exc}")
                continue
            # Avoid adding the exact same file twice.
            if any(d.sha256 == digest and d.filename == path.name for d in self.drivers):
                self._log(f"Skipped duplicate import: {path.name}")
                continue
            self.drivers.append(DriverRecord(
                path=str(path),
                filename=path.name,
                sha256=digest,
            ))
            added += 1
        self.refresh_driver_list()
        self._log(f"Imported {added} driver file(s). No files have been injected.")

    def refresh_driver_list(self):
        current = self.driver_list.currentRow()
        self.driver_list.blockSignals(True)
        self.driver_list.clear()
        for record in self.drivers:
            item = QListWidgetItem(record.filename)
            item.setToolTip(record.path)
            self.driver_list.addItem(item)
        self.driver_list.blockSignals(False)
        if self.drivers:
            self.driver_list.setCurrentRow(min(max(current, 0), len(self.drivers) - 1))
        else:
            self.load_selected_driver(-1)

    def load_selected_driver(self, row: int):
        if row < 0 or row >= len(self.drivers):
            self.filename_label.setText("—")
            self.hash_label.setText("—")
            return
        record = self.drivers[row]
        self.filename_label.setText(record.filename)
        self.hash_label.setText(record.sha256)
        self.manual_check.setChecked(record.keep_manual)
        self.network_check.setChecked(record.keep_network)
        self.strategy.setCurrentText(record.strategy)
        self.source_type.setCurrentText(record.source_type)
        self.source_location.setText(record.source_location)

    def apply_driver_settings(self):
        row = self.driver_list.currentRow()
        if row < 0 or row >= len(self.drivers):
            QMessageBox.information(self, "Select a driver", "Choose a driver first.")
            return
        record = self.drivers[row]
        record.keep_manual = self.manual_check.isChecked()
        record.keep_network = self.network_check.isChecked()
        record.strategy = self.strategy.currentText()
        record.source_type = self.source_type.currentText()
        record.source_location = self.source_location.text().strip()
        self._log(f"Saved settings for {record.filename}.")

    def remove_driver(self):
        row = self.driver_list.currentRow()
        if row < 0 or row >= len(self.drivers):
            return
        record = self.drivers[row]
        answer = QMessageBox.question(
            self, "Remove driver",
            f"Remove {record.filename} from this project?\nThe original file will not be deleted.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if answer == QMessageBox.Yes:
            self.drivers.pop(row)
            self.refresh_driver_list()
            self._log(f"Removed {record.filename} from project; source file untouched.")

    def analyze_conflicts(self):
        if not self.drivers:
            QMessageBox.information(self, "No drivers", "Import at least one driver file first.")
            return
        names: dict[str, list[DriverRecord]] = {}
        for record in self.drivers:
            names.setdefault(record.filename.casefold(), []).append(record)

        self._log("---- Preservation-first conflict analysis ----")
        conflicts = 0
        for same_name in names.values():
            if len(same_name) > 1:
                hashes = {r.sha256 for r in same_name}
                conflicts += 1
                if len(hashes) == 1:
                    self._log(
                        f"IDENTICAL-NAME GROUP: {same_name[0].filename} — "
                        "same filename and same SHA-256; duplicate content."
                    )
                else:
                    self._log(
                        f"CONFLICT: {same_name[0].filename} — same filename, "
                        "different contents. Recommended action: cancel this injection "
                        "and inspect both files."
                    )
                    for record in same_name:
                        self._log(f"  File: {record.path}")
                        self._log(f"  SHA-256: {record.sha256}")
        if conflicts == 0:
            self._log(
                "No duplicate filenames were found among imported files. "
                "This does NOT prove kernel or package compatibility."
            )
        self._log("Analysis complete. No files were overwritten, renamed, or deleted.")

    def save_project(self):
        if not self.drivers:
            QMessageBox.information(self, "No drivers", "Import at least one driver first.")
            return
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save project manifest", "driver-project.json",
            "Project manifest (*.json)"
        )
        if not filename:
            return
        manifest_path = Path(filename)
        project_dir = manifest_path.parent / (manifest_path.stem + "_staging")
        try:
            project_dir.mkdir(parents=True, exist_ok=True)
            staged = []
            for index, record in enumerate(self.drivers, start=1):
                source = Path(record.path)
                # Preserve original filename. If a collision occurs, do not overwrite:
                # store in a numbered subfolder.
                target_dir = project_dir / f"driver_{index:03d}"
                target_dir.mkdir(parents=True, exist_ok=True)
                target = target_dir / record.filename
                shutil.copy2(source, target)
                item = asdict(record)
                item["staged_path"] = str(target)
                staged.append(item)

            manifest = {
                "application": APP_NAME,
                "project_version": PROJECT_VERSION,
                "created_utc": datetime.now(timezone.utc).isoformat(),
                "source_image": str(self.image_path) if self.image_path else None,
                "preservation_policy": "never overwrite source files in Phase 1",
                "drivers": staged,
                "limitations": [
                    "No ISO/USB image modification is performed.",
                    "No driver compatibility is guaranteed.",
                    "No network downloads or updater modifications are performed.",
                ],
            }
            manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        except Exception as exc:
            QMessageBox.critical(self, "Save failed", str(exc))
            self._log(f"Save failed: {exc}")
            return
        self._log(f"Project saved: {manifest_path}")
        self._log(f"Driver staging copies saved under: {project_dir}")
        QMessageBox.information(
            self, "Project saved",
            f"Project manifest and staging copies saved.\n\n{manifest_path}\n\n"
            "The original image and imported driver files were not modified."
        )


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
