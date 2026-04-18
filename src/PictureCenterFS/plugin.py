######################################
# PictureCenterFS for VU+            #
#                                    #
#   Enigma2 Plugin                   #
#                                    #
#  Coded by shadowrider (c)2011      #
#  Py3-Version: Mr.Servo (@openA.TV) #
######################################

# PYTHON IMPORTS
from fnmatch import fnmatch
from os import makedirs, listdir, remove, rename, symlink, unlink, readlink
from os.path import exists, basename, dirname, isdir, isfile, join, getsize, getmtime, splitext, split, ismount, islink
from shutil import rmtree
from PIL import Image, ImageDraw
from PIL.ExifTags import TAGS
from random import shuffle, randint
from re import compile
from skin import parseColor
from sys import getrecursionlimit, setrecursionlimit
from time import strftime, strptime, gmtime, mktime
from threading import Thread, Lock
from xml.etree.cElementTree import parse as cet_parse

# ENIGMA IMPORTS
from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_VALIGN_CENTER, ePoint, eSize, ePicLoad, eTimer, getDesktop, iPlayableService, eServiceReference, gMainDC
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.AVSwitch import AVSwitch
from Components.config import config, ConfigDirectory, ConfigSubsection, ConfigInteger, ConfigSelection, ConfigText, ConfigEnableDisable, getConfigListEntry, NoSave, ConfigSequence, ConfigText, ConfigNothing
from Components.ConfigList import ConfigListScreen
from Components.Console import Console
from Components.Harddisk import harddiskmanager
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText
from Components.Pixmap import Pixmap
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Components.ServiceEventTracker import ServiceEventTracker
from Components.ServicePosition import ServicePositionGauge
from configparser import ConfigParser
from Plugins.Plugin import PluginDescriptor
from Screens.ChoiceBox import ChoiceBox
from Screens.HelpMenu import HelpableScreen
from Screens.InfoBarGenerics import InfoBarSeek
from Screens.LocationBox import LocationBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Tools.Directories import SCOPE_SYSETC, SCOPE_PLUGINS, SCOPE_CURRENT_SKIN, resolveFilename, pathExists, fileExists, removeDir, createDir
from Tools.LoadPixmap import LoadPixmap

# PLUGIN IMPORTS
from . import _ # for localized messages
from .files import PictureCenterFS7_Filemenu, backup, save_mark

version = "9.0beta"
DPKG = False
XML_FSTAB = resolveFilename(SCOPE_SYSETC, "enigma2/automounts.xml")
DATAPATH = resolveFilename(SCOPE_SYSETC, "ConfFS/")
DATAFILE = join(DATAPATH, "PictureCenterFS.dat")
SKIN_EXT = resolveFilename(SCOPE_PLUGINS, "Extensions/PictureCenterFS/skin/")
skin_ext_zusatz = ""
TYPE_PIC = (".jpg", ".jpeg", ".jpe", ".bmp", ".png")
TYPE_MOV = (".mpg", ".mov", ".mp4", ".mkv", ".avi", ".mpeg", ".mts", ".m2ts", ".wmv", ".flv")
# pics = ["txt_pin.png","pic.png","up.png","pin.png","ordner.png","err_pin.png","mov.png","pcfs_play.png","pcfs_random.png","pcfs_pause.png"]

def getScale():
	return AVSwitch().getFramebufferScale()
size_w = getDesktop(0).size().width()
size_h = getDesktop(0).size().height()
if size_w > 1850:
	skin_ext_zusatz = "fHD/"
	font1 = 30
	font2 = 18
	zeil_high = 40
else:
	skin_ext_zusatz = "HD/"
	font1 = 26
	font2 = 18
	zeil_high = 30
icon_path = SKIN_EXT + skin_ext_zusatz + "pictures/"
icon_path1 = SKIN_EXT + "pictures/"
pics2 = {"txt_pin": icon_path + "txt_pin.png", "pic": icon_path + "pic.png", "up": icon_path + "up.png", "pin": icon_path + "pin.png",
	   "ordner": icon_path + "ordner.png", "err_pin": icon_path + "err_pin.png", "mov": icon_path1 + "mov.png",
	   "pcfs_play": icon_path1 + "pcfs_play.png", "pcfs_random": icon_path1 + "pcfs_random.png", "pcfs_pause": icon_path1 + "pcfs_pause.png",
	   "b_pcfs_play": icon_path1 + "b_pcfs_play.png", "b_pcfs_random": icon_path1 + "b_pcfs_random.png", "b_pcfs_pause": icon_path1 + "b_pcfs_pause.png"}
if exists(resolveFilename(SCOPE_CURRENT_SKIN, "Extensions/PictureCenterFS/pictures")):
	for k in pics2.keys():
		fl = "Extensions/PictureCenterFS/pictures/" + k + ".png"
		if fileExists(resolveFilename(SCOPE_CURRENT_SKIN, fl)):
			pics2[k] = resolveFilename(SCOPE_CURRENT_SKIN, fl)
elif exists(resolveFilename(SCOPE_CURRENT_SKIN, "extensions/")):
	for k in pics2.keys():
		fl = "extensions/" + k + ".png"
		if fileExists(resolveFilename(SCOPE_CURRENT_SKIN, fl)):
			k = resolveFilename(SCOPE_CURRENT_SKIN, fl)
config.plugins.PictureCenterFS = ConfigSubsection()
config.plugins.PictureCenterFS.hauptmenu = ConfigSelection(default="1", choices=[("1", _("Menu")), ("2", _("Menu & Mainmenu")), ("3", _("Menu & Extensionsmenu")), ("4", _("Menu, Mainmenu & Extensionsmenu"))])
if config.plugins.PictureCenterFS.hauptmenu.value == "true":
	config.plugins.PictureCenterFS.hauptmenu.value = "1"
Farbe = [("transparent", _("transparent")), ("skin0", _("from Plugin-Skin")), ("skin", _("from System-Skin")), ("black", _("black")), ("white", _("white")),
 ("gray", _("gray")), ("silver", _("silver")), ("slategray", _("slategray")),
	("aquamarine", _("aquamarine")),
 ("yellow", _("yellow")), ("greenyellow", _("greenyellow")), ("gold", _("gold")),
 ("red", _("red")), ("tomato", _("tomato")), ("darkred", _("darkred")), ("indianred", _("indianred")), ("orange", _("orange")), ("darkorange", _("darkorange")), ("orangered", _("orangered")),
 ("green", _("green")), ("lawngreen", _("lawngreen")), ("darkgreen", _("darkgreen")), ("lime", _("lime")), ("lightgreen", _("lightgreen")),
 ("blue", _("blue")), ("blueviolet", _("blueviolet")), ("indigo", _("indigo")), ("darkblue", _("darkblue")), ("cadetblue", _("cadetblue")), ("cornflowerblue", _("cornflowerblue")), ("lightblue", _("lightblue")),
 ("magenta", _("magenta")), ("violet", _("violet")), ("darkorchid", _("darkorchid")), ("deeppink", _("deeppink")), ("cyan", _("cyan")),
 ("brown", _("brown")), ("sandybrown", _("sandybrown")), ("moccasin", _("moccasin")), ("rosybrown", _("rosybrown")), ("olive", _("olive")), ]
framesize = NoSave(ConfigInteger(default=0, limits=(0, 9999)))
thumbsize = NoSave(ConfigInteger(default=200, limits=(100, 999)))
thumbdelaying = NoSave(ConfigInteger(default=500, limits=(100, 9999)))
distance_infoline2 = NoSave(ConfigSequence(seperator=",", default=[130, 130], limits=[(0, 9999), (0, 9999)]))
slidetime = NoSave(ConfigInteger(default=5, limits=(1, 999)))
slideeffekt = NoSave(ConfigSelection(default=0, choices=[(0, _("Off")), (1, _("best")), (2, _("speed"))]))
maxtime = NoSave(ConfigInteger(default=30, limits=(1, 60)))
zoomsize = NoSave(ConfigInteger(default=200, limits=(100, size_h - 100)))
sprungzahl = NoSave(ConfigInteger(default=5, limits=(1, 30)))
resize = NoSave(ConfigSelection(default="1", choices=[("0", _("simple")), ("1", _("better"))]))
thumbquali = NoSave(ConfigSelection(default=0, choices=[(0, _("speed")), (1, _("quality"))]))
thumbtxtsize = NoSave(ConfigInteger(default=14, limits=(14, 35)))
thumbtxtcol = NoSave(ConfigSelection(default="#0038FF48", choices=[("#00000000", _("black")), ("#009eb9ff", _("blue")), ("#00ff5a51", _("red")), ("#00ffe875", _("yellow")), ("#0038FF48", _("green"))]))
thumbbackcol = NoSave(ConfigSelection(default="#00000000", choices=[("#00000000", _("black")), ("#009eb9ff", _("blue")), ("#00ff5a51", _("red")), ("#00ffe875", _("yellow")), ("#0038FF48", _("green"))]))
info_size = NoSave(ConfigSelection(default=0, choices=[(0, _("normal")), (1, _("big")), (2, _("from skin"))]))
cache = NoSave(ConfigEnableDisable(default=True))
infoline = NoSave(ConfigEnableDisable(default=False))
excludeconf = NoSave(ConfigText(default="mp4,mpg", fixed_size=False))
ch_tast = NoSave(ConfigSelection(default="up", choices=[("down", _("Next Page")), ("up", _("Preview Page"))]))
std_read_sub = NoSave(ConfigEnableDisable(default=True))
saver_on = NoSave(ConfigEnableDisable(default=True))
saver_path = NoSave(ConfigDirectory(default="/media/hdd/"))
saver_subdirs = NoSave(ConfigEnableDisable(default=True))
list_func = NoSave(ConfigEnableDisable(default=False))
loop2 = NoSave(ConfigSelection(default="restart", choices=[("restart", _("Endless")), ("stop", _("Stop")), ("exit", _("Back to Startscreen"))]))
loop3 = NoSave(ConfigSelection(default="restart", choices=[("restart", _("Endless")), ("stop", _("Stop")), ("exit", _("Back to Startscreen"))]))
symbols = NoSave(ConfigEnableDisable(default=True))
symbols_ah = NoSave(ConfigInteger(default=0, limits=(0, 600)))
transparent = NoSave(ConfigEnableDisable(default=False))
show_name = NoSave(ConfigEnableDisable(default=True))
a_rotate = NoSave(ConfigEnableDisable(default=False))
bgcolor = NoSave(ConfigSelection(choices=Farbe, default="skin0"))
z1_bgcolor = NoSave(ConfigSelection(choices=Farbe, default="transparent"))
textcolor = NoSave(ConfigSelection(default="#0038FF48", choices=[("#00000000", _("black")), ("#009eb9ff", _("blue")), ("#00ff5a51", _("red")), ("#00ffe875", _("yellow")), ("#0038FF48", _("green")), ("skin", _("from skin"))]))
default_dir = NoSave(ConfigDirectory(default="/tmp"))
default_ok = NoSave(ConfigSelection(default="Folder- and Filelist", choices=[("Folder- and Filelist", _("Folder- and Filelist")), ("Show Pictures", _("Show Pictures")), ("Diashow", _("Diashow"))]))
std_read_sub = NoSave(ConfigEnableDisable(default=True))
playvideo = NoSave(ConfigEnableDisable(default=False))
fromskin = NoSave(ConfigSelection(default=1, choices=[(2, _("from settings")), (1, _("from skin"))]))
osd_alpha_off = NoSave(ConfigEnableDisable(default=True))
resolu = NoSave(ConfigSelection(default=None, choices=[(None, _("Same resolution as skin")), ("(720, 576)", "720x576"), ("(1280, 720)", "1280x720"), ("(1920, 1080)", "1920x1080"), ("(4096, 2160)", "4096x2160")]))  #, ("(4096, 2160)", "4096x2160")
pil_vers = Image.__version__
if pil_vers < "1.1.6":
	pil_install = "veraltet"
else:
	pil_install = "ok"
sorten = [("all", _("None")), ("name", _("Name")), ("revers", _("Name reverse"))]
if pil_install == "ok":
	sorten.append(("date", _("record date forward")))
	sorten.append(("date_reverse", _("record date descending")))
filesort = NoSave(ConfigSelection(default="name", choices=sorten))
sorten2 = sorten
sorten2.append(("random", _("Random")))
fullbildsort = NoSave(ConfigSelection(default="all", choices=sorten2))
saver_random = NoSave(ConfigSelection(default="all", choices=sorten2))
if not exists(DATAPATH):
	makedirs(DATAPATH)
if not exists(DATAFILE):
	open(DATAFILE, "w").close()
configparser1 = ConfigParser()
configparser1.read(DATAFILE)
if configparser1.has_section("settings"):
	l1 = configparser1.items("settings")
	for nam in l1:
		if nam[1].strip() == "True":
			vars()[nam[0]].value = True   #True
		elif nam[1].strip() == "False" or nam[1].strip() == "None":
			vars()[nam[0]].value = False
		elif nam[0].strip() == "filesort":
			if ("date" in nam[1] and pil_install != "ok") or "random" in nam[1] or "all" in nam[1]:
				filesort.value = "name"
			else:
				filesort.value = nam[1].strip().lower()
		elif nam[0].strip() == "fullbildsort":
			if ("date" in nam[1] and pil_install != "ok"):
				fullbildsort.value = "name"
			else:
				fullbildsort.value = nam[1].strip().lower()
		elif nam[0].strip() == "distance_infoline2":
			i1 = nam[1].replace("[", "").replace("]", "").split(",")
			i_space = [int(i1[0]), int(i1[1])]
			distance_infoline2.value = i_space
		else:
			try:
				vars()[nam[0]].value = int(nam[1].strip())
			except Exception:
				vars()[nam[0]].value = nam[1]
vollbildsets = [fullbildsort.value, infoline.value, playvideo.value, std_read_sub.value, filesort.value]
exclude = ()
if len(excludeconf.value.strip()):
	exclude = excludeconf.value.split(",")

