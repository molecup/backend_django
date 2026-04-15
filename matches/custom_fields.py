import xml.etree.cElementTree as et

from django.core.exceptions import ValidationError

from django import forms
from django.core.exceptions import ValidationError
from django.db import models



from django.core.validators import (
    FileExtensionValidator,
    get_available_image_extensions,
)

def validate_image_and_svg_file_extension(value):
    allowed_extensions = get_available_image_extensions() + ["svg"]
    return FileExtensionValidator(allowed_extensions=allowed_extensions)(value)


class SVGAndImageField(models.ImageField):
    def formfield(self, **kwargs):
        defaults = {'form_class': SVGAndImageFieldForm}
        defaults.update(kwargs)
        return super().formfield(**defaults)
    

class SVGAndImageFieldForm(forms.ImageField):
    default_validators = [validate_image_and_svg_file_extension]
    def to_python(self, data):
        try:
            f = super().to_python(data)
        except ValidationError:
            return validate_svg(data)

        return f
    

def validate_svg(f):
    # Find "start" word in file and get "tag" from there
    f.seek(0)
    tag = None
    try:
        for event, el in et.iterparse(f, ('start',)):
            tag = el.tag
            break
    except et.ParseError:
        pass

    # Check that this "tag" is correct
    if tag != '{http://www.w3.org/2000/svg}svg':
        raise ValidationError('Uploaded file is not an image or SVG file.')

    # Do not forget to "reset" file
    f.seek(0)

    return f