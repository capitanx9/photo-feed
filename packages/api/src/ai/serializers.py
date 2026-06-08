import logging

from botocore.exceptions import BotoCoreError, NoCredentialsError
from common.s3 import make_download_presign_for_generated
from django.conf import settings
from rest_framework import serializers

from .models import GenerationJob

logger = logging.getLogger(__name__)

# ======================================================================
# Generation request
# ======================================================================


class GenerationCreateSerializer(serializers.Serializer):
    prompt = serializers.CharField(min_length=1, max_length=500)
    negative_prompt = serializers.CharField(
        allow_blank=True, required=False, default="", max_length=500
    )
    variants_count = serializers.IntegerField(min_value=1, max_value=settings.AI_MAX_VARIANTS)
    aspect_ratio = serializers.ChoiceField(choices=settings.AI_ALLOWED_ASPECT_RATIOS)


# ======================================================================
# Generation job (read)
# ======================================================================


class GenerationJobSerializer(serializers.ModelSerializer):
    image_urls = serializers.SerializerMethodField()

    class Meta:
        model = GenerationJob
        fields = [
            "id",
            "prompt",
            "negative_prompt",
            "variants_count",
            "aspect_ratio",
            "status",
            "image_urls",
            "error",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_image_urls(self, obj: GenerationJob) -> list[str]:
        if obj.status != GenerationJob.Status.READY:
            return []
        try:
            return [make_download_presign_for_generated(key=key) for key in obj.image_keys]
        except (NoCredentialsError, BotoCoreError):
            logger.warning("Skipping presigns for job %s — no AWS credentials available.", obj.pk)
            return []


class GenerationCreateResponseSerializer(serializers.Serializer):
    job_id = serializers.IntegerField()
    status_url = serializers.CharField()
