from django.http import FileResponse
from django.urls import reverse
from drf_spectacular.utils import (
    OpenApiTypes,
    extend_schema,
)
from rest_framework import status
from rest_framework.parsers import (
    FormParser,
    MultiPartParser,
)
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from audit.services import AuditService
from uploads.models import UserFile
from uploads.serializers import (
    DownloadLinkResponseSerializer,
    DownloadLinkSerializer,
    UserFileSerializer,
)
from uploads.services import (
    FileDownloadLinkService,
)


class FileUploadAPIView(APIView):
    """Загрузка файла."""

    permission_classes = [
        IsAuthenticated,
    ]

    parser_classes = [
        MultiPartParser,
        FormParser,
    ]

    @extend_schema(
        tags=['Files'],
        request=UserFileSerializer,
        responses={201: UserFileSerializer},
    )
    def post(self, request):
        serializer = UserFileSerializer(
            data=request.data,
            context={
                'request': request,
            },
        )

        serializer.is_valid(raise_exception=True)

        user_file = serializer.save()

        AuditService.log(
            user=request.user,
            actor=request.user,
            action='file_upload',
            obj=user_file,
            new_values={
                'original_name': (user_file.original_name),
                'size': user_file.size,
                'content_type': (user_file.content_type),
            },
            request_id=(
                request.headers.get(
                    'X-Request-ID',
                    '',
                )
            ),
            ip_address=(request.META.get('REMOTE_ADDR')),
            user_agent=(
                request.headers.get(
                    'User-Agent',
                    '',
                )
            ),
        )

        return Response(
            UserFileSerializer(user_file).data,
            status=(status.HTTP_201_CREATED),
        )


class FileDownloadLinkAPIView(APIView):
    """Создать временную ссылку."""

    permission_classes = [
        IsAuthenticated,
    ]

    @extend_schema(
        tags=['Files'],
        request=DownloadLinkSerializer,
        responses={200: (DownloadLinkResponseSerializer)},
    )
    def post(
        self,
        request,
        pk,
    ):
        user_file = UserFile.objects.filter(
            id=pk,
            user=request.user,
        ).first()

        if user_file is None:
            return Response(
                {'detail': ('Файл не найден.')},
                status=(status.HTTP_404_NOT_FOUND),
            )

        serializer = DownloadLinkSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        result = FileDownloadLinkService.create_token(
            user_file=user_file,
            expires_in_seconds=(serializer.validated_data.get('expires_in_seconds')),
        )

        url = request.build_absolute_uri(
            reverse(
                'public-file-download',
                kwargs={
                    'token': (result['token']),
                },
            )
        )

        return Response(
            {
                'data': {
                    'url': url,
                    'expires_at': (result['expires_at']),
                }
            },
            status=status.HTTP_200_OK,
        )


class FileDeleteAPIView(APIView):
    """Удалить свой файл."""

    permission_classes = [
        IsAuthenticated,
    ]

    @extend_schema(
        tags=['Files'],
        request=None,
        responses={
            204: None,
        },
    )
    def delete(
        self,
        request,
        pk,
    ):
        user_file = UserFile.objects.filter(
            id=pk,
            user=request.user,
        ).first()

        if user_file is None:
            return Response(
                {'detail': ('Файл не найден.')},
                status=(status.HTTP_404_NOT_FOUND),
            )

        AuditService.log(
            user=request.user,
            actor=request.user,
            action='file_delete',
            obj=user_file,
            old_values={
                'original_name': (user_file.original_name),
                'size': user_file.size,
            },
            request_id=(
                request.headers.get(
                    'X-Request-ID',
                    '',
                )
            ),
            ip_address=(request.META.get('REMOTE_ADDR')),
            user_agent=(
                request.headers.get(
                    'User-Agent',
                    '',
                )
            ),
        )

        if user_file.file:
            user_file.file.delete(save=False)

        user_file.delete()

        return Response(status=(status.HTTP_204_NO_CONTENT))


class PublicFileDownloadAPIView(APIView):
    """Скачивание по временной ссылке."""

    permission_classes = [
        AllowAny,
    ]

    authentication_classes = []

    @extend_schema(
        tags=['Files'],
        auth=[],
        responses={
            (
                200,
                'application/octet-stream',
            ): OpenApiTypes.BINARY,
        },
    )
    def get(
        self,
        request,
        token,
    ):
        try:
            file_id = FileDownloadLinkService.validate_token(token)

        except ValueError:
            return Response(
                {'detail': ('Ссылка недействительна или истекла.')},
                status=(status.HTTP_404_NOT_FOUND),
            )

        user_file = UserFile.objects.filter(id=file_id).first()

        if user_file is None or not user_file.file:
            return Response(
                {'detail': ('Файл не найден.')},
                status=(status.HTTP_404_NOT_FOUND),
            )

        user_file.file.open('rb')

        return FileResponse(
            user_file.file,
            content_type=(user_file.content_type or 'application/octet-stream'),
            as_attachment=True,
            filename=(user_file.original_name),
        )
