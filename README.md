# ScriptReader
Reads and creates wav files based on a script

Installation
--------------

Will need espeak-ng and sox installed

For linux
==============

sudo apt-get install espeak-ng libsndfile1 sox

uv

wget -qO- https://astral.sh/uv/install.sh | sh

Windows
===============
From the command line

winget install ChrisBagwell.SoX
winget install eSpeak-NG.eSpeak-NG

uv 

py -m pip install uv

Everyone
===========

git clone https://github.com/noodlepopllc/ScriptReader.git
cd ScriptReader
uv run ScriptReader -h

Usage
---------------
First time it is run it will create a config.json file the file contents are the following
{"alex": {"voice": "am_fenrir", "speed": 1.0, "mix": 100}}

This will be the default voice, to change or add additional voices run the gui

uv run ScriptReader.py --gui

This will allow you to edit Alex voice or create new ones by changing the name, you can also play to create a sample and download it for reference voices for other AI TTS models. Such as chatterbox or indextts.

The script format is simple, name: text, it will say whatever is on the line and use the configuration from the voice in the config or default to alex, can add as many voices as you like. 

There are additional options, -q or silence will remove any silences in the wave and -s or segment will break up line into individual sentences.




