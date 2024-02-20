from babelfont.convertors import Convert
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(prog="babelfont", description='Convert between font formats')
    parser.add_argument('input', metavar='IN', help="Input file")
    parser.add_argument('output', metavar='OUT', help="Output file")
    args = parser.parse_args()

    try:
      font = Convert(args.input).load()
    except Exception as e:
      print("Couldn't read %s: %s" % (args.input, e))
      raise e
      sys.exit(1)

    try:
      Convert(args.output).save(font)
    except Exception as e:
      print("Couldn't write %s: %s" % (args.output, e))
      raise e
      sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    sys.exit(main())
