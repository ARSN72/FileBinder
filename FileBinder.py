import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QListWidget, 
                             QFileDialog, QMessageBox, QProgressBar, QTextEdit, QLabel, QDialog, QGridLayout, 
                             QScrollArea, QTabWidget, QListWidgetItem)
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QUrl
from PyQt6.QtGui import QDesktopServices
import subprocess
import shutil
import tempfile

class BinderThread(QThread):
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, selected_files, output_file, icon_file):
        super().__init__()
        self.selected_files = selected_files
        self.output_file = output_file
        self.icon_file = icon_file
        self.cancelled = False

    def run(self):
        try:
            self.progress.emit(0)
            self.log.emit("Starting file binding process...")

            with tempfile.TemporaryDirectory() as temp_dir:
                if self.cancelled:
                    return

                self.progress.emit(10)
                self.log.emit("Created temporary directory")

                opener_script = os.path.join(temp_dir, "opener_script.py")
                with open(opener_script, "w") as f:
                    f.write("import os\nimport sys\n\n")
                    for file in self.selected_files:
                        f.write(f"os.startfile(r'{os.path.basename(file)}')\n")
                
                if self.cancelled:
                    return

                self.progress.emit(30)
                self.log.emit("Created opener script")

                for file in self.selected_files:
                    shutil.copy2(file, temp_dir)
                    if self.cancelled:
                        return
                
                self.progress.emit(50)
                self.log.emit("Copied selected files to temporary directory")

                if self.cancelled:
                    return

                icon_param = f"--icon={self.icon_file}" if self.icon_file else ""
                subprocess.run(["pyinstaller", "--onefile", "--windowed", "--add-data", f"{temp_dir}/*;.", icon_param, opener_script], check=True)
                
                if self.cancelled:
                    return

                self.progress.emit(80)
                self.log.emit("Created executable with PyInstaller")

                shutil.move(os.path.join("dist", "opener_script.exe"), self.output_file)
                
                if self.cancelled:
                    return

                self.progress.emit(90)
                self.log.emit("Moved executable to desired location")

                shutil.rmtree("build", ignore_errors=True)
                os.remove("opener_script.spec")

                self.progress.emit(100)
                self.log.emit("Cleaned up temporary files")

            self.finished.emit()
        except Exception as e:
            self.log.emit(f"Error: {str(e)}")

    def cancel(self):
        self.cancelled = True

class IconBrowser(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Icon Browser")
        self.setFixedSize(400, 300)
        self.selected_icon = ""
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        grid_layout = QGridLayout(scroll_content)

        icon_dir = "icons"  # Directory containing built-in icons
        row, col = 0, 0
        for icon_file in os.listdir(icon_dir):
            if icon_file.endswith(".ico"):
                icon_path = os.path.join(icon_dir, icon_file)
                icon_button = QPushButton()
                icon_button.setIcon(QIcon(icon_path))
                icon_button.setIconSize(QSize(32, 32))
                icon_button.clicked.connect(lambda _, path=icon_path: self.select_icon(path))
                grid_layout.addWidget(icon_button, row, col)
                col += 1
                if col > 4:
                    col = 0
                    row += 1

        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

        custom_icon_button = QPushButton("Select Custom Icon")
        custom_icon_button.clicked.connect(self.select_custom_icon)
        layout.addWidget(custom_icon_button)

        self.setLayout(layout)

    def select_icon(self, icon_path):
        self.selected_icon = icon_path
        self.accept()

    def select_custom_icon(self):
        file_dialog = QFileDialog()
        icon_path, _ = file_dialog.getOpenFileName(self, "Select Custom Icon", "", "Icon Files (*.ico)")
        if icon_path:
            self.selected_icon = icon_path
            self.accept()

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About File Binder")
        self.setFixedSize(400, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        logo_label = QLabel()
        logo_pixmap = QPixmap('logo.png')
        logo_label.setPixmap(logo_pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio))
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)

        app_name = QLabel("File Binder")
        app_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_name.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(app_name)

        description = QLabel("Designed and Developed For Vth Semester, Mini Project by:-")
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setWordWrap(True)
        layout.addWidget(description)

        developers = [
            {"name": "Arshan Mansuri", "enrollment": "0808CB221010", "Portfolio": "https://arsn72.github.io/INTRO/"},
            {"name": "Anurag Malviya", "enrollment": "0808CB221009", "Portfolio": "https://www.linkedin.com/in/anurag-malviya-7629b0255/"}
        ]

        for dev in developers:
            dev_name = QLabel(dev['name'])
            dev_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(dev_name)

            enrollment = QLabel(f"Enrollment No:- {dev['enrollment']}")
            enrollment.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(enrollment)

            portfolio_button = QPushButton("Portfolio")
            portfolio_button.clicked.connect(lambda _, url=dev['Portfolio']: QDesktopServices.openUrl(QUrl(url)))
            layout.addWidget(portfolio_button)

        contribute_button = QPushButton("Contribute on GitHub")
        contribute_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/ARSN72/FileBinder")))
        layout.addWidget(contribute_button)

        self.setLayout(layout)

