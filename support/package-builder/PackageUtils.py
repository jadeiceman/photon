import os
import shutil
import re
import random
import string
from CommandUtils import CommandUtils
from Logger import Logger
from constants import constants
import PullSources
from SpecData import SPECS
from distutils.version import LooseVersion

class PackageUtils(object):

    def __init__(self, logName=None, logPath=None):
        if logName is None:
            logName = "PackageUtils"
        if logPath is None:
            logPath = constants.logPath
        self.logName = logName
        self.logPath = logPath
        self.logger = Logger.getLogger(logName, logPath, constants.logLevel)
        self.rpmBinary = "rpm"
        self.installRPMPackageOptions = "-Uvh"
        self.nodepsRPMPackageOptions = "--nodeps"

        self.rpmbuildBinary = "rpmbuild"
        self.rpmbuildBuildallOption = "-ba --clean"
        self.rpmbuildNocheckOption = "--nocheck"
        self.rpmbuildCheckOption = "-bi --clean"
        self.queryRpmPackageOptions = "-qa"
        self.forceRpmPackageOptions = "--force"
        self.replaceRpmPackageOptions = "--replacepkgs"
        self.adjustGCCSpecScript = "adjust-gcc-specs.sh"
        self.rpmFilesToInstallInAOneShot = ""
        self.packagesToInstallInAOneShot = ""
        self.noDepsRPMFilesToInstallInAOneShot = ""
        self.noDepsPackagesToInstallInAOneShot = ""
        self.logfnvalue = None

    def prepRPMforInstall(self, package, version, noDeps=False, destLogPath=None, arch=None):
        if not arch:
            arch=constants.currentArch
        rpmfile = self.findRPMFile(package, version, arch)
        if rpmfile is None:
            self.logger.error("No rpm file found for package: " + package)
            raise Exception("Missing rpm file")

        rpmName = os.path.basename(rpmfile)
        #TODO: path from constants
        if "PUBLISHRPMS" in rpmfile:
            rpmDestFile = "/publishrpms/"
        elif "PUBLISHXRPMS" in rpmfile:
            rpmDestFile = "/publishxrpms/"
        elif constants.inputRPMSPath and constants.inputRPMSPath in rpmfile:
            rpmDestFile = "/inputrpms/"
        else:
            rpmDestFile = constants.topDirPath + "/RPMS/"

        if "noarch" in rpmfile:
            rpmDestFile += "noarch/"
        else:
            rpmDestFile += arch+"/"
        rpmDestFile += rpmName

        if noDeps:
            self.noDepsRPMFilesToInstallInAOneShot += " " + rpmDestFile
            self.noDepsPackagesToInstallInAOneShot += " " + package
        else:
            self.rpmFilesToInstallInAOneShot += " " + rpmDestFile
            self.packagesToInstallInAOneShot += " " + package

    def installRPMSInOneShot(self, sandbox, arch):
        rpmInstallcmd = self.rpmBinary + " " + self.installRPMPackageOptions
        if constants.crossCompiling and arch == constants.targetArch:
            rpmInstallcmd += " --ignorearch --noscripts --root /target-" + constants.targetArch

        # TODO: Container sandbox might need  + self.forceRpmPackageOptions
        if self.noDepsRPMFilesToInstallInAOneShot != "":
            self.logger.debug("Installing nodeps rpms: " +
                             self.noDepsPackagesToInstallInAOneShot)
            cmd = (rpmInstallcmd+" "+self.nodepsRPMPackageOptions + " " +
                   self.noDepsRPMFilesToInstallInAOneShot)
            returnVal = sandbox.run(cmd, logfn=self.logger.debug)
            if returnVal != 0:
                self.logger.debug("Command Executed:" + cmd)
                self.logger.error("Unable to install rpms. Error {}".format(returnVal))
                raise Exception("RPM installation failed")
        if self.rpmFilesToInstallInAOneShot != "":
            self.logger.debug("Installing rpms: " + self.packagesToInstallInAOneShot)
            cmd = rpmInstallcmd+" "+self.rpmFilesToInstallInAOneShot
            returnVal = sandbox.run(cmd, logfn=self.logger.debug)
            if returnVal != 0:
                self.logger.debug("Command Executed:" + cmd)
                self.logger.error("Unable to install rpms")
                raise Exception("RPM installation failed")

    def buildRPMSForGivenPackage(self, sandbox, package, version, destLogPath):
        self.logger.info("Building package : " + package)

        listSourcesFiles = SPECS.getData().getSources(package, version)
        listPatchFiles = SPECS.getData().getPatches(package, version)
        specFile = SPECS.getData().getSpecFile(package, version)
        specName = SPECS.getData().getSpecName(package) + ".spec"
        sourcePath = constants.topDirPath + "/SOURCES/"
        specPath = constants.topDirPath + "/SPECS/"
        if (constants.rpmCheck and
                package in constants.testForceRPMS and
                SPECS.getData().isCheckAvailable(package, version)):
            logFilePath = destLogPath + "/" + package + "-test.log"
        else:
            logFilePath = destLogPath + "/" + package + ".log"
        sandbox.put(specFile, specPath + specName)

        sources_urls, macros = self._getAdditionalBuildOptions(package)
        self.logger.debug("Extra macros for " + package + ": " + str(macros))
        self.logger.debug("Extra source URLs for " + package + ": " + str(sources_urls))
        constants.setExtraSourcesURLs(package, sources_urls)

        self._copySources(sandbox, listSourcesFiles, package, version, sourcePath)
        self._copySources(sandbox, listPatchFiles, package, version, sourcePath)

        #Adding rpm macros
        listRPMMacros = constants.userDefinedMacros
        for macroName, value in listRPMMacros.items():
            macros.append(macroName + " " + value)

        listRPMFiles = []
        listSRPMFiles = []
        try:
            listRPMFiles, listSRPMFiles = self._buildRPM(sandbox, specPath + specName,
                                                         logFilePath, package, version, macros)
            logmsg = package + " build done - RPMs : [ "
            for f in listRPMFiles:
                logmsg += (os.path.basename(f) + " ")
            logmsg += "]\n"
            self.logger.info(logmsg)
        except Exception as e:
            self.logger.error("Failed while building rpm:" + package)
            raise e
        finally:
            if (constants.rpmCheck and
                    package in constants.testForceRPMS and
                    SPECS.getData().isCheckAvailable(package, version)):
                cmd = ("sed -i '/^Executing(%check):/,/^Processing files:/{//!b};d' " + logFilePath)
                CommandUtils().runCommandInShell(cmd, logfn=self.logger.debug)
            if constants.crossCompiling:
                for f in listRPMFiles:
                    workingDir = os.getcwd()
                    cmd = "%s/../../tools/scripts/check-rpm-arch.sh %s" % (workingDir, 
                            constants.rpmPath + "/" + constants.targetArch + "/" + os.path.basename(f))
                    retVal = CommandUtils().runCommandInShell(cmd, logfn=self.logger.debug, showOutput=True)
                    if retVal != 0:
                        raise NameError("%s failed %s architecture check" % (f, constants.targetArch))
                    else:
                        self.logger.debug("RPM passed architecture check")
        self.logger.debug("RPM build is successful")

    def findRPMFile(self, package,version="*",arch=None, throw=False):
        if not arch:
            arch=constants.currentArch

        cmdUtils = CommandUtils()
        if version == "*":
                version = SPECS.getData(arch).getHighestVersion(package)
        release = SPECS.getData(arch).getRelease(package, version)
        buildarch=SPECS.getData(arch).getBuildArch(package, version)
        filename= package + "-" + version + "-" + release + "." + buildarch+".rpm"

        fullpath = constants.rpmPath + "/" + buildarch + "/" + filename
        if os.path.isfile(fullpath):
            return fullpath

        if constants.inputRPMSPath is not None:
            fullpath = constants.inputRPMSPath + "/" + buildarch + "/" + filename
        if os.path.isfile(fullpath):
            return fullpath

        if throw:
            raise Exception("RPM %s not found" % (filename))
        return None

    def findInstalledRPMPackages(self, sandbox, arch):
        rpms = None
        def setOutValue(data):
            nonlocal rpms
            rpms = data
        cmd = self.rpmBinary + " " + self.queryRpmPackageOptions
        if constants.crossCompiling and arch == constants.targetArch:
            cmd += " --root /target-" + constants.targetArch
        sandbox.run(cmd, logfn=setOutValue)
        return rpms.split()

    def adjustGCCSpecs(self, sandbox, package, version):
        # TODO: need to harden cross compiller also
        opt = " " + SPECS.getData().getSecurityHardeningOption(package, version)
        sandbox.put(self.adjustGCCSpecScript, "/tmp")
        cmd = "/tmp/" + self.adjustGCCSpecScript + opt
        returnVal = sandbox.run(cmd, logfn=self.logger.debug)
        if returnVal == 0:
            return

        # in debugging ...
        sandbox.run("ls -la /tmp/" + self.adjustGCCSpecScript,
                    logfn=self.logger.debug)
        sandbox.run("lsof /tmp/" + self.adjustGCCSpecScript,
                    logfn=self.logger.debug)
        sandbox.run("ps ax", logfn=self.logger.debug)

        self.logger.error("Failed while adjusting gcc specs")
        raise Exception("Failed while adjusting gcc specs")

    def _verifyShaAndGetSourcePath(self, source, package, version):
        cmdUtils = CommandUtils()
        # Fetch/verify sources if sha1 not None.
        sha1 = SPECS.getData().getSHA1(package, version, source)
        if sha1 is not None:
            PullSources.get(package, source, sha1, constants.sourcePath,
                            constants.getPullSourcesURLs(package), self.logger)

        sourcePath = cmdUtils.findFile(source, constants.sourcePath)
        if not sourcePath:
            sourcePath = cmdUtils.findFile(source, os.path.dirname(SPECS.getData().getSpecFile(package, version)))
            if not sourcePath:
                if sha1 is None:
                    self.logger.error("No sha1 found or missing source for " + source)
                    raise Exception("No sha1 found or missing source for " + source)
                else:
                    self.logger.error("Missing source: " + source +
                                      ". Cannot find sources for package: " + package)
                    raise Exception("Missing source")
        else:
            if sha1 is None:
                self.logger.error("No sha1 found for "+source)
                raise Exception("No sha1 found")
        if len(sourcePath) > 1:
            self.logger.error("Multiple sources found for source:" + source + "\n" +
                              ",".join(sourcePath) +"\nUnable to determine one.")
            raise Exception("Multiple sources found")
        return sourcePath

    def _copySources(self, sandbox, listSourceFiles, package, version, destDir):
        # Fetch and verify sha1 if missing
        for source in listSourceFiles:
            sourcePath = self._verifyShaAndGetSourcePath(source, package, version)
            self.logger.debug("Copying... Source path :" + source +
                             " Source filename: " + sourcePath[0])
            sandbox.put(sourcePath[0], destDir)

    def _getAdditionalBuildOptions(self, package):
        pullsources_urls = []
        macros = []
        if package in constants.buildOptions.keys():
            pkg = constants.buildOptions[package]
            pullsources_urls.extend(pkg["pullsources"])
            macros.extend(pkg["macros"])
        return pullsources_urls, macros


    def _buildRPM(self, sandbox, specFile, logFile, package, version, macros):
        self.logger.debug("RPM Macros: %s", macros)
        rpmBuildcmd = self.rpmbuildBinary + " " + self.rpmbuildBuildallOption
        
        if constants.logLevel == "debug":
            rpmBuildcmd += ' -vv'
            self.logger.debug("Log file path: %s", logFile)

        if constants.rpmCheck and package in constants.testForceRPMS:
            self.logger.debug("#" * (68 + 2 * len(package)))
            if (not SPECS.getData().isCheckAvailable(package, version)) or \
                    (package in constants.listMakeCheckPkgToSkip):
                self.logger.info("####### " + package +
                                 " MakeCheck is not available. Skipping MakeCheck TEST for " +
                                 package + " #######")
                rpmBuildcmd = self.rpmbuildBinary + " --clean"
            else:
                self.logger.info("####### " + package +
                                 " MakeCheck is available. Running MakeCheck TEST for " +
                                 package + " #######")
                rpmBuildcmd = self.rpmbuildBinary + " " + self.rpmbuildCheckOption
            self.logger.debug("#" * (68 + 2 * len(package)))
        else:
            rpmBuildcmd += " " + self.rpmbuildNocheckOption

        for macro in macros:
            rpmBuildcmd += ' --define \"%s\"' % macro

        if constants.crossCompiling:
            buildTuple = '%s-unknown-linux-gnu' % constants.buildArch
            targetMacroPath = '%s/macros/macros.%s' % (constants.topDirPath, constants.targetArch)
            localTargetMacroPath = sandbox.getID() + targetMacroPath
            macroPath = '/etc/rpm/macros.%s' % constants.targetArch

            rpmBuildcmd += ' --define \"_build %s\"' % buildTuple
            rpmBuildcmd += ' --define \"_host %s\"' % constants.targetArchTuple
            rpmBuildcmd += ' --define \"cross_compile 1\"'
            
            self.logger.debug("Searching for macro file: %s" % localTargetMacroPath)
            if os.path.isfile(localTargetMacroPath):
                self.logger.debug("Using macro file: %s..." % targetMacroPath)
                shutil.copyfile(localTargetMacroPath, sandbox.getID() + macroPath)
                # rpmBuildcmd += ' \'--macros=<%s>\'' % targetMacroPath
            else:
                rpmBuildcmd += ' --define \"_arch %s\"' % constants.targetArch
                rpmBuildcmd += ' --define \"_datarootdir /usr/share\"'
                rpmBuildcmd += ' --define \"__strip %s-strip\"' % constants.targetArchTuple
                rpmBuildcmd += ' --define \"__objdump %s-objdump\"' % hostTuple

            # Target should be informat of cpu-vendor-os (e.g. arm-unknown-linux)
            tupleParts = constants.targetArchTuple.split('-')
            rpmBuildcmd += ' --target=%s-%s-%s' % (tupleParts[0], tupleParts[1], tupleParts[2])
            
        rpmBuildcmd += " " + specFile

        self.logger.debug("Building rpm....")
        self.logger.debug(rpmBuildcmd)
        
        sandbox.run("uname -a", logfile = logFile, logfn = self.logger.debug)

        returnVal = sandbox.run(rpmBuildcmd, logfile = logFile, showOutput = True)

        if constants.rpmCheck and package in constants.testForceRPMS:
            if (not SPECS.getData().isCheckAvailable(package, version)) or \
                    (package in constants.listMakeCheckPkgToSkip):
                constants.testLogger.info(package + " : N/A")
            elif returnVal == 0:
                constants.testLogger.info(package + " : PASS")
            else:
                constants.testLogger.info(package + " : FAIL")

        if constants.rpmCheck:
            if returnVal != 0 and constants.rpmCheckStopOnError:
                self.logger.error("Checking rpm is failed " + specFile)
                raise Exception("RPM check failed")
        else:
            if returnVal != 0:
                self.logger.error("Building rpm is failed " + specFile)
                raise Exception("RPM build failed")

        #Extracting rpms created from log file
        listRPMFiles = []
        listSRPMFiles = []
        stageLogFile = logFile.replace(constants.topDirPath + "/LOGS", constants.logPath )
        with open(stageLogFile, 'r') as logfile:
            fileContents = logfile.readlines()
            for i in range(0, len(fileContents)):
                if re.search("^Wrote:", fileContents[i]):
                    listcontents = fileContents[i].split()
                    if ((len(listcontents) == 2) and
                            listcontents[1].strip().endswith(".rpm") and
                            "/RPMS/" in listcontents[1]):
                        listRPMFiles.append(listcontents[1])
                    if ((len(listcontents) == 2) and
                            listcontents[1].strip().endswith(".src.rpm") and
                            "/SRPMS/" in listcontents[1]):
                        listSRPMFiles.append(listcontents[1])
        return listRPMFiles, listSRPMFiles

