# Irre Katze Level Editor

This is an editor to create custom levels for the game "Irre Katze".

In order to play the levels you need the original game which is available for free at https://www.j-ws.de/index_lidos_modul_02.php?content_id=1.


## About the game

You need to help a cat finding it's way through a two-dimensional world collecting all food and moving some objects (like inserting a light bulb into a lamp).

Throughout the game you need to figure out the physics of the world (like when and how do things fall) and experiment how certain objects behave (like what happens if you smoke a pipe of... eh, I don't know what's in there...)

As far as I know the game is available in German only but that should not be a problem because it does not really involve any text.

The game is available for free at the above mentioned [link](https://www.j-ws.de/index_lidos_modul_02.php?content_id=1).

Just download it, unpack it and explore the world!


## Installing this level editor

You don't really need to install this program.
You need python to run it.
Just execute `py/gui_main.py` and you can start to create a new level.

If you don't have Python you can download it from https://www.python.org/downloads/.

However, you may want to create a link to start the level editor more easily. This is described in the following subsections.

### Linux (Debian & Gnome 3)

Run `create_desktop_file.sh` in the directory where it is located.
This creates a file called `irka-editor.desktop`. 
Move it to `~/.local/share/applications/` or whereever the dektop files are gathered on your system.
Then the Gonme Menu should find this program (possibly you need to log out and log in).
It is also possible to make a right click on a `afg` file (the file format in which the levels are saved) and say Open With > Irre Katze Level Editor.

```
$ git clone https://github.com/j-kun/Irre-Katze-Level-Editor.git
$ cd Irre-Katze-Level-Editor
$ bash create_desktop_file.sh
$ mv irka-editor.desktop ~/.local/share/applications/
```

### Windows

Create a shortcut and insert as Target: `pythonw py/gui_main.py`.
(If `pythonw.exe` is not in one of the directories specified by the `%PATH%` variable you need to specify the comlete path like for example `C:\Python27\pythonw.exe`. If the shortcut is located somewhere else than in the root directory of the repository the path to the file must be changed accordingly. If a path contains spaces it must be enclosed in double quotes.)


## License

This software as well as the icons which I have created myself are licensed under the WTFPL - see the [LICENSE.md](LICENSE.md) file for details.

