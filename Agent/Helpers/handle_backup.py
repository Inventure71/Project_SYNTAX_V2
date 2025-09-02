import shutil

def delete_backup(backup_path: str = "Backup") -> None:
    """
    Delete a backup of the file.
    """
    shutil.rmtree(backup_path, ignore_errors=True)


def save_backup(file_path: str = "Game", backup_path: str = "Backup") -> None:
    """
    Save a backup of the file.
    """

    shutil.copytree(file_path, backup_path, dirs_exist_ok=True)


def restore_backup(file_path: str = "Game", backup_path: str = "Backup", auto_delete: bool = False, complete_replace: bool = True) -> None:
    """
    Restore a backup of the file.
    """
    if complete_replace:
        shutil.rmtree(file_path, ignore_errors=True)

    shutil.copytree(backup_path, file_path, dirs_exist_ok=True)

    if auto_delete:
        delete_backup(backup_path)


