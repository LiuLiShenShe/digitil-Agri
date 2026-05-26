import torch
from typing import *
from contextlib import contextmanager
from transformers import AutoModelForImageSegmentation
from torchvision import transforms
from PIL import Image
import transformers.modeling_utils as modeling_utils

# Patch transformers 5.x _move_missing_keys_from_meta_to_device for models that
# expose _tied_weights_keys but not all_tied_weights_keys (older trust_remote_code models)
_orig_move = modeling_utils.PreTrainedModel._move_missing_keys_from_meta_to_device
def _patched_move(self, *args, **kwargs):
    if not hasattr(self, 'all_tied_weights_keys'):
        twk = getattr(self, '_tied_weights_keys', None)
        self.all_tied_weights_keys = twk if twk is not None else {}
    return _orig_move(self, *args, **kwargs)
modeling_utils.PreTrainedModel._move_missing_keys_from_meta_to_device = _patched_move


@contextmanager
def _disable_meta_init_for_transformers5_remote_model():
    """Older trust_remote_code RMBG models call Tensor.item() during __init__."""
    orig_get_init_context = modeling_utils.PreTrainedModel.get_init_context
    orig_mark = modeling_utils.PreTrainedModel.mark_tied_weights_as_initialized

    @classmethod
    def _patched_get_init_context(cls, dtype, is_quantized, _is_ds_init_called, allow_all_kernels):
        contexts = orig_get_init_context.__func__(cls, dtype, is_quantized, _is_ds_init_called, allow_all_kernels)
        return [
            ctx for ctx in contexts
            if not (isinstance(ctx, torch.device) and ctx.type == 'meta')
        ]

    def _patched_mark(self, *args, **kwargs):
        if not hasattr(self, 'all_tied_weights_keys'):
            twk = getattr(self, '_tied_weights_keys', None)
            self.all_tied_weights_keys = twk if twk is not None else {}
        return orig_mark(self, *args, **kwargs)

    modeling_utils.PreTrainedModel.get_init_context = _patched_get_init_context
    modeling_utils.PreTrainedModel.mark_tied_weights_as_initialized = _patched_mark
    try:
        yield
    finally:
        modeling_utils.PreTrainedModel.get_init_context = orig_get_init_context
        modeling_utils.PreTrainedModel.mark_tied_weights_as_initialized = orig_mark


class BiRefNet:
    def __init__(self, model_name: str = "ZhengPeng7/BiRefNet"):
        with _disable_meta_init_for_transformers5_remote_model():
            self.model = AutoModelForImageSegmentation.from_pretrained(
                model_name, trust_remote_code=True
            )
        self.model.eval()
        self.transform_image = transforms.Compose(
            [
                transforms.Resize((1024, 1024)),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            ]
        )
    
    def to(self, device: str):
        self.model.to(device)

    def cuda(self):
        self.model.cuda()

    def cpu(self):
        self.model.cpu()
        
    def __call__(self, image: Image.Image) -> Image.Image:
        image_size = image.size
        input_images = self.transform_image(image).unsqueeze(0).to("cuda")
        # Prediction
        with torch.no_grad():
            preds = self.model(input_images)[-1].sigmoid().cpu()
        pred = preds[0].squeeze()
        pred_pil = transforms.ToPILImage()(pred)
        mask = pred_pil.resize(image_size)
        image.putalpha(mask)
        return image
    
