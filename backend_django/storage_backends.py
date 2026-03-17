from django.conf import settings

if settings.USE_S3:
    from storages.backends.s3boto3 import S3Boto3Storage

    from storages.backends.s3boto3 import S3Boto3Storage

    class StaticStorage(S3Boto3Storage):
        location = 'static'
        default_acl = 'public-read'

    class PublicMediaStorage(S3Boto3Storage):
        location = 'media'
        default_acl = 'public-read'
        file_overwrite = False

    class PrivateMediaStorage(S3Boto3Storage):
        location = 'private'
        default_acl = 'private'
        file_overwrite = False
        custom_domain = False

else:
    from django.core.files.storage import FileSystemStorage
    import os
    # Local storage fallback
    class StaticStorage(FileSystemStorage):
        location = os.path.join(settings.BASE_DIR, 'staticfiles')
        base_url = settings.STATIC_URL

    class PublicMediaStorage(FileSystemStorage):
        # By default, FileSystemStorage uses settings.MEDIA_ROOT and settings.MEDIA_URL
        pass

    class PrivateMediaStorage(FileSystemStorage):
        # We define a custom location for private files to keep them separate
        location = os.path.join(settings.BASE_DIR, 'private')
        base_url = '/private/'