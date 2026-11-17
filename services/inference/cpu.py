"""Qwen CPU compatibility adapter. No network access or remote Python code."""
from pathlib import Path
from services.inference.initialize import verify

class CPUGenerator:
    def __init__(self, path, settings, manifest):
        import torch
        from transformers import AutoProcessor, Qwen3VLForConditionalGeneration
        verify(Path(path), manifest['files'])
        self.settings = settings
        self.processor = AutoProcessor.from_pretrained(str(path), local_files_only=True, trust_remote_code=False)
        self.model = Qwen3VLForConditionalGeneration.from_pretrained(
            str(path), torch_dtype=torch.float32, local_files_only=True,
            trust_remote_code=False, attn_implementation='sdpa').to('cpu').eval()

    def generate(self, image, prompt):
        import torch
        from PIL import Image
        torch.manual_seed(self.settings['seed'])
        pixels = image.copy()
        pixels.thumbnail((self.settings['generator_max_side'],) * 2, Image.Resampling.BICUBIC)
        messages = [{'role':'user', 'content':[{'type':'image','image':pixels}, {'type':'text','text':prompt}]}]
        inputs = self.processor.apply_chat_template(messages, tokenize=True, add_generation_prompt=True,
            return_dict=True, return_tensors='pt')
        with torch.inference_mode():
            output = self.model.generate(**inputs, do_sample=False, max_new_tokens=self.settings['max_tokens'])
        return self.processor.batch_decode(output[:, inputs['input_ids'].shape[1]:],
            skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]
