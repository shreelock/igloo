import argparse

from automatons import notifier
from automatons import populator
from automatons import jarvis

if __name__ == '__main__':
    parser = argparse.ArgumentParser(usage='run.py [options]')
    parser.add_argument("--populator", action="store_true", help="run populator")
    parser.add_argument("--notifier", action="store_true", help="run notifier")
    parser.add_argument("--jarvis", action="store_true", help="run jarvis")
    args = parser.parse_args()
    
    if args.populator:
        populator.run()
    elif args.notifier:
        notifier.run()
    elif args.jarvis:
        jarvis.poll()
    else:
        parser.print_help()
