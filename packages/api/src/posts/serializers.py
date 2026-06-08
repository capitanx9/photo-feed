import logging

from botocore.exceptions import BotoCoreError, NoCredentialsError
from common.s3 import make_download_presign
from rest_framework import serializers

from .models import Post, PostMedia

logger = logging.getLogger(__name__)

# ======================================================================
# PostMedia payload
# ======================================================================


class PostMediaSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = PostMedia
        fields = ["id", "kind", "status", "url", "created_at"]
        read_only_fields = fields

    def get_url(self, obj: PostMedia) -> str | None:
        key = obj.s3_key_resized or obj.s3_key_raw
        if not key or obj.status != PostMedia.Status.READY:
            return None
        try:
            return make_download_presign(key=key)
        except (NoCredentialsError, BotoCoreError):
            # Local dev without AWS creds (or seed data with placeholder keys) —
            # don't 500 the whole feed, just hide the URL.
            logger.warning("Skipping presign for %s — no AWS credentials available.", key)
            return None


# ======================================================================
# Post payload
# ======================================================================


class PostSerializer(serializers.ModelSerializer):
    media = PostMediaSerializer(many=True, read_only=True)
    owner_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Post
        fields = ["id", "owner_id", "caption", "price", "status", "media", "created_at"]
        read_only_fields = ["id", "owner_id", "status", "media", "created_at"]


class PostCreateSerializer(serializers.Serializer):
    caption = serializers.CharField(allow_blank=True, required=False, default="")
    price = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )
    media_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)


# ======================================================================
# Upload presign request/response
# ======================================================================


class UploadURLRequestSerializer(serializers.Serializer):
    content_type = serializers.CharField()
    content_length = serializers.IntegerField(min_value=1)
    kind = serializers.ChoiceField(
        choices=PostMedia.Kind.choices,
        default=PostMedia.Kind.POST,
    )


class UploadURLResponseSerializer(serializers.Serializer):
    media_id = serializers.IntegerField()
    upload_url = serializers.URLField()
    s3_key = serializers.CharField()
    expires_in = serializers.IntegerField()


# ======================================================================
# Webhook payload (Lambda -> Django)
# ======================================================================


class MediaProcessedSerializer(serializers.Serializer):
    s3_key = serializers.CharField()
    s3_key_resized = serializers.CharField(allow_blank=True, required=False, default="")
    status = serializers.ChoiceField(choices=[PostMedia.Status.READY, PostMedia.Status.FAILED])
