"""Pure compact-layout sizing; does not interact with any desktop window."""
def fit_scale(width,height,preferred=1):
    return round(max(.72,min(preferred,width/980,height/740)),3)
