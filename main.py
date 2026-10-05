"""
CLI entry point to generate video according to instructions using Google Flow / Veo engine.
"""

import argparse
import sys
from google_flow_video import GoogleFlowVideoClient


def main():
    parser = argparse.ArgumentParser(
        description="Generate videos from instructions using Google's video generation engine (Veo / Google Flow)."
    )
    parser.add_argument(
        "--prompt",
        "-p",
        type=str,
        required=True,
        help="Text instructions describing the video to generate (e.g. 'Cinematic sunset over mountain peak with golden light, drone camera sweeping left')",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="output.mp4",
        help="Output file path (default: output.mp4)",
    )
    parser.add_argument(
        "--duration",
        "-d",
        type=int,
        default=5,
        help="Duration in seconds (e.g. 5)",
    )
    parser.add_argument(
        "--aspect-ratio",
        "-a",
        type=str,
        choices=["16:9", "9:16"],
        default="16:9",
        help="Aspect ratio: '16:9' (landscape/widescreen) or '9:16' (portrait/shorts)",
    )
    parser.add_argument(
        "--resolution",
        "-r",
        type=str,
        choices=["720p", "1080p"],
        default="720p",
        help="Resolution: '720p' or '1080p'",
    )
    parser.add_argument(
        "--image",
        "-i",
        type=str,
        default=None,
        help="Optional path to starting image for Image-to-Video generation",
    )
    parser.add_argument(
        "--no-enhance",
        action="store_true",
        help="Disable automatic prompt enhancement",
    )

    args = parser.parse_args()

    try:
        client = GoogleFlowVideoClient()

        if args.image:
            print(f"Generating video from image: {args.image}")
            output_file = client.generate_from_image(
                image_path=args.image,
                prompt=args.prompt,
                output_path=args.output,
                duration_seconds=args.duration,
                aspect_ratio=args.aspect_ratio,
                resolution=args.resolution,
            )
        else:
            output_file = client.generate_video(
                prompt=args.prompt,
                output_path=args.output,
                duration_seconds=args.duration,
                aspect_ratio=args.aspect_ratio,
                resolution=args.resolution,
                enhance_prompt=not args.no_enhance,
            )

        print(f"\n[Success] Your video has been generated and saved to: {output_file}")

    except Exception as e:
        print(f"\n[Error] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
