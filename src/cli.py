from miu import __meta__, main
import argparse


def cli():
    parser = argparse.ArgumentParser(__meta__.__description__)
    parser.add_argument('path', type=str, help="Path where to process audio file(s).")
    parser.add_argument('config', type=str, help="Path where to find JSON configuration.")
    args = parser.parse_args()
    main.MusicInfoUpdater(**vars(args))


if __name__ == "__main__":
    cli()
