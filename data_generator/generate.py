from data_generator.generate_dataset import generate

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate UrbanTransit IQ data")
    parser.add_argument("--size", choices=["demo", "competition"], default="demo")
    args = parser.parse_args()
    generate(args.size)
