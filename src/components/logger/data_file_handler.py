from io import TextIOWrapper
from logging import FileHandler
from pathlib import Path
import datetime

class DataFileHandler(FileHandler):
    def _open(self):
        """Open the current base file with date prefix and ensure directory exists."""
        p = Path(self.baseFilename)
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        new_filename = f"{date_str}{p.name}"
        full_path = p.parent / new_filename
        
        # 确保目录存在
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        return self._builtin_open(
            full_path,
            self.mode,
            encoding=self.encoding,
            errors=self.errors
        )
