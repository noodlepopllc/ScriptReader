import sys, os, requests, librosa, sox
from kokoro_onnx import Kokoro
from pathlib import Path
from json import dump, load
import gradio as gr
import soundfile as sf
from kokoro_onnx.tokenizer import Tokenizer
import numpy as np
from spacy_download import load_spacy

# uv run spacy download en_core_web_sm

class Voice(object):

    required = {'kokoro-v1.0.onnx':
                'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx',
                'voices-v1.0.bin':
                'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin'}

    def __init__(self, config, silence, segment):
        self.silence = silence
        self.segment = segment
        self.config = config
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
        for k in Voice.required:
            if not os.path.exists(k):
                self.download_file_requests(Voice.required[k],k)

    def remove_silence(self, input_file, output_file):
        tfm = sox.Transformer()
        tfm.silence()
        tfm.build_file(input_file, output_file)



    def readScript(self, script):
        nlp = load_spacy("en_core_web_sm", exclude=["parser", "tagger"])
        nlp.add_pipe('sentencizer')
        rscript = []

        with open(script,'r') as infile:
            for line in infile:
                l = line.replace("*","")
                key =  l.split(':')[0].split(' ')[0].lower().strip()
                rest = l.split(':')
                if len(rest) > 1:
                    rest = rest[1].strip()
                if len(key) > 0:
                    text = rest
                    print(text)
                    if self.segment:
                        doc = nlp(text)
                        for x in doc.sents:
                            tmp = {key:str(x)}
                            print(tmp)
                            rscript.append(tmp)
                    else:
                        rscript.append({key:text})
        print(rscript)
        return rscript

    def existing(self, js):
        if os.path.exists(js):
            with open(js,'r') as f:
                return load(f)
        return []


    def create_wav(self, text, path='tmp2.wav', key=''):
        voice = self.config[key]
        voices = voice['voice'].split(':')
        voice1 = voices[0]
        voice2 = voices[-1] if len(voices) > 1 else None
        mix = voice['mix']
        speed = voice['speed']
        sample_rate, samples = self.create(text, voice1, voice2, mix, speed)[0]
        tmp = 'tmp.wav' if self.silence else path
        sf.write(tmp, samples, sample_rate)
        if self.silence:
            self.remove_silence(tmp, path)
        return round(librosa.get_duration(path=path),2)

    def gui(self):
        app = self.create_app()
        app.launch()


    def create(self, text: str, voice: str, blend_voice_name: str = None, blend_voice_slider: float = 0.0, speed: float = 1.0):
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

    def save(self, name: str, voice: str, blend_voice_name: str = None, blend_voice_slider: float = 0.0, speed: float = 1.0):
        v = voice
        if blend_voice_name is not None:
            v = f'{voice}:{blend_voice_name}'
        self.config[name.lower()] = {'voice':v,'speed':speed,'mix':blend_voice_slider}

        with open('config.json', 'w') as outfile:
            dump(self.config, outfile)
        


    def create_app(self):
        with gr.Blocks(theme=gr.themes.Soft(font=[gr.themes.GoogleFont("Roboto")])) as ui:
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
                    name_input = gr.Text(
                        label="Actor Name",
                        rtl=False,
                        value="Alex",
                    )
                    save_button = gr.Button("Save")

                with gr.Column():
                    phonemes_output = gr.Textbox(label="Phonemes")
                    audio_output = gr.Audio()

                submit_button.click(
                    fn=self.create,
                    inputs=[text_input, voice_input, blend_voice_input, blend_voice_slider,speed],
                    outputs=[audio_output, phonemes_output],
                )

                save_button.click(
                    fn=self.save,
                    inputs=[name_input, voice_input, blend_voice_input, blend_voice_slider,speed],
                    outputs=None
                )
            
        return ui

    def main(self, script):
        jsonpath = script.split('.')[-2] + '.json'
        outp = self.existing(jsonpath)
        inp = self.readScript(script)
        if len(outp) == len(inp):
            return
        prefix = Path(script).stem

        for idx in range(len(outp),len(inp)):
            key = [x for x in inp[idx].keys()][0]
            if key not in self.config:
                key = 'alex'
            text = inp[idx][key]
            voice = self.config[key]
            p = f'{prefix}_{idx:03}_{key}.wav'
            inp[idx]['path'] = p
            inp[idx]['duration'] = self.create_wav(text, p, key)
            outp.append(inp[idx])
        with open(jsonpath,'w') as outfile:
            dump(outp,outfile,indent=4)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Create voices')
    parser.add_argument('-i','--input', type=str, default=None, help='script path')
    parser.add_argument('-u', '--gui', action='store_true', help='show gui')
    parser.add_argument('-q', '--silence', action='store_true', help='remove silence')
    parser.add_argument('-s', '--segment', action='store_true', help='segment sentences')
    args = parser.parse_args()
    voice = None
    if not os.path.exists('config.json'):
        with open('config.json', 'w') as outfile:
            dump({'alex':{'voice':'am_fenrir','speed':1.0,'mix':100}}, outfile)
    with open('config.json','r') as infile:
        voice = Voice(load(infile),args.silence,args.segment)
    if args.gui:
        voice.gui()
    else:
        voice.main(args.input)
