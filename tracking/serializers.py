from rest_framework import serializers
from .models import CaseTransition


class CaseTransitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseTransition
        fields = '__all__'