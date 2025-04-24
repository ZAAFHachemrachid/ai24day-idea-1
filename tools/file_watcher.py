import time
import sys
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os

class PyFileHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_modified = 0
        self.process = None
        self.start_app()
    
    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            # Debounce multiple events
            current_time = time.time()
            if current_time - self.last_modified < 1:
                return
            self.last_modified = current_time
            
            print(f"\n[*] Python file changed: {event.src_path}")
            self.restart_app()
    
    def start_app(self):
        print("\n[*] Starting application...")
        # Kill existing process if it exists
        if self.process:
            self.process.kill()
            self.process.wait()
        
        # Start the main application
        self.process = subprocess.Popen([sys.executable, 'src/main.py'])
    
    def restart_app(self):
        print("[*] Restarting application...")
        self.start_app()

if __name__ == "__main__":
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Create an observer and file handler
    observer = Observer()
    handler = PyFileHandler()
    
    # Schedule watching the src directory
    src_path = os.path.join(project_root, 'src')
    observer.schedule(handler, src_path, recursive=True)
    observer.start()
    
    print(f"[*] Watching for changes in {src_path}")
    print("[*] Press Ctrl+C to stop")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Stopping file watcher...")
        if handler.process:
            handler.process.kill()
        observer.stop()
        observer.join()