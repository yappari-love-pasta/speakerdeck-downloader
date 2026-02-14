#!/usr/bin/env python3
"""
SpeakerDeck PDF Downloader
Downloads presentations from SpeakerDeck as PDF files.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image
from io import BytesIO


class SpeakerDeckDownloader:
    """Downloads SpeakerDeck presentations as PDF."""

    def __init__(self, url: str, output_dir: str = "."):
        self.url = url
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def validate_url(self) -> bool:
        """Validate if the URL is a valid SpeakerDeck URL."""
        pattern = r'^https?://speakerdeck\.com/[\w-]+/[\w-]+$'
        return bool(re.match(pattern, self.url))

    def get_presentation_info(self) -> dict:
        """Extract presentation information from the page."""
        print(f"Fetching presentation info from: {self.url}")

        try:
            response = self.session.get(self.url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching URL: {e}")
            sys.exit(1)

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract title
        title_tag = soup.find('meta', property='og:title')
        title = title_tag['content'] if title_tag else 'presentation'

        # Clean title for filename
        title = re.sub(r'[^\w\s-]', '', title).strip()
        title = re.sub(r'[-\s]+', '-', title)

        # Find presentation ID and slide count
        presentation_id = None
        slide_count = 0

        # Method 1: Extract from img tags in the page
        img_tags = soup.find_all('img', src=re.compile(r'files\.speakerdeck\.com/presentations/'))
        if img_tags:
            for img in img_tags:
                src = img.get('src', '')
                match = re.search(r'presentations/([a-f0-9]+)/(?:preview_)?slide_(\d+)\.jpg', src)
                if match:
                    presentation_id = match.group(1)
                    slide_num = int(match.group(2))
                    slide_count = max(slide_count, slide_num + 1)

        # Method 2: Extract from JSON-LD schema
        if not presentation_id:
            json_ld = soup.find('script', type='application/ld+json')
            if json_ld:
                import json
                try:
                    data = json.loads(json_ld.string)
                    thumbnail_url = data.get('thumbnailUrl', '')
                    match = re.search(r'presentations/([a-f0-9]+)/', thumbnail_url)
                    if match:
                        presentation_id = match.group(1)
                except:
                    pass

        # Method 3: Extract from any URL in the page
        if not presentation_id:
            all_text = response.text
            match = re.search(r'files\.speakerdeck\.com/presentations/([a-f0-9]+)/', all_text)
            if match:
                presentation_id = match.group(1)

        # Try to find slide count from meta tags
        if slide_count == 0:
            # Look for slide count in page content
            page_text = soup.get_text()
            match = re.search(r'(\d+)\s*slides?', page_text, re.IGNORECASE)
            if match:
                slide_count = int(match.group(1))

        # If we still don't have slide count, try to find it by testing URLs
        if slide_count == 0 and presentation_id:
            print("Detecting number of slides...")
            slide_count = self._detect_slide_count(presentation_id)

        if not presentation_id:
            print("Error: Could not find presentation ID.")
            sys.exit(1)

        if slide_count == 0:
            print("Error: Could not determine the number of slides.")
            sys.exit(1)

        # Build slide image URLs
        slide_images = []
        for i in range(slide_count):
            url = f"https://files.speakerdeck.com/presentations/{presentation_id}/slide_{i}.jpg"
            slide_images.append(url)

        print(f"Found presentation ID: {presentation_id}")
        print(f"Total slides: {slide_count}")

        return {
            'title': title,
            'slide_images': slide_images,
            'total_slides': len(slide_images)
        }

    def _detect_slide_count(self, presentation_id: str, max_slides: int = 300) -> int:
        """Detect the number of slides by binary search."""
        def slide_exists(slide_num: int) -> bool:
            url = f"https://files.speakerdeck.com/presentations/{presentation_id}/slide_{slide_num}.jpg"
            try:
                response = self.session.head(url, timeout=10)
                return response.status_code == 200
            except:
                return False

        # Binary search for the last slide
        left, right = 0, max_slides
        last_valid = 0

        while left <= right:
            mid = (left + right) // 2
            if slide_exists(mid):
                last_valid = mid
                left = mid + 1
            else:
                right = mid - 1

        return last_valid + 1 if last_valid >= 0 else 0

    def download_image(self, url: str) -> Image.Image:
        """Download and return an image."""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return Image.open(BytesIO(response.content))
        except Exception as e:
            print(f"Error downloading image {url}: {e}")
            raise

    def create_pdf(self, info: dict) -> str:
        """Create PDF from slide images."""
        output_file = self.output_dir / f"{info['title']}.pdf"

        print(f"\nDownloading {info['total_slides']} slides...")

        # Download first image to get dimensions
        first_image = self.download_image(info['slide_images'][0])
        page_width, page_height = first_image.size

        # Create PDF
        c = canvas.Canvas(str(output_file), pagesize=(page_width, page_height))

        for i, img_url in enumerate(info['slide_images'], 1):
            print(f"Processing slide {i}/{info['total_slides']}...", end='\r')

            try:
                img = self.download_image(img_url)

                # Save image to temporary bytes buffer
                img_buffer = BytesIO()
                img.save(img_buffer, format='JPEG')
                img_buffer.seek(0)

                # Draw image on PDF using ImageReader
                img_reader = ImageReader(img_buffer)
                c.drawImage(
                    img_reader,
                    0, 0,
                    width=page_width,
                    height=page_height
                )

                if i < info['total_slides']:
                    c.showPage()

            except Exception as e:
                print(f"\nWarning: Failed to process slide {i}: {e}")
                continue

        c.save()
        print(f"\n\nPDF saved successfully: {output_file}")
        return str(output_file)

    def download(self) -> str:
        """Main download method."""
        if not self.validate_url():
            print("Error: Invalid SpeakerDeck URL format.")
            print("Expected format: https://speakerdeck.com/username/presentation-name")
            sys.exit(1)

        info = self.get_presentation_info()
        return self.create_pdf(info)


def main():
    parser = argparse.ArgumentParser(
        description='Download SpeakerDeck presentations as PDF files.'
    )
    parser.add_argument(
        'url',
        help='SpeakerDeck presentation URL (e.g., https://speakerdeck.com/username/presentation)'
    )
    parser.add_argument(
        '-o', '--output',
        default='.',
        help='Output directory (default: current directory)'
    )

    args = parser.parse_args()

    downloader = SpeakerDeckDownloader(args.url, args.output)
    downloader.download()


if __name__ == '__main__':
    main()
