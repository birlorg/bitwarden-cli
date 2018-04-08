import os
import subprocess
import sys
import tempfile
"""
Utilities for slab mode.
"""
SLABSCRIPT = """
	tell app "System Events"
		Activate

		set SlabList to {}
		set Answer to (choose from list SlabList with title "sudolikeaboss")

		if Answer is false then
			error number -128 (* user cancelled *)
		else
			set Answer to Answer's item 1 (* extract choice from list *)
		end if
	end tell
	tell app "iTerm2"
		Activate
		return Answer
	end tell
"""


def appleScriptChooser(choices):
    """give user a choice of items. return selected item"""
    fd = tempfile.NamedTemporaryFile(delete=False)
    #choices = ['a','b','c']
    s = '{ "' + '","'.join(choices) + '" }'
    fd.write(SLABSCRIPT.format(s).encode('utf-8'))
    name = fd.name
    #print("fname:%s" % name, file=sys.stderr)
    fd.close()

    try:
        out = subprocess.check_output(
            ['/usr/bin/osascript', name], universal_newlines=True)
        # str(out).strip().replace('\n','')
        out = out.rstrip()
        #print("out:%s" % out, file=sys.stderr)
    except:
        sys.exit()

    os.unlink(name)
    return out


def chooseGUIChooser(choices):
    """use choose gui for choices
    https://github.com/sdegutis/choose
    """
    try:
        out = subprocess.run(['/usr/local/bin/choose'], stdout=subprocess.PIPE,
                             input='\n'.join(choices), universal_newlines=True)
    except:
        sys.exit()
    return out.stdout.strip()


def choice(choices):
    """give user a choice of items, return selected item
    if choose-gui is installed, use that, otherwise fall back to applescript
    """
    if os.path.exists('/usr/local/bin/choose'):
        return chooseGUIChooser(choices)
    else:
        return appleScriptChooser(choices)
