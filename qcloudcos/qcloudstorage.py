import os
from django.conf import settings
from django.core.files.storage import Storage
from django.core.exceptions import SuspiciousFileOperation
from django.utils.text import get_valid_filename
from django.utils.crypto import get_random_string
from qcloudcos.cos_object import CosObject


class QcloudStorage(Storage):
    # Following methods will have to be overridden:delete(),exists(),listdir(),size(),url()
    def __init__(self, option=None):
        if not option:
            self.option = settings.QCLOUD_STORAGE_OPTION

    def _open(self, name, mode='rb'):
        # Use to open the file
        if name.startswith('http'):
            # 直接存的URL，直接返回，这类数据不支持取content
            return ''
        cos = CosObject()
        if name[0] != '/':
            name = '/' + name
        response = cos.get_object(name, True)
        return response.content

    def _save(self, name, content,max_length=None):
        # Called by Storage.save().
        # The name will already have gone through get_valid_name() and get_available_name(),
        # and the content will be a File object itself
        # Should return the actual name of name of the file saved

        if name.startswith('http'):
            # 直接存的URL，直接返回，这类数据不支持取content
            return name
        name = self._get_valid_name(name)
        name = self._get_available_name(name,max_length=max_length)
        content = content.read()
        cos_object = CosObject()
        response = cos_object.put_object(name, content)
        return response.request.path_url

    def _get_valid_name(self, name):
        # Returns a filename suitable for use with the underlying storage system.
        # The name argument passed to this method is either the original filename sent to the server or,
        # if upload_to is a callable, the filename returned by that method after any path information is removed.
        # Override this to customize how non-standard characters are converted to safe filenames.
        if name.startswith('http'):
            # 直接存的URL，直接返回，这类数据不支持取content
            return name
        dir_name, file_name = os.path.split(name)
        if len(file_name)>30:
            file_name=file_name[-30:-1]+file_name[-1]
        file_name = get_valid_filename(file_name)
        name = '/'.join(os.path.join(dir_name, file_name).split('\\'))
        if name[0] != '/':
            name = '/' + name
        return name

    def _get_available_name(self, name, max_length=None):
        # Returns a filename that is available in the storage mechanism,
        # possibly taking the provided filename into account.
        # The name argument passed to this method will have already cleaned to a filename valid for the storage system, according to the get_valid_name() method described above.

        dir_name, file_name = os.path.split(name)
        file_root, file_ext = os.path.splitext(file_name)
        while self.exists(name) or (max_length and len(name) > max_length):
            # file_ext includes the dot.
            name = os.path.join(dir_name, "%s_%s%s" % (file_root, get_random_string(7), file_ext))
            if max_length is None:
                continue
            # Truncate file_root if max_length exceeded.
            truncation = len(name) - max_length
            if truncation > 0:
                file_root = file_root[:-truncation]
                # Entire file_root was truncated in attempt to find an available filename.
                if not file_root:
                    raise SuspiciousFileOperation(
                        'Storage can not find an available filename for "%s". '
                        'Please make sure that the corresponding file field '
                        'allows sufficient "max_length".' % name
                    )
                name = os.path.join(dir_name, "%s_%s%s" % (file_root, get_random_string(7), file_ext))
        return name

    def exists(self, name):
        # Returns True if a file referenced by the given name already exists in the storage system,
        # or False if the name is available for a new file.
        if name.startswith('http'):
            # 直接存的URL，直接返回，这类数据不支持取content
            return True
        name = self._get_valid_name(name)
        cos = CosObject()
        response = cos.head_object(name, True)
        if response.status_code == 200:
            return True
        else:
            return False

    def url(self, name):
        # Returns the URL where the contents of the file referenced by name can be accessed.
        if name.startswith('http'):
            # 直接存的URL，直接返回，这类数据不支持取content
            return name
        if name[0] != '/':
            name = '/' + name
        if getattr(settings, 'COS_URL', ''):
            url = "%s%s" % (
                settings.COS_URL,
                name,
            )
        else:
            if settings.COS_USE_CDN:
                cdn_host = 'file'
            else:
                cdn_host = self.option['region']
            url = "http://%s-%s.%s.myqcloud.com%s" % (
                self.option['bucket'],
                self.option['Appid'],
                cdn_host,
                name,
            )

        return url

    def size(self, name):
        # Returns the total size, in bytes, of the file referenced by name.
        if name.startswith('http'):
            # 直接存的URL，直接返回，这类数据不支持取content
            return 0
        name = self._get_valid_name(name)
        cos = CosObject()
        response = cos.head_object(name, True)
        if response.status_code == 200:
            return response.headers['Content-Length']

    def delete(self, name):
        if name.startswith('http'):
            # 直接存的URL，直接返回，这类数据不支持取content
            return
        name = self._get_valid_name(name)
        cos = CosObject()
        cos.delete_object(name)
