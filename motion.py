"""Short, cancellable introduction motion; reduced motion stays immediate."""
def introduce(root,panel,reduced=False):
    generation=getattr(panel,'_motion_generation',0)+1;panel._motion_generation=generation
    if reduced:panel.place_configure(rely=.5);return
    for tick in range(9):
        def frame(index=tick):
            if panel.winfo_exists() and panel._motion_generation==generation:
                progress=index/8
                panel.place_configure(rely=.5+.012*(1-progress)**3)
        root.after(tick*22,frame)
