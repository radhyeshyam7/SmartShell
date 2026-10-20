from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging
from datetime import datetime

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, llm_translator):
        self.llm_translator = llm_translator
        self.recent_changes = []

    def on_created(self, event):
        if not event.is_directory:
            self._handle_change('created', event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self._handle_change('modified', event.src_path)

    def _handle_change(self, action, path):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.recent_changes.append({
            'action': action,
            'path': path,
            'timestamp': timestamp
        })
        logging.info(f"File {action}: {path}")

class FileMonitor:
    def __init__(self, llm_translator, path="."):
        self.event_handler = FileChangeHandler(llm_translator)
        self.observer = Observer()
        self.observer.schedule(self.event_handler, path, recursive=False)

    def start(self):
        self.observer.start()

    def stop(self):
        self.observer.stop()
        self.observer.join()

    def get_recent_changes(self):
        return self.event_handler.recent_changes
