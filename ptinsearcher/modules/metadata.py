import os
import stat
import tempfile
import exiftool


def exiftool_is_executable():
    """Check whether exiftool is exif_executable if not truthy raises an PermissionError"""
    exif_executable = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "utils", "ExifTool", "exiftool"))
    is_executable = os.access(exif_executable, os.X_OK)
    if not is_executable:
        try:
            os.chmod(exif_executable, os.stat(exif_executable).st_mode | stat.S_IEXEC)
            return True
        except:
            raise PermissionError(f"Cannot execute nor set execution privileges for exiftool. Please run script as sudo or try running 'sudo chmod +x {exif_executable}'")


def get_metadata(page_content=None, filepath=None):
    """returns metadata"""
    exif_executable = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "utils", "ExifTool", "exiftool"))
    if page_content:
        tmp = tempfile.NamedTemporaryFile()
        with open(tmp.name, 'w') as f:
            f.write(page_content)
        with exiftool.ExifTool(executable=exif_executable) as et:
            metadata_dict = et.execute_json(tmp.name)[0]
    if filepath:
        with exiftool.ExifTool(executable=exif_executable) as et:
            metadata_dict = et.execute_json(filepath)[0]

    blacklist = ["SourceFile", "ExifTool:ExifToolVersion", "File:FileName", "File:Directory", "File:FileSize", "File:FileModifyDate", "File:FileInodeChangeDate", "File:FilePermissions", "File:FileAccessDate", "File:FileType", "File:FileTypeExtension", "File:MIMEType"]
    for i in blacklist:
        if metadata_dict.get(i):
            metadata_dict.pop(i)

    return metadata_dict