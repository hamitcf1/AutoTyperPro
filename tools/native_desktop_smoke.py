"""Exercise the application's own native Mac menu; sends no keyboard/mouse input."""
from pathlib import Path
import queue
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import customtkinter as ctk
from desktop_integration import DesktopIntegration
if sys.platform!='darwin':raise SystemExit('This native menu smoke test requires macOS')
root=ctk.CTk();events=queue.Queue();desktop=DesktopIntegration(events,Path('assets/icon.png'))
try:
    assert desktop.start();desktop.update('Ready');root.update()
    menu=desktop.driver.status_item.menu()
    for command in ('open','stop_all','about','quit'):
        index=next(i for i in range(menu.numberOfItems()) if menu.itemAtIndex_(i).representedObject()==command)
        menu.performActionForItemAtIndex_(index);assert events.get_nowait()==command
    desktop.stop();assert not desktop.ready and desktop.driver.status_item is None
    desktop.enqueue('open');assert events.empty()
    print('Native Mac desktop PASS: menu commands, queue delivery, status item cleanup, late callbacks ignored')
finally:
    desktop.stop();root.destroy()
