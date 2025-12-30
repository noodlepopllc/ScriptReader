# wan2gp-kokoro
Allows use of the excellent kokoro-tts library from within wan2gp

## Installation

Will need espeak-ng installed

### For linux

#### espeak-ng and sox

```
sudo apt-get install espeak-ng libsndfile1
```

### Windows

#### espeak-ng - From the command line 

```
winget install eSpeak-NG.eSpeak-NG
```

Copy wan2gp-kokoro into Wan2GP/plugins directory

Then start your wan2gp virtual environment as normal

finally 

```
pip install -r Wan2GP/plugings/wan2gp-kokoro/requirements.txt
```

Now can start wan2gp as normal, go to plugins tab and enable the plugin.


