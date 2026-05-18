from rest_framework import serializers

# ======================================================================
# Error envelope
# ======================================================================


class ErrorSerializer(serializers.Serializer):
    detail = serializers.CharField()


# ======================================================================
# Health payload
# ======================================================================


class HealthSerializer(serializers.Serializer):
    ok = serializers.BooleanField()