class FileBinder(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Binder")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon("app_icon.ico"))
        
        self.selected_files = []
        self.icon_file = ""
        self.output_file = ""
        self.default_icon = "app_icon.ico"
        
        self.init_ui()
    
    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_files_tab(), "Files")
        self.tabs.addTab(self.create_icon_tab(), "Icon")
        self.tabs.addTab(self.create_log_tab(), "Log")
        main_layout.addWidget(self.tabs)
        
        button_layout = QHBoxLayout()
        
        bind_button = QPushButton("Bind Files")
        bind_button.clicked.connect(self.bind_files)
        button_layout.addWidget(bind_button)
        
        about_button = QPushButton("About")
        about_button.clicked.connect(self.show_about)
        button_layout.addWidget(about_button)
        
        main_layout.addLayout(button_layout)
        
        self.status_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_layout.addWidget(self.progress_bar)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_binding)
        self.cancel_button.setVisible(False)
        self.status_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(self.status_layout)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
    
    def create_files_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        select_button = QPushButton("Select Files")
        select_button.clicked.connect(self.select_files)
        layout.addWidget(select_button)
        
        self.file_list = QListWidget()
        self.file_list.setStyleSheet("QListWidget::item { padding: 5px; }")
        layout.addWidget(self.file_list)
        
        remove_button = QPushButton("Remove Selected File")
        remove_button.clicked.connect(self.remove_file)
        layout.addWidget(remove_button)
        
        output_layout = QHBoxLayout()
        output_label = QLabel("Output File:")
        self.output_edit = QLabel("No output file selected")
        output_browse = QPushButton("Browse")
        output_browse.clicked.connect(self.browse_output)
        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_edit)
        output_layout.addWidget(output_browse)
        layout.addLayout(output_layout)
        
        widget.setLayout(layout)
        return widget
    
    def create_icon_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
       
        select_icon_button = QPushButton("Browse Icons")
        select_icon_button.clicked.connect(self.browse_icons)
        layout.addWidget(select_icon_button)
        
        self.icon_label = QLabel("If no icon selected (default app icon will be applied)")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon_label)
        
        widget.setLayout(layout)
        return widget
    
    def create_log_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        layout.addWidget(self.log_display)
        
        widget.setLayout(layout)
        return widget
    
    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files")
        self.selected_files.extend(files)
        self.update_file_list()
    
    def remove_file(self):
        current_item = self.file_list.currentItem()
        if current_item:
            file_path = current_item.text()
            self.selected_files.remove(file_path)
            self.update_file_list()
    
    def update_file_list(self):
        self.file_list.clear()
        for file in self.selected_files:
            item = QListWidgetItem(QIcon("file_icon.png"), file)
            self.file_list.addItem(item)
    
    def browse_icons(self):
        icon_browser = IconBrowser(self)
        if icon_browser.exec() == QDialog.DialogCode.Accepted:
            self.icon_file = icon_browser.selected_icon
            self.update_icon_display()

    def update_icon_display(self):
        if self.icon_file:
            self.icon_label.setText(f"Selected icon: {os.path.basename(self.icon_file)}")
            icon_pixmap = QPixmap(self.icon_file)
            if not icon_pixmap.isNull():
                icon_pixmap = icon_pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio)
                self.icon_label.setPixmap(icon_pixmap)
            else:
                self.icon_label.setText(f"Selected icon: {os.path.basename(self.icon_file)} (Preview not available)")
        else:
            self.icon_label.setText("No icon selected (default app icon will be used)")
            self.icon_label.setPixmap(QPixmap())
    
    def browse_output(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Bound File", "", "Executable (*.exe)")
        if file_name:
            self.output_edit.setText(file_name)
            self.output_file = file_name
    
    def bind_files(self):
        if len(self.selected_files) < 2:
            QMessageBox.warning(self, "Warning", "Please select at least two files to bind.")
            return
        
        if not self.output_file:
            QMessageBox.warning(self, "Warning", "Please specify an output file.")
            return
        
        self.progress_bar.setVisible(True)
        self.cancel_button.setVisible(True)
        self.log_display.clear()
        
        icon_to_use = self.icon_file if self.icon_file else self.default_icon
        self.binder_thread = BinderThread(self.selected_files, self.output_file, icon_to_use)
        self.binder_thread.progress.connect(self.update_progress)
        self.binder_thread.log.connect(self.update_log)
        self.binder_thread.finished.connect(self.binding_finished)
        self.binder_thread.start()
    
    def update_progress(self,
value):
        self.progress_bar.setValue(value)
    
    def update_log(self, message):
        self.log_display.append(message)
        self.tabs.setCurrentIndex(2)  # Switch to Log tab
    
    def binding_finished(self):
        self.progress_bar.setVisible(False)
        self.cancel_button.setVisible(False)
        if not self.binder_thread.cancelled:
            QMessageBox.information(self, "Success", "Bound file created successfully!")
        else:
            QMessageBox.information(self, "Cancelled", "File binding process was cancelled.")
    
    def cancel_binding(self):
        if self.binder_thread and self.binder_thread.isRunning():
            self.binder_thread.cancel()
            self.log_display.append("Cancelling binding process...")
    
    def show_about(self):
        about_dialog = AboutDialog(self)
        about_dialog.exec()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    binder = FileBinder()
    binder.show()
    sys.exit(app.exec())

