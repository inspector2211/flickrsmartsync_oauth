import os
import sys

if __name__ == "__main__":
    # Access from source
    sys.path.insert(0, os.sep.join(os.path.dirname(__file__).split(os.sep)[:-1]))

    import flickrsmartsync_oauth
    flickrsmartsync_oauth.main()

