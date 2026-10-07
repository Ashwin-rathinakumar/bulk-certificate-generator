import os
import uuid
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from app.core.config import settings


def ensure_certificate_template() -> Path:
    """
    Ensures that the predefined certificate template PNG file exists.
    If it does not exist, generates a crisp professional certificate template.
    """
    template_path = settings.template_path
    if template_path.exists():
        return template_path

    # Ensure parent templates directory exists
    template_path.parent.mkdir(parents=True, exist_ok=True)

    # Dimensions for landscape certificate (1600 x 1200)
    width, height = 1600, 1200
    background_color = (252, 252, 250)  # Soft cream/parchment
    border_gold = (212, 175, 55)         # Gold border
    border_navy = (24, 43, 73)           # Navy outer border

    image = Image.new("RGB", (width, height), background_color)
    draw = ImageDraw.Draw(image)

    # Outer Navy Border
    draw.rectangle([30, 30, width - 30, height - 30], outline=border_navy, width=6)
    # Inner Gold Border
    draw.rectangle([45, 45, width - 45, height - 45], outline=border_gold, width=3)
    # Thin Inner Border
    draw.rectangle([55, 55, width - 55, height - 55], outline=border_navy, width=1)

    # Header Ribbon / Banner background line
    draw.line([200, 220, width - 200, 220], fill=border_gold, width=2)
    draw.line([200, 225, width - 200, 225], fill=border_navy, width=1)

    # Footer Line
    draw.line([200, height - 200, width - 200, height - 200], fill=border_gold, width=2)

    image.save(template_path, "PNG")
    return template_path


class CertificateService:
    """Service responsible for rendering and saving recipient certificates."""

    def __init__(self):
        self.template_path = ensure_certificate_template()

    def _get_font(self, size: int):
        """Attempts to load a clean TrueType font, falling back to PIL default font if unavailable."""
        # Common fonts on Windows / cross-platform with good Unicode coverage
        font_candidates = ["arial.ttf", "calibri.ttf", "DejaVuSans.ttf", "FreeSans.ttf"]
        for font_name in font_candidates:
            try:
                return ImageFont.truetype(font_name, size)
            except IOError:
                continue
        # Fallback to default Pillow font if system fonts aren't found
        return ImageFont.load_default()

    def _get_fitted_font(self, text: str, initial_size: int, max_width: int, draw: ImageDraw.Draw):
        """
        Dynamically reduces font size so text fits within max_width without overflowing margins.
        """
        current_size = initial_size
        min_size = 18
        while current_size > min_size:
            font = self._get_font(current_size)
            try:
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
            except Exception:
                text_width = len(text) * (current_size * 0.6)
            
            if text_width <= max_width:
                return font
            current_size -= 4
        return self._get_font(min_size)

    def generate_certificate(
        self,
        recipient_name: str,
        recipient_email: str,
        certificate_title: str,
        organization: str,
        issue_date: str,
        certificate_id: int,
        job_id: int
    ) -> str:
        """
        Generates a personalized PDF certificate for a recipient.
        
        Args:
            recipient_name: Full name of recipient
            recipient_email: Recipient email address
            certificate_title: Title/Course name for the certificate
            organization: Issuing organization
            issue_date: Date of issuance (YYYY-MM-DD)
            certificate_id: DB ID of the certificate
            job_id: DB ID of the parent job

        Returns:
            str: Relative or absolute path to the generated PDF file.
        """
        # Ensure template exists
        if not self.template_path.exists():
            ensure_certificate_template()

        image = Image.open(self.template_path).convert("RGB")
        draw = ImageDraw.Draw(image)
        width, height = image.size
        max_content_width = width - 300  # Leave 150px margin on each side

        navy_color = (24, 43, 73)
        gold_color = (180, 140, 20)
        dark_gray = (60, 60, 60)

        # Load static fonts
        header_font = self._get_font(52)
        subtitle_font = self._get_font(28)
        body_font = self._get_font(32)
        footer_font = self._get_font(24)

        # Dynamically fit recipient name and certificate title fonts
        name_font = self._get_fitted_font(recipient_name, initial_size=60, max_width=max_content_width, draw=draw)
        title_font = self._get_fitted_font(certificate_title, initial_size=44, max_width=max_content_width, draw=draw)

        # Draw static headers
        draw.text((width / 2, 140), "CERTIFICATE OF COMPLETION", fill=navy_color, font=header_font, anchor="mm")
        draw.text((width / 2, 320), "THIS IS PROUDLY PRESENTED TO", fill=gold_color, font=subtitle_font, anchor="mm")

        # Draw Recipient Name (Center)
        draw.text((width / 2, 430), recipient_name, fill=navy_color, font=name_font, anchor="mm")
        draw.line([300, 480, width - 300, 480], fill=navy_color, width=2)

        # Draw Context Line
        draw.text((width / 2, 570), "FOR SUCCESSFULLY COMPLETING THE REQUIREMENTS FOR", fill=dark_gray, font=body_font, anchor="mm")

        # Draw Certificate Title
        draw.text((width / 2, 670), certificate_title, fill=gold_color, font=title_font, anchor="mm")

        # Draw Organization and Date
        info_str = f"Issued by {organization} on {issue_date}"
        draw.text((width / 2, 800), info_str, fill=dark_gray, font=body_font, anchor="mm")

        # Draw Certificate Footer & Verification ID
        cert_ref = f"Certificate ID: CERT-{job_id:04d}-{certificate_id:06d}"
        draw.text((width / 2, height - 120), cert_ref, fill=(120, 120, 120), font=footer_font, anchor="mm")

        # Ensure output directory exists
        output_dir = settings.generated_dir_path

        # Generate unique PDF filename to avoid collisions or path traversal
        safe_uuid = uuid.uuid4().hex[:8]
        filename = f"certificate_{job_id}_{certificate_id}_{safe_uuid}.pdf"
        output_path = output_dir / filename

        # Save image converted to PDF format
        image.save(output_path, "PDF")

        return str(output_path)


certificate_service = CertificateService()
