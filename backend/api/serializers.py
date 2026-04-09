"""
DRF serializers for the API app.
"""
import os
from rest_framework import serializers


class FileUploadSerializer(serializers.Serializer):
    """Validates file upload requests.

    Accepts PDF and TXT files up to 10 MB.
    """

    file = serializers.FileField(required=True)

    ALLOWED_EXTENSIONS = (".pdf", ".txt")
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

    def validate_file(self, value):
        # Check extension
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f"Unsupported file type '{ext}'. "
                f"Allowed types: {', '.join(self.ALLOWED_EXTENSIONS)}"
            )

        # Check file size
        if value.size > self.MAX_FILE_SIZE:
            max_mb = self.MAX_FILE_SIZE // (1024 * 1024)
            raise serializers.ValidationError(
                f"File too large ({value.size / (1024*1024):.1f} MB). "
                f"Maximum allowed: {max_mb} MB."
            )

        return value


class TextInputSerializer(serializers.Serializer):
    """Validates raw text paste requests."""

    text = serializers.CharField(
        required=True,
        allow_blank=False,
        trim_whitespace=True,
        error_messages={
            "blank": "Text input cannot be empty.",
            "required": "The 'text' field is required.",
        },
    )

    def validate_text(self, value):
        if len(value.strip()) < 20:
            raise serializers.ValidationError(
                "Text is too short. Please provide at least 20 characters."
            )
        return value
