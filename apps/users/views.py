from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
import openai
from core.settings.base import OPENAI_API_KEY
from openai import OpenAI
from .serializers import TravelPlanSerializer
from datetime import datetime


class TravelPlanAPIView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Sayohat rejasini yaratadi va AI yordamida o'zbek tilida batafsil reja tuzadi.",
        request_body=TravelPlanSerializer,
        responses={
            200: openapi.Response(
                description="Sayohat rejasi muvaffaqiyatli yaratildi",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING,
                                                  example="Sayohat rejasi muvaffaqiyatli yaratildi"),
                        'travel_plan': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'location': openapi.Schema(type=openapi.TYPE_STRING, example="Toshkent"),
                                'start_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE,
                                                             example="2025-05-01"),
                                'end_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE,
                                                           example="2025-05-07"),
                                'budget_from': openapi.Schema(type=openapi.TYPE_NUMBER, example=500.0),
                                'budget_to': openapi.Schema(type=openapi.TYPE_NUMBER, example=1000.0),
                                'interests': openapi.Schema(type=openapi.TYPE_ARRAY,
                                                            items=openapi.Items(type=openapi.TYPE_STRING),
                                                            example=["tarix", "oshxona"]),
                                'having_disability': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                            }
                        ),
                        'ai_itinerary': openapi.Schema(type=openapi.TYPE_STRING,
                                                       example="Toshkent shahriga 2025-yil 1-maydan 7-maygacha sayohat rejasi: 1-kun: Kelish, Hotel Uzbekistanda joylashish...")
                    }
                )
            ),
            400: openapi.Response(
                description="Noto‘g‘ri kiritilgan ma’lumotlar",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'errors': openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 example={"end_date": ["Bu maydon talab qilinadi."]})
                    }
                )
            )
        }
    )
    def post(self, request):
        serializer = TravelPlanSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        # Create a prompt from validated data (in English or Uzbek, AI will handle either)
        prompt = (
            f"{validated_data['location']} shahriga {validated_data['start_date']} dan "
            f"{validated_data['end_date']} gacha sayohat rejasini tuzing. Byudjet: "
            f"{validated_data['budget_from']} So'm - {validated_data['budget_to']} So'm. "
            f"Qiziqishlar: {', '.join(validated_data.get('interests', []))}. "
            f"Nogironlik uchun qulayliklar: {'Ha' if validated_data['having_disability'] else 'Yo‘q'}."
        )

        ai_response = plan_travel(prompt)

        response_data = {
            "message": "Sayohat rejasi muvaffaqiyatli yaratildi",
            "travel_plan": validated_data,
            "ai_itinerary": ai_response
        }

        return Response(response_data, status=status.HTTP_200_OK)


def plan_travel(prompt):
    """
    Sayohatni rejalashtirish uchun OpenAI ga so'rov yuboradi va AI tomonidan yaratilgan sayohat rejasini qaytaradi.
    Javob o'zbek tilida bo'ladi.

    Args:
        prompt (str): Sayohat tafsilotlarini o'z ichiga olgan matn (masalan, manzil, sanalar, byudjet, qiziqishlar).

    Returns:
        str: AI tomonidan yaratilgan sayohat rejasi (o'zbek tilida) yoki xato xabari.
    """
    try:
        # OpenAI klientini ishga tushirish
        client = OpenAI(api_key=OPENAI_API_KEY)

        # OpenAI ga so'rov yuborish
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """Siz sayohatni rejalashtiruvchi yordamchisiz. Sizning vazifangiz foydalanuvchi 
                    kiritgan ma'lumotlarga asoslanib, batafsil va shaxsiylashtirilgan sayohat rejasini tuzishdir. 
                    Foydalanuvchi ma'lumotlari manzil, sayohat sanalari, byudjet, qiziqishlar va maxsus talablarni 
                    (masalan, nogironlik uchun qulayliklar) o'z ichiga olishi mumkin. Aniq, tushunarli va byudjetga
                     mos keladigan sayohat rejasini tuzing, unda tavsiya etilgan faoliyatlar, turar joylar, ovqatlanish 
                     joylari va sayohat bo'yicha maslahatlar bo'lsin. Agar ma'lumotlar noaniq bo'lsa, oqilona taxminlar 
                     qiling va ularni tushuntiring. Javob faqat o'zbek tilida bo'lsin va faqat sayohat rejasiga e'tibor qarating."""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        # AI javobini qaytarish
        return completion.choices[0].message.content

    except Exception as e:
        return f"Xato yuz berdi: {e}"
