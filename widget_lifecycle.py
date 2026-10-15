"""Remove scaling subscriptions before disposing an owned Tk widget subtree."""
from customtkinter.windows.widgets.scaling.scaling_base_class import CTkScalingBaseClass

def destroy_tree(widget):
    # Popup menus can be absent from winfo_children. Tk's Python children
    # registry still owns them. CTk5.2 DropdownMenu.destroy omits scaling
    # cleanup, so later density changes otherwise call a destroyed Tcl menu.
    for child in list(widget.children.values()):destroy_tree(child)
    if isinstance(widget,CTkScalingBaseClass):CTkScalingBaseClass.destroy(widget)
    widget.destroy()