class PictureCenterFS7(Screen, HelpableScreen):
	with open(SKIN_EXT + skin_ext_zusatz + "pcfs.xml") as tmpskin:
		skin = tmpskin.read()

	def __init__(self, session,):
		self.alt_osd_alpha = None
		self.markfile = None
		if osd_alpha_off.value:
			self.alt_osd_alpha = str(open("/proc/stb/video/alpha", "r").read().strip())
			open("/proc/stb/video/alpha", "w").write(str(255))
		Screen.__init__(self, session)
		self.skinName = "PictureCenterFS7"
		HelpableScreen.__init__(self)
		self["pcfsKeyActions"] = HelpableActionMap(self, "pcfsKeyActions",
		{
				"cancel": (self.KeyExit, _("Close PictureCenterFS")),
				"red": (self.KeyRed, _("Filelist or Filemenu")),
				"green": (self.KeyGreen, _("Play Slideshow")),
				"play": (self.KeyGreen, _("Play Slideshow")),
				"playpause": (self.KeyGreen, _("Play Slideshow")),
				"yellow": (self.KeyYellow, _("Thumbs")),
				"blue": (self.KeyBlue, _("Show Pictures")),
				"ok": (self.KeyOk, _(default_ok.value)),
				"menu": (self.showMainMenu, _("Show Menu")),
				"info": (self.StartExif, _("Show Exif-Data")),
				"0": (self.make, _("Make Bookmark")),
				"Back": (self.sel_sort, _("other sort")),
				"For": (self.sel_sort, _("other sort")),
		}, -1)
		self.ThumbTimer = eTimer()
		if DPKG:
			self.ThumbTimer_conn = self.ThumbTimer.timeout.connect(self.showThn)
		else:
			self.ThumbTimer.callback.append(self.showThn)
		self.exiter = 0
		self.nameliste = []
		self.index = 0
		self.art = ""
		self.st_aktiv = True
		self["bgr2"] = Pixmap()
		self["button_menu"] = Pixmap()
		self["button_help"] = Pixmap()
		self["button_epg"] = Pixmap()
		self["button_blue"] = Pixmap()
		self["button_ok"] = Pixmap()
		self["button_0"] = Pixmap()
		self["thumb"] = Pixmap()
		self["thumb"].hide()
		self["button_yellow"] = Pixmap()
		self["button_green"] = Pixmap()
		self["button_red"] = Pixmap()
		self["pc_list"] = List([])
		self["key_red"] = Label("")
		self["key_ok"] = Label("")
		self["key_0"] = Label("")
		self["key_green"] = Label("")
		self["key_yellow"] = Label("")
		self["key_blue"] = Label("")
		self["key_sort"] = Label("")
		self["Bez_sort"] = Label(_("sorted by") + ":")
		self["dats"] = Label("")
		self.akt_mark = None
		self["pc_list"].onSelectionChanged.append(self.selectionChanged)
		self.hide_button()
		self.picload = ePicLoad()
		if DPKG:
			self.picload_conn = self.picload.PictureData.connect(self.showPic)
		else:
			self.picload.PictureData.get().append(self.showPic)
		self.onLayoutFinish.append(self.setConf)
		self.onLayoutFinish.append(self.start)

	def check_failed(self):
		self.session.openWithCallback(self.KeyExit, MessageBox, _("Modul PIL is not installed!\nPlease install current version of python-imaging from feed\nor install PIL > 1.1.5"), type=MessageBox.TYPE_ERROR)

	def sel_sort(self):
		sb = [(_("Name"), "name"), (_("Name reverse"), "revers")]
		if pil_install == "ok":
			sb.append((_("record date forward"), "date"))
			sb.append((_("record date descending"), "date_reverse"))
		self.session.openWithCallback(self.sel_sortCallback, ChoiceBox, title=_("PictureCenterFS - Sort"), list=sb)

	def sel_sortCallback(self, ret=None):
		global vollbildsets
		if ret and ret[1] != vollbildsets[4]:
			vollbildsets[4] = ret[1]
			self.set_sortText()
		if self.filelist and len(self.filelist):
			self.Pic_tools_back(self.pfad)

	def start(self):
		self.limit = getrecursionlimit()
		setrecursionlimit(30000)
		self.marker_listen = [i for i in listdir(DATAPATH) if i.endswith('_pcfs.txt')]
		self.list = []
		self.filelist = []
		if pil_install != "ok":
			msgtxt = []
			if pil_install == "veraltet":
				msgtxt.append("Modul PIL Version is too old!")
			else:
				msgtxt.append("Modul PIL is not installed!")
			for txt in msgtxt + [" ", "Please install current version", "of python-imaging from feed", "  or", "install PIL Version > 1.1.5"]:
				self.list.append(("/tmp", txt, 0, "all", False, "bookmark", 2, False, False, None))
		else:
			self.dirlist = 0
			self.configparser2 = ConfigParser()
			self.configparser2.read(DATAFILE)
			sections2 = self.configparser2.sections()
			for section in sections2:
				if section != "settings":
					online = 0
					self.read_sub = std_read_sub.value
					self.path = "/tmp"
					self.sortierung = vollbildsets[4]  # "all"
					self.infoline = infoline.value
					self.videoplay = playvideo.value
					l1 = self.configparser2.items(section)
					for nam in l1:
						ndex = 0
						if nam[1].strip() == "True":
							vars()[nam[0]] = True   # True
						elif nam[1].strip() == "False":
							vars()[nam[0]] = False
						elif nam[0] == "index":
							ndex = int(nam[1].strip())
						else:
							vars()[nam[0]] = nam[1].strip()
					if pathExists(self.path):
						online = 1
						pinpng = LoadPixmap(pics2["pin"])
					else:
						pinpng = LoadPixmap(pics2["err_pin"])
					eintrag = (self.path, section, 0, self.sortierung, self.read_sub, "bookmark", online, self.infoline, self.videoplay, pinpng, ndex)
					self.list.append(eintrag)
			#self.list.sort()
			self.set_sortText()
			txtPin = LoadPixmap(pics2["txt_pin"])
			dirpng = LoadPixmap(pics2["ordner"])
			self.list.sort(key=lambda x: x[1].lower())
			self.list.insert(0, (default_dir.value, _("select DIR"), None, vollbildsets[4], "True2", "dirs", 1, None, infoline.value, dirpng, 0))
			online = 0
			pinpng = LoadPixmap(pics2["err_pin"])
			if pathExists(default_dir.value):
				online = 1
				pinpng = LoadPixmap(pics2["pin"])
			self.list.insert(1, (default_dir.value, _("Default dir"), 0, vollbildsets[4], False, "bookmark", online, infoline.value, playvideo.value, pinpng, 0))
			if list_func.value:
				if len(self.marker_listen):
					self.list.append(("/tmp/pcfs_mark", _("Marked pictures"), 0, None, False, "filelist", 1, True, False, txtPin))
					for x in self.marker_listen:
						self.list.append((DATAPATH + x, basename(x.strip()), 0, None, False, "filelist", 1, infoline.value, playvideo.value, txtPin))
		self.st_aktiv = True
		self["pc_list"].setList(self.list)
		self.setTitle("PictureCenterFS" + "  " + version)

	def KeyExit(self):
		if self.list[0][5] == 'back' or (self.filelist and len(self.filelist)):
			self.start()
		elif str(self["pc_list"].getCurrent()[5]) == "back":
			self.start()
		else:
			self.exiter = 1
			self.ThumbTimer.stop()
			setrecursionlimit(self.limit)
			if self.alt_osd_alpha:
				open("/proc/stb/video/alpha", "w").write(self.alt_osd_alpha)
			if exists("/tmp/changed2.JPG"):
				remove("/tmp/changed2.JPG")
			if exists("/tmp/bgr.png"):
				remove("/tmp/bgr.png")
			self.close()

	def up(self):
		self["pc_list"].up()
		self.selectionChanged()

	def down(self):
		self["pc_list"].down()
		self.selectionChanged()

	def set_sortText(self):
		for x in sorten2:
			if x[0] == vollbildsets[4]:  # aktsortin:
				self["key_sort"].setText(_(x[1]))

	def selectionChanged(self):
		global vollbildsets
		if self.exiter == 0:
			eintr = self["pc_list"].getCurrent()
			self.art = eintr[5]
			n_sort = filesort.value
			if self.st_aktiv:
				if eintr[1] == _("select DIR") or eintr[1] == _("Default dir"):
					vollbildsets = [fullbildsort.value, infoline.value, playvideo.value, "True2", filesort.value, 0]
				else:
				#if eintr[5]=="bookmark":
					vollbildsets = [eintr[3], eintr[7], eintr[8], eintr[4], eintr[3]]
			self.set_sortText()
			self["dats"].setText("")
			self.len1 = 0
			self.hide_button()
			self.markfile = None
			self["thumb"].hide()
			if self.art == "file":
				self["dats"].setText(str(eintr[8]))
				self["button_red"].show()
				self["button_epg"].show()
				self["key_ok"].setText(_("Show"))
				self["key_red"].setText(_("FileMenu"))
				self["key_blue"].setText(_("Show Pictures"))
				self["button_blue"].show()
				self["key_green"].setText(_("Slideshow"))
				self["button_green"].show()
				self["key_yellow"].setText(_("Thumbs"))
				self["button_yellow"].show()
				self.ThumbTimer.start(thumbdelaying.value, True)
				self.dirname = dirname(eintr[0]) + "/"
			elif self.art == "dir":
				self["key_red"].setText(_("Folder- and Filelist"))
				self["button_red"].show()
				self["key_ok"].setText(_(default_ok.value))
				self["key_yellow"].setText(_("Thumbs"))
				self["button_yellow"].show()
				self["key_green"].setText(_("Slideshow"))
				self["button_green"].show()
				self["key_blue"].setText(_("Show Pictures"))
				self["button_blue"].show()
				self["key_0"].setText(_("Make Bookmark"))
				self["button_0"].show()
				self["button_epg"].show()
			elif self.art == "back":
				self["key_blue"].setText(_("back to Bookmarks"))
				self["button_blue"].show()
				self["key_ok"].setText(_("back to Bookmarks"))
			elif self.art == "ouverDir":
				self["key_blue"].setText(_("Parent Directory"))
				self["button_blue"].show()
				self["key_ok"].setText(_("Parent Directory"))
			elif (self.art == "filelist" or self.art == "bookmark") and eintr[6] == 1:
				if self.art == "filelist":
					self.markfile = eintr[0]
				self["key_red"].setText(_("Folder- and Filelist"))
				self["button_red"].show()
				self["key_ok"].setText(_(default_ok.value))
				self["key_yellow"].setText(_("Thumbs"))
				self["button_yellow"].show()
				self["key_green"].setText(_("Slideshow"))
				self["button_green"].show()
				self["key_blue"].setText(_("Show Pictures"))
				self["button_blue"].show()
				self["button_epg"].show()
			elif self.art == "ouverDir":
				self["key_red"].setText(_("Folder- and Filelist"))
				self["button_red"].show()
				try:
					filelist1 = file_list(eintr[0]).Dateiliste2
					self.len1 = len(filelist1)
					if self.len1 > 0:
						self["key_ok"].setText(_(default_ok.value))
						self["key_yellow"].setText(_("Thumbs"))
						self["button_yellow"].show()
						self["key_green"].setText(_("Slideshow"))
						self["button_green"].show()
						self["key_blue"].setText(_("Show Pictures"))
						self["button_blue"].show()
				except Exception:
					self.art = "ouverDir2"

	def hide_button(self):
		self["key_blue"].setText("")
		self["button_blue"].hide()
		self["key_red"].setText("")
		self["button_red"].hide()
		self["key_yellow"].setText("")
		self["button_yellow"].hide()
		if self["pc_list"].getCurrent() and self["pc_list"].getCurrent()[5] == "bookmark" and self["pc_list"].getCurrent()[6] == 0:
			self["button_green"].show()
			self["key_green"].setText("refresh mounts")
		else:
			self["button_green"].hide()
			self["key_green"].setText("")
		self["button_epg"].hide()
		self["key_ok"].setText("")
		self["key_0"].setText("")
		self["button_0"].hide()

	def mount_restart(self):
		AutoMount()
		self.start()

	def KeyRed(self):
		self.latest_dir = self["pc_list"].getCurrent()[0]
		if self.art == "dir" or self.art == "bookmark" or self.art == "ouverDir" or self.art == "filelist":
			idx = 0
			if self["pc_list"].getCurrent()[1] == "last_path" and self.index == 0:  # self.art=="bookmark":
				idx = self["pc_list"].getCurrent()[10]
			self.Pic_tools_back(self.latest_dir, idx)

		elif self.art == "file":
			self.latest_dir2 = self.latest_dir.replace(basename(self.latest_dir), "")
			self.index = self["pc_list"].getIndex()
			self.session.openWithCallback(self.KeyRed2, PictureCenterFS7_Filemenu, self.latest_dir)

	def KeyRed2(self, edit=0):
		if edit and self.markfile:
			self.filelist = read_marks(3, None, self.latest_dir)
		self.Pic_tools_back(self.latest_dir2)
		if self.index > len(self.list) - 1:
			self.index = self.index - 1
		self["pc_list"].setIndex(self.index)
		self.selectionChanged()

	def KeyGreen(self):
		if self["pc_list"].getCurrent()[5] != "back":
			akt_bm = self["pc_list"].getCurrent()
			if self.art == "bookmark":
				if akt_bm[6] == 0:
					self.mount_restart()
					#self.session.open(MessageBox,_("If a mapped drive is not ready to join, please to join/turn on.\n\nIf the device is ready to please run via menu 'refresh mounts'."), MessageBox.TYPE_INFO)
				else:
					self.session.openWithCallback(self.nopic, Pic_Full_View3, akt_bm[0], 0, None, 1, self.markfile)
			if self.art == "dir" or self.art == "filelist":  # or self.art=="ouverDir":
				akt_bm = self["pc_list"].getCurrent()
				if akt_bm[2] is not None:
					self.session.openWithCallback(self.nopic, Pic_Full_View3, akt_bm[0], 0, None, 1, self.markfile)
				else:
					self.session.openWithCallback(self.nopic, Pic_Full_View3, akt_bm[0], 0, None, 1, self.markfile)
			elif self.art == "file":
				index_nr = 0
				akt_bm = self["pc_list"].getCurrent()
				file_bez = (akt_bm[0], akt_bm[1], akt_bm[3], akt_bm[4], akt_bm[5], 1, akt_bm[7], akt_bm[8])
				piclist = file_list(self.dirname).Dateiliste
				if file_bez in piclist:
					index_nr = piclist.index(file_bez)
				self.session.openWithCallback(self.nopic, Pic_Full_View3, self.dirname, index_nr, piclist, 1)

	def KeyYellow(self):
		if self.art:
			path = self["pc_list"].getCurrent()[0]
			if self.art == "dir" or self.art == "bookmark" or self.art == "filelist":  # or self.art=="ouverDir":
				self.session.openWithCallback(self.nopic, Pic_Thumb, 0, path)
			elif self.art == "file":
				self.session.openWithCallback(self.nopic, Pic_Thumb, 0, self.dirname)

	def KeyBlue(self):
		if self["pc_list"].getCurrent()[5] != "ouverDir":
		#path,index=0,liste=None,slideshow=0,ind_wahl=None
			if self.art == "file":
				akt_bm = self["pc_list"].getCurrent()
				index_nr = 0
				akt_bm = self["pc_list"].getCurrent()
				file_bez = (akt_bm[0], akt_bm[1], akt_bm[3], akt_bm[4], akt_bm[5], 1, akt_bm[7], akt_bm[8])
				piclist = file_list(self.dirname).Dateiliste
				if file_bez in piclist:
					index_nr = piclist.index(file_bez)
				#self.session.openWithCallback(self.nopic,Pic_Full_View3,self.dirname,index_nr,piclist,1)
				file_bez = (akt_bm[0], self["pc_list"].getIndex(), vollbildsets[4], akt_bm[4], akt_bm[5], 1, vollbildsets[0], akt_bm[8])
				#piclist=file_list(self.dirname).Dateiliste

				self.session.open(Pic_Full_View3, self.dirname, index_nr, piclist, 0, file_bez)
			elif self.art == "bookmark" or self.art == "filelist" or self.art == "dir" or self.art == "ouverDir":
				akt_bm = self["pc_list"].getCurrent()
				ndex = 0
				if self.art == "bookmark":
					ndex = self["pc_list"].getCurrent()[10]
				#self.session.openWithCallback(self.nopic,Pic_Full_View3,akt_bm[0],0,self.markfile,0)
				#self.session.openWithCallback(self.nopic,Pic_Full_View3,akt_bm[0],akt_bm[1],vollbildsets[5],self.markfile,1)
				self.session.openWithCallback(self.nopic, Pic_Full_View3, akt_bm[0], ndex, self.markfile, 0)
			elif self.art == "back":
				self.start()

	def Full_View_back(self, args=None):
		if osd_alpha_off.value:
			self.alt_osd_alpha = str(open("/proc/stb/video/alpha", "r").read().strip())
			open("/proc/stb/video/alpha", "w").write(str(255))

	def KeyOk(self):
		if self["pc_list"].getCurrent()[5] == "back":
			self.start()
		elif self["pc_list"].getCurrent()[5] == "dir" or self["pc_list"].getCurrent()[5] == "dirs":
			self.Pic_tools_back(self["pc_list"].getCurrent()[0])
		elif self["pc_list"].getCurrent()[5] == "ouverDir":
			self.Pic_tools_back(self["pc_list"].getCurrent()[0])
		elif self.art == "file":
			index_nr = 0
			akt_bm = self["pc_list"].getCurrent()
			#file_bez=(akt_bm[0],akt_bm[1],vollbildsets[4],akt_bm[4],akt_bm[5],1,akt_bm[7],akt_bm[8])
			file_bez = (akt_bm[0], akt_bm[1], akt_bm[3], akt_bm[4], akt_bm[5], 1, akt_bm[7], akt_bm[8])
			piclist = file_list(self.dirname).Dateiliste
			if file_bez in piclist:
				index_nr = piclist.index(file_bez)
			self.session.open(Pic_Full_View3, self.dirname, index_nr, piclist, 0)
		elif self.art == "dir" or self.art == "bookmark" or self.art == "filelist":
			if self["pc_list"].getCurrent()[6] == 2:
				self.close()
			elif self["pc_list"].getCurrent()[6] == 0:
				self.session.open(MessageBox, _("If a mapped drive is not ready to join, please to join/turn on.\n\nIf the device is ready to please run via menu 'refresh mounts'."), MessageBox.TYPE_INFO)
			else:
				if default_ok.value.strip() == "Folder- and Filelist":
					self.KeyRed()
				else:
					akt_bm = self["pc_list"].getCurrent()
					if akt_bm[2] is not None:
						if default_ok.value == "Show Pictures":
							self.KeyBlue()
						elif default_ok.value == "Diashow":
							self.KeyGreen()

	def nopic(self, call):
		self.Full_View_back()
		if call:
			self.session.open(MessageBox, _("No Picture found on in this Dir"), MessageBox.TYPE_INFO)

	def path_wahl(self):
		self.session.openWithCallback(self.Pic_tools_back, BackupLocationBox, _("Please select path..."), default_dir.value, "")

	def showMainMenu(self):
		menu = []
		if self["pc_list"].getCurrent() is not None:
			selected = self["pc_list"].getCurrent()
			if selected[5] == "file":
				menu.append((_("file-actions"), self.KeyRed))
			if selected[5] == "dir":
				menu.append((_("Make Bookmark of selected dir"), self.make))
			elif selected[5] == "bookmark" and selected[1] != _("Default dir"):
				self.name = selected[1]
				menu.append((_("Edit / Delete Bookmark"), self.edit))
			menu.append((_("Settings"), self.showConfig))
			menu.append((_("New Bookmark"), self.new))
			if list_func.value:
				menu.append((_('Options for picture lists'), self.showMarkerMenu))
			menu.append((_("Refresh mounts"), self.mount_restart))
			menu.append((_('Backup ConfFS-Dir'), self.backup))
			menu.append((_('Restore ConfFS-Dir'), self.restore))
			menu.append((_("About"), self.showAbout))
			self.session.openWithCallback(self.menuCallback, ChoiceBox, title=_("PictureCenterFS - Menu"), list=menu)

	def showMarkerMenu(self):
		menu = []
		if self["pc_list"].getCurrent() is not None:
			menu.append((_('Empty temporary marked list'), self.leere_marks))
			menu.append((_('Save temporary marked list'), self.save_marks))
			if len(self.marker_listen):
				menu.append((_('Delete saved list'), self.delete_marks))
			self.session.openWithCallback(self.menuCallback, ChoiceBox, title=_("PictureCenterFS - ") + _('Options for picture lists'), list=menu)

	def menuCallback(self, choice):
		if choice is not None:
			choice[1]()

	def backup(self):
		backup(self.session).start(3)

	def restore(self):
		backup(self.session).start(5)

	def showConfig(self):
		self.session.openWithCallback(self.settings_back, PictureCenterFS7_Setup2)

	def settings_back(self):
		global filesort
		global vollbildsets
		global exclude
		global distance_infoline2
		configparser1 = ConfigParser()
		configparser1.read(DATAFILE)
		if configparser1.has_section("settings"):
			l1 = configparser1.items("settings")
			for nam in l1:
				if nam[0].strip() != "distance_infoline":
					if nam[1].strip() == "True":
						vars()[nam[0]].value = True   #True
					elif nam[1].strip() == "False":
						vars()[nam[0]].value = False
					elif nam[0].strip() == "filesort":
						if "date" in nam[1] and pil_install != "ok":
							filesort.value = "name"
						else:
							filesort.value = nam[1].strip()
					elif nam[0].strip() == "distance_infoline2":
						i1 = nam[1].replace("[", "").replace("]", "").split(",")
						i_space = [int(i1[0]), int(i1[1])]
						distance_infoline2.value = i_space
					else:
						try:
							vars()[nam[0]].value = int(nam[1].strip())
						except Exception:
							vars()[nam[0]].value = nam[1]
			vollbildsets = [fullbildsort.value, infoline.value, playvideo.value, std_read_sub.value, filesort.value]
			exclude = ()
			if len(excludeconf.value.strip()):
				exclude = excludeconf.value.split(",")
		if self.filelist and len(self.filelist):
			self.Pic_tools_back(self.pfad)
		else:
			self.start()

	def new(self):
		self.session.openWithCallback(self.start, PictureCenterFS7_Edit, name="", neu=1)

	def edit(self):
		self.session.openWithCallback(self.start, PictureCenterFS7_Edit, name=self.name, neu=0)

	def make(self):
		if self["pc_list"].getCurrent():
			if isdir(self["pc_list"].getCurrent()[0]):
				self.session.open(PictureCenterFS7_Edit, name=self["pc_list"].getCurrent()[0], neu=2)
			else:
				self.session.open(MessageBox, _("no valid directory"), MessageBox.TYPE_INFO)

	def Pic_tools_back(self, path1=None, selection=0, sortin=filesort.value):
		if path1:
			sortin = vollbildsets[4]

			self.hide_button()
			self.art = ""
			self.pfad = path1
			self.nlist = []
			self.filelist = []
			if self.markfile:
				self.filelist = read_marks(self["pc_list"].getCurrent()[0])
			else:
				self.filelist = file_list(self.pfad, 1).Dateiliste    # path,subdirs=False,videoplay=False, sortart="Name")
			if self.filelist is None:
				self.filelist = []
			filepng = LoadPixmap(pics2["pic"])
			odirpng = LoadPixmap(pics2["up"])
			bmpng = LoadPixmap(pics2["pin"])
			opng = LoadPixmap(pics2["ordner"])
			o_anz = 0
			for x in self.filelist:
				if not x[1].startswith("."):
					if x[4] == "file":
						self.nlist.append((x[0], x[1], None, x[2], x[3], x[4], 1, x[6], x[7], filepng))
					else:
						self.nlist.append((x[0], x[1], None, sortin, x[3], x[4], 1, x[6], x[7], opng))
						o_anz += 1
			self.nlist.insert(0, ("Bookmarks", _("back to Bookmarks"), None, sortin, False, "back", None, None, None, bmpng, 0))
			if not self.markfile:
				# o_anz+=1
				self.nlist.insert(1, ('/'.join(path1.split('/')[:-2]) + '/', "<" + _("Parent Directory") + ">", None, sortin, std_read_sub, "ouverDir", 1, 0, None, odirpng, 0))       #_("Current Dir")
			self.st_aktiv = False
			self["pc_list"].setList(self.nlist)
			selnr = selection + o_anz
			with open("/tmp/004.txt", "a") as f:
				f.write("%s, %s, %s\n" % (selnr, selection, len(self.nlist)))
			if len(self.nlist) <= selnr or selection == 0:
				selnr = 0
			if selnr > 0:
				self["pc_list"].setIndex(selnr)

	def showPic(self, picInfo=""):
		ptr = self.picload.getData()
		if ptr is not None:
			self["thumb"].instance.setPixmap(ptr)
			self["thumb"].show()

	def showThn(self, datei=None):
		self.ThumbTimer.stop()
		pic = None
		if self["pc_list"].getCurrent()[0].lower().endswith(TYPE_MOV):
			pic = SKIN_EXT + "/pictures/mov.jpg"
		elif self["pc_list"].getCurrent()[0].lower().endswith(TYPE_PIC):
			pic = self["pc_list"].getCurrent()[0]
		if pic:
			if thumbquali.value == 0:
				self.picload.getThumbnail(str(pic))  # == 1:
			else:
				self.picload.startDecode(pic)

	def setConf(self):
		self.setTitle("PictureCenterFS " + version)
		sc = getScale()
		self.picload.setPara((self["thumb"].instance.size().width(), self["thumb"].instance.size().height(), sc[0], sc[1], cache.value, int(resize.value), bgcolor.value))  # cache.value
		if bgcolor.value != "skin0":
			if pil_install == "ok" and bgcolor.value != "skin" and bgcolor.value != "transparent":
				im = Image.new('P', (size_w + 50, size_h + 50), 0)
				draw = ImageDraw.Draw(im)
				draw.rectangle((0, 0, size_w + 50, size_h + 50), bgcolor.value)
				im.save('/tmp/bgr.png', 'PNG')
				self["bgr2"].instance.setPixmapFromFile("/tmp/bgr.png")
				self["bgr2"].instance.setTransparent(0)
			elif bgcolor.value == "skin" or bgcolor.value == "transparent":
				self["bgr2"].instance.setTransparent(1)
				self["bgr2"].hide()

	def StartExif(self):
		dates = self["pc_list"].getCurrent()
		if self.art == "file" and dates[0].lower().endswith(TYPE_PIC) and exists(dates[0]):
			img = Image.open(dates[0])
			info1 = img.getexif()
			if info1:
				info = dict((TAGS[k], v) for k, v in info1.items() if k in TAGS)
				self.session.open(Show_Exif, info, dates[0])
		elif self.art == "dir" or self.art == "bookmark" or self.art == "ouverDir":
			filelist1 = file_list(dates[0]).Dateiliste2
			anz = len(filelist1)
			text = str(anz) + " " + _("pictures in") + "\n" + dates[0]
			self.session.open(MessageBox, text, MessageBox.TYPE_INFO)

	def leere_marks(self, args=None):
		open("/tmp/pcfs_mark", "w").close()

	def save_marks(self, args=None):
		self.session.openWithCallback(self.save_marks2, VirtualKeyBoard, title=_("Enter File-Name:"), text="")

	def save_marks2(self, name=None):
		self.safe_name = ""
		if name:
			name = name.split(".")
			self.safe_name = "%s_pcfs.txt" % name[0]
		if pathExists(join(DATAPATH, self.safe_name)):
			self.safe_name = name
			self.session.openWithCallback(self.save_marks3, MessageBox, _("file exist on this path, overwrite?"), MessageBox.TYPE_YESNO)
		else:
			self.save_marks3(self)

	def save_marks3(self, answer):
		if answer == True and self.safe_name:
			save_mark(self.session, answer)
			self.safe_name = ""
			#self.marker_listen=[i for i in listdir(DATAPATH) if i.endswith('_pcfs.txt')]
			self.start()

	def delete_marks(self):
		listen = [[x, DATAPATH + x] for x in self.marker_listen]
		self.session.openWithCallback(self.delete_marks2, ChoiceBox, title=_("PictureCenterFS - ") + _('Delete picture list file'), list=listen)

	def delete_marks2(self, answer):
		if answer:
			self.del_file = answer[1]
			self.session.openWithCallback(self.delete_marks3, MessageBox, _("File") + "\n" + answer[0] + "\n" + _("really delete?"), MessageBox.TYPE_YESNO)

	def delete_marks3(self, answer):
		if answer and self.del_file:
			remove(self.del_file)
			self.del_file = None
			self.start()

	def texteingabeFinished(self, ret):
		if ret is not None:
			self.conf_name.value = ret

	def showAbout(self, args=None):
		self.session.open(MessageBox, "PictureCenterFS\nAutor: shadowrider\n", MessageBox.TYPE_INFO)


