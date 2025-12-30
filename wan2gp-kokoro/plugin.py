import gradio as gr
from shared.utils.plugins import WAN2GPPlugin
from shared.utils.process_locks import acquire_GPU_ressources, release_GPU_ressources, any_GPU_process_running
import time, os, requests
from kokoro_onnx import Kokoro
from kokoro_onnx.tokenizer import Tokenizer
import numpy as np

PlugIn_Name = "Kokoro TTS"
PlugIn_Id ="KokoroTTS"

def acquire_GPU(state):
    GPU_process_running = any_GPU_process_running(state, PlugIn_Id)
    if GPU_process_running:
        gr.Error("Another PlugIn is using the GPU")
    acquire_GPU_ressources(state, PlugIn_Id, PlugIn_Name, gr= gr)      

def release_GPU(state):
    release_GPU_ressources(state, PlugIn_Id)

class ConfigTabPlugin(WAN2GPPlugin):
    
    def __init__(self):
        super().__init__()
        self.name = PlugIn_Name
        self.version = "1.0.0"
        self.description = PlugIn_Name
        self.check_required()
        self.kokoro = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
        self.tokenizer = Tokenizer()

    def download_file_requests(self, url, filename):
        with requests.get(url, stream=True) as r:
            r.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    # If you have a large file, setting a chunk size is a good idea
                    f.write(chunk)
        print(f"Downloaded '{filename}' successfully.")

    def check_required(self):
        required = {'kokoro-v1.0.onnx':
                'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx',
                'voices-v1.0.bin':
                'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin'}

        for k in required:
            if not os.path.exists(k):
                self.download_file_requests(required[k],k)

    def setup_ui(self):
        self.request_global("get_current_model_settings")
        self.request_component("refresh_form_trigger")      
        self.request_component("state")
        self.request_component("resolution")
        self.request_component("main_tabs")

        self.add_tab(
            tab_id=PlugIn_Id,
            label=PlugIn_Name,
            component_constructor=self.create_config_ui,
        )


    def on_tab_select(self, state: dict) -> None:
        settings = self.get_current_model_settings(state)
        prompt = settings["prompt"]
        return prompt


    def on_tab_deselect(self, state: dict) -> None:
        pass

    def create_config_ui(self):

        def create(text: str, voice: str, blend_voice_name: str = None, blend_voice_slider: float = 0.0, speed: float = 1.0):
            phonemes = self.tokenizer.phonemize(text, lang="en-us")

            # Blending
            if blend_voice_name:
                first_voice = self.kokoro.get_voice_style(voice)
                second_voice = self.kokoro.get_voice_style(blend_voice_name)
                voice = np.add(first_voice * ((blend_voice_slider) / 100), second_voice * ((100 - blend_voice_slider) / 100))
            samples, sample_rate = self.kokoro.create(
                phonemes, voice=voice, speed=speed, is_phonemes=True
            )
            return [(sample_rate, samples), phonemes]
        
        with gr.Row():
            with gr.Column():
                text_input = gr.TextArea(
                    label="Input Text",
                    rtl=False,
                    value="Kokoro TTS. Turning words into emotion, one voice at a time!",
                )
                voice_input = gr.Dropdown(
                    label="Voice", value="af_sky", choices=sorted(self.kokoro.get_voices())
                )
                blend_voice_input = gr.Dropdown(
                    label="Blend Voice (Optional)",
                    value=None,
                    choices=sorted(self.kokoro.get_voices()) + [None],
                )
                blend_voice_slider = gr.Slider(
                    label="Blend Voice Amount",
                    value=100.0,
                    minimum=0.0,
                    maximum=100.0
                )
                speed = gr.Slider(
                    label="Speed",
                    value=1.0,
                    minimum=0.5,
                    maximum=1.0
                    )
                submit_button = gr.Button("Create")

            with gr.Column():
                phonemes_output = gr.Textbox(label="Phonemes")
                audio_output = gr.Audio()

            submit_button.click(
                fn=create,
                inputs=[text_input, voice_input, blend_voice_input, blend_voice_slider,speed],
                outputs=[audio_output, phonemes_output],
            )



   
