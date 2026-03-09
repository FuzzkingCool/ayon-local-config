# -*- coding: utf-8 -*-
import json
import os
import shutil
import traceback
from datetime import datetime

from qtpy import QtWidgets

from ayon_local_config.logger import log
from ayon_local_config.plugin import LocalConfigCompatibleAction


def _save_migration_report(report, dest_dir):
    """Save migration report to a JSON file in dest_dir. Returns path or None."""
    if not report:
        return None
    try:
        os.makedirs(dest_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(
            dest_dir, f"sandbox_migration_report_{timestamp}.json"
        )
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(
                {"summary": {"total_issues": len(report)}, "issues": report},
                f,
                indent=2,
            )
        return report_path
    except Exception as e:
        log.error(f"Failed to save migration report: {e}", exc_info=True)
        return None


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
        log.debug(
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
                log.debug(f"AYON Local Sandbox Path is already set to: {new_sandbox}")
                # Still update the environment variable to ensure it's registered
                self._update_environment_variable(new_sandbox)
                return

            # Check if current sandbox exists and has files
            if current_sandbox and os.path.exists(current_sandbox):
                # Ask user first if they want to migrate files
                migrate_reply = QtWidgets.QMessageBox.question(
                    None,
                    "Migrate Sandbox Files?",
                    f"Current sandbox location:\n{current_sandbox}\n\n"
                    f"New sandbox location:\n{new_sandbox}\n\n"
                    "Do you want to copy files from the current sandbox to the new location?\n\n"
                    "(Selecting 'No' will just update the path without copying any files)",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                    QtWidgets.QMessageBox.Yes,
                )

                if migrate_reply == QtWidgets.QMessageBox.Yes:
                    # Show scanning progress dialog
                    scanning_dialog = ScanningProgressDialog(None)
                    scanning_dialog.show()
                    scanning_dialog.set_status("Scanning sandbox directory for files...")
                    QtWidgets.QApplication.processEvents()

                    try:
                        # Fast count and size calculation with progress tracking
                        file_count, total_size_bytes = self._count_and_size_bytes(
                            current_sandbox, scanning_dialog
                        )

                        if scanning_dialog.cancelled:
                            scanning_dialog.close()
                            log.debug("File scanning was cancelled by user")
                            return

                        # Close scanning dialog
                        scanning_dialog.close()

                        if file_count == 0:
                            QtWidgets.QMessageBox.information(
                                None,
                                "Sandbox Path Updated",
                                f"AYON Local Sandbox Path updated to:\n{new_sandbox}\n\n"
                                "No files found in the previous location.",
                            )
                        else:
                            total_size_gb = total_size_bytes / (1024 * 1024 * 1024)
                            
                            # Confirm copy with detailed information
                            confirm_reply = QtWidgets.QMessageBox.question(
                                None,
                                "Confirm File Copy",
                                f"Found {file_count} files ({total_size_gb:.2f} GB) in current sandbox:\n{current_sandbox}\n\n"
                                f"Copy these files to the new sandbox path?\n{new_sandbox}",
                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                QtWidgets.QMessageBox.Yes,
                            )

                            if confirm_reply == QtWidgets.QMessageBox.Yes:
                                copy_success, report = self._copy_sandbox_files(
                                    current_sandbox, new_sandbox
                                )

                                if copy_success:
                                    # Ask if user wants to delete old files
                                    delete_reply = QtWidgets.QMessageBox.question(
                                        None,
                                        "Delete Old Files?",
                                        f"Successfully copied files to:\n{new_sandbox}\n\n"
                                        f"Do you want to delete the old sandbox directory?\n{current_sandbox}",
                                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                        QtWidgets.QMessageBox.No,
                                    )

                                    if delete_reply == QtWidgets.QMessageBox.Yes:
                                        delete_error = self._delete_old_sandbox(
                                            current_sandbox, report
                                        )
                                    report_path = _save_migration_report(
                                        report, new_sandbox
                                    )
                                    msg_extra = ""
                                    if report_path:
                                        msg_extra = (
                                            f"\n\nA report of {len(report)} issue(s) was saved to:\n{report_path}"
                                        )
                                    if delete_reply == QtWidgets.QMessageBox.Yes:
                                        if not delete_error:
                                            QtWidgets.QMessageBox.information(
                                                None,
                                                "Migration Complete",
                                                f"Successfully migrated sandbox:\n"
                                                f"From: {current_sandbox}\n"
                                                f"To: {new_sandbox}\n\n"
                                                f"Old directory has been deleted."
                                                + msg_extra,
                                            )
                                        else:
                                            QtWidgets.QMessageBox.warning(
                                                None,
                                                "Cleanup Warning",
                                                f"Files were copied to:\n{new_sandbox}\n\n"
                                                f"Failed to delete old directory:\n{current_sandbox}\n\n"
                                                f"Error: {delete_error.get('error', '')}"
                                                + msg_extra,
                                            )
                                    else:
                                        QtWidgets.QMessageBox.information(
                                            None,
                                            "Files Copied",
                                            f"Successfully copied files to:\n{new_sandbox}\n\n"
                                            f"Old directory preserved at:\n{current_sandbox}"
                                            + msg_extra,
                                        )
                                else:
                                    report_path = _save_migration_report(
                                        report, new_sandbox
                                    )
                                    msg = (
                                        "File copy operation was cancelled or failed.\n"
                                        "Sandbox path has been updated but files were not copied."
                                    )
                                    if report_path:
                                        msg += (
                                            f"\n\nA report of {len(report)} issue(s) was saved to:\n{report_path}"
                                        )
                                    QtWidgets.QMessageBox.warning(
                                        None,
                                        "Copy Cancelled",
                                        msg,
                                    )
                            else:
                                QtWidgets.QMessageBox.information(
                                    None,
                                    "Sandbox Path Updated",
                                    f"AYON Local Sandbox Path updated to:\n{new_sandbox}\n\n"
                                    "Files were not copied from the previous location.",
                                )

                    except Exception as e:
                        scanning_dialog.close()
                        log.error(
                            f"Error during file scanning: {e}",
                            exc_info=True,
                        )
                        QtWidgets.QMessageBox.critical(
                            None,
                            "Scanning Error",
                            f"Error scanning sandbox directory: {str(e)}",
                        )
                        return
                else:
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
            log.error(
                f"Error in set AYON sandbox path action: {e}",
                exc_info=True,
            )
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

    def _count_and_size_bytes(self, root_path, progress_dialog=None):
        """Fast count and size calculation using os.scandir with progress tracking"""
        total_size = 0
        file_count = 0
        stack = [root_path]
        processed_dirs = 0

        while stack:
            if progress_dialog and progress_dialog.cancelled:
                return 0, 0

            directory = stack.pop()
            processed_dirs += 1

            # Update progress periodically
            if progress_dialog and processed_dirs % 10 == 0:
                progress_dialog.set_status(
                    f"Scanning: {os.path.basename(directory)}"
                )

            try:
                with os.scandir(directory) as it:
                    for entry in it:
                        try:
                            if entry.is_dir(follow_symlinks=True):
                                stack.append(entry.path)
                            elif entry.is_file(follow_symlinks=True):
                                file_count += 1
                                total_size += entry.stat(follow_symlinks=False).st_size
                        except (PermissionError, OSError):
                            log.debug(
                                f"Skipping (count): {entry.path}",
                                exc_info=True,
                            )
            except (PermissionError, OSError):
                log.debug(
                    f"Skipping directory (count): {directory}",
                    exc_info=True,
                )

        return file_count, total_size

    def _copy_sandbox_files(self, source_path, dest_path):
        """Copy files from source to destination sandbox with progress tracking.

        Returns:
            tuple: (success: bool, report: list of dicts for user-facing errors)
        """
        progress_dialog = None
        report = []
        try:
            # Create destination directory if it doesn't exist
            os.makedirs(dest_path, exist_ok=True)

            # First, count total files to copy for progress bar
            file_count, _ = self._count_and_size_bytes(source_path)

            if file_count == 0:
                return True, report

            # Create and show progress dialog
            progress_dialog = CopyProgressDialog(None, file_count)
            progress_dialog.show()
            progress_dialog.set_status("Starting copy operation...")
            QtWidgets.QApplication.processEvents()

            copied_files = 0
            stack = [source_path]

            while stack:
                # Check if operation was cancelled
                if progress_dialog.cancelled:
                    log.debug("File copy operation cancelled by user")
                    progress_dialog.close()
                    return False, report

                directory = stack.pop()

                try:
                    with os.scandir(directory) as it:
                        for entry in it:
                            try:
                                # Calculate relative path from source
                                rel_path = os.path.relpath(entry.path, source_path)
                                dest_entry = os.path.join(dest_path, rel_path)

                                if entry.is_dir(follow_symlinks=True):
                                    stack.append(entry.path)
                                    try:
                                        os.makedirs(dest_entry, exist_ok=True)
                                    except (PermissionError, OSError) as e:
                                        log.warning(
                                            f"Could not create directory {dest_entry}: {e}",
                                            exc_info=True,
                                        )
                                        report.append(
                                            {
                                                "path": dest_entry,
                                                "kind": "makedirs_failed",
                                                "error": str(e),
                                                "traceback": traceback.format_exc(),
                                            }
                                        )
                                elif entry.is_file(follow_symlinks=True):
                                    dest_dir = os.path.dirname(dest_entry)
                                    os.makedirs(dest_dir, exist_ok=True)
                                    shutil.copy2(entry.path, dest_entry)
                                    copied_files += 1
                                    progress_dialog.update_progress(
                                        entry.path, copied_files, entry.path
                                    )
                                    log.debug(f"Copied {entry.path} to {dest_entry}")
                            except (PermissionError, OSError) as e:
                                log.warning(
                                    f"Skipping {entry.path}: {e}",
                                    exc_info=True,
                                )
                                report.append(
                                    {
                                        "path": entry.path,
                                        "kind": "skip_file",
                                        "error": str(e),
                                        "traceback": traceback.format_exc(),
                                    }
                                )
                                continue
                except (PermissionError, OSError) as e:
                    log.warning(
                        f"Skipping directory {directory}: {e}",
                        exc_info=True,
                    )
                    report.append(
                        {
                            "path": directory,
                            "kind": "skip_directory",
                            "error": str(e),
                            "traceback": traceback.format_exc(),
                        }
                    )
                    continue

            # Close progress dialog
            progress_dialog.close()
            return True, report

        except Exception as e:
            if progress_dialog:
                progress_dialog.close()
            log.error(
                f"Error copying sandbox files: {e}",
                exc_info=True,
            )
            report.append(
                {
                    "path": source_path,
                    "kind": "copy_failed",
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                }
            )
            return False, report

    def _delete_old_sandbox(self, old_sandbox_path, report=None):
        """Delete the old sandbox directory after successful migration.

        Returns:
            None on success, or a report entry dict on failure (for caller to append and show).
        """
        try:
            if os.path.exists(old_sandbox_path):
                shutil.rmtree(old_sandbox_path)
                log.debug(f"Deleted old sandbox directory: {old_sandbox_path}")
            else:
                log.warning(
                    f"Old sandbox directory not found: {old_sandbox_path}"
                )
            return None
        except Exception as e:
            log.error(
                f"Error deleting old sandbox directory {old_sandbox_path}: {e}",
                exc_info=True,
            )
            entry = {
                "path": old_sandbox_path,
                "kind": "delete_failed",
                "error": str(e),
                "traceback": traceback.format_exc(),
            }
            if report is not None:
                report.append(entry)
            return entry

    def _update_environment_variable(self, new_sandbox_path):
        """Update the AYON_LOCAL_SANDBOX environment variable using the registry"""
        self.register_environment_variable(
            "AYON_LOCAL_SANDBOX",
            new_sandbox_path,
            "AYON Local Sandbox Path - automatically set by Local Config addon",
        )
        log.debug(f"Registered AYON_LOCAL_SANDBOX with registry: {new_sandbox_path}")
