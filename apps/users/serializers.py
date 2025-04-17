from rest_framework import serializers


class TravelPlanSerializer(serializers.Serializer):
    location = serializers.CharField(max_length=100)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    budget_from = serializers.FloatField()
    budget_to = serializers.FloatField()
    interests = serializers.ListField(
        child=serializers.CharField(max_length=100), required=False
    )
    having_disability = serializers.BooleanField()