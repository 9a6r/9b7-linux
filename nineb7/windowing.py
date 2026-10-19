"""Startup presentation for Studio workspaces."""
from PySide6.QtCore import QEvent, QObject, QTimer


class _MaximizeOnExpose(QObject):
    def eventFilter(self, handle, event):
        if event.type() == QEvent.Type.Expose and handle.isExposed():
            handle.removeEventFilter(self)
            # DEsk ignores maximize requests sent before the first Wayland
            # configure. Wait for exposure, then let it choose the work area.
            QTimer.singleShot(0, self.parent().showMaximized)
            self.deleteLater()
        return False


def show_workspace(window):
    """Open maximized within the desktop work area; normal restore still works."""
    window.show()
    handle = window.windowHandle()
    if handle.isExposed():
        window.showMaximized()
    else:
        handle.installEventFilter(_MaximizeOnExpose(window))
