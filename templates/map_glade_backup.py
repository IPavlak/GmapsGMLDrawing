#!/usr/bin/env python
# -*- coding: utf-8 -*- 

## Here we imported both Gtk library and the WebKit2 engine. 
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk, WebKit2
from time import sleep
import thread

def load_finished(webview, event):
    if event == WebKit2.LoadEvent.FINISHED:
        js = "marker_uav.setPosition(new google.maps.LatLng(40.414565, -3.711707));"
        mapHolder.run_javascript(js)

def js2py(webview, event):
    print("radi")

builder = Gtk.Builder() 
builder.add_from_file("map.glade") 
# builder.connect_signals(Handler()) 

window = builder.get_object("map_window") 

mapHolder = WebKit2.WebView()
## To disallow editing the webpage. 
mapHolder.set_editable(True)

# print console log
settings = mapHolder.get_settings()
settings.set_enable_write_console_messages_to_stdout(True)
mapHolder.set_settings(settings)
mapHolder.connect('load-changed', load_finished)   # connect() je iz GObject-a
mapHolder.connect('notify::title', js2py)

# mapHolder.load_html(open('map.html').read(), None)
mapHolder.load_uri("http://127.0.0.1:5000")
# mapHolder.load_uri('file:///home/ivan/Documents/diplomski/map.html')
mapBox = builder.get_object('map_box')
mapBox.pack_start(mapHolder, True, True, 0)
# mapBox.add(mapHolder)
mapHolder.show_all()

window.connect("delete-event", Gtk.main_quit) 
window.show_all() 
Gtk.main()