######################################################################
class file_list:
	def __init__(self, path, spez=None):
		sortart = vollbildsets[4]
		subdirs = vollbildsets[3]
		if spez:
			subdirs = "True2"
		videoplay = vollbildsets[2]
		#if not sortart:
		#   sortart=aktsortin
		if sortart == "random":
			sortart = "name"
		elif pil_install != "ok" and "date" in sortart:
			sortart = "name"
		self.Dateiliste = []
		self.Dateiliste2 = []
		startDir = path
		typ_list = TYPE_PIC
		if not videoplay:
			typ_list = TYPE_PIC + TYPE_MOV
		directories = [startDir]
		while len(directories) > 0:
			directory = directories.pop()
			if isdir(directory):
				for name in listdir(directory):
					if name:
						excludes = None
						if len(exclude):
							for x in exclude:
								if x.lower() in name.lower():
									excludes = 1
									break
						adding = 1
						fullpath = join(directory, name)
						if not excludes and not name.startswith(".") and not fullpath.startswith(".") and not name.startswith("@"):
							if isfile(fullpath) and getsize(fullpath) > 0:
								if name.lower().endswith(typ_list) and fullpath != '/tmp/bgr.png':  #,"gif"
									xf_date = (0, "")
									xf = None
									if "date" in sortart:
										#xf=self.get_exif(fullpath)
										if name.lower().endswith(TYPE_PIC):
											xf = self.get_exif(fullpath)
										if name.lower().endswith(TYPE_MOV) or not xf:
											x1 = getmtime(fullpath)
											xf = (x1, strftime("%d.%m.%Y", gmtime(x1)))
										#xf= strftime('%Y:%m:%d %H:%M:%S',self.get_exif(fullpath))
										if xf:
											xf_date = xf  # mktime(xf)
									self.Dateiliste2.append((fullpath, name, sortart, True, "file", 1, xf_date[0], xf_date[1]))
							elif isdir(fullpath):
								if cache.value == False and fullpath.endswith(".Thumbnails"):
									rmtree(fullpath)
									adding = 0
								if subdirs == True and adding == 1:
									directories.append(fullpath)
								elif str(subdirs) == "True2" and adding == 1:
									self.Dateiliste.append((fullpath + "/", name, sortart, True, "dir", True, 1, 0))
		if "date" in sortart:
			self.Dateiliste2.sort(key=lambda x: x[6])
		elif sortart == "name" or sortart == "revers":
			self.Dateiliste2.sort(key=lambda x: "".join(x[1]).lower())
		if "revers" in sortart:
			self.Dateiliste2.reverse()
		self.Dateiliste.sort(key=lambda x: "".join(x[1]).lower())

		self.Dateiliste.extend(self.Dateiliste2)

	def get_exif(self, fn=None):
		ret = None
		if fn and exists(fn):
			i = Image.open(fn)
			info = i.getexif()
			if info:
				for tag, value in info.items():
					decoded = TAGS.get(tag, tag)
					if decoded == "DateTimeOriginal":
						xf = strptime(value, '%Y:%m:%d %H:%M:%S')
						if xf:
							xf3 = strftime("%d.%m.%Y", xf)
							ret = (mktime(xf), xf3)
							return ret
######################################################################

class PictureCenterFS7_Edit(Screen, ConfigListScreen, HelpableScreen):
	with open(SKIN_EXT + skin_ext_zusatz + "pcFS_setup.xml") as tmpskin:
		skin = tmpskin.read()

	def __init__(self, session, name="", neu=0):
		self.neu = neu
		self.name = ""
		self.altname = name
		#sortierung="all"
		#self.read_sub=True
		path = ""
		self.configparser = ConfigParser()
		self.configparser.read(DATAFILE)
		sections = self.configparser.sections()
		self.conf_name = NoSave(ConfigText(default=self.name, fixed_size=False))
		self.conf_path = NoSave(ConfigText(default=path, fixed_size=False))
		sortierung1 = filesort.value
		if pil_install != "ok" and filesort.value == "date":
			sortierung1 = "name"
		self.conf_sortierung = NoSave(ConfigSelection(default=sortierung1, choices=sorten2))
		#else:
		#    self.conf_sortierung=NoSave(ConfigSelection(default=sortierung, choices = [("all", _("None")), ("Random", _("Random")), ("Name", _("Name")), ("revers", _("Name reverse"))]))
		self.conf_read_subdirs = NoSave(ConfigEnableDisable(default=True))
		self.conf_infoline = NoSave(ConfigEnableDisable(default=True))
		self.conf_videoplay = NoSave(ConfigEnableDisable(default=False))
		titel1 = " PictureCenterFS - " + _("New Bookmark")
		if self.neu == 0:
			self.name = name
			titel1 = " PictureCenterFS - " + _("Edit Bookmark")
			if name != "" and self.configparser.has_section(self.name):
				self.conf_name.setValue(name)
				self.conf_path.setValue(self.configparser.get(self.name, "path"))
				if self.configparser.has_option(self.name, "sortierung"):
					self.conf_sortierung.value = self.configparser.get(self.name, "sortierung")
				if self.configparser.has_option(self.name, "read_sub"):
					self.conf_read_subdirs.value = self.configparser.getboolean(self.name, "read_sub")
				if self.configparser.has_option(self.name, "infoline"):
					self.conf_infoline.value = self.configparser.getboolean(self.name, "infoline")
				if self.configparser.has_option(self.name, "videoplay"):
					self.conf_videoplay.value = self.configparser.getboolean(self.name, "videoplay")
								#if self.configparser.get(self.name, "read_sub")=="False":self.conf_read_subdirs.value=False
		elif self.neu == 2:
			self.name = ""
			self.conf_path.value = name
		Screen.__init__(self, session)
		self.skinName = "PictureCenterFS7_Edit"
		HelpableScreen.__init__(self)
		self["key_red"] = Label(_("Delete"))
		self["balken"] = Label("")
		self["key_green"] = Label(_("Save"))
		self["key_yellow"] = Label("")
		self["key_blue"] = Label("")
		self["pic_red"] = Pixmap()
		self["pic_green"] = Pixmap()
		self["pic_yellow"] = Pixmap()
		self["pic_blue"] = Pixmap()
		self["bgr2"] = Pixmap()
		self["pcfsKeyActions"] = HelpableActionMap(self, "pcfsKeyActions",
		{
			"green": (self.save, _("Save")),
			"ok": (self.ok_button, _("edit selected")),
			"red": (self.red_button, _("Delete")),
			"cancel": (self.close, _("Close"))
		}, -2)
		self.setTitle(titel1)
		pcFSConfigList = []
		self.dummy = getConfigListEntry(_(" >> select and press OK for edit >>"), ConfigNothing())
		pcFSConfigList.append(self.dummy)
		#pcFSConfigList.append(getConfigListEntry(_(" >> select and press OK for edit >>"),ConfigNothing() ))
		pcFSConfigList.append(getConfigListEntry(_("Bookmark-Name:"), self.conf_name))
		pcFSConfigList.append(getConfigListEntry(_("Picture-Path:"), self.conf_path))
		pcFSConfigList.append(getConfigListEntry(_("Read sub-dir's"), self.conf_read_subdirs))
		pcFSConfigList.append(getConfigListEntry(_("Picture Sorting:"), self.conf_sortierung))
		pcFSConfigList.append(getConfigListEntry(_("Show Infoline"), self.conf_infoline))
		pcFSConfigList.append(getConfigListEntry(_("Ignore video:"), self.conf_videoplay))
		ConfigListScreen.__init__(self, pcFSConfigList, session=self.session)

	def ok_button(self):
		self.cur = self["config"].getCurrent()
		self.cur = self.cur and self.cur[1]
		if self.cur == self.conf_path:  # or self.cur==self.conf_genre2:
			self.path_wahl()
		elif self.cur == self.conf_name:
			self.session.openWithCallback(
						self.texteingabeFinished,
						VirtualKeyBoard,
						title=_("Enter Bookmark-Name:"),
						text=self.conf_name.value
				)

	def texteingabeFinished(self, ret):
		if ret is not None:
			self.conf_name.value = ret

	def path_wahl(self):
		self.session.openWithCallback(self.call_path, BackupLocationBox, _("Please select the Bookmark path..."), "")

	def call_path(self, call):
		if call:
			self.conf_path.value = call

	def red_button(self):
		if len(self.conf_name.value) > 0:
			self.session.openWithCallback(self.delete2, MessageBox, self.name + _("Delete Bookmark really?"), MessageBox.TYPE_YESNO)

	def delete2(self, call):
		if call:
			self.configparser.remove_section(self.name)
			with open(DATAFILE, "w") as fp:
				self.configparser.write(fp)
			self.close()

	def save(self):
		if len(self.conf_name.value) > 0:
			filelist1 = file_list(self.conf_path.value).Dateiliste2
			if not isdir(self.conf_path.value):
				self.session.open(MessageBox, _("Path failed"), MessageBox.TYPE_ERROR)
			elif len(filelist1) < 1:
				self.session.openWithCallback(self.no_pic, MessageBox, _("No Picture in this dir"), MessageBox.TYPE_YESNO)

			else:
				self.save1()
		else:
			self.session.open(MessageBox, _("No Name!"), MessageBox.TYPE_ERROR)

	def no_pic(self, answer):
		if answer:
			self.save1()

	def save1(self):
		self.configparser2 = ConfigParser()
		self.configparser2.read(DATAFILE)
		if len(self.altname) > 0 and self.configparser2.has_section(self.altname):
			self.configparser2.remove_section(self.altname)
			self.session.openWithCallback(self.save2, MessageBox,self.altname +_("Bookmark overwrite?"), MessageBox.TYPE_YESNO)
		try:
			self.configparser2.add_section(self.conf_name.value)
			self.save3()
		except Exception as e:
			self.session.openWithCallback(self.save2, MessageBox, self.conf_name.value + _("Bookmark exist, overwrite?"), MessageBox.TYPE_YESNO)

	def save2(self, answer):
		if answer:
			self.configparser2.remove_section(self.conf_name.value)
			self.configparser2.add_section(self.conf_name.value)
			self.save3()
		else:
			self.name = self.conf_name.value

	def save3(self):
		self.configparser2.set(self.conf_name.value, "path", self.conf_path.value)
		self.configparser2.set(self.conf_name.value, "read_sub", self.conf_read_subdirs.value)
		self.configparser2.set(self.conf_name.value, "sortierung", self.conf_sortierung.value)
		self.configparser2.set(self.conf_name.value, "infoline", self.conf_infoline.value)
		self.configparser2.set(self.conf_name.value, "videoplay", self.conf_videoplay.value)
		with open(DATAFILE, "w") as fp:
			self.configparser2.write(fp)
		self.close()


class BackupLocationBox(LocationBox):
	def __init__(self, session, text, dir=None, minFree=None):
		inhibitDirs = ["/bin", "/boot", "/dev", "/lib", "/proc", "/sbin", "/sys", "/usr", "/var"]
		LocationBox.__init__(self, session, text=text, currDir=dir, bookmarks=None, inhibitDirs=inhibitDirs, minFree=minFree)
		self.skinName = "LocationBox"
###############################################################################


#------------------------------------------------------------------------------------------

