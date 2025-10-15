# -*- coding: utf-8 -*-
import os
import shutil

from qtpy import QtWidgets

from ayon_local_config.logger import log
from ayon_local_config.plugin import LocalConfigCompatibleAction


class CopyProgressDialog(QtWidgets.QDialog):
    """Progress dialog for file copying operations"""

    def __init__(self, parent=None, total_files=0):
        super().__init__(parent)
        self.setWindowTitle("Copying Files...")
        self.setModal(True)
        self.setFixedSize(400, 150)

        # Create layout
        layout = QtWidgets.QVBoxLayout()

        # Status label
        self.status_label = QtWidgets.QLabel("Preparing to copy files...")
        layout.addWidget(self.status_label)

        # Progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setMaximum(total_files)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Cancel button
        self.cancel_button = QtWidgets.QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_operation)
        layout.addWidget(self.cancel_button)

        self.setLayout(layout)
        self.cancelled = False

    def cancel_operation(self):
        """Mark operation as cancelled"""
        self.cancelled = True
        self.close()

    def update_progress(self, current_file, file_count, current_file_path):
        """Update progress bar and status"""
        self.progress_bar.setValue(file_count)
        self.status_label.setText(
            f"Copying {file_count}/{self.progress_bar.maximum()}: {os.path.basename(current_file_path)}"
        )
        QtWidgets.QApplication.processEvents()

    def set_status(self, message):
        """Set status message"""
        self.status_label.setText(message)
        QtWidgets.QApplication.processEvents()


