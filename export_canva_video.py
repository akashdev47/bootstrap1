"""
Export any Canva design as an MP4 video using the Canva Connect API.
"""

import argparse
import sys
import re
from canva_client import CanvaClient


def extract_design_id(input_str: str) -> str:
    """Extract design ID from either a raw ID or a Canva URL."""
    # Match patterns like https://www.canva.com/design/DAGxxxxxx/...
    match = re.search(r"/design/([A-Za-z0-9_-]+)", input_str)
    if match:
        return match.group(1)
    return input_str.strip()


def main():
    parser = argparse.ArgumentParser(
        description="Export a Canva design as an MP4 video."
    )
    parser.add_argument(
        "--design-id",
        "-d",
        type=str,
        required=True,
        help="Canva Design ID or full Canva design URL (e.g. DAGxxxxxx)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="canva_video.mp4",
        help="Output file path for the exported .mp4 video (default: canva_video.mp4)",
    )
    parser.add_argument(
        "--quality",
        "-q",
        type=str,
        choices=["regular", "high"],
        default="regular",
        help="Export quality: 'regular' or 'high'",
    )

    args = parser.parse_args()
    design_id = extract_design_id(args.design_id)

    print("=" * 60)
    print(" Canva Video Exporter")
    print("=" * 60)
    print(f"Design ID : {design_id}")
    print(f"Output    : {args.output}")
    print(f"Quality   : {args.quality}")
    print("-" * 60)

    try:
        client = CanvaClient()
        output_file = client.export_video_and_download(
            design_id=design_id,
            output_path=args.output,
            verbose=True,
        )
        print("\n" + "=" * 60)
        print(f"[Success] Your Canva video has been exported and downloaded to:")
        print(f"  {output_file}")
        print("=" * 60)
    except Exception as e:
        print(f"\n[Error] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