class PictureCenterFS7_Setup2(Screen, ConfigListScreen, HelpableScreen):
	with open(SKIN_EXT + skin_ext_zusatz + "pcFS_setup.xml") as tmpskin:
		skin = tmpskin.read()

	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = "PictureCenterFS7_Setup2"
		HelpableScreen.__init__(self)
		titel1 = "PictureCenterFS " + _("Settings")
		self.auswahl = NoSave(ConfigSelection(default="0", choices=[("0", _("main")), ("1", _("Default for full screen and diashow")), ("2", _("Infoline")), ("3", _("Thumbnails")), ("4", _("Screensaver"))]))
		self.fake_entry = NoSave(ConfigNothing())
		self["key_red"] = Label(_("Cancel"))
		self["balken"] = Label(_("Press OK") + ", " + _("Select with left / right") + " " + _("main") + ", " + _("Infoline") + ", " + _("Default for full screen and diashow") + ", " + _("Thumbnails"))
		self["key_green"] = Label(_("Save"))
		self["key_yellow"] = Label("")
		self["key_blue"] = Label("")
		self["pic_red"] = Pixmap()
		self["pic_green"] = Pixmap()
		self["pic_yellow"] = Pixmap()
		self["pic_blue"] = Pixmap()
		self["bgr2"] = Pixmap()
		self.onChangedEntry = []
		self.session = session

		self["pcfsKeyActions"] = HelpableActionMap(self, "pcfsKeyActions",
				{
				"green": (self.save, _("Save")),
				"red": (self.keyCancel, _("Cancel")),
				"ok": (self.ok_button, _("edit if possible")),
				"cancel": (self.keyCancel, _("Cancel and close")),
				}, -2)
		self.refresh()
		self.setTitle(titel1)
		ConfigListScreen.__init__(self, self.liste, on_change=self.reloadList)  # on_change = self.changedEntry)
		if not self.set_help in self["config"].onSelectionChanged:
			self["config"].onSelectionChanged.append(self.set_help)

	def refresh(self):
		liste = []
		liste.append(getConfigListEntry(_("Select Options area") + " (< >)", self.fake_entry))
		liste.append(getConfigListEntry(_("Show options for:"), self.auswahl))
		if self.auswahl.value == "1":
			liste.append(getConfigListEntry(_("(more settings in Bookmarks)"), self.fake_entry))
		liste.append(getConfigListEntry("", self.fake_entry))
		if self.auswahl.value == "0":
			liste.append(getConfigListEntry(_("Show in mainmenu"), config.plugins.PictureCenterFS.hauptmenu))
			liste.append(getConfigListEntry(_("Picture Sorting:"), filesort))
			liste.append(getConfigListEntry(_("Exclude if in name:"), excludeconf))
			liste.append(getConfigListEntry(_("Ch+ Button-Aktion"), ch_tast))
			liste.append(getConfigListEntry(_("default action for 'OK'"), default_ok))
			liste.append(getConfigListEntry(_("Default dir"), default_dir))
			liste.append(getConfigListEntry(_("Read sub-dir's"), std_read_sub))
			liste.append(getConfigListEntry(_("Background"), bgcolor))
			liste.append(getConfigListEntry(_("Turn off GUI transparency"), osd_alpha_off))
			liste.append(getConfigListEntry(_("Picture-list functions"), list_func))
			liste.append(getConfigListEntry(_("Activate Screensaver-Plugin"), saver_on))
		elif self.auswahl.value == "4":
			# if saver_on:
			liste.append(getConfigListEntry("   " + _("Path for pictures"), saver_path))
			liste.append(getConfigListEntry("   " + _("Order"), saver_random))
			liste.append(getConfigListEntry("   " + _("Show from subdirs"), saver_subdirs))
			# liste.append(getConfigListEntry(_("Turn off GUI transparency"), osd_alpha_off))
		elif self.auswahl.value == "1":
			liste.append(getConfigListEntry(_("Show symbol for play and random"), symbols))
			if symbols.value:
				liste.append(getConfigListEntry(_("Symbols auto hide (sek)"), symbols_ah))
			liste.append(getConfigListEntry(_("Show Picture Name in Display:"), show_name))
			liste.append(getConfigListEntry(_("Sizes and positions"), fromskin))
			if fromskin.value == 2:
				liste.append(getConfigListEntry(_("Image distance to the edge"), framesize))
				liste.append(getConfigListEntry(_("Resloution"), resolu))
			liste.append(getConfigListEntry(_("Picture Sorting:"), fullbildsort))
			liste.append(getConfigListEntry(_("What do at the end (not random)"), loop2))
			liste.append(getConfigListEntry(_("What do at the end (random play)"), loop3))
			liste.append(getConfigListEntry(_("Slideshow Interval (sec.)"), slidetime))
			liste.append(getConfigListEntry(_("Slide-effekt"), slideeffekt))
			liste.append(getConfigListEntry(_("Break load (sec.)"), maxtime))
			liste.append(getConfigListEntry(_("Auto-Rotate"), a_rotate))
			liste.append(getConfigListEntry(_("Start sizing zoom"), zoomsize))
			# liste.append(getConfigListEntry(_("Show Infoline"), infoline))
		elif self.auswahl.value == "2":
			liste.append(getConfigListEntry(_("Show Infoline"), infoline))
			liste.append(getConfigListEntry(_("Info Color"), textcolor))
			if fromskin.value == 2:
				liste.append(getConfigListEntry(_("Infoline distance left, top") + "(100=0)", distance_infoline2))
				liste.append(getConfigListEntry(_("Infoline Backgroundcolor"), z1_bgcolor))
				liste.append(getConfigListEntry(_("Size for Info"), info_size))
		elif self.auswahl.value == "3":
			liste.append(getConfigListEntry(_("Thumbnail in filelist"), thumbquali))
			liste.append(getConfigListEntry(_("Thumbnail delaying ms"), thumbdelaying))
			liste.append(getConfigListEntry(_("Cache Thumbnails"), cache))
			liste.append(getConfigListEntry(_("Thumb size"), thumbsize))
			liste.append(getConfigListEntry(_("No. of pages jump"), sprungzahl))
			liste.append(getConfigListEntry(_("Text size"), thumbtxtsize))
			liste.append(getConfigListEntry(_("Text color"), thumbtxtcol))
			liste.append(getConfigListEntry(_("Back color"), thumbbackcol))
			liste.append(getConfigListEntry(_("Scaling Mode"), resize))
		self.liste = liste

	def reloadList(self):
		self.refresh()
		self["config"].setList(self.liste)
		self.set_help()

	def set_help(self):
		self.cur = self["config"].getCurrent()
		self.cur = self.cur and self.cur[1]
		if self.cur == self.auswahl:
			self["balken"].setText(_("Press OK") + ", " + _("Select with left / right") + " " + _("main") + ", " + _("Infoline") + ", " + _("Default for full screen and diashow") + ", " + _("Thumbnails"))
		elif self.cur == z1_bgcolor or self.cur == bgcolor or self.cur == thumbbackcol:
			self["balken"].setText(_("Select with left / right") + " " + _("color or transparent"))
		elif self.cur == default_dir or self.cur == saver_path:
			self["balken"].setText(_("Press OK"))
		elif self.cur == default_dir or self.cur == excludeconf:
			self["balken"].setText(_("Files and dirs with the partial term in the name are not list and displayed\n separate several with comma (OK to edit)"))
		else:
			self["balken"].setText(_("Select with left / right") + " " + _("or change the entry"))

	def keyCancel(self):
		self.session.openWithCallback(
						self.cancelConfirm,
						MessageBox, _("Really close without saving settings?"), MessageBox.TYPE_YESNO)

	def cancelConfirm(self, result):
		if result:
			self.close()

	def ok_button(self):
		self.cur = self["config"].getCurrent()
		self.cur = self.cur and self.cur[1]
		if self.cur == default_dir:
			self.session.openWithCallback(self.call_path, BackupLocationBox, _("Please select the default dir..."), "")
		elif self.cur == saver_path:
			self.session.openWithCallback(self.call_path, BackupLocationBox, _("Please select dir..."), "")
		elif self.cur == self.auswahl:
			self.session.openWithCallback(self.lCallback, ChoiceBox, list=[(_("main"), "0"), (_("Default for full screen and diashow"), "1"), (_("Infoline"), "2",), (_("Thumbnails"), "3")])
		elif self.cur == excludeconf:
			self.session.openWithCallback(
						self.texteingabeFinished,
						VirtualKeyBoard,
						title=_("Do not show when in Name (separate with comma):"),
						text=excludeconf.value
				)

	def texteingabeFinished(self, ret):
		global exclude
		if ret is not None:
			excludeconf.value = ret
			exclude = ()
			if len(excludeconf.value.strip()):
				exclude = excludeconf.value.split(",")

	def lCallback(self, call):
		if call:
			self.auswahl.value = call[1]
			self.reloadList()

	def call_path(self, call):
		if call:
			if self.cur == default_dir:
				default_dir.value = call
			elif self.cur == saver_path:
				saver_path.value = call
			self.reloadList()

	def save(self):

		config.plugins.PictureCenterFS.hauptmenu.save()
		self.configparser = ConfigParser()
		self.configparser.read(DATAFILE)

		if self.configparser.has_section("settings"):
			self.configparser.remove_section("settings")
		self.configparser.add_section("settings")
		self.configparser.set("settings", "slidetime", str(slidetime.value))
		self.configparser.set("settings", "symbols_ah", str(symbols_ah.value))
		self.configparser.set("settings", "list_func", str(list_func.value))
		self.configparser.set("settings", "slideeffekt", str(slideeffekt.value))
		self.configparser.set("settings", "maxtime", str(maxtime.value))
		#self.configparser.set("settings", "resize", resize.value)
		self.configparser.set("settings", "thumbquali", str(thumbquali.value))
		self.configparser.set("settings", "thumbdelaying", str(thumbdelaying.value))
		self.configparser.set("settings", "thumbsize", str(thumbsize.value))
		self.configparser.set("settings", "cache", str(cache.value))
		self.configparser.set("settings", "infoline", str(infoline.value))
		self.configparser.set("settings", "fullbildsort", str(fullbildsort.value))
		self.configparser.set("settings", "filesort", str(filesort.value))
		self.configparser.set("settings", "excludeconf", str(excludeconf.value))
		self.configparser.set("settings", "framesize", str(framesize.value))
		self.configparser.set("settings", "fromskin", str(fromskin.value))
		self.configparser.set("settings", "distance_infoline2", str(distance_infoline2.value))
		self.configparser.set("settings", "loop2", str(loop2.value))
		self.configparser.set("settings", "bgcolor", str(bgcolor.value))
		self.configparser.set("settings", "z1_bgcolor", str(z1_bgcolor.value))
		self.configparser.set("settings", "textcolor", str(textcolor.value))
		self.configparser.set("settings", "default_dir", str(default_dir.value))
		self.configparser.set("settings", "std_read_sub", str(std_read_sub.value))
		self.configparser.set("settings", "default_ok", str(default_ok.value))
		self.configparser.set("settings", "a_rotate", str(a_rotate.value))
		self.configparser.set("settings", "zoomsize", str(zoomsize.value))
		self.configparser.set("settings", "ch_tast", str(ch_tast.value))
		self.configparser.set("settings", "sprungzahl", str(sprungzahl.value))
		self.configparser.set("settings", "symbols", str(symbols.value))
		self.configparser.set("settings", "thumbtxtsize", str(thumbtxtsize.value))
		self.configparser.set("settings", "info_size", str(info_size.value))
		self.configparser.set("settings", "thumbtxtcol", str(thumbtxtcol.value))
		self.configparser.set("settings", "thumbbackcol", str(thumbbackcol.value))
		self.configparser.set("settings", "show_name", str(show_name.value))
		self.configparser.set("settings", "saver_on", str(saver_on.value))
		self.configparser.set("settings", "saver_path", str(saver_path.value))
		self.configparser.set("settings", "saver_random", str(saver_random.value))
		self.configparser.set("settings", "saver_subdirs", str(saver_subdirs.value))
		self.configparser.set("settings", "resolu", str(resolu.value))
		with open(DATAFILE, "w") as fp:
			self.configparser.write(fp)
		self.close()
#---------------------------------------------------------------------------


class Show_Exif(Screen):
	with open(SKIN_EXT + skin_ext_zusatz + "pcFS_exif.xml") as tmpskin:
		skin = tmpskin.read()

	def __init__(self, session, exiflist, path):
		Screen.__init__(self, session)
		self.skinName = "Show_Exif"
		self.path = path
		self["key_red"] = StaticText(_("Close"))
		self["thumb"] = Pixmap()
		self["scrolltext"] = Label(_("scroll with right / left"))
		self.picload = ePicLoad()
		if DPKG:
			self.picload_conn = self.picload.PictureData.connect(self.showPic)
		else:
			self.picload.PictureData.get().append(self.showPic)

		path1 = path.replace(path.split('/')[-1], "")
		self.name = path.split('/')[-1]
		exifdesc = [_("filename") + ':', "EXIF-Version:", "Make:", "Camera:", "Date/Time:", "Width / Height:", "Flash used:", "Orientation:", "User Comments:", "Metering Mode:", "Exposure Program:", "Light Source:", "CompressedBitsPerPixel:", "ISO Speed Rating:", "X-Resolution:", "Y-Resolution:", "Resolution Unit:", "Brightness:", "Exposure Time:", "Exposure Bias:", "Distance:", "CCD-Width:", "ApertureFNumber:"]
		list = []
		list.append((_("Name: "), self.name))
		list.append((_("Path: "), path1))

		comment = ""
		if isinstance(exiflist, dict):
			for k, v in exiflist.items():
				if str(k) != "MakerNote":
					if type(v) is str:
						v = v.replace("UNICODE", "").replace("\x00", "")
						if k == "UserComment":
							comment = v
					list.append((k, str(v)))
		else:
			for x in range(len(exiflist)):
			#res=[]
				if x > 0:
					v = exiflist[x]
					if exifdesc[x] == "UserComment":
						v = str(v.replace("UNICODE", "").replace("\x00", "").decode("latin-1", "ignore"))
						comment = exiflist[x]
					list.append((exifdesc[x], exiflist[x]))
		self["menu"] = List(list)
		self["comment"] = StaticText(comment)

		self["actions"] = ActionMap(["SetupActions", "ColorActions", "DirectionActions"],
		{
				"cancel": self.close,
		}, -1)

#			 "up": 	self.up,
#			 "down": self.down,
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):

		size_w = getDesktop(0).size().width()
		size_h = getDesktop(0).size().height()
		self.instance.move(ePoint(0, 0))
		self.instance.resize(eSize(size_w, size_h))
		self.setTitle(_("Info") + ": " + self.name)
		sc = getScale()
		self.picload.setPara((self["thumb"].instance.size().width(), self["thumb"].instance.size().height(), sc[0], sc[1], cache.value, int(resize.value), bgcolor.value))  # cache.value
		self.picload.startDecode(self.path)

	def showPic(self, picInfo=""):
		ptr = self.picload.getData()
		if ptr is not None:
			self["thumb"].instance.setPixmap(ptr)
			self["thumb"].show()

#	def down(self):
#            self[self.currentList].pageDown()
#	def up(self):
#            self[self.currentList].pageUp()
#----------------------------------------------------------------------------------------


T_INDEX = 0
T_FRAME_POS = 1
T_PAGE = 2
T_NAME = 3
T_FULL = 4


class Pic_Thumb(Screen, HelpableScreen):
	def __init__(self, session, lastindex, path):
		self.sets = (path, vollbildsets[3], vollbildsets[2])
		self.markerfile = False
		#vollbildsets=(fullbildsort.value,infoline.value,playvideo.value,std_read_sub.value,filesort.value)
		self.art = vollbildsets[0]
		if self.art == "random" or self.art == "all":
			self.art = "name"
		if path.endswith("_pcfs.txt") or path == "/tmp/pcfs_mark":
			piclist = read_marks(path)
			self.markerfile = True
		else:
			piclist = file_list(self.sets[0]).Dateiliste
			#self.sets=(path,read_sub,videoplay)
		if piclist is None:
			piclist = []
		self.path = path
		self.read_sub = vollbildsets[3]
		self.textcolor = thumbtxtcol.value
		self.color = thumbbackcol.value
		#self.infoline= infoline
		txtsize = thumbtxtsize.value  # +6
		textsize = txtsize + 6
		self.spaceX = 35
		self.picX = int(thumbsize.value)  # 190
		self.spaceY = 30
		self.picY = int(thumbsize.value)  # 200
		self.fertig = 1
		size_w = getDesktop(0).size().width()
		size_h = getDesktop(0).size().height()
		self.thumbsX = int(size_w / (self.spaceX + self.picX))  # thumbnails in X
		self.thumbsY = int(size_h / (self.spaceY + self.picY))  # thumbnails in Y
		self.thumbsC = int(self.thumbsX * self.thumbsY)  # all thumbnails
		self.positionlist = []
		skincontent = ""
		posX = -1
		for x in range(self.thumbsC):
			posY = int(x / self.thumbsX)
			posX += 1
			if posX >= self.thumbsX:
				posX = 0
			absX = self.spaceX + (posX * (self.spaceX + self.picX))
			absY = self.spaceY + (posY * (self.spaceY + self.picY))
			self.positionlist.append((absX, absY))
			skincontent += "<widget source=\"label" + str(x) + "\" render=\"Label\" position=\"" + str(absX + 5) + "," + str(absY + self.picY - textsize) + "\" size=\"" + str(self.picX - 10) + "," + str(textsize) + "\" font=\"Regular;" + str(txtsize) + "\" zPosition=\"3\" transparent=\"1\" noWrap=\"1\" foregroundColor=\"" + self.textcolor + "\" />"
			if "date" in self.art:
				skincontent += "<widget source=\"label2" + str(x) + "\" render=\"Label\" position=\"" + str(absX + 5) + "," + str(absY + self.picY) + "\" size=\"" + str(self.picX - 10) + "," + str(textsize) + "\" font=\"Regular;" + str(txtsize) + "\" zPosition=\"3\" transparent=\"1\" noWrap=\"1\" foregroundColor=\"" + self.textcolor + "\" />"
			skincontent += "<widget name=\"thumb" + str(x) + "\" position=\"" + str(absX + 5) + "," + str(absY + 5) + "\" size=\"" + str(self.picX - 10) + "," + str(self.picY - (textsize * 2)) + "\" zPosition=\"3\" transparent=\"1\" alphatest=\"on\" />"
		# Screen, backgroundlabel and MovingPixmap
		self.skin = "<screen position=\"center,center\" size=\"" + str(size_w) + "," + str(size_h) + "\" flags=\"wfNoBorder\" > \
			<eLabel position=\"0,0\" zPosition=\"0\" size=\"" + str(size_w) + "," + str(size_h) + "\" backgroundColor=\"" + self.color + "\" /> \
			<widget name=\"frame1\" position=\"35,34\" zPosition=\"1\" size=\"" + str(self.picX) + "," + str(self.picY + 9 - (textsize * 2)) + "\" backgroundColor=\"" + self.textcolor + "\" /> \
			<widget name=\"frame2\" position=\"44,44\" zPosition=\"2\" size=\"" + str(self.picX - 10) + "," + str(self.picY - (textsize * 2)) + "\" backgroundColor=\"" + self.color + "\" />" + skincontent + "</screen>"
