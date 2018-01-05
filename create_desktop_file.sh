#!/usr/bin/env sh

path=`pwd`

cat > "irka-editor.desktop" <<-eof
#!/usr/bin/env xdg-open
[Desktop Entry]
Encoding=UTF-8
Name=Irre Katze Level Editor
Keywords=irka;
Comment[de]=Ein Level Editor für das Spiel "Irre Katze"
Exec=python3 $path/py/gui_main.py %U
Terminal=false
Icon=$path/images/gif/irka48.gif
Type=Application
eof
