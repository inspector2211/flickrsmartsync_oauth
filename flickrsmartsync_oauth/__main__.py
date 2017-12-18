import os
import sys

if __name__ == "__main__": # if running from source
    module_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(module_dir)
    sys.path.insert(0, parent_dir) # insert parent directory at start of module search path
    import flickrsmartsync_oauth
    flickrsmartsync_oauth.main()