#			<widget source=\"session.VideoPicture\" render=\"Pig\" position=\"" + str(size_w) + ",0\" zPosition=\"-8\" size=\"100,100\" /> \
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		t1 = _("not activated")
		if list_func.value:
			t1 = _("Add to marked list")
		self["pcfsKeyActions"] = HelpableActionMap(self, "pcfsKeyActions",
		{
				"record": (self.mark_list, t1),
				"cancel": (self.Exit, _("back to Bookmarks")),
				"ok": (self.KeyOk, _("Open selected picture")),
				"left": (self.key_left, _("left")),
				"right": (self.key_right, _("right")),
				"up": (self.key_up, _("Up")),
				"down": (self.key_down, _("Down")),
				"info": (self.StartExif, _("Show Exif-Data")),
				"green": (self.slideshow, _("Play Slideshow")),
				"play": (self.slideshow, _("Play Slideshow")),
				"playpause": (self.slideshow, _("Play Slideshow")),
				"blue": (self.show_pictures, _("Show Pictures")),
				"prevBouquet": (self.next_page, _("Next Page")),
				"nextBouquet": (self.prev_page, _("Preview Page")),
				"Back": (self.first_page, _("First Page")),
				"For": (self.last_page, _("Last Page")),
				"rewind": (self.zehnback_page, str(sprungzahl.value) + _(" Pages back")),
				"fastfor": (self.zehnvor_page, str(sprungzahl.value) + _(" Pages for")),
		}, -1)
		titel1 = " PictureCenterFS - " + _("Thumbs")
		self.setTitle(titel1)
		self["frame1"] = Label()
		self["frame2"] = Label()
		for x in range(self.thumbsC):
			self["label" + str(x)] = StaticText()
			self["label2" + str(x)] = StaticText()
			self["thumb" + str(x)] = Pixmap()
		self.Thumbnaillist = []
		self.filelist = []
		self.currPage = -1
		self.dirlistcount = 0
		self.path = path
		index = 0
		framePos = 0
		Page = 0
		self.all_liste = piclist
		for x in piclist:
#			if x[1] == False:
			datum = 0
			if len(x) > 7 and x[7] != "":
				datum = str(x[7])
			self.filelist.append((index, framePos, Page, x[1], x[0], datum))
			index += 1
			framePos += 1
			if framePos > (self.thumbsC - 1):
				framePos = 0
				Page += 1
#			else:
#				self.dirlistcount += 1
		self.maxentry = len(self.filelist) - 1
		self.index = lastindex - self.dirlistcount
		if self.index < 0:
			self.index = 0
		self.picload = ePicLoad()
		if DPKG:
			self.picload_conn = self.picload.PictureData.connect(self.showPic)
		else:
			self.picload.PictureData.get().append(self.showPic)
		if len(self.filelist) < 1:
			self.close(2)
		else:
			self.onLayoutFinish.append(self.setPicloadConf)
		self.ThumbTimer = eTimer()
		if DPKG:
			self.ThumbTimer_conn = self.ThumbTimer.timeout.connect(self.showPic)
		else:
			self.ThumbTimer.callback.append(self.showPic)
#		if  len(piclist) <1:
#			self.close(2)

	def setPicloadConf(self):
		sc = getScale()
		self.picload.setPara([self["thumb0"].instance.size().width(), self["thumb0"].instance.size().height(), sc[0], sc[1], cache.value, int(resize.value), self.color])

		self.paintFrame()

	def paintFrame(self):
		#print "index=" + str(self.index)
		if self.maxentry < self.index or self.index < 0:
			return

		pos = self.positionlist[self.filelist[self.index][T_FRAME_POS]]
		#self["frame"].moveTo( pos[0], pos[1], 1)
		#self["frame"].startMoving()
		self["frame1"].instance.move(ePoint(pos[0], pos[1]))
		self["frame2"].instance.move(ePoint(pos[0] + 5, pos[1] + 5))
		if self.currPage != self.filelist[self.index][T_PAGE]:
			self.currPage = self.filelist[self.index][T_PAGE]
			self.newPage()

	def newPage(self):
		self.Thumbnaillist = []
		#clear Labels and Thumbnail
		for x in range(self.thumbsC):
			self["label" + str(x)].setText("")
			self["label2" + str(x)].setText("")
			self["thumb" + str(x)].hide()
		#paint Labels and fill Thumbnail-List
		for x in self.filelist:
			if x[T_PAGE] == self.currPage:
				self["label" + str(x[T_FRAME_POS])].setText("(" + str(x[T_INDEX] + 1) + ") " + x[T_NAME])
				self["label2" + str(x[T_FRAME_POS])].setText(str(x[5]))
				self.Thumbnaillist.append([0, x[T_FRAME_POS], x[T_FULL]])

		self.showPic()

	def showPic(self, picInfo=""):
		self.fertig = 0
		i = 0
		for x in range(len(self.Thumbnaillist) + 1):
			i += 1
			if i > len(self.Thumbnaillist):
				self.fertig = 1
			else:
				if self.Thumbnaillist[x][0] == 0:
					pic = self.Thumbnaillist[x][2]
					if self.Thumbnaillist[x][2].lower().endswith(TYPE_MOV):
						pic = SKIN_EXT + "/pictures/mov.jpg"

					if self.picload.getThumbnail(pic) == 1:  # zu tun probier noch mal
						self.ThumbTimer.start(300, True)
					else:
						self.Thumbnaillist[x][0] = 1
					break
				elif self.Thumbnaillist[x][0] == 1:
					self.Thumbnaillist[x][0] = 2
					ptr = self.picload.getData()
					if ptr is not None:
						self["thumb" + str(self.Thumbnaillist[x][1])].instance.setPixmap(ptr)
						self["thumb" + str(self.Thumbnaillist[x][1])].show()

	def mark_list(self):
		if list_func.value and not self.markerfile:
			read_marks("/tmp/pcfs_mark", self.filelist[self.index][4])

	def key_left(self):
		if self.fertig == 1:
			self.index -= 1
			if self.index < 0:
				self.index = self.maxentry
			self.paintFrame()

	def key_right(self):
		if self.fertig == 1:
			self.index += 1
			if self.index > self.maxentry:
				self.index = 0
			self.paintFrame()

	def key_up(self):
		if self.fertig == 1:
			self.index -= self.thumbsX
			if self.index < 0:
				self.index = self.maxentry
			self.paintFrame()

	def key_down(self):
		if self.fertig == 1:
			self.index += self.thumbsX
			if self.index > self.maxentry:
				self.index = 0
			self.paintFrame()

	def next_page(self, umkehr=None):
		if self.fertig == 1:
			if not umkehr and ch_tast.value == "down":
				self.prev_page("1")
			else:
				if self.fertig == 1:
					self.index = self.index + (self.thumbsY * self.thumbsX)
					if self.index > self.maxentry:
						self.index = 0
					self.paintFrame()

	def prev_page(self, umkehr=None):
		if self.fertig == 1:
			if not umkehr and ch_tast.value == "down":
				self.next_page("1")
			else:
				if self.fertig == 1:
					self.index = self.index - (self.thumbsY * self.thumbsX)
					if self.index < 0:
						self.index = self.maxentry
					self.paintFrame()

	def first_page(self):
		if self.fertig == 1:
			self.index = 0
			self.paintFrame()

	def last_page(self):
		if self.fertig == 1:
			rest = self.maxentry % (self.thumbsY * self.thumbsX)
			self.index = self.maxentry - rest  # +1-(self.thumbsY*self.thumbsX)
			self.paintFrame()

	def zehnvor_page(self):
		if self.fertig == 1:
			self.index1 = self.index + (int(sprungzahl.value) * self.thumbsY * self.thumbsX)
			if self.index < self.maxentry + 1:
				self.index = self.index1
			self.paintFrame()

	def zehnback_page(self):
		if self.fertig == 1:
			self.index1 = self.index - (int(sprungzahl.value) * self.thumbsY * self.thumbsX)
			if self.index > -1:
				self.index = self.index1
			self.paintFrame()

	def StartExif(self):
		if not self.filelist[self.index][T_FULL].lower().endswith(TYPE_MOV):
			if self.maxentry < 0:
				return
			if exists(self.filelist[self.index][T_FULL]):
				try:
					img = Image.open(self.filelist[self.index][T_FULL])
					info = dict((TAGS[k], v) for k, v in img.getexif().items() if k in TAGS)
				except Exception:
					info = self.picload.getInfo(self.filelist[self.index][T_FULL])
				self.session.open(Show_Exif, info, self.filelist[self.index][T_FULL])

	def KeyOk(self):
		if self.maxentry < 0:
			return
		self.old_index = self.index
		self.session.openWithCallback(self.callbackView, Pic_Full_View3, self.filelist[self.index][T_FULL], self.index, self.all_liste, 0)

	def callbackView(self, filelist):
		if self.path == "/tmp/pcfs_mark":
			piclist = read_marks(1)
		else:
			piclist = file_list(self.sets[0]).Dateiliste
		if piclist is None:
			piclist = []
		index = 0
		framePos = 0
		Page = 0
		self.filelist = []
		for x in piclist:
			self.filelist.append((index, framePos, Page, x[1], x[0], x[7]))
			index += 1
			framePos += 1
			if framePos > (self.thumbsC - 1):
				framePos = 0
				Page += 1
		self.maxentry = len(self.filelist) - 1
		self.newPage()
		self.paintFrame()

	def Exit(self):
		del self.picload
		self.close(None)

	def slideshow(self):
		self.session.openWithCallback(self.callbackView, Pic_Full_View3, self.path, self.index, self.all_liste, 1)

	def show_pictures(self):
		self.session.openWithCallback(self.callbackView, Pic_Full_View3, self.path, self.index, self.all_liste, 0)

#---------------------------------------------------------------------------


class full_text(MenuList):
	def __init__(self, list, enableWrapAround=False):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)

	def postWidgetCreate(self, instance):
		MenuList.postWidgetCreate(self, instance)
		self.instance = instance

	def buildList(self, listnew):
		listnew1 = [listnew]
		col2 = None
		nameliste = []
		res = []
		if len(listnew1) > 0:
			self.instance.setItemHeight(listnew[1])
			self.l.setFont(0, gFont("Regular", listnew[2]))
			for name in listnew1:
				res = [name]
				res.append(MultiContentEntryText(pos=(5, 0), size=name[4], font=0, text=name[0], flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, border_width=0, backcolor=col2))  #,color=col1 ,backcolor =col2
			nameliste.append(res)
			self.l.setList(nameliste)


class Pic_Full_View3(Screen, InfoBarSeek, HelpableScreen):
	with open(SKIN_EXT + skin_ext_zusatz + "pcFS_full.xml") as tmpskin:
		skin = tmpskin.read()

	def __init__(self, session, path, index=0, liste=None, slideshow=0, ind_wahl=None):
			#         self.dirname,0,fullbildsort.value,0,False,infoline.value,piclist,file_bez)
		#alte wbrfs_Version
		with open("/tmp/001.txt", "a") as f:
			f.write(str(path) + "\n" + str(index) + "\n" + str(liste) + "\n" + str(slideshow) + "\n" + str(ind_wahl) + "\n")
		ind_wahl = None
		index = 0
		if liste == "random":
			liste = None
			ind_wahl = None
			slideshow = "saver"
		#alte wbrfs_Version ende
		self.alt_osd_alpha = None
		self.merkpath = path
		self.picload = ePicLoad()
		if osd_alpha_off.value:
			self.alt_osd_alpha = str(open("/proc/stb/video/alpha", "r").read().strip())
			open("/proc/stb/video/alpha", "w").write(str(255))
		print("[PictureCenterFS] start fullsize")
		self.session = session
		#self.videoplay=videoplay
		#vollbildsets=(fullbildsort.value,infoline.value,playvideo.value,std_read_sub.value)
		self.slideshow = slideshow
		if str(index) == "saver":
			self.art = saver_random.value.lower()
			self.videoplay = False
			self.txt = False
			self.read_sub = saver_subdirs.value
			self.slideshow = 1
		else:
			self.art = vollbildsets[0].lower()
			self.videoplay = vollbildsets[2]  # videoplay
			self.txt = vollbildsets[1]
			self.read_sub = vollbildsets[3]
		self.sets = None
		self.im = None
		self.filelist = []
		#self.art=art.lower()
		self.end = 0
		self.path = None
		self.movepoint = 0
		self.fertig_index = 0
		self.index = index
		self.exif = None
		self.alt_exif = None

		#self.txt=i_line
		self.markerfile = False
		self.symbols_on = symbols.value
		self.onChangedEntry = []
		self.altservice = self.session.nav.getCurrentlyPlayingServiceReference()
		if liste and not liste == path:
			self.filelist = list(liste)
			self.end = 1
		elif index < 0:
			self.filelist.append((path, path, self.art, "False", "file"))
			index = 0
		else:
			self.path = path
			#self.read_sub=read_sub
			if path.endswith("_pcfs.txt") or path == "/tmp/pcfs_mark":
				self.filelist = read_marks(path)
				self.markerfile = True
				if path == "/tmp/pcfs_mark":
					self.slideshow = 0
					self.art = self.art
					self.txt = True
			else:
				self.filelist = file_list(self.path).Dateiliste  # filelist
		if self.filelist is None:
			self.filelist = []
		if index >= 0:
			self.index = index
		self.akt_index = self.index
		if ind_wahl:
			if ind_wahl in self.filelist:
				self.akt_index = self.filelist.index(ind_wahl)
		if len(self.filelist) < 2:
			self.slideshow = 0
		self.zoom_on = False
		self.rotate_index = None
		self.rotat_pic = ""
		self.textcolor = textcolor.value
		self.bgcolor = bgcolor.value
		#self.txt=i_line
		self.rot_source = None
		self.move = 0
		self.v_pause = 0
		self.erststart = 0
		self.pic_fertig = 1
		self.prev_index = None
		self.pause = 0
		self.marklist = []
		self.lastindex = None
		#self.size_w = None
		self.size_w = getDesktop(0).size().width()
		self.size_h = getDesktop(0).size().height()
		self.oldsize = (self.size_w, self.size_h)
		if gMainDC and fromskin.value == 2:
			try:
				if (self.size_w, self.size_h) != eval(resolu.value):
					print("[PictureCenterFS] resize screen")
					gMainDC.getInstance().setResolution(self.size_w, self.size_h)
					getDesktop(0).resize(eSize(self.size_w, self.size_h))
					(self.size_w, self.size_h) = (size_w, size_h)
			except Exception:
				self.size_w = None
				print("[PictureCenterFS] resize failed")
