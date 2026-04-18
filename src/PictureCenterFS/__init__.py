from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from gettext import bindtextdomain, dgettext, gettext


def localeInit():
	bindtextdomain("PictureCenterFS", resolveFilename(SCOPE_PLUGINS, "Extensions/PictureCenterFS/locale"))


def _(txt):
	t = dgettext("PictureCenterFS", txt)
	if t == txt:
		t = gettext(txt)
	return t


localeInit()
language.addCallback(localeInit)

__version__ = "1.0"
