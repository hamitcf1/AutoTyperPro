"""Pure compact-layout sizing; does not interact with any desktop window."""
def fit_scale(width,height,preferred=1):
    return round(max(.72,min(preferred,width/980,height/740)),3)

import customtkinter as ctk

class ResponsiveWindow(ctk.CTk):
    def _set_scaling(self,new_widget_scaling,new_window_scaling):
        # CTk normally locks min/max for a second for *every* widget-scale
        # change. Fit-to-window scaling must not lock the user's resize drag.
        # Keep its normal geometry handling only when the window DPI changes.
        if new_window_scaling==self._get_window_scaling():
            super(ctk.CTk,self)._set_scaling(new_widget_scaling,new_window_scaling)
        else:super()._set_scaling(new_widget_scaling,new_window_scaling)