#                elif fromskin.value==1 and resolu.value:
#                     #(size_w2, size_h2) = eval(resolu.value)
#                     try:
#                        #print "[PictureCenterFS] resize screen"
#                        if (self.size_w, self.size_h) != eval(resolu.value):
#                            #(size_w, size_h) = eval(resolu.value)
#                            #gMainDC.getInstance().setResolution(size_w, size_h)
#                            #getDesktop(0).resize(eSize(size_w, size_h))
#                            (self.size_w, self.size_h)=eval(resolu.value)
#                     except Exception:
#			    self.size_w = None
				#print "[PictureCenterFS] resize failed"
		#with open("/tmp/pcfs1","a") as f:
		#	f.write(str(self.size_w)+","+str(self.size_h)+"\n")
		self.size_w = self.size_w - (framesize.value * 2)
		self.size_h = self.size_h - (framesize.value * 2)
		self.sc = AVSwitch().getFramebufferScale()
		Screen.__init__(self, session)
		self.skinName = "Pic_Full_View3"
		self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
						iPlayableService.evEOF: self.next_from_mov,
				})                                                   #alphatest=\"on\"    #ackgroundColor=\""+ self.bgcolor +"\" transparent=\"1\"
		HelpableScreen.__init__(self)
		t1 = _("not activated")
		if list_func.value:
			t1 = _("Add to marked list")
		#self.action_prio = -1
		InfoBarSeek.__init__(self, actionmap="MediaPlayerSeekActions")
		#self["pcfsvKeyActions"] = HelpableActionMap(self, "MediaPlayerSeekActions",

		self["pcfsKeyActions"] = HelpableActionMap(self, "pcfsKeyActions",
		{
				"cancel": (self.Exit, _("Back to Startscreen")),
				"record": (self.mark_list, t1),
				"green": (self.PlayPause, _("Slideshow")),
				"yellow": (self.toggle_art, _("toggle Slideshow random/sorted")),
				"play": (self.PlayPause, _("Play Slideshow")),
				"pause": (self.PlayPause, _("Pause / Resume Slideshow")),
				"playpause": (self.PlayPause, _("Pause / Resume Slideshow")),
				"stop": (self.Slide_stop, _("Stop Slideshow")),
				"red": (self.text, _("Show/Hide Text")),
				"left": (self.prevPic, _("Prev. Picture or zoom range left")),
				"right": (self.nextPic, _("Next Picture or zoom range right")),
				"up": (self.zoom_up, _("Zoom range Up")),
				"down": (self.zoom_down, _("Zoom range Down")),
				"menu": (self.Pic_tools, _("Options for select Picture")),
				"info": (self.StartExif, _("Show Exif-Data")),
				"nextBouquet": (self.faster, _("Slide-time faster")),
				"prevBouquet": (self.slower, _("Slide-time slower")),
				"Back": (self.zoomfenster_minus, _("reduced zoom range")),
				"For": (self.zoomfenster_plus, _("increased zoom range")),
				"9": (self.rotat_rechts, _("Rotate 90->")),
				"7": (self.rotat_links, _("Rotate <-90")),
				"4": (self.FLIP_TOP_BOTTOM, _("Flip image horizontally")),
				"2": (self.FLIP_LEFT_RIGHT, _("Flip image vertically")),
				"5": (self.manipulation_exit, _("Image manipulation undo")),
				"ok": (self.KeyOk, _("Start Zoom")),
				"blue": (self.blue, _("Zoom"))
		}, 0)

		self["txt_zeile"] = Label()
		self["playline"] = ServicePositionGauge(self.session.nav)

		self["pic"] = Pixmap()
		self["pic2"] = Pixmap()
		self["pic2"].hide()
		#self["bgr"] = Label()

		self["backline"] = Pixmap()
		self["txt_bgr"] = Label()
		self["play_icon"] = Pixmap()
		self["bgr2"] = Pixmap()

		self["klo"] = Pixmap()
		self["klu"] = Pixmap()
		self["kro"] = Pixmap()
		self["kru"] = Pixmap()

		self.abstand = 200
		self.or_index = 0
		self.old_index = None
		self.load = False
		self.maxTimer = eTimer()
		self.symb_hideTimer = eTimer()
		self.maxtime = maxtime.value
		self.symbol_hide = 0
		if symbols.value == True:
			self.symbol_hide = int(symbols_ah.value)
		if DPKG:
			self.maxTimer_conn = self.maxTimer.timeout.connect(self.nextPic)
			self.symb_hideTimer_conn = self.symb_hideTimer.timeout.connect(self.symb_hide)
		else:
			self.maxTimer.callback.append(self.nextPic)
			self.symb_hideTimer.callback.append(self.symb_hide)
		self.currPic = []
		self.currPic2 = None
		self.currPic3 = None
		self.next_currPic = None
		self.show_wart = 0
		self.alt_pic = None
		self.shownow = True
		self.moveTimer = eTimer()
		if DPKG:
			self.moveTimer_conn = self.moveTimer.timeout.connect(self.movePic)
		else:
			self.moveTimer.callback.append(self.movePic)
		titel1 = " PictureCenterFS"
		self.setTitle(titel1)
		if len(self.filelist) < 1:
			self.maxentry = 0
			self.eExit(2)
		else:
			if self.art == "random":
				shuffle(self.filelist)
			self.maxentry = len(self.filelist) - 1
			#if ind_wahl and ind_wahl in self.filelist:
			#    index=self.filelist.index(ind_wahl)
			#if index >=0:
			#    self.index = index
			self.picload = ePicLoad()
			if DPKG:
				self.picload_conn = self.picload.PictureData.connect(self.finish_decode)
			else:
				self.picload.PictureData.get().append(self.finish_decode)
			self.slideTimer = eTimer()
			if DPKG:
				self.slideTimer_conn = self.slideTimer.timeout.connect(self.ShowPicture2)
			else:
				self.slideTimer.callback.append(self.ShowPicture2)
			self.slidetime = slidetime.value
			if self.maxentry >= 0:
				self.onLayoutFinish.append(self.setPicloadConf)

	def symb_hide(self):
		if self.pause != 1:
			self["play_icon"].hide()
			self.symbols_on = None

	def setPicloadConf(self):
		self.onLayoutFinish.remove(self.setPicloadConf)
		size_w2 = self.instance.size().width()
		size_h = self.instance.size().height()
		self["playline"].hide()
		self.zoom_out()
		pic_path = SKIN_EXT + "pictures/"
		self.random_icon = pics2["pcfs_random"]
		self.play_icon = pics2["pcfs_play"]
		self.pause_icon = pics2["pcfs_pause"]
		space = framesize.value
		self.space = space
		self.space_top = distance_infoline2.value[1] - 100   #top
		space_left = distance_infoline2.value[0] - 100   #top
		self.zeil_size = self["play_icon"].instance.size().height()
		symb_size = (0, 0)
		if fromskin.value == 2:
			print("pcfs resize all")
			self.instance.resize(eSize(self.oldsize[0], self.oldsize[1]))
			self.instance.move(ePoint(0, 0))
			size_w2 = self.instance.size().width()
			size_h = self.instance.size().height()

			bigger = 0

			#symb_size=(0,0)
			if self.symbols_on == True:
				if info_size.value == 2:
					symb_size = (self["play_icon"].instance.size().width(), self["play_icon"].instance.size().height())
				elif info_size.value == 1:
					symb_size = (35, 35)
					bigger = 10
					self.random_icon = pics2["b_pcfs_random"]  #+b_pic
					self.play_icon = pics2["b_pcfs_play"]
					self.pause_icon = pics2["b_pcfs_pause"]
				elif info_size.value == 0:
					symb_size = (25, 25)
			self.zeil_size = symb_size[1]
			self["play_icon"].resize(eSize(symb_size[0], symb_size[1]))
			self["play_icon"].move(ePoint(space_left + 5, self.space_top + 4))
			text_size = symb_size[1] - 5

			if self.txt != True:
				self["pic"].resize(eSize(size_w2 - (space * 2), size_h - (space * 2)))
				self["pic"].move(ePoint(space, space))
			else:
				self["pic"].resize(eSize(size_w2 - (space * 2), size_h - symb_size[1] - (space * 2)))
				self["pic"].move(ePoint(space, space + symb_size[1]))

			self.text_anfang = space_left + ((symb_size[0] + 10) * 1)

			self.space = space
#                self["pic"].move(ePoint(space,space))
			self["bgr2"].resize(eSize(size_w2 + 50, size_h + 50))
			self["bgr2"].move(ePoint(0, 0))

			if bgcolor.value == "transparent":
				self["bgr2"].hide()

			self["playline"].move(ePoint((size_w2 - 400) / 2, size_h - 50))

#                self["play_icon"].move(ePoint(space_left+5, self.space_top+4))
			self["txt_zeile"].resize(eSize(size_w2, symb_size[1]))
			self["txt_zeile"].instance.setFont(gFont("Regular", text_size))

			self.text_anfang
			self["txt_zeile"].move(ePoint(self.text_anfang, self.space_top + 4))

			self["backline"].move(ePoint(space_left, self.space_top))
			self["backline"].resize(eSize(size_w2 + 100, symb_size[0] + 10))

			if textcolor.value != "skin":
				self["txt_zeile"].instance.setForegroundColor(parseColor(textcolor.value))
				self["txt_zeile"].instance.setShadowColor(parseColor("#000000"))

		else:
#                pic_path=SKIN_EXT+"pictures/"
			self.random_icon = pics2["pcfs_random"]
			self.play_icon = pics2["pcfs_play"]
			self.pause_icon = pics2["pcfs_pause"]

			self.text_anfang = 0
			if textcolor.value != "skin":
				self["txt_zeile"].instance.setForegroundColor(parseColor(textcolor.value))

		if slideeffekt.value:
			self["pic2"].resize(eSize(size_w2 - (space * 2), size_h - (space * 2)))
			self.pic2_pos = (size_w2 - space, size_h - space, symb_size[1])
			self.move_art = 0  # randint(1,2)
		if pil_install == "ok" and bgcolor.value != "skin" and bgcolor.value != "transparent":
			colb = bgcolor.value
			if bgcolor.value == "skin0":
				colb = "black"
			im = Image.new('P', (size_w2 + 50, size_h + 50), 0)
			draw = ImageDraw.Draw(im)
			draw.rectangle((0, 0, size_w2 + 50, size_h + 50), colb)
			im.save('/tmp/bgr.png', 'PNG')
			self["bgr2"].instance.setPixmapFromFile("/tmp/bgr.png")
			self["bgr2"].instance.setTransparent(0)
			self["backline"].instance.setPixmapFromFile("/tmp/tbgr.png")
		if self.txt != True:
			self["txt_zeile"].hide()
			self["backline"].hide()
			#if self.txt:
		elif z1_bgcolor.value == "transparent":
			self["backline"].hide()
		if self.art == "random":
			self.icon = self.random_icon
		else:
			self.icon = self.play_icon
		self["play_icon"].instance.setPixmapFromFile(self.icon)
		if self.slideshow == 0:
			self["play_icon"].hide()

		if self.txt == True:
			self.set_text(_("please wait, loading picture..."))
		#sc = getScale()
		self.picload.setPara([self["pic"].instance.size().width(), self["pic"].instance.size().height(), self.sc[0], self.sc[1], False, 1, self.bgcolor])
		#self.picload.setPara([self.size_w, self.size_h, sc[0], sc[1], False, 1, self.bgcolor])
		self.start_decode()

	def set_text(self, text=""):
		self["txt_zeile"].setText(text)
		#self.selectionChanged()

	def mark_list(self):
		if list_func.value and not self.markerfile:
			if self.filelist is None:
				self.filelist = []
			if self.lastindex is None:
				self.lastindex = 0
			if not self.filelist[self.lastindex][0].startswith("/tmp/changed"):
				read_marks("/tmp/pcfs_mark", self.filelist[self.lastindex][0])

	def zoom_out(self):
		#self.abstand=300
		self.abstand = int(zoomsize.value)
		self.posa = int(((getDesktop(0).size().width() - framesize.value) / 2) - (int(self.abstand / 2)))
		self.posb = int(((getDesktop(0).size().height() - framesize.value) / 2) - (int(self.abstand / 2)))
		#self.abstand=400
		self.zoom_move()
		self["klo"].hide()
		self["klu"].hide()
		self["kro"].hide()
		self["kru"].hide()
		self.zoom_on = 0

	def rotat_filetest(self, aktion=None):
		if self.move == 0:
			if pil_install != "ok":
				self.rot_source = None
				self.session.open(MessageBox, _("PIL is not installed"), MessageBox.TYPE_INFO, timeout=15)
			else:
				if not self.slideTimer.isActive() and self.load == False and self.filelist and self.akt_index:

					if self.or_index is None:
						self.or_index = self.akt_index
					if self.filelist[0][0] == '/tmp/changed.' + self.source_typ:
						if exists('/tmp/changed2.' + self.source_typ):
							remove('/tmp/changed2.' + self.source_typ)
						rename('/tmp/changed.' + self.source_typ, '/tmp/changed2.' + self.source_typ)
						self.rot_source = '/tmp/changed2.' + self.source_typ

						del self.filelist[0]
						self.maxentry = self.maxentry - 1
					else:
						self.rot_source = self.filelist[self.akt_index][0]
						self.source_typ = self.filelist[self.akt_index][0].split(".")[-1]
					self.rotat_pic = '/tmp/changed.' + self.source_typ  # self.filelist[self.akt_index][0]
					if exists(self.rot_source):
						self.im = Image.open(self.rot_source)
						if self.im and aktion:
							if aktion == 1:
								self.im.rotate(270).save('/tmp/changed.' + self.source_typ)  #, 'rechts'
							elif aktion == 2:
								self.im.rotate(90).save('/tmp/changed.' + self.source_typ)  #, links'
							elif aktion == 3:
								self.im.transpose(method=1).save('/tmp/changed.' + self.source_typ)
							elif aktion == 4:
								self.im.transpose(method=0).save('/tmp/changed.' + self.source_typ)
							self.rotat2()

	def FLIP_TOP_BOTTOM(self):
		self.rotat_filetest(3)

	def FLIP_LEFT_RIGHT(self):
		self.rotat_filetest(4)

	def rotat_rechts(self):
		self.rotat_filetest(1)

	def rotat_links(self):
		self.rotat_filetest(2)

	def zoom(self):
		if not self.slideTimer.isActive() and self.load == False:
			self.zoom_on = 1
			self["klo"].show()
			self["klu"].show()
			self["kro"].show()
			self["kru"].show()
			self.zoom_move()

	def zoom_rechts(self):
		self.posa += 10
		self.zoom_move()

	def zoom_links(self):
		self.posa -= 10
		self.zoom_move()

	def zoom_up(self):
		self.posb -= 10
		self.zoom_move()

	def zoom_down(self):
		self.posb += 10
		self.zoom_move()

	def zoomfenster_plus(self):
		self.abstand += 5
		self.zoom_move()

	def zoomfenster_minus(self):
		self.abstand -= 5
		self.zoom_move()

	def zoom_move(self):
		self.eck_liste = [("klo", self.posa, self.posb), ("kro", self.posa + self.abstand, self.posb), ("klu", self.posa, self.posb + self.abstand), ("kru", self.posa + self.abstand, self.posb + self.abstand)]
		for x in self.eck_liste:
			self[x[0]].move(ePoint(x[1], x[2]))

	def KeyOk(self):
		if self.move == 0:
			if self.zoom_on == 1:
				self.rotat_filetest()
			if self.rot_source and self.im:
				size_h = self["pic"].instance.size().height()
				size_b = self["pic"].instance.size().width()
				scale = max(float(self.im.size[1]) / float(size_h), float(self.im.size[0]) / float(size_b))
				h_verlust = (getDesktop(0).size().height() - (self.im.size[1] / scale)) / 2
				b_verlust = (getDesktop(0).size().width() - (self.im.size[0] / scale)) / 2
				left = (self.posa - b_verlust) * scale
				right = (self.posa - b_verlust + self.abstand + 40) * scale
				upper = (self.posb - h_verlust) * scale
				lower = (self.posb - h_verlust + self.abstand + 40) * scale
				if left < 0 or left >= self.im.size[0]:
					left = 0
				if upper < 9 or upper >= self.im.size[1]:
					upper = 0
				if right > self.im.size[0] or right <= 0:
					right = self.im.size[0]
				if lower > self.im.size[1] or lower <= 0:
					lower = self.im.size[1]
				self.im.crop((int(left), int(upper), int(right), int(lower))).save('/tmp/changed.' + self.source_typ)          #, 'JPEG'
				self.zoom_out()
				self.rotat2()

	def blue(self):
		if self.slideTimer.isActive():
			self.PlayPause()
		if not self.slideTimer.isActive() and self.load == False and self.zoom_on == 0 and self.move == 0:
			self.zoom_on = 1
			self["klo"].show()
			self["klu"].show()
			self["kro"].show()
			self["kru"].show()
		elif self.zoom_on == 1:
			self.KeyOk()

	def rotat2(self):
		if self.filelist:
			self.filelist.insert(0, ('/tmp/changed.' + self.source_typ, '/tmp/changed.' + self.source_typ, "all", True, "file", 1))
		self.tTimer = eTimer()
		if DPKG:
			self.tTimer_conn = self.tTimer.timeout.connect(self.rotate)
		else:
			self.tTimer.callback.append(self.rotate)
		self.tTimer.start(20)
		self.rotate()

	def rotate(self):
		self.tTimer.stop()
		del self.im
		self.im = None
		self.maxentry = self.maxentry + 1
		self.rotate_index = self.index
		self.erststart = 0
		self.shownow = True
		if self.filelist:
			self.picload.startDecode(self.filelist[0][0])

	def clear_rotate(self, art=0):
		if exists('/tmp/changed2.' + self.source_typ):
			remove('/tmp/changed2.' + self.source_typ)
		if exists('/tmp/changed.' + self.source_typ):
			remove('/tmp/changed.' + self.source_typ)
		if self.filelist:
			del self.filelist[self.filelist.index(('/tmp/changed.' + self.source_typ, '/tmp/changed.' + self.source_typ, "all", True, "file", 1))]
		self.maxentry = self.maxentry - 1
		self.rotate_index = None
		self.rotat_pic = ""
		self.index = self.or_index if self.index < 0 else 0
		self.or_index = 0
		if art == 2:
			self.next()
		elif art == 1:
			self.prev()
		if art > 0:
			if self.pause == 1:
				self.Pause_end()
			else:
				self.erststart = 0
				self.shownow = True
				self.currPic3 = None
				self.start_decode()

	def createSummary(self):
		return pcFSLCDScreen

	def selectionChanged(self):
		if self.maxentry:
			name = ""
			num = 1
			if self.currPic:
				name = self.currPic[7]  # .split(" ",1)
				num = self.currPic[1]
			play = ""
			if self.slideshow == 1:
				play = ">"
			if self.pause == 1 or self.v_pause == 1:
				play = "II"
			for cb in self.onChangedEntry:
				cb(play, str(self.maxentry + 1), str(num + 1), name)

	def ShowPicture(self):
		if self.erststart == 0 and self.symbols_on and self.symbol_hide > 0:
			self.symb_hideTimer.start(int(self.symbol_hide) * 1000)
		self.erststart = 1
		if self.slideTimer.isActive():
			self.slideTimer.stop()
		self.akt_index = self.index
		#self.selectionChanged()
		if self.shownow and len(self.currPic):
			self.lastindex = self.currPic[1]
			self.shownow = False
			self.source_typ = self.currPic[5]
			if show_name.value:
				self.setTitle(self.currPic[6])
			if self.currPic[3] != "original" or self.currPic[4] == "pic":
				if self.move == 1:
					self["playline"].hide()
					self.session.nav.stopService()
					self.session.nav.playService(self.altservice)
					self.move = 0
					if self.txt == True:
						self["txt_zeile"].show()
						if z1_bgcolor.value != "transparent":
							self["backline"].show()
				if bgcolor.value != "skin" and bgcolor.value != "transparent":
					self["bgr2"].show()

				self["pic"].show()
				self["pic"].instance.setPixmap(self.currPic[2])

				if slideeffekt.value:
					self["pic2"].hide()
				self.set_text(self.currPic[0])
				if self.maxentry > 0:
					if self.slideshow == 1:
						if self.pause == 0:
							if self.symbols_on:
								self["play_icon"].instance.setPixmapFromFile(self.icon)
							self.slideTimer.startLongTimer(self.slidetime)  # ()
			elif self.currPic[4] == "movie":
				self["bgr2"].hide()
				self["backline"].hide()
				self["pic2"].hide()
				self["pic"].hide()

				fileRef = eServiceReference("4097:0:0:0:0:0:0:0:0:0:" + self.currPic[0])
				self.session.nav.playService(fileRef)
				self["txt_zeile"].instance.setTransparent(1)
				self["playline"].show()
				self.move = 1
				if self.txt == True:
					self.set_text(self.currPic[6])
			self.selectionChanged()

	def finish_decode(self, picInfo=""):
		self.load = False
		rt = "original"
		typ = "unknown"
		self.currPic0 = []
		if picInfo.lower().endswith(TYPE_MOV):
			text = picInfo
			text_name = text.split('/')[-1]
			# pure_name=text_name.replace("."+text_name.split(".")[-1],"")
			text2 = "(" + str(self.index + 1) + "/" + str(self.maxentry + 1) + ") " + text_name
			typ = text_name.split(".")[-1]
			pure_name = text_name.replace("." + typ, "")
			self.currPic0 = []
			self.currPic0.append(text)
			self.currPic0.append(self.index)
			self.currPic0.append(None)
			self.currPic0.append("original")
			self.currPic0.append("movie")
			self.currPic0.append(typ)
			self.currPic0.append(text2)
			self.currPic0.append(pure_name)
		else:
			ptr = self.picload.getData()
			print("4")
			if ptr is not None:
				text = ""
				text = picInfo.split('\n', 1)
				text_name = text[0].split('/')[-1]
				typ = text_name.split(".")[-1]
				pure_name = text_name.replace("." + typ, "")
				typ2 = "pic" if ".%s" % typ.lower() in TYPE_PIC else "unknown"
				if self.filelist:
					if '/tmp/changed2' in text[0]:
						text_name = self.filelist[self.index][0].split('/')[-1] + " (" + _("auto rotated") + ")"
						text = "(" + str(self.index + 1) + "/" + str(self.maxentry + 1) + ") " + text_name
					if text_name.startswith("changed"):
						text = "(" + str(self.index + 1) + "/" + str(self.maxentry + 1) + ") " + self.filelist[self.or_index + 1][0].split('/')[-1] + " (" + _("changed") + ")"
						rt = "changed"
				self.currPic0 = []
				self.currPic0.append(text)
				self.currPic0.append(self.index)
				self.currPic0.append(ptr)
				self.currPic0.append(rt)
				self.currPic0.append(typ2)
				self.currPic0.append(typ)
				self.currPic0.append(text_name)
				self.currPic0.append(pure_name)
			print("5")
		self.pic_fertig = 1
		self.maxTimer.stop()
		if self.erststart == 0 or not self.currPic:
			self.currPic = self.currPic0
			self.ShowPicture()
			self.next()
			self.start_decode()
		else:
			self.currPic3 = self.currPic0

	def load_new(self):
		if not self.currPic3:
			self.next()
			self.start_decode()

	def ShowPicture2(self):
		if self.lastindex and self.maxentry > 0:
			loop = 1
			if self.lastindex == self.maxentry:
				loop = 0
				loop_art = loop2.value
				if self.art == "random":
					loop_art = loop3.value
				if loop_art == "stop":
					self.Slide_stop()
				elif loop_art == "exit":
					self.eExit(None)
				elif loop_art == "restart":
					loop = 1
			if loop == 1:
				self.shownow = True
				self.show_wart = None
				if not self.currPic3:
					if self.pic_fertig == 1:
						self.load_new()
					self.slideTimer.start(100)
				else:
					if self.currPic3:
						self.currPic = self.currPic3
						self.next()
						self.start_decode()
						if slideeffekt.value and self.currPic[4] == "pic":
							self.move_art = 0
							width, l_rand = (0, 0)
							height, o_rand = (0, 0)
							if self.filelist and exists(self.filelist[self.currPic[1]][0]):
								im = Image.open(self.filelist[self.currPic[1]][0])
								(width, height) = im.size
								l_rand = (self.pic2_pos[0] - width) / 2
								o_rand = (self.pic2_pos[1] - height) / 2
								self.move_art = randint(1, 8)
							self.movepoint1 = self.space
							self.movepoint2 = self.space
							if self.move_art == 1:  # oben links
								self.movepoint1 = 0 - width - l_rand  # +self.space
								self.movepoint2 = 0 - width - l_rand  # self.pic2_pos[0]#+self.space
							elif self.move_art == 2:   # oben rechts ok
								self.movepoint1 = width + l_rand + self.space  # -self.space
								self.movepoint2 = 0 - width - l_rand + self.space  # +self.space

							elif self.move_art == 7:  #unten rechts
								self.movepoint1 = width + l_rand  #self.space+
								self.movepoint2 = width + l_rand  # +self.space
							elif self.move_art == 8:     #unten links ok
								self.movepoint1 = 0 - width - l_rand + self.space     #+self.space
								self.movepoint2 = width + l_rand + self.space  # +self.pic2_pos[2]

							elif self.move_art == 3:  # von oben  ok
								self.movepoint2 = 0 - height  # +self.space
							elif self.move_art == 4:  # von rechts ok
								self.movepoint1 = width + l_rand
							elif self.move_art == 5:  # von unten ok
								self.movepoint2 = self.pic2_pos[0] - o_rand - self.space  # height+self.space
							elif self.move_art == 6:    # von links ok
								self.movepoint1 = 0 - width - l_rand  # +self.space
							self["pic2"].instance.setPixmap(self.currPic[2])
							#self.moveTimer.startLongTimer(self.slidetime)
							if self.move == 1:
								self["playline"].hide()
								self.session.nav.stopService()
								self.session.nav.playService(self.altservice)
								self.move = 0
							self.movePic()
						else:
							self.slidePic()

	def movePic(self):
		if slideeffekt.value:
			soll = 1
			plus = slideeffekt.value
			self["pic2"].show()
			if self.move_art == 0:
				self.movepoint1 = self.space
				self.movepoint2 = self.space
			elif self.move_art == 1:
				if self.movepoint1 < self.space:
					soll = 0
					self.movepoint1 = self.movepoint1 + plus
					self.movepoint2 = self.movepoint2 + plus
			elif self.move_art == 2:
				if self.movepoint1 > self.space:
					soll = 0
					self.movepoint1 = self.movepoint1 - plus
					self.movepoint2 = self.movepoint2 + plus
			elif self.move_art == 3:
				if self.movepoint2 < self.space:
					soll = 0
					self.movepoint2 = self.movepoint2 + plus
			elif self.move_art == 4:
				if self.movepoint1 > self.space:
					soll = 0
					self.movepoint1 = self.movepoint1 - plus
			elif self.move_art == 5:
				if self.movepoint2 > self.space:
					soll = 0
					self.movepoint2 = self.movepoint2 - plus
			elif self.move_art == 6:
				if self.movepoint1 < self.space:
					soll = 0
					self.movepoint1 = self.movepoint1 + plus
			elif self.move_art == 7:
				if self.movepoint1 > self.space:
					soll = 0
					self.movepoint1 = self.movepoint1 - plus
					self.movepoint2 = self.movepoint2 - plus
			elif self.move_art == 8:
				if self.movepoint1 < self.space:
					soll = 0
					self.movepoint1 = self.movepoint1 + plus
					self.movepoint2 = self.movepoint2 - plus

			if soll == 0:
				self["pic2"].move(ePoint(self.movepoint1, self.movepoint2))
				self.moveTimer.start(50)
			else:
				self.moveTimer.stop()
				self.movepoint = 0 - self.pic2_pos[0]
				self.movepoint1 = 0 - self.pic2_pos[1]
				self.ShowPicture()

	def next_from_mov(self):
		if self.move == 1:
			self.ShowPicture2()

	def start_decode(self):
		if self.pic_fertig == 1:
			self.load = True
			self.pic_fertig = 0
			indx = self.index
			self.maxTimer.start(self.maxtime * 1000)
			print("#####self.filelist: %s" % str(self.filelist))
			pic = self.filelist[indx][0] if self.filelist else ""
			print("1")
			dreh = ""
			if self.exif:
				self.alt_exif = self.exif
			self.exif = None
			if pic.lower().endswith(TYPE_PIC) and exists(pic):
				img = Image.open(pic)
				if img and img.getexif():
					self.exif = dict((TAGS[k], v) for k, v in img.getexif().items() if k in TAGS)
					if a_rotate.value:
						rotlist = ('', '', '', "Bottom-Right", '', '', "Left-Bottom", '', "Right-Top")
						if 'Orientation' in self.exif and int(self.exif['Orientation']) in (3, 6, 8):
							dreh = rotlist[int(self.exif['Orientation'])]
					if not self.exif:
						dreh = str(self.picload.getInfo(pic)[7])
					if not self.im and dreh in ("Left-Bottom", "Right-Top", "Bottom-Right") and self.filelist and exists(self.filelist[indx][0]):
						self.source_typ = self.filelist[indx][0].split(".")[-1]  # .lower()
						im = Image.open(self.filelist[indx][0])
						if dreh == "Left-Bottom":
							im.rotate(270).save('/tmp/changed2.' + self.source_typ)
						elif dreh == "Right-Top":
							im.rotate(90).save('/tmp/changed2.' + self.source_typ)
						elif dreh == "Bottom-Right":
							im.rotate(180).save('/tmp/changed2.' + self.source_typ)
						del im
						pic = '/tmp/changed2.' + self.source_typ
				print("2")
				self.picload.startDecode(pic)
			elif pic.lower().endswith(TYPE_MOV):
				self.finish_decode(pic)
			#self.selectionChanged()
			print("3")

	def next(self):
		self.index = self.akt_index + 1
		if self.index > self.maxentry:
			if self.art == "random" and self.filelist:
				shuffle(self.filelist)
			self.index = 0

	def prev(self):
		self.index = self.akt_index - 1
		if self.index < 0:
			self.index = self.maxentry

	def slidePic(self):
		if not self.currPic:
			self.slideTimer.start(100)
		elif self.currPic:
			self.shownow = True
			self.ShowPicture()
		else:
			self.slideTimer.start(100)

	def PlayPause(self):

		if self.move == 1:
			self.playpauseService()
		else:
			if self.slideshow == 1 and self.pause == 0:
				self.moveTimer.stop()
				if self.slideTimer.isActive():
					self.slideTimer.stop()
				self["play_icon"].instance.setPixmapFromFile(self.pause_icon)
				self["play_icon"].show()
				self.symbols_on = True
				self.pause = 1
			else:
				self.Pause_end()
			self.selectionChanged()

	def Pause_end(self):
		if self.maxentry > 0:
			if self.move == 1:
				self.playpauseService()
			else:
				if self.symbols_on:
					self["play_icon"].instance.setPixmapFromFile(self.icon)
					self["play_icon"].show()
					if int(self.symbol_hide):
						self.symb_hideTimer.start(int(self.symbol_hide) * 1000)
				self.slideshow = 1
				self.pause = 0
				if self.zoom_on == 1 or self.rotate_index is not None:
					self.manipulation_exit()
				else:
					self.erststart = 0
					self.slideTimer.startLongTimer(2)
				self.selectionChanged()

	def Slide_stop(self):
		if self.move == 1:
			self.move = 0
			self["pic"].show()
			#self["bgr"].show()
			self.session.nav.stopService()
			self.session.nav.playService(self.altservice)

		if self.slideTimer.isActive():
			self.slideTimer.stop()
		if self.moveTimer.isActive():
			self.moveTimer.stop()
		self.old_index = None
		self["pic"].show()
		self["pic2"].hide()
		self["playline"].hide()
		if bgcolor.value != "skin" and bgcolor.value != "transparent":
			self["bgr2"].show()
		self.slideshow = 0
		self["play_icon"].hide()
		#self["random"].hide()

	def prevPic(self):
		self.moveTimer.stop()
		if self.load == False:
			if self.zoom_on == 1:
				self.zoom_links()
			else:
				if self.slideshow == 1 and self.pause == 0:
					self.PlayPause()
				if self.rotate_index:
					self.clear_rotate(1)

				else:
					if self.move == 1:
						self.session.nav.stopService()
					self.currPic = []
					self.prev()
					self.erststart = 0
					self.shownow = True
					self.start_decode()

	def nextPic(self):
		self.moveTimer.stop()
		if self.zoom_on == 1:
			self.zoom_rechts()
		else:
			if self.rotate_index is not None:
				self.clear_rotate(2)
			else:
				if self.slideTimer.isActive():
					self.slideTimer.stop()
				if self.slideshow == 1 and self.pause == 0:
					self.ShowPicture2()
				else:
					self.next()
					self.erststart = 0
					self.shownow = True
					self.start_decode()

	def Pic_tools(self):
		if self.slideshow == 1 and self.pause == 0:
			self.PlayPause()
		if self.move == 1:
			self["pic"].show()
			#self["bgr"].show()
			self.session.nav.playService(self.altservice)
			self.move = 0
		pic = ""
		if self.rotate_index is not None:
			pic = self.rot_source
		elif self.filelist:
			pic = self.filelist[self.akt_index][0]
		self.session.openWithCallback(self.Pic_tools_back, PictureCenterFS7_Filemenu, pic, self.rotat_pic)

	def Pic_tools_back(self, edit=None):
		if self.rotate_index is not None:
			self.clear_rotate()
		elif edit:
			if self.path:
				self.filelist = []
				if self.markerfile:
					self.filelist = read_marks(self.path, None, self.filelist[self.akt_index][0])
				else:
					list_new = file_list(self.path).Dateiliste
					add_list = [x for x in list_new if x not in self.filelist]
					self.filelist = [x for x in self.filelist if x in list_new]
					if len(add_list):
						add_list.reverse()
						for x in add_list:
							self.filelist.insert(self.akt_index, x)
				if self.filelist and len(self.filelist):
					self.maxentry = len(self.filelist) - 1
					self.nextPic()
				else:
					self.Exit()
		else:
			self.nextPic()
		if self.pause == 1:
			self.Pause_end()

	def StartExif(self):
		if self.filelist is None:
			self.filelist = []
		if not self.filelist[self.akt_index][0].lower().endswith(TYPE_MOV):
			e_date = None
			if self.slideTimer.isActive():
				self.PlayPause()
			if self.maxentry < 0:
				return
			#f=open("/tmp/exif","w")
			#f.write(str(self.exif)+"\n")
			if self.alt_exif:
				e_date = self.alt_exif
			elif self.exif:
				e_date = self.exif
			if e_date is None:
				e_date = self.picload.getInfo(self.filelist[self.akt_index][0])
			#f.write(str(self.filelist[self.akt_index][0])+"\n")
			#f.write(str(e_date)+"\n")
			#f.close()
			self.session.openWithCallback(self.restart, Show_Exif, e_date, self.filelist[self.akt_index][0])

	def restart(self):
		pass

	def faster(self):
		if self.slidetime > 2:
			self.slidetime = self.slidetime - 1
			self.slidetime_msg()

	def slower(self):
		self.slidetime = self.slidetime + 1
		self.slidetime_msg()

	def slidetime_msg(self):
		sl_text = _("Slide Time has been changed to") + " " + str(self.slidetime) + " " + _("seconds")
		self.session.open(MessageBox, sl_text, MessageBox.TYPE_INFO, timeout=3)

	def toggle_art(self):
		if self.art == "random" and self.filelist:
			self.filelist.sort(key=lambda x: "".join(x[1]).lower())
			self.art = "all"
			self.icon = self.play_icon
		elif self.filelist:
			self.art = "random"
			shuffle(self.filelist)
			self.icon = self.random_icon
		if self.symbols_on:
			self["play_icon"].hide()
			self["play_icon"].instance.setPixmapFromFile(self.icon)
			self["play_icon"].show()
			if self.symbol_hide > 0:
				self.symb_hideTimer.start(int(self.symbol_hide) * 1000)
		#if fromskin.value==2:self["txt_zeile"].move(ePoint(text_anfang, self.space_top+4))

	def text(self):
		size_w = self.instance.size().width()
		size_h = self.instance.size().height()

		if self.txt == False:
			self.txt = True
			zeil = self.zeil_size
			self["txt_zeile"].show()
			if z1_bgcolor.value != "transparent":
				self["backline"].show()
		else:
			self.txt = False
			zeil = 0
			#self.set_text("")
			self["txt_zeile"].hide()
			self["backline"].hide()

		self["pic"].resize(eSize(size_w - (framesize.value * 2), size_h - self.zeil_size - (framesize.value * 2)))
		self["pic"].move(ePoint(framesize.value, framesize.value + zeil))
		self.picload.setPara([self["pic"].instance.size().width(), self["pic"].instance.size().height(), self.sc[0], self.sc[1], False, 1, self.bgcolor])

	def manipulation_exit(self):
		if self.zoom_on == 1:

			self.clear_rotate(3)
			self.zoom_out()
		elif self.rotate_index is not None:
			self.clear_rotate(3)

###  movie ############################
########################
	def playpauseService(self):
		if self.move == 1:
			service = self.session.nav.getCurrentService()
			if service:

				servicePause = service.pause()
				if servicePause is not None:
					if self.v_pause == 0:
						self.v_pause = 1
						servicePause.pause()
						self["play_icon"].instance.setPixmapFromFile(self.pause_icon)

					else:
						self.v_pause = 0
						self["play_icon"].instance.setPixmapFromFile(self.icon)
						if self.symbols_on and self.symbol_hide > 0:
							self.symb_hideTimer.start(int(self.symbol_hide) * 1000)
						servicePause.unpause()
					self.selectionChanged()

	def lockShow(self):
		pass

	def unlockShow(self):
		pass

#######################################
#######################################
	def eExit(self, ref=None):
		#gMainDC.getInstance().setResolution(self.oldsize[0],self.oldsize[1])
		#getDesktop(0).resize(eSize(self.oldsize[0],self.oldsize[1]))
		if self.alt_osd_alpha:
			open("/proc/stb/video/alpha", "w").write(self.alt_osd_alpha)
		self.close(ref)

	def Exit(self):
		self.configparser2 = ConfigParser()
		self.configparser2.read(DATAFILE)
		if self.configparser2.has_section("last_path"):
			self.configparser2.remove_section("last_path")
		self.configparser2.add_section("last_path")
		self.configparser2.set("last_path", "path", self.merkpath)
		self.configparser2.set("last_path", "read_sub", str(vollbildsets[3]))
		self.configparser2.set("last_path", "sortierung", vollbildsets[0].lower())
		self.configparser2.set("last_path", "infoline", vollbildsets[1] or "")
		self.configparser2.set("last_path", "videoplay", vollbildsets[2] or "")
		ind = self.index - 1
		if ind < 0 or self.art == "random":
			self.index = 0
		self.configparser2.set("last_path", "index", str(ind))
		with open(DATAFILE, "w") as fp:
			self.configparser2.write(fp)
		self.moveTimer.stop()
		self.session.nav.playService(self.altservice)
		self.instance.resize(eSize(getDesktop(0).size().width(), getDesktop(0).size().height()))
		if self.zoom_on == 1 or self.rotate_index is not None:
			self.manipulation_exit()
		else:
			#if self.size_w:
			#gMainDC.getInstance().setResolution(self.oldsize[0],self.oldsize[1])
			#getDesktop(0).resize(eSize(self.oldsize[0],self.oldsize[1]))
			if self.alt_osd_alpha:
				open("/proc/stb/video/alpha", "w").write(self.alt_osd_alpha)
			if self.picload:
				del self.picload
			if self.end == 1:
				self.close(self.filelist)
			else:
				self.close(None)


