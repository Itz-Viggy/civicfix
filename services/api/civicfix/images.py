from io import BytesIO
import warnings
from PIL import Image,ImageOps,UnidentifiedImageError
MAX_FILE=10*1024*1024
MAX_REQUEST=11*1024*1024
Image.MAX_IMAGE_PIXELS=20_000_000
class ImageFailure(Exception):
    def __init__(self,status,code): self.status=status; self.code=code

def sanitize(data,mime):
    if len(data)>MAX_FILE: raise ImageFailure(413,'photo_too_large')
    expected={'image/jpeg':'JPEG','image/png':'PNG','image/webp':'WEBP'}
    if mime not in expected: raise ImageFailure(415,'unsupported_image_type')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error',Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as source:
                if source.format!=expected[mime]: raise ImageFailure(415,'mime_mismatch')
                w,h=source.size
                if w*h>20_000_000 or min(w,h)<1 or max(w,h)>10000: raise ImageFailure(422,'image_dimensions')
                if getattr(source,'n_frames',1)!=1: raise ImageFailure(415,'animated_image')
                source.load(); image=ImageOps.exif_transpose(source)
                if image.mode in ('RGBA','LA','P'):
                    rgba=image.convert('RGBA'); out=Image.new('RGB',rgba.size,'white'); out.paste(rgba,mask=rgba.getchannel('A')); image=out
                else: image=image.convert('RGB')
                image.thumbnail((1280,1280),Image.Resampling.LANCZOS)
                # Copy pixels into a fresh image so no source metadata survives.
                clean=Image.new('RGB',image.size); clean.paste(image)
                result=BytesIO(); clean.save(result,'JPEG',quality=90,subsampling=2,optimize=False)
                return result.getvalue(),clean.size
    except ImageFailure: raise
    except (UnidentifiedImageError,OSError,ValueError,Image.DecompressionBombWarning,Image.DecompressionBombError):
        raise ImageFailure(422,'invalid_image')
