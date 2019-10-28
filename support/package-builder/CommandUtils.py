# pylint: disable=invalid-name,missing-docstring
import subprocess
import os

class CommandUtils:

    @staticmethod
    def findFile(filename, sourcePath):
        process = subprocess.Popen(["find", "-L", sourcePath, "-name", filename,
                                    "-not", "-type", "d"], stdout=subprocess.PIPE)
        # We don't check the return val here because find could return 1 but still be
        # able to find
        # the result. We shouldn't blindly return None without even checking the result.
        # The reason we want to suppress this is because for built RPMs, we first copy it to
        # the location with a random name and move it to the real name. find will complain our
        # action and return 1.
        # find's flag ignore_readdir_race can suppress this but it isn't working.
        # https://bugs.centos.org/view.php?id=13685

        #if returnVal != 0:
        #    return None
        result = process.communicate()[0]
        if result is None:
            return None
        return result.decode().split()

    @staticmethod
    def runCommandInShell(cmd, logfile=None, logfn=None, showOutput=False):
        # print(">> runCommandInShell: %s" % cmd)
        # print(">> logfile: %s, logfn: %s, showOutput: %s" % (logfile, logfn, showOutput))

        retval = 0
        process = subprocess.Popen("%s" %cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1 if showOutput else -1)
        
        if logfile is None and logfn is None:
            logfile = os.devnull
        elif logfile and logfn:
            logfile = None

        f = None
        if logfile:
            f = open(logfile, "w")

        while process.poll() is None:
            output = process.stdout.readline().decode()
            if not output: break
            else:
                if showOutput:
                    print(" | %s" % output.strip())
                if f:
                    f.write(output.strip())

        if f:
            f.close()

        if logfn:
            logfn(process.communicate()[0].decode())

        retval = process.poll()
        
        return retval