class AutoMount():
	"""Manages Mounts declared in a XML-Document."""

	def __init__(self):
		self.automounts = {}
		self.restartConsole = Console()
		self.MountConsole = Console()
		self.removeConsole = Console()
		self.activeMountsCounter = 0
		# Initialize Timer
		self.callback = None
		self.timer = eTimer()
		if DPKG:
			self.timer_conn = self.timer.timeout.connect(self.mountTimeout)
		else:
			self.timer.callback.append(self.mountTimeout)

		self.getAutoMountPoints()

	def regExpMatch(self, pattern, string):
		if string is None:
			return None
		return pattern.search(string).group()

	# helper function to convert ips from a sring to a list of ints
	def convertIP(self, ip):
		strIP = ip.split('.')
		ip = []
		for x in strIP:
			ip.append(int(x))
		return ip

	def getAutoMountPoints(self, callback=None):
		# Initialize mounts to empty list
		automounts = []
		self.automounts = {}
		self.activeMountsCounter = 0
		if not exists(XML_FSTAB):
			return
		tree = cet_parse(XML_FSTAB).getroot()

		def getValue(definitions, default):
			# Initialize Output
			# How many definitions are present
			Len = len(definitions)
			return Len > 0 and definitions[Len - 1].text or default
		# Config is stored in "mountmanager" element
		# Read out NFS Mounts
		for nfs in tree.findall("nfs"):
			for mount in nfs.findall("mount"):
				data = {'isMounted': None, 'active': False, 'ip': False, 'sharename': False, 'sharedir': False, 'username': False,
										'password': False, 'mounttype': False, 'options': False, 'hdd_replacement': False}
				try:
					data['mounttype'] = 'nfs'
					data['active'] = getValue(mount.findall("active"), False)
					if data["active"] == 'True' or data["active"] == True:
						self.activeMountsCounter += 1
					data['hdd_replacement'] = getValue(mount.findall("hdd_replacement"), "False")
					data['ip'] = getValue(mount.findall("ip"), "192.168.0.0")
					data['sharedir'] = getValue(mount.findall("sharedir"), "/exports/")
					data['sharename'] = getValue(mount.findall("sharename"), "MEDIA")
					data['options'] = getValue(mount.findall("options"), "rw,nolock,tcp")
					print("NFSMOUNT", data)
					self.automounts[data['sharename']] = data
				except Exception as e:
					print("[MountManager] Error reading Mounts:", e)
		# Read out CIFS Mounts
		for nfs in tree.findall("cifs"):
			for mount in nfs.findall("mount"):
				data = {'isMounted': None, 'active': False, 'ip': False, 'sharename': False, 'sharedir': False, 'username': False,
										'password': False, 'mounttype': False, 'options': False, 'hdd_replacement': False}
				try:
					data['mounttype'] = 'cifs'
					data['active'] = getValue(mount.findall("active"), False)
					if data["active"] == 'True' or data["active"] == True:
						self.activeMountsCounter += 1
					data['hdd_replacement'] = getValue(mount.findall("hdd_replacement"), "False")
					data['ip'] = getValue(mount.findall("ip"), "192.168.0.0")
					data['sharedir'] = getValue(mount.findall("sharedir"), "/exports/")
					data['sharename'] = getValue(mount.findall("sharename"), "MEDIA")
					data['options'] = getValue(mount.findall("options"), "rw,nolock")
					data['username'] = getValue(mount.findall("username"), "guest")
					data['password'] = getValue(mount.findall("password"), "")
					print("CIFSMOUNT", data)
					self.automounts[data['sharename']] = data
				except Exception as e:
					print("[MountManager] Error reading Mounts:", e)
		try:
			with open('/etc/auto.network', 'r') as fp:
				automounts = fp.readlines()
		except Exception:
			print("[AutoMount.py] /etc/auto.network - opening failed")
		ipRegexp = '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}'
		cifsIpLinePattern = compile('://' + ipRegexp + '/')
		nfsIpLinePattern = compile(ipRegexp + ':/')
		ipPattern = compile(ipRegexp)
		for line in automounts:
			print("[AutoMount.py] Line:", line)
			split = line.strip().split('\t', 2)
			if split[0] == '*':
				continue
			if len(split) == 2 and split[0][0] == '*':
				continue
			if len(split) == 3:
				data = {'isMounted': None, 'active': False, 'ip': False, 'sharename': False, 'sharedir': False, 'username': False, 'password': False, 'mounttype': False, 'options': False}
				currshare = ""
				if split[0][0] == '#':
					data['active'] = False
					currshare = split[0][1:]
					data['sharename'] = currshare
				else:
					data['active'] = True
					self.activeMountsCounter += 1
					currshare = split[0]
					data['sharename'] = currshare
				sharedir = ""
				if '-fstype=cifs' in split[1]:
					data['mounttype'] = 'cifs'
					options = split[1][split[1].index('-fstype=cifs') + 13: split[1].index(',user=')]
					if options is not None:
						data['options'] = options
					if 'user=' in split[1]:
						username = split[1][split[1].index(',user=') + 6: split[1].index(',pass=')]
						if username is not None:
							data['username'] = username
					if 'pass=' in split[1]:
						password = split[1][split[1].index(',pass=') + 6:]
						if password is not None:
							data['password'] = password
					ip = self.regExpMatch(ipPattern, self.regExpMatch(cifsIpLinePattern, split[2]))
					if ip is not None:
						data['ip'] = ip
						sharedir = split[2][split[2].index(ip) + len(ip) + 1:]
					if sharedir is not None:
						tmpsharedir = sharedir.replace("\\ ", " ")
						if tmpsharedir[-2:] == "\$":
							tmpdir = tmpsharedir.replace("\$", "$")
							tmpsharedir = tmpdir
						data['sharedir'] = tmpsharedir
				if '-fstype=nfs' in split[1]:
					data['mounttype'] = 'nfs'
					options = split[1][split[1].index('-fstype=nfs') + 12:]
					if options is not None:
						data['options'] = options
					ip = self.regExpMatch(ipPattern, self.regExpMatch(nfsIpLinePattern, split[2]))
					if ip is not None:
						data['ip'] = ip
						sharedir = split[2][split[2].index(ip) + len(ip) + 1:]
					if sharedir is not None:
						tmpsharedir = sharedir.replace("\\ ", " ")
						if tmpsharedir[-2:] == "\$":
							tmpdir = tmpsharedir.replace("\$", "$")
							tmpsharedir = tmpdir
						data['sharedir'] = tmpsharedir
				#self.automounts[currshare] = data
				self.automounts[data['sharename']] = data
		print("[AutoMount.py] -getAutoMountPoints:self.automounts -->", self.automounts)
		if len(self.automounts) == 0:
			print("[AutoMount.py] self.automounts without mounts", self.automounts)
			if callback is not None:
				callback(True)
		else:
			for sharename, sharedata in self.automounts.items():
				self.CheckMountPoint(sharedata, callback)

	def CheckMountPoint(self, data, callback):
		print("[AutoMount.py] CheckMountPoint")
		print("[AutoMount.py] activeMounts:--->", self.activeMountsCounter)
		if not self.MountConsole:
			self.MountConsole = Console()

		self.command = None
		if self.activeMountsCounter == 0:
			print("self.automounts without active mounts", self.automounts)
			if data['active'] == 'False' or data['active'] is False:
				path = '/media/net/' + data['sharename']
				umountcmd = 'umount -fl ' + path
				print("[AutoMount.py] UMOUNT-CMD--->", umountcmd)
				self.MountConsole.ePopen(umountcmd, self.CheckMountPointFinished, [data, callback])
		else:
			if data['active'] == 'False' or data['active'] is False:
				path = '/media/net/' + data['sharename']
				self.command = 'umount -fl ' + path
			if data['active'] == 'True' or data['active'] is True:
				path = '/media/net/' + data['sharename']
				if exists(path) is False:
					createDir(path)
				tmpsharedir = data['sharedir'].replace(" ", "\\ ")
				if tmpsharedir[-1:] == "$":
					tmpdir = tmpsharedir.replace("$", "\\$")
					tmpsharedir = tmpdir
				if data['mounttype'] == 'nfs' and not ismount(path):
						tmpcmd = 'mount -t nfs -o tcp,' + data['options'] + data['ip'] + ':/' + tmpsharedir + ' ' + path
						self.command = tmpcmd
				if data['mounttype'] == 'cifs' and not ismount(path):
						tmpusername = data['username'].replace(" ", "\\ ")
						tmpcmd = 'mount -t cifs -o ' + data['options'] + ',iocharset=utf8,rsize=8192,wsize=8192,username=' + tmpusername + ',password=' + data['password'] + ' //' + data['ip'] + '/' + tmpsharedir + ' ' + path
						self.command = tmpcmd
			if self.command is not None:
				print("[AutoMount.py] U/MOUNTCMD--->", self.command)
				self.MountConsole.ePopen(self.command, self.CheckMountPointFinished, [data, callback])
			else:
				self.CheckMountPointFinished(None, None, [data, callback])

	def CheckMountPointFinished(self, result, retval, extra_args):
		print("[AutoMount.py] CheckMountPointFinished")
		print("[AutoMount.py] result", result)
		print("[AutoMount.py] retval", retval)
		(data, callback) = extra_args
		if self.MountConsole:
			print("LEN", len(self.MountConsole.appContainers))
		path = '/media/net/' + data['sharename']
		print("PATH im CheckMountPointFinished", path)
		if exists(path):
			if ismount(path):
				if self.automounts and data['sharename'] in self.automounts:
					self.automounts[data['sharename']]['isMounted'] = True
					desc = data['sharename']
					harddiskmanager.addMountedPartition(path, desc)
			else:
				if self.automounts and data['sharename'] in self.automounts:
					self.automounts[data['sharename']]['isMounted'] = False
				if exists(path):
					if not ismount(path):
						removeDir(path)
						harddiskmanager.removeMountedPartition(path)

		if self.MountConsole:
			if len(self.MountConsole.appContainers) == 0:
				if callback is not None:
					self.callback = callback
					self.timer.startLongTimer(10)

	def makeHDDlink(self, path):
		hdd_dir = '/media/hdd'
		print("[AutoMount.py] symlink %s %s" % (path, hdd_dir))
		if islink(hdd_dir):
			if readlink(hdd_dir) != path:
				remove(hdd_dir)
				symlink(path, hdd_dir)
		elif ismount(hdd_dir) is False:
			if isdir(hdd_dir):
				self.rm_rf(hdd_dir)
		try:
			symlink(path, hdd_dir)
		except OSError:
			print("[AutoMount.py] add symlink fails!")
		if exists(hdd_dir + '/movie') is False:
			createDir(hdd_dir + '/movie')

	def rm_rf(self, d):  # only for removing the ipkg stuff from /media/hdd subdirs
		for path in (join(d, f) for f in listdir(d)):
			if isdir(path):
				self.rm_rf(path)
			else:
				unlink(path)
		removeDir(d)

	def mountTimeout(self):
		self.timer.stop()
		if self.MountConsole:
			if len(self.MountConsole.appContainers) == 0:
				print("self.automounts after mounting", self.automounts)
				if self.callback is not None:
					self.callback(True)

	def getMountsList(self):
		return self.automounts

	def getMountsAttribute(self, mountpoint, attribute):
		if mountpoint in self.automounts:
			if attribute in self.automounts[mountpoint]:
				return self.automounts[mountpoint][attribute]
		return None

	def setMountsAttribute(self, mountpoint, attribute, value):
		print("setting for mountpoint", mountpoint, "attribute", attribute, " to value", value)
		if mountpoint in self.automounts:
			self.automounts[mountpoint][attribute] = value

	def writeMountsConfig(self):
		pass

	def stopMountConsole(self):
		if self.MountConsole is not None:
			self.MountConsole = None

	def removeMount(self, mountpoint, callback=None):
		print("[AutoMount.py] removing mount: ", mountpoint)
		self.newautomounts = {}
		for sharename, sharedata in self.automounts.items():
			if sharename is not mountpoint.strip():
				self.newautomounts[sharename] = sharedata
		self.automounts.clear()
		self.automounts = self.newautomounts
		if not self.removeConsole:
			self.removeConsole = Console()
		path = '/media/net/' + mountpoint
		umountcmd = 'umount -fl ' + path
		print("[AutoMount.py] UMOUNT-CMD--->", umountcmd)
		self.removeConsole.ePopen(umountcmd, self.removeMountPointFinished, [path, callback])

	def removeMountPointFinished(self, result, retval, extra_args):
		print("[AutoMount.py] removeMountPointFinished")
		print("[AutoMount.py] result", result)
		print("[AutoMount.py] retval", retval)
		(path, callback) = extra_args
		if exists(path):
			if not ismount(path):
				removeDir(path)
				harddiskmanager.removeMountedPartition(path)

		if self.removeConsole:
			if len(self.removeConsole.appContainers) == 0:
				if callback is not None:
					self.callback = callback
					self.timer.startLongTimer(10)


class picload_thread(Thread):
	#Dateiliste = {}
	curPic = []
	#DateilisteLock = Lock()
	curPic = Lock()

	def __init__(self, suchstring, pfad, endung, sum):
		Thread.__init__(self)
		self.suchstring = suchstring
		self.eEndung = endung
		self.startDir = pfad
		self.suchart = sum
		self.killed = False

	def run(self):
		Suchstring = self.suchstring
		Suchstring = "*" + Suchstring.replace(' ', '*') + "*".lower()
		ordner = []
		files = []
		liste = []
		ordner1 = []
		directories = [self.startDir]
		#f=open("/tmp/ordner","a")
		while len(directories) > 0:
			if self.killed:
				break
			directory = directories.pop()
			for name in listdir(directory):
				fullpath = join(directory, name)
				if isfile(fullpath):
					if self.suchart == "Files" or self.suchart == "beides":
						if fnmatch(name.lower(), Suchstring):
							if len(self.eEndung) and splitext(fullpath)[1].replace(".", "") in self.eEndung:
								files.append(("f", basename(fullpath), fullpath))
							else:
								files.append(("f", basename(fullpath), fullpath))
				elif isdir(fullpath):
					directories.append(fullpath)  # It's a directory, store it.
					if self.suchart == "Ordner" or self.suchart == "beides":
						if fnmatch((fullpath.lower()), Suchstring):
							dira = (split(fullpath)[-1])
							#f.write(str(fullpath)+"\n"+str(ordner1)+"\n\n")
							if str(fullpath) not in ordner1:
								ordner.append(("d", dira, fullpath))
							ordner1.append(str(fullpath))
				liste = []
				if len(files):
					files.sort()
				if len(ordner):
					ordner.sort()
				#f.write(str(ordner1)+"\n")
				liste.extend(ordner)
				liste.extend(files)
#				suche_thread.FindlisteLock.acquire()
#				suche_thread.Findliste = liste
#				suche_thread.FindlisteLock.release()
			if self.killed:
				break
		self.killed = True

def read_marks(file0=None, add_file=None, del_file=None):
	if file0:
		filelist = []
		if not exists("/tmp/pcfs_mark"):
			open("/tmp/pcfs_mark", "w").close()
		if del_file:
			with open(file0, "r") as f:
				lines = f.readlines()
			with open(file0, 'w') as f:
				for x in lines:
					if del_file != x.strip():
						f.write(x)
						filelist.append((x.strip(), basename(x.strip()), "all", True, "file", 1, 0))
		else:
			if isfile(file0):
				with open(file0, "r+") as marks:
					for line in marks.readlines():
						if len(line.strip()):
							filelist.append((line.strip(), basename(line.strip()), "all", True, "file", 1, 0))
					if add_file and add_file not in filelist:
						marks.write(str(add_file) + "\n")
						filelist.append((add_file, basename(add_file), "all", True, "file", 1, 0))
		return filelist if file0 else []


class pcFSLCDScreen(Screen):
	skin = open("/usr/lib/enigma2/python/Plugins/Extensions/PictureCenterFS/skin/display.xml").read()

	def __init__(self, session, parent):
		Screen.__init__(self, session, parent=parent)
		self.skinName = "pcFSLCDScreen"
		self["title"] = Label("PictureCenterFS")
		self["plays"] = Label("")
		self["index"] = Label("")
		self["anzahl"] = Label("")
		self["name1"] = Label("")
		self.onShow.append(self.addWatcher)
		self.onHide.append(self.removeWatcher)

	def addWatcher(self):
		self.parent.onChangedEntry.append(self.selectionChanged)
		self.parent.selectionChanged()

	def removeWatcher(self):
		self.parent.onChangedEntry.remove(self.selectionChanged)

	def selectionChanged(self, play, gesamt, nummer, name1):
		self["plays"].setText(play)
		self["index"].setText(nummer)
		self["anzahl"].setText(gesamt)
		self["name1"].setText(name1)
#------------------------------------------------------------------------------------------

def main(session, **kwargs):
#	try:
	session.open(PictureCenterFS7)
#	except Exception:
#		from traceback import print_exc
#		print_exc()

def menu(menuid, **kwargs):
	if menuid == "mainmenu":
		return [("PictureCenterFS", main, "pcfs", 66)]
	return []

def screensaver(session, **kwargs):
	if saver_on and saver_path.value:
		session.open(Pic_Full_View3, saver_path.value, "saver")

def Plugins(**kwargs):
	plist = []
	plist.append(PluginDescriptor(name="PictureCenterFS", description=_("see your picture comfortable and more"), where=[PluginDescriptor.WHERE_PLUGINMENU], icon="PictureCenterFS.png", fnc=main))
	configparser1 = ConfigParser()
	configparser1.read(DATAFILE)
	if configparser1.has_section("settings") and configparser1.has_option("settings", "saver_on"):
		if configparser1.get("settings", "saver_on") != "False":
			plist.append(PluginDescriptor(name="Screensaver PCFS", description=_("yor picture as screensaver"), where=[PluginDescriptor.WHERE_PLUGINMENU], icon="PictureCenterFS.png", fnc=screensaver))
	if int(config.plugins.PictureCenterFS.hauptmenu.value) == 2:
		plist.append(PluginDescriptor(name="PictureCenterFS", icon="PictureCenterFS.png", where=PluginDescriptor.WHERE_MENU, fnc=menu))
	elif int(config.plugins.PictureCenterFS.hauptmenu.value) == 3:
		plist.append(PluginDescriptor(name="PictureCenterFS", description=_("see yor picture comfortable and more"), icon="PictureCenterFS.png", where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main))
	elif int(config.plugins.PictureCenterFS.hauptmenu.value) == 4:
		plist.append(PluginDescriptor(name="PictureCenterFS", description=_("see yor picture comfortable and more"), icon="PictureCenterFS.png", where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main))
		plist.append(PluginDescriptor(name="PictureCenterFS", icon="PictureCenterFS.png", where=PluginDescriptor.WHERE_MENU, fnc=menu))
	return plist
