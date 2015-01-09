#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import thread
import ConfigParser

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import Pango
from gi.repository import GObject
from gi.repository import GdkPixbuf

screen = Gdk.Screen().get_default()
WIDTH = screen.get_width()
HEIGHT = screen.get_height()
APPS_DIR = '/usr/share/applications'
DEFAULT_ICON = '/usr/share/icons/Faenza/mimetypes/48/empty.png'
ICON_SIZE = 96
DEFAULT_PIXBUF = GdkPixbuf.Pixbuf.new_from_file_at_size(
    DEFAULT_ICON, ICON_SIZE, ICON_SIZE)

KEYS = [32]  # Espacio
KEYS += range(65, 91)  # 65: "A", 90: "Z"
KEYS += range(97, 123)  # 97: "a", 90: "z"


def get_icon(path):
    """
    Recibe el nombre de un ícono, su dirección, o abreviación
    de dirección y devuelve un pixbuf para poder crear imágenes.
    """

    icon_theme = Gtk.IconTheme()
    pixbuf = DEFAULT_PIXBUF

    if '/' in path:
        if not os.path.exists(path):
            return DEFAULT_PIXBUF

        archivo = Gio.File.new_for_path(path)
        info = archivo.query_info('standard::icon',
                                  Gio.FileQueryInfoFlags.NOFOLLOW_SYMLINKS,
                                  None)
        icono = info.get_icon()
        tipos = icono.get_names()

        if 'image-x-generic' in tipos:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(path, ICON_SIZE, ICON_SIZE)

        else:
            if path.endswith('.desktop'):
                cfg = ConfigParser.ConfigParser()
                cfg.read([path])

                if cfg.has_option('Desktop Entry', 'Icon'):
                    if '/' in cfg.get('Desktop Entry', 'Icon'):
                        icon = cfg.get('Desktop Entry', 'Icon')
                        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(
                            icon, ICON_SIZE, ICON_SIZE)

                    else:
                        pixbuf = icon_theme.load_icon(
                            cfg.get('Desktop Entry', 'Icon'), ICON_SIZE, 0)

                else:
                    pixbuf = icon_theme.load_icon(DEFAULT_ICON, ICON_SIZE, 0)

            else:
                try:
                    pixbuf = icon_theme.choose_icon(
                        tipos, ICON_SIZE, 0).load_icon()

                except:
                    pixbuf = icon_theme.load_icon(DEFAULT_ICON, ICON_SIZE, 0)

    else:
        if '.' in path:
            path = path.split('.')[0]

        if icon_theme.has_icon(path):
            pixbuf = icon_theme.load_icon(path, ICON_SIZE, 0)

        else:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(
                DEFAULT_ICON, ICON_SIZE, ICON_SIZE)

    return pixbuf


def get_app(archivo):
    """
    Obtiene la información de un .desktop,
    y la devuelve en un diccionario.
    """

    categorias = {}
    icon_theme = Gtk.IconTheme()
    aplicacion = None

    if archivo.endswith('.desktop'):
        archivo = os.path.join(APPS_DIR, archivo)
        cfg = ConfigParser.ConfigParser()
        nombre = None
        icono = None
        ejecutar = None

        cfg.read([archivo])

        if cfg.has_option('Desktop Entry', 'Name'):
            nombre = cfg.get('Desktop Entry', 'Name')

        if cfg.has_option('Desktop Entry', 'Name[es]'):
            nombre = cfg.get('Desktop Entry', 'Name[es]')

        if cfg.has_option('Desktop Entry', 'Icon'):
            icono = cfg.get('Desktop Entry', 'Icon')

        else:
            icono = 'text-x-preview'

        if cfg.has_option('Desktop Entry', 'Exec'):
            ejecutar = cfg.get('Desktop Entry', 'Exec')

            if '%' in ejecutar:
                # Para programas que el comando a ejecutar termina en %U
                # por ejemplo, esto hace que el programa reconozca a %U
                # como un argumento y el programa no se inicialice
                # correctamente

                t = ''
                for x in ejecutar:
                    t += x if x != '%' and x != ejecutar[ejecutar.index('%') + 1] else ''

                ejecutar = t

        if nombre and ejecutar:
            aplicacion = {
                'nombre': nombre,
                'icono': icono,
                'ejecutar': ejecutar,
            }

    return aplicacion


