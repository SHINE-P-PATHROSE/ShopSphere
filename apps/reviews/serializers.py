"""Review serializers."""
from rest_framework import serializers
from .models import Review, ReviewImage


class ReviewImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewImage
        fields = ['id', 'image', 'alt_text']


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    images = ReviewImageSerializer(many=True, read_only=True)

    class Meta:
        model = Review
        fields = [
            'id', 'user', 'user_name', 'product', 'rating', 'title', 'body',
            'is_verified_purchase', 'helpful_count', 'images', 'created_at',
        ]
        read_only_fields = ['user', 'is_verified_purchase', 'helpful_count']


class ReviewCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    rating = serializers.IntegerField(min_value=1, max_value=5)
    title = serializers.CharField(max_length=200, required=False, allow_blank=True)
    body = serializers.CharField()
