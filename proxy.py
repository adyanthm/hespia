"""
Hespia — Advanced Web Proxy Tool
Entry point.

Usage:
    python proxy.py [--host HOST] [--port PORT]

Requirements:
    pip install -r requirements.txt
"""
import sys
import os
import argparse

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_dependencies():
    """Check that all required packages are available."""
    missing = []
    packages = {
        "PySide6": "PySide6",
        "mitmproxy": "mitmproxy",
    }
    for name, pkg in packages.items():
        try:
            __import__(name.split(".")[0])
        except ImportError:
            missing.append(pkg)

    if missing:
        print("=" * 60)
        print("ERROR: Missing required packages:")
        for pkg in missing:
            print(f"  - {pkg}")
        print("\nInstall them with:")
        print(f"  pip install {' '.join(missing)}")
        print("  (or) pip install -r requirements.txt")
        print("=" * 60)
        sys.exit(1)


def main():
    check_dependencies()

    parser = argparse.ArgumentParser(
        description="Hespia — Advanced Web Proxy Tool"
    )
    parser.add_argument(
        "--host", default="127.0.0.1",
        help="Proxy listen address (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port", type=int, default=8080,
        help="Proxy listen port (default: 8080)"
    )
    parser.add_argument(
        "--auto-start", action="store_true",
        help="Automatically start the proxy on launch"
    )
    args = parser.parse_args()

    from PySide6.QtWidgets import QApplication, QSplashScreen
    from PySide6.QtGui import QPixmap, QColor, QFont
    from PySide6.QtCore import Qt, QTimer

    # High-DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    
    # ── Splash Screen ──
    banner_pix = QPixmap("media/banner.png")
    
    # Scale relative to screen size (IDE-like: roughly 35% of screen width)
    screen = app.primaryScreen()
    screen_width = screen.availableGeometry().width()
    splash_width = int(screen_width * 0.47)
    
    scaled_pix = banner_pix.scaled(splash_width, splash_width, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    
    splash = QSplashScreen(scaled_pix, Qt.WindowType.WindowStaysOnTopHint)
    splash.show()
    app.processEvents()
    
    app.setApplicationName("Hespia")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Hespia")

    # Set default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    from ui.main_window import MainWindow
    window = MainWindow()
    window._current_host = args.host
    window._current_port = args.port

    if args.auto_start:
        window._start_proxy(args.host, args.port)

    # Fade out splash and show main window
    window.showMaximized()
    splash.finish(window)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