class ScanningProgressDialog(QtWidgets.QDialog):
    """Progress dialog for file scanning operations"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Scanning Files...")
        self.setModal(True)
        self.setFixedSize(400, 120)

        # Create layout
        layout = QtWidgets.QVBoxLayout()

        # Status label
        self.status_label = QtWidgets.QLabel("Scanning directory for files...")
        layout.addWidget(self.status_label)

        # Progress bar (indeterminate for scanning)
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        layout.addWidget(self.progress_bar)

        # Cancel button
        self.cancel_button = QtWidgets.QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_operation)
        layout.addWidget(self.cancel_button)

        self.setLayout(layout)
        self.cancelled = False

    def cancel_operation(self):
        """Mark operation as cancelled"""
        self.cancelled = True
        self.close()

    def set_status(self, message):
        """Set status message"""
        self.status_label.setText(message)
        QtWidgets.QApplication.processEvents()

    def set_determinate_progress(self, current, total):
        """Switch to determinate progress bar"""
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(current)
        QtWidgets.QApplication.processEvents()


class SetAyonSandboxPathAction(LocalConfigCompatibleAction):
    """Action to manage AYON local sandbox path changes"""

    # AYON action metadata
    name = "set_ayon_sandbox_path"
    label = "Set AYON Sandbox Path"
    icon = None
    color = "#4a90e2"
    order = 50

    # Canonical AYON families approach
    families = ["local_config"]

    def execute_with_config(self, config_data):
        """Execute the sandbox path management action"""
        log.info(
            f"SetAyonSandboxPathAction.execute_with_config called with config_data keys: {list(config_data.keys())}"
        )
        try:
            # Get current and new sandbox paths
            current_sandbox = self._get_current_sandbox_path()
            new_sandbox = self._get_new_sandbox_path(config_data)

            if not new_sandbox:
                QtWidgets.QMessageBox.warning(
                    None,
                    "No Sandbox Path",
                    "No AYON Local Sandbox Path found in configuration.\n"
                    "Please set the AYON Local Sandbox Path in your local settings.",
                )
                return

            # Normalize paths
            current_sandbox = (
                os.path.normpath(current_sandbox) if current_sandbox else None
            )
            new_sandbox = os.path.normpath(new_sandbox)

            # Check if paths are the same
            if current_sandbox and os.path.samefile(current_sandbox, new_sandbox):
                log.info(f"AYON Local Sandbox Path is already set to: {new_sandbox}")
                # Still update the environment variable to ensure it's registered
                self._update_environment_variable(new_sandbox)
                return

            # Check if current sandbox exists and has files
            if current_sandbox and os.path.exists(current_sandbox):
                # Show scanning progress dialog
                scanning_dialog = ScanningProgressDialog(None)
                scanning_dialog.show()
                scanning_dialog.set_status("Scanning sandbox directory for files...")
                QtWidgets.QApplication.processEvents()

                try:
                    # Scan for files with progress tracking
                    files_to_copy = self._get_sandbox_files(
                        current_sandbox, scanning_dialog
                    )

                    if scanning_dialog.cancelled:
                        scanning_dialog.close()
                        log.info("File scanning was cancelled by user")
                        return

                    if files_to_copy:
                        # Calculate total size with progress tracking
                        scanning_dialog.set_status("Calculating total file size...")
                        total_size_gb = self._calculate_total_size(
                            files_to_copy, scanning_dialog
                        )

                        if scanning_dialog.cancelled:
                            scanning_dialog.close()
                            log.info("Size calculation was cancelled by user")
                            return

                        # Close scanning dialog
                        scanning_dialog.close()

                        # Ask user if they want to copy files with detailed information
                        reply = QtWidgets.QMessageBox.question(
                            None,
                            "Copy Sandbox Files?",
                            f"Found {len(files_to_copy)} files ({total_size_gb:.2f} GB) in current sandbox:\n{current_sandbox}\n\n"
                            f"Do you want to copy these files to the new sandbox path?\n{new_sandbox}",
                            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                            QtWidgets.QMessageBox.Yes,
                        )
                    else:
                        # Close scanning dialog
                        scanning_dialog.close()

                        QtWidgets.QMessageBox.information(
                            None,
                            "Sandbox Path Updated",
                            f"AYON Local Sandbox Path updated to:\n{new_sandbox}\n\n"
                            "No files found in the previous location.",
                        )

                except Exception as e:
                    scanning_dialog.close()
                    log.error(f"Error during file scanning: {e}")
                    QtWidgets.QMessageBox.critical(
                        None,
                        "Scanning Error",
                        f"Error scanning sandbox directory: {str(e)}",
                    )
                    return

                # Handle the copy operation if user confirmed
                if "reply" in locals() and reply == QtWidgets.QMessageBox.Yes:
                    copy_success = self._copy_sandbox_files(
                        current_sandbox, new_sandbox, files_to_copy
                    )

                    if copy_success:
                        # Ask if user wants to delete old files
                        delete_reply = QtWidgets.QMessageBox.question(
                            None,
                            "Delete Old Files?",
                            f"Successfully copied {len(files_to_copy)} files to:\n{new_sandbox}\n\n"
                            f"Do you want to delete the old sandbox directory?\n{current_sandbox}",
                            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                            QtWidgets.QMessageBox.No,
                        )

                        if delete_reply == QtWidgets.QMessageBox.Yes:
                            self._delete_old_sandbox(current_sandbox)
                            QtWidgets.QMessageBox.information(
                                None,
                                "Migration Complete",
                                f"Successfully migrated sandbox:\n"
                                f"From: {current_sandbox}\n"
                                f"To: {new_sandbox}\n\n"
                                f"Old directory has been deleted.",
                            )
                        else:
                            QtWidgets.QMessageBox.information(
                                None,
                                "Files Copied",
                                f"Successfully copied {len(files_to_copy)} files to:\n{new_sandbox}\n\n"
                                f"Old directory preserved at:\n{current_sandbox}",
                            )
                    else:
                        QtWidgets.QMessageBox.warning(
                            None,
                            "Copy Cancelled",
                            "File copy operation was cancelled or failed.\n"
                            "Sandbox path has been updated but files were not copied.",
                        )
                elif "reply" in locals() and reply == QtWidgets.QMessageBox.No:
                    QtWidgets.QMessageBox.information(
                        None,
                        "Sandbox Path Updated",
                        f"AYON Local Sandbox Path updated to:\n{new_sandbox}\n\n"
                        "Files were not copied from the previous location.",
                    )
            else:
                # Current sandbox doesn't exist or is None
                if current_sandbox and not os.path.exists(current_sandbox):
                    log.warning(
                        f"Current sandbox path does not exist: {current_sandbox}"
                    )
                    QtWidgets.QMessageBox.information(
                        None,
                        "Sandbox Path Set",
                        f"AYON Local Sandbox Path set to:\n{new_sandbox}\n\n"
                        f"Previous sandbox path ({current_sandbox}) did not exist, so no files were copied.",
                    )
                else:
                    QtWidgets.QMessageBox.information(
                        None,
                        "Sandbox Path Set",
                        f"AYON Local Sandbox Path set to:\n{new_sandbox}\n\n"
                        "This will be the new location for AYON logs, workfiles, and settings.",
                    )

            # Update environment variable
            self._update_environment_variable(new_sandbox)

        except Exception as e:
            log.error(f"Error in set AYON sandbox path action: {e}")
            QtWidgets.QMessageBox.critical(
                None, "Error", f"Error setting AYON sandbox path: {str(e)}"
            )

    def _get_current_sandbox_path(self):
        """Get the current AYON sandbox path from environment or default"""
        # Check AYON_LOCAL_SANDBOX environment variable
        sandbox_path = os.environ.get("AYON_LOCAL_SANDBOX")
        if sandbox_path:
            return sandbox_path

        # Default to ~/.ayon
        home_dir = os.path.expanduser("~")
        return os.path.join(home_dir, ".ayon")

    def _get_new_sandbox_path(self, config_data):
        """Get the new sandbox path from config data"""
        user_settings = config_data.get("user_settings", {})
        sandbox_path = user_settings.get("ayon_sandbox_folder")
        if sandbox_path:
            # Expand user home directory and normalize path
            sandbox_path = os.path.expanduser(sandbox_path)
            sandbox_path = os.path.normpath(sandbox_path)
        return sandbox_path

    def _get_sandbox_files(self, sandbox_path, progress_dialog=None):
        """Get list of files in the sandbox directory with progress tracking"""
        files_to_copy = []

        try:
            # Count total directories first for progress tracking
            total_dirs = 0
            for root, dirs, files in os.walk(sandbox_path):
                total_dirs += 1
                if progress_dialog and progress_dialog.cancelled:
                    return []

            # Reset for actual scanning
            scanned_dirs = 0
            for root, dirs, files in os.walk(sandbox_path):
                if progress_dialog and progress_dialog.cancelled:
                    return []

                # Update progress
                if progress_dialog:
                    progress_dialog.set_determinate_progress(scanned_dirs, total_dirs)
                    progress_dialog.set_status(
                        f"Scanning directory: {os.path.basename(root)}"
                    )

                for file in files:
                    file_path = os.path.join(root, file)
                    # Skip hidden files and system files
                    if not file.startswith(".") and not file.startswith("~"):
                        files_to_copy.append(file_path)

                scanned_dirs += 1

        except Exception as e:
            log.warning(f"Error scanning sandbox directory {sandbox_path}: {e}")

        return files_to_copy

    def _calculate_total_size(self, files_list, progress_dialog=None):
        """Calculate total size of files in GB with progress tracking"""
        total_size = 0
        total_files = len(files_list)

        for i, file_path in enumerate(files_list):
            if progress_dialog and progress_dialog.cancelled:
                return 0

            # Update progress
            if progress_dialog:
                progress_dialog.set_determinate_progress(i, total_files)
                progress_dialog.set_status(
                    f"Calculating size: {os.path.basename(file_path)}"
                )

            try:
                if os.path.exists(file_path):
                    total_size += os.path.getsize(file_path)
            except (OSError, IOError):
                # Skip files that can't be accessed
                continue

        return total_size / (1024 * 1024 * 1024)  # Convert to GB

    def _copy_sandbox_files(self, source_path, dest_path, files_to_copy):
        """Copy files from source to destination sandbox with progress tracking"""
        progress_dialog = None
        try:
            # Create destination directory if it doesn't exist
            os.makedirs(dest_path, exist_ok=True)

            # Create and show progress dialog
            progress_dialog = CopyProgressDialog(None, len(files_to_copy))
            progress_dialog.show()
            progress_dialog.set_status("Starting copy operation...")
            QtWidgets.QApplication.processEvents()

            copied_files = 0
            for i, source_file in enumerate(files_to_copy):
                # Check if operation was cancelled
                if progress_dialog.cancelled:
                    log.info("File copy operation cancelled by user")
                    return False

                # Calculate relative path from source
                rel_path = os.path.relpath(source_file, source_path)
                dest_file = os.path.join(dest_path, rel_path)

                # Create destination directory if needed
                dest_dir = os.path.dirname(dest_file)
                os.makedirs(dest_dir, exist_ok=True)

                # Copy file
                shutil.copy2(source_file, dest_file)
                copied_files += 1

                # Update progress
                progress_dialog.update_progress(source_file, copied_files, source_file)
                log.debug(f"Copied {source_file} to {dest_file}")

            # Close progress dialog
            progress_dialog.close()
            return True

        except Exception as e:
            if progress_dialog:
                progress_dialog.close()
            log.error(f"Error copying sandbox files: {e}")
            raise

    def _delete_old_sandbox(self, old_sandbox_path):
        """Delete the old sandbox directory after successful migration"""
        try:
            if os.path.exists(old_sandbox_path):
                import shutil

                shutil.rmtree(old_sandbox_path)
                log.info(f"Deleted old sandbox directory: {old_sandbox_path}")
            else:
                log.warning(f"Old sandbox directory not found: {old_sandbox_path}")
        except Exception as e:
            log.error(f"Error deleting old sandbox directory {old_sandbox_path}: {e}")
            # Don't raise the exception - the migration was successful, just cleanup failed
            QtWidgets.QMessageBox.warning(
                None,
                "Cleanup Warning",
                f"Files were successfully copied, but failed to delete old directory:\n{old_sandbox_path}\n\n"
                f"Error: {str(e)}\n\n"
                "You may need to manually delete the old directory.",
            )

    def _update_environment_variable(self, new_sandbox_path):
        """Update the AYON_LOCAL_SANDBOX environment variable using the registry"""
        self.register_environment_variable(
            "AYON_LOCAL_SANDBOX",
            new_sandbox_path,
            "AYON Local Sandbox Path - automatically set by Local Config addon",
        )
        log.info(f"Registered AYON_LOCAL_SANDBOX with registry: {new_sandbox_path}")
