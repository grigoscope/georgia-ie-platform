from rest_framework import status
from rest_framework.parsers import (
    FormParser,
    MultiPartParser,
)
from rest_framework.permissions import (
    IsAuthenticated,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import (
    EntrepreneurProfile,
)
from accounts.profile_serializers import (
    EntrepreneurProfileSerializer,
    ProfileImageUploadSerializer,
)


class ProfileAPIView(APIView):
    """Просмотр и изменение профиля."""

    serializer_class = EntrepreneurProfileSerializer

    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        profile = EntrepreneurProfile.objects.filter(user=request.user).first()

        if profile is None:
            return Response(
                {
                    'profile_exists': False,
                    'business_name': '',
                    'entrepreneur_status': '',
                    'tin': '',
                    'legal_address': '',
                    'email': '',
                    'phone': '',
                    'tax_rate': '1.00',
                    'accounting_start_date': None,
                    'timezone': 'Asia/Tbilisi',
                    'language': 'ru',
                    'invoice_prefix': 'INV-',
                    'next_invoice_number': 1,
                    'telegram_connected': False,
                    'signature_url': None,
                    'logo_url': None,
                },
                status=status.HTTP_200_OK,
            )

        serializer = EntrepreneurProfileSerializer(
            profile,
            context={
                'request': request,
            },
        )

        data = serializer.data
        data['profile_exists'] = True

        return Response(
            data,
            status=status.HTTP_200_OK,
        )

    def patch(self, request):
        profile = EntrepreneurProfile.objects.filter(user=request.user).first()

        if profile is None:
            missing_fields = []

            if not request.data.get('business_name'):
                missing_fields.append('business_name')

            if not request.data.get('tin'):
                missing_fields.append('tin')

            if missing_fields:
                return Response(
                    {
                        'detail': ('Для создания профиля обязательны business_name и tin.'),
                        'fields': (missing_fields),
                    },
                    status=(status.HTTP_400_BAD_REQUEST),
                )

            serializer = EntrepreneurProfileSerializer(
                data=request.data,
                partial=True,
                context={
                    'request': request,
                },
            )

            serializer.is_valid(raise_exception=True)

            profile = serializer.save(user=request.user)

        else:
            serializer = EntrepreneurProfileSerializer(
                profile,
                data=request.data,
                partial=True,
                context={
                    'request': request,
                },
            )

            serializer.is_valid(raise_exception=True)

            profile = serializer.save()

        result = EntrepreneurProfileSerializer(
            profile,
            context={
                'request': request,
            },
        )

        data = result.data
        data['profile_exists'] = True

        return Response(
            data,
            status=status.HTTP_200_OK,
        )


class ProfileFileAPIView(APIView):
    """
    Базовый endpoint для подписи
    или логотипа.
    """

    serializer_class = ProfileImageUploadSerializer

    permission_classes = [
        IsAuthenticated,
    ]

    parser_classes = [
        MultiPartParser,
        FormParser,
    ]

    field_name = None

    def _get_profile(
        self,
        request,
    ):
        return EntrepreneurProfile.objects.filter(user=request.user).first()

    def post(self, request):
        profile = self._get_profile(request)

        if profile is None:
            return Response(
                {'detail': ('Сначала заполните профиль предпринимателя.')},
                status=(status.HTTP_400_BAD_REQUEST),
            )

        serializer = ProfileImageUploadSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data['file']

        field = getattr(
            profile,
            self.field_name,
        )

        if field:
            field.delete(save=False)

        field.save(
            uploaded_file.name,
            uploaded_file,
            save=False,
        )

        profile.save(
            update_fields=[
                self.field_name,
                'updated_at',
            ]
        )

        response_serializer = EntrepreneurProfileSerializer(
            profile,
            context={
                'request': request,
            },
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request):
        profile = self._get_profile(request)

        if profile is None:
            return Response(status=(status.HTTP_204_NO_CONTENT))

        field = getattr(
            profile,
            self.field_name,
        )

        if field:
            field.delete(save=False)

            setattr(
                profile,
                self.field_name,
                None,
            )

            profile.save(
                update_fields=[
                    self.field_name,
                    'updated_at',
                ]
            )

        return Response(status=(status.HTTP_204_NO_CONTENT))


class ProfileSignatureAPIView(ProfileFileAPIView):
    """Подпись предпринимателя."""

    field_name = 'signature_file'


class ProfileLogoAPIView(ProfileFileAPIView):
    """Логотип предпринимателя."""

    field_name = 'logo_file'