def run_app(app):
    """
    Recibe un diccionario(ver "get_app") y ejecuta la aplicacion a la que el diccionario hace referencia.
    """

    os.system(app['ejecutar'])


class AppsEntry(Gtk.Entry):

    __gsignals__ = {
        'run-app': (GObject.SIGNAL_RUN_FIRST, None, [])
        }

    def __init__(self):
        Gtk.Entry.__init__(self)

        self.set_placeholder_text('Buscar...')
        self.props.xalign = 0.015
        self.en_foco = True

        self.modify_font(Pango.FontDescription('Bold 35'))
        self.connect('focus-in-event', self.__focus_in_event_cb)
        self.connect('focus-out-event', self.__focus_out_event_cb)

    def __focus_in_event_cb(self, *args):
        self.en_foco = True

    def __focus_out_event_cb(self, *args):
        self.en_foco = False


class AppButton(Gtk.Button):

    __gsignals__ = {
        'run-app': (GObject.SIGNAL_RUN_FIRST, None, []),
        'favorited': (GObject.SIGNAL_RUN_FIRST, None, []),
        }

    def __init__(self, app):
        Gtk.Button.__init__(self)

        self.app = app
        vbox = Gtk.VBox()
        pixbuf = get_icon(app['icono'])
        imagen = Gtk.Image.new_from_pixbuf(pixbuf)
        texto = app['nombre']
        texto = texto[:20] + '...' if len(texto) > 20 else texto
        label = Gtk.Label(texto)

        self.set_can_focus(False)
        label.modify_font(Pango.FontDescription('Bold 15'))

        self.connect('button-release-event', self.button_press_event_cb)

        vbox.pack_end(label, False, False, 0)
        vbox.pack_start(imagen, True, True, 0)
        self.add(vbox)

    def button_press_event_cb(self, widget, event):
        if event.button == 1:
            self.emit('run-app')


class Menu(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self)

        scrolled = Gtk.ScrolledWindow()
        self.box = Gtk.VBox()
        self.entry = AppsEntry()
        self.fbox = Gtk.FlowBox()

        self.fbox.set_max_children_per_line(5)
        self.fbox.set_border_width(10)
        self.fbox.set_column_spacing(2)
        self.fbox.set_row_spacing(2)
        self.set_decorated(0)
        self.set_size_request(WIDTH, HEIGHT)

        self.entry.connect('changed', self.search_app)
        self.connect('destroy', Gtk.main_quit)
        self.connect('key-press-event', self.key_press_event_cb)

        scrolled.add(self.fbox)
        self.box.pack_start(self.entry, False, False, 20)
        self.box.pack_start(scrolled, True, True, 0)
        self.add(self.box)

        GObject.idle_add(self.show_all_apps)

    def key_press_event_cb(self, widget, event):
        key = event.keyval
        if key == 65307:  # Escape
            Gtk.main_quit()

        elif key in KEYS and not self.entry.en_foco:
            texto = self.entry.get_text() + chr(key)
            self.entry.set_text(texto)
            self.entry.grab_focus()

    def show_all_apps(self, *args):
        apps = {}

        for archivo in os.listdir(APPS_DIR):
            app = get_app(archivo)

            if app:
                apps[app['nombre']] = app
                boton = AppButton(app)
                boton.connect('clicked', self.run_app)
                self.fbox.add(boton)

        self.show_all()

    def search_app(self, widget):
        for x in self.fbox.get_children():
            boton = x.get_children()[0]
            if widget.get_text().lower() in boton.app['nombre'].lower():
                x.show_all()

            else:
                x.hide()

    def run_app(self, boton):
        thread.start_new_thread(run_app, (boton.app,))
        Gtk.main_quit()


if __name__ == '__main__':
    Menu()
    Gtk.main()
