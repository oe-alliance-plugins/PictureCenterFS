# PYTHON IMPORTS
from os import listdir, remove
from os.path import exists, basename, dirname, split, getsize

# ENIGMA IMPORTS
from enigma import getDesktop, ePicLoad
from Components.ActionMap import NumberActionMap
from Components.AVSwitch import AVSwitch
from Components.Pixmap import Pixmap
from Components.Sources.List import List
from Screens.Console import Console
from Screens.LocationBox import LocationBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Tools.Directories import copyfile
from Tools.LoadPixmap import LoadPixmap

# PLUGIN IMPORTS
from . import _ # for localized messages

try:
	from enigma import eMediaDatabase
	DPKG = True
except:
	DPKG = False
plugin = "PictureCenterFS"
skin_zusatz = "fHD" if getDesktop(0).size().width() > 1850 else "HD"


class PictureCenterFS7_Filemenu(Screen):
	skindatei = "/usr/lib/enigma2/python/Plugins/Extensions/PictureCenterFS/skin/%s/pcFS_menulist.xml" % skin_zusatz
	with open(skindatei) as tmpskin:
		skin = tmpskin.read()

	def __init__(self, session, file1, file2=""):
		self.file1 = file1
		self.file2 = file2
		self.edit = 0
		Screen.__init__(self, session)
		self.skinName = "PictureCenterFS7_Filemenu"
		self.session = session
		self.settigspath = ""
		mlist = []
		template = "default"
		pics = ["nix", None, None, None]
		nums = ["", "1 ", "2 ", "3 "]
		if skin_zusatz != "SD/" and exists(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/buttons/key_" + str(len(pics)) + ".png")):
			template = "with_numpic"
			for i in range(1, len(pics)):
				pics[i] = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/buttons/key_" + str(i) + ".png"))
				nums[i] = ""
		mlist.append((nums[1] + _('Copy selected/displayed file'), 'copy', pics[1]))
		if len(self.file2) > 0:
			mlist.append((nums[2] + _('save changes in the original image'), 'save_rotat', pics[2]))
			self.setTitle(plugin + ": " + _("Options for edited image"))
		else:
			mlist.append((nums[2] + _('Move selected/displayed file'), 'move', pics[2]))
			mlist.append((nums[3] + _('Delete selected/displayed file'), 'delete', pics[3]))
		self.m_liste = mlist
		self["m_liste"] = List(mlist)  # File_List(list=list, selection = 0)
		self["m_liste"].style = template
		if skin_zusatz != "SD/":
			self["thumb"] = Pixmap()
			self.picload = ePicLoad()
			if DPKG:
				self.picload_conn = self.picload.PictureData.connect(self.showPic)
			else:
				self.picload.PictureData.get().append(self.showPic)
		self.setTitle(plugin + ": " + _("Options for selected/displayed file"))
		self["actions"] = NumberActionMap(["OkCancelActions", "ColorActions", "InputActions", "DirectionActions"],
		{
				"ok": self.run,
				"cancel": self.exit,
				"1": self.keyNumberGlobal,
				"2": self.keyNumberGlobal,
				"3": self.keyNumberGlobal,
				"4": self.keyNumberGlobal,
				#"5": self.keyNumberGlobal,   "cancel": self.close,
				#"6": self.keyNumberGlobal,
				#"7": self.keyNumberGlobal,
				#"8": self.keyNumberGlobal,
				#"9": self.keyNumberGlobal,
				#"0": self.keyNumberGlobal,
				#"green": self.setMainMenu,
				#"yellow": self.restore,
				#"blue": self.internet_import
		}, -1)
		if skin_zusatz != "SD/":
			self.onLayoutFinish.append(self.show_pic)

	def show_pic(self):
		if skin_zusatz != "SD/":
			sc = AVSwitch().getFramebufferScale()
			self.picload.setPara((self["thumb"].instance.size().width(), self["thumb"].instance.size().height(), sc[0], sc[1], False, 1, '#000000'))  # cache.value
			if self.file2 and len(self.file2):
				pic = self.file2
			else:
				pic = self.file1
			self.picload.startDecode(pic)

	def showPic(self, picInfo=""):
		if skin_zusatz != "SD/":
			ptr = self.picload.getData()
			if ptr != None:
				self["thumb"].instance.setPixmap(ptr)

	def keyNumberGlobal(self, number):
		self["m_liste"].setIndex(number - 1)
		self.run()

	def run(self):
		ind = self["m_liste"].getIndex()
		returnValue = self.m_liste[ind][1]  # self["m_liste"].l.getCurrentSelection()[1]
		if returnValue == 'delete':
			self.del_file()
		elif returnValue == 'copy':
			self.copy()
		elif returnValue == 'move':
			self.move()
		elif returnValue == 'save_rotat':
			self.save_rotat()

#bearbeiten ############################################
	def save_rotat(self):
		text1 = _("selceted File is:") + "\n" + self.file1 + "\n\n"
		self.session.openWithCallback(self.save_rotat2, MessageBox, _(text1 + _("Do you really overwrite this file?")), MessageBox.TYPE_YESNO)

	def save_rotat2(self, args=None):
		if args:
			try:
				copyfile(source, target)
				self.session.openWithCallback(self.exit, MessageBox, (self.file1 + "\n" + _("file successfully saved")), MessageBox.TYPE_INFO)
			except OSError as e:
				txt = 'error: \n%s' % e
				self.session.openWithCallback(self.exit, MessageBox, txt, MessageBox.TYPE_INFO)

	def copy(self):
		if len(self.file2) <= 0:
			self.file2 = self.file1
		self.endung = "." + basename(self.file1).split(".")[-1]
		text1 = basename(self.file1).replace("." + basename(self.file1).split(".")[-1], "")
		self.session.openWithCallback(self.copy2, VirtualKeyBoard, title=_("Edit file-save-name:"), text=text1)

	def copy2(self, filename):
		if filename:
			self.oldpath = dirname(self.file1) + "/"
			self.filename = filename + self.endung
		else:
			self.filename = basename(self.file1)
		self.session.openWithCallback(self.callCopy, BackupLocationBox, _("Please select target path..."), split(dirname(self.file1))[0] + "/", getsize(self.file1))  # "/tmp/")

	def callCopy(self, path):
		if path is not None:
			f = open("/tmp/files.txt", "a")
			f.write(self.file1 + "\n" + self.file2 + "\n")
			self.copy_source = self.file2
			self.copy_target = path + self.filename
			if exists(path + self.filename):
				self.session.openWithCallback(self.callCopy2, MessageBox, _("file exist on this path, overwrite?"), MessageBox.TYPE_YESNO)
			else:
				self.callCopy2(1)

	def callCopy2(self, answer):
		if answer:
			try:
				copyfile(self.copy_source, self.copy_target)
				self.session.openWithCallback(self.exit, MessageBox, (self.file1 + "\n" + _("file successfully copied at") + "\n" + self.filename), MessageBox.TYPE_INFO)
			except OSError as e:
				txt = 'error: \n%s' % e
				self.session.openWithCallback(self.exit, MessageBox, txt, MessageBox.TYPE_INFO)

	def move(self):
		self.session.openWithCallback(self.callmove, BackupLocationBox, _("Please select target path..."), "", "/tmp/")

	def del_file(self):
		text1 = _("selceted File is:") + "\n" + self.file1 + "\n\n"
		self.session.openWithCallback(self.del_file_ok, MessageBox, _(text1 + _("Do you really want to delete this file?")), MessageBox.TYPE_YESNO)

	def del_file_ok(self, answer):
		if answer:
			try:
				remove(self.file1)
				self.edit = 1
				self.session.openWithCallback(self.exit, MessageBox, (self.file1 + "\n" + _("file is deleted")), MessageBox.TYPE_INFO)
			except OSError as e:
				txt = 'error: \n%s' % e
				self.session.openWithCallback(self.exit, MessageBox, txt, MessageBox.TYPE_INFO)

	def callmove(self, path):
		if path is not None:
			source = self.file1
			target = path + basename(self.file1)
			try:
				copyfile(source, target)
				self.del_file_ok("ok")
				self.edit = 1
				self.session.openWithCallback(self.exit, MessageBox, (self.file1 + "\n" + _("file successfully moved")), MessageBox.TYPE_INFO)
			except OSError as e:
				txt = 'error: \n%s' % e
				self.session.openWithCallback(self.exit, MessageBox, txt, MessageBox.TYPE_INFO)

	def exit(self, args=None):
		if args:
			self.close(1)
		else:
			self.close()


class save_mark:
	def __init__(self, session, name):
		copyfile("/tmp/pcfs_mark", "/etc/ConfFS/" + name)


class backup:
	def __init__(self, session):
		self.session = session
		self.settigspath = None
		self.num = None
		self.file1 = None

	def start(self, num=None):
		if num:
			self.num = num
		if self.num == 5:
			self.restore()
		elif self.num == 3:
			self.backup()

	def backup(self):
		self.session.openWithCallback(self.callBackup, BackupLocationBox, _("Please select the backup path..."), "")

	def callBackup(self, path):
		if self.num and path is not None:
			if pathExists(path):
				if self.num == 3:
					self.settigspath = path + "ConfFS_backup.tar.gz"
				if fileExists(self.settigspath):
					self.session.openWithCallback(self.callOverwriteBackup, MessageBox, _("Overwrite existing Backup?"), type=MessageBox.TYPE_YESNO,)
				else:
					self.callOverwriteBackup(True)
			else:
				self.err(_("Backup failed"))
				self.session.open(MessageBox, _("Directory %s nonexistent.") % (path), type=MessageBox.TYPE_ERROR, timeout=5)
		else:
			self.err(_("Backup failed"))

	def callOverwriteBackup(self, res):
		if res:
			self.cBackup()

	def cBackup(self, num=None):
		if num:
			self.num = num
		if self.num and self.settigspath:
			mpath = "/etc/ConfFS/"
			if pathExists(mpath) is True:
				files = []
				for file in listdir(mpath):
					files.append("/etc/ConfFS/" + file)
				tarFiles = ""
				for arg in files:
					tarFiles += "%s " % arg
			try:
				com = "tar czvf %s %s" % (self.settigspath, tarFiles)
				self.session.open(Console, _("Backup Settings..."), [com])
			except Exception:
				self.err(_("backup failed"))

	def restore(self):
		if self.num == 5:
			self.tarfile = "ConfFS_backup.tar.gz"
			self.session.openWithCallback(self.callRestore, BackupLocationBox, _("Please select the restore path..."), "")

	def callRestore(self, path1):
		if self.tarfile and path1:
			self.settigspath = path1 + self.tarfile
			if fileExists(self.settigspath):
				self.session.openWithCallback(self.callOverwriteSettings, MessageBox, _("Overwrite existing Files?"), type=MessageBox.TYPE_YESNO,)

			else:
				self.session.open(MessageBox, _("File %s nonexistent.") % (path1), type=MessageBox.TYPE_ERROR, timeout=5)
		else:
			self.err("restore failed")

	def callOverwriteSettings(self, res=None):
		if res:
			try:
				com = "cd /; tar xzvf %s" % (self.settigspath)
				self.session.open(Console, _("Restore Settings..."), [com])
			except Exception:
				self.err(_("restore failed"))

	def err(self, res):
		self.session.open(MessageBox,res,type = MessageBox.TYPE_ERROR,timeout = 5)


class BackupLocationBox(LocationBox):
	def __init__(self, session, text, dir=None, minFree=None):
		inhibitDirs = ["/bin", "/boot", "/dev", "/lib", "/proc", "/sbin", "/sys", "/usr", "/var"]
		LocationBox.__init__(self, session, text=text, currDir=dir, inhibitDirs=inhibitDirs, minFree=minFree)
		self.skinName = "LocationBox"
