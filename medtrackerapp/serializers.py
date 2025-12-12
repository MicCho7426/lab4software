from rest_framework import serializers
from .models import Medication, DoseLog
from django.utils import timezone

class MedicationSerializer(serializers.ModelSerializer):
    adherence = serializers.SerializerMethodField()

    class Meta:
        model = Medication
        fields = ["id", "name", "dosage_mg", "prescribed_per_day", "adherence"]

    def get_adherence(self, obj):
        return obj.adherence_rate()

    def validate_dosage_mg(self, value):
        if value <= 0:
            raise serializers.ValidationError("Dosage must be positive.")
        return value

    def validate_prescribed_per_day(self, value):
        if value <= 0:
            raise serializers.ValidationError("Prescribed amount must be positive.")
        return value


class DoseLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoseLog
        fields = ["id", "medication", "taken_at", "was_taken"]

    def validate_taken_at(self, value):
        if value > timezone.now():
            raise serializers.ValidationError("Date cannot be in the future.")
        return value