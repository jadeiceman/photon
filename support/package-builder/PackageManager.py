import os
import threading
import copy
from PackageBuildDataGenerator import PackageBuildDataGenerator
from Logger import Logger
from constants import constants
import docker
from CommandUtils import CommandUtils
from PackageUtils import PackageUtils
from ToolChainUtils import ToolChainUtils
from Scheduler import Scheduler
from ThreadPool import ThreadPool
from SpecData import SPECS
from StringUtils import StringUtils
from Sandbox import Chroot, Container

class PackageManager(object):

    def __init__(self, logName=None, logPath=None, pkgBuildType="chroot"):
        if logName is None:
            logName = "PackageManager"
        if logPath is None:
            logPath = constants.logPath
        self.logName = logName
        self.logPath = logPath
        self.logLevel = constants.logLevel
        self.logger = Logger.getLogger(logName, logPath, constants.logLevel)
        self.mapCyclesToPackageList = {}
        self.mapPackageToCycle = {}
        self.sortedPackageList = []
        self.listOfPackagesAlreadyBuilt = set()
        self.pkgBuildType = pkgBuildType
        if self.pkgBuildType == "container":
            self.dockerClient = docker.from_env(version="auto")

    def buildToolChain(self):
        self.logger.debug(">>>> PackageManager buildToolChain")
        pkgCount = 0
        try:
            tUtils = ToolChainUtils()
            pkgCount = tUtils.buildCoreToolChainPackages()
        except Exception as e:
            self.logger.error("Unable to build tool chain")
            self.logger.error(e)
            raise e
        return pkgCount

    def buildToolChainPackages(self, buildThreads):
        pkgCount = self.buildToolChain()
        # Stage 2 makes sence only for native tools
        if not constants.crossCompiling:
            if self.pkgBuildType == "container":
                # Stage 1 build container
                #TODO image name constants.buildContainerImageName
                if pkgCount > 0 or not self.dockerClient.images.list(constants.buildContainerImage):
                    self._createBuildContainer(True)
            self.logger.info("Step 2 : Building stage 2 of the toolchain...")
            self.logger.info(constants.listToolChainPackages)
            self.logger.info("")
            self._buildGivenPackages(constants.listToolChainPackages, buildThreads)
            self.logger.info("The entire toolchain is now available")
            self.logger.info(45 * '-')
            self.logger.info("")
        if self.pkgBuildType == "container":
            # Stage 2 build container
            #TODO: rebuild container only if anything in listToolChainPackages was built
            self._createBuildContainer(False)

    def buildPackages(self, listPackages, buildThreads):
        self.logger.debug(">>>> PackageManager buildPackages start...")
        if constants.rpmCheck:
            constants.rpmCheck = False
            constants.addMacro("with_check", "0")
            self.buildToolChainPackages(buildThreads)
            self._buildTestPackages(buildThreads)
            constants.rpmCheck = True
            constants.addMacro("with_check", "1")
            self._buildGivenPackages(listPackages, buildThreads)
        else:
            self.buildToolChainPackages(buildThreads)
            self.logger.info("Step 3 : Building the following package(s) and dependencies...")
            self.logger.info(listPackages)
            self.logger.info("")
            self._buildGivenPackages(listPackages, buildThreads)
        self.logger.info("Package build has been completed")
        self.logger.info("")

    def _readPackageBuildData(self, listPackages):
        try:
            pkgBuildDataGen = PackageBuildDataGenerator(self.logName, self.logPath)
            self.mapCyclesToPackageList, self.mapPackageToCycle, self.sortedPackageList = (
                pkgBuildDataGen.getPackageBuildData(listPackages))

        except Exception as e:
            self.logger.exception(e)
            self.logger.error("unable to get sorted list")
            return False
        return True

    # Returns list of base package names which spec file has all subpackages built
    # Returns set of package name and version like
    # ["name1-vers1", "name2-vers2",..]
    def _readAlreadyAvailablePackages(self):
        listAvailablePackages = set()
        pkgUtils = PackageUtils(self.logName, self.logPath)
        listPackages = SPECS.getData().getListPackages()
        for package in listPackages:
            for version in SPECS.getData().getVersions(package):
                # Mark package available only if all subpackages are available
                packageIsAlreadyBuilt=True
                listRPMPackages = SPECS.getData().getRPMPackages(package, version)
                for rpmPkg in listRPMPackages:
                    if pkgUtils.findRPMFile(rpmPkg, version) is None:
                    #if pkgUtils.findRPMFile(rpmPkg, version, constants.buildArch) is None:
                        packageIsAlreadyBuilt=False
                        break;
                if packageIsAlreadyBuilt:
                    listAvailablePackages.add(package+"-"+version)

        return listAvailablePackages

    def _calculateParams(self, listPackages):
        self.mapCyclesToPackageList.clear()
        self.mapPackageToCycle.clear()
        self.sortedPackageList = []

        self.listOfPackagesAlreadyBuilt = self._readAlreadyAvailablePackages()
        if self.listOfPackagesAlreadyBuilt:
            self.logger.debug("List of already available packages:")
            self.logger.debug(self.listOfPackagesAlreadyBuilt)

        #if constants.currentArch == "arm":
        #    self.logger.debug(">>>> LOADING CUSTOM PACKAGE LIST")
        #    f = open("phase1_package_list.txt", "r")
        #    constants.customPackageList = f.read().splitlines()
        #    f.close()
        #else:
        #    listPackagesToBuild = copy.copy(listPackages)

        listPackagesToBuild = copy.copy(listPackages)

        for pkg in listPackages:
            if (pkg in self.listOfPackagesAlreadyBuilt and
                    not constants.rpmCheck and
                    pkg in listPackagesToBuild):                
                listPackagesToBuild.remove(pkg)
                #self.logger.debug(">>>> REMOVED: %s" % pkg)

        if constants.rpmCheck:
            self.sortedPackageList = listPackagesToBuild
        else:
            if not self._readPackageBuildData(listPackagesToBuild):
                return False

        if self.sortedPackageList:
            self.logger.info("List of packages yet to be built...")
            self.logger.info(str(set(self.sortedPackageList) - set(self.listOfPackagesAlreadyBuilt)))
            self.logger.info("")
            
            ## Analyze pkgs to be built, but exclude ones with python or perl dependencies
            #allStagedPkgs = []

            #stagedPkgs, remainingPkgs = self._analyzePackages(listPackages,
            #        ["python2-2.7.15", "python3-3.7.3", "perl-5.28.0", "automake-1.16.1"])

            #allStagedPkgs = allStagedPkgs + stagedPkgs

            #stagedPkgs, remainingPkgs = self._analyzePackages(listPackages,
            #        ["perl-5.28.0"],
            #        remainingPkgs,
            #        allStagedPkgs,
            #        "python_")

            #allStagedPkgs = allStagedPkgs + stagedPkgs

            ##stagedPkgs, remainingPkgs = self._analyzePackages(listPackages,
            ##        ["python2-2.7.15", "python3-3.7.3"],
            ##        remainingPkgs,
            ##        allStagedPkgs,
            ##        "perl_")

            ##allStagedPkgs = allStagedPkgs + stagedPkgs

            ## Analyze the remaining packages that have exclusions
            #if len(remainingPkgs) > 0:
            #    self.logger.debug("Remaining pkgs:\n  > %s\n\n" % "\n  > ".join(remainingPkgs))
            #    self._analyzePackages(listPackages, 
            #            None, 
            #            remainingPkgs,
            #            allStagedPkgs,
            #            "remaining_")

            #raise NameError("Done")

        return True

    def _analyzePackages(self, 
            listPackages, 
            problemDeps = None, 
            packagesToBuild = None,
            additionalPackages = None,
            prefix = None,
            packagesToFlag = ["python2-2.7.15", "python3-3.7.3", "perl-5.28.0"]):

        self.logger.debug("\n\n>>>> Analyzing packages...")

        outputDir = os.getcwd() + "/_analyzePackagesOutput"
        self.logger.debug("Creating output directory (%s)..." % outputDir)
        os.makedirs(outputDir, mode=0o777, exist_ok=True)

#        problemDeps = ["python2-2.7.15", "python3-3.7.3", "perl-5.28.0"]
        
        excludeProblemDeps = problemDeps != None

        # Use default if none specified
        if packagesToBuild == None:
            packagesToBuild = set(self.sortedPackageList) - set(self.listOfPackagesAlreadyBuilt)

        if additionalPackages == None:
            additionalPackages = set()

        if prefix == None:
            prefix = ""

        pkgBuildDataGen = PackageBuildDataGenerator(self.logName, self.logPath)
        pkgBuildDataGen.getPackageBuildData(listPackages)

        stageNum = 1
        stageDict = {}
        problemDict = {}
        while len(packagesToBuild) > 0:
            if stageNum not in stageDict.keys():
                stageDict[stageNum] = []

            nextPackagesToBuild = packagesToBuild.copy()

            for pkg in packagesToBuild:
                depListForPkg = pkgBuildDataGen.getSortListForPackage(pkg)

                # Remove itself from list
                depListForPkg.remove(pkg)
                depSet = set(depListForPkg)

                if excludeProblemDeps:
                    # Check if it has a problem dep
                    foundProblem = None
                    for problemDep in set(problemDeps):
                        if problemDep in depSet:
                            if problemDep not in problemDict.keys():
                                problemDict[problemDep] = []
                            problemDict[problemDep].append(pkg)
                            nextPackagesToBuild.remove(pkg)
                            foundProblem = problemDep
                            break

                    if foundProblem is not None:
                        self.logger.debug("Problem dep detected (%s), skipping %s..." % (foundProblem, pkg))
                        continue

                depSatisfied = True
                if len(depSet) > 0:
                    stageDeps = self._flatten(stageDict.values())
                    # For each dependency, go through the previous stage's packages and the list of already built packages 
                    # to see if the dependency pkg is there
                    for dep in depSet:
                        if (dep in (set(stageDeps) - set(stageDict[stageNum])) 
                         or dep in set(self.listOfPackagesAlreadyBuilt)
                         or dep in additionalPackages):
                            # Dep found, move on to next one
                            continue
                        else:
                            # Couldn't find dep in previous stage or already built pkgs
                            # self.logger.debug(">>> Couldn't find %s for %s" % (dep, pkg))
                            depSatisfied = False
                            break

                # If all dep pkgs have been built or will be, add it to the stage
                if depSatisfied:
                    stageDict[stageNum].append(pkg)
                    nextPackagesToBuild.remove(pkg)

            #self.logger.debug("Next packages to build (%s): %s)" % (len(nextPackagesToBuild), nextPackagesToBuild))
            self.logger.debug("\nStage %s (%s): %s\n" % (stageNum, len(stageDict[stageNum]), stageDict[stageNum]))
            packagesToBuild = nextPackagesToBuild.copy()

            # Output the stage's pkgs to a file
            if len(stageDict[stageNum]) > 0:
                  f = open(outputDir + "/%s__st%s_packages.txt" % (prefix, stageNum), "w")
                  f.write("\n".join(stageDict[stageNum]))
                  f.close()

            # Check to see if no new packages have been added to the current stage and the previous one
            # This means that the remaining pkgs have deps that weren't in the original full pkg list
            if stageNum > 1 and len(stageDict[stageNum]) == 0 and len(stageDict[stageNum-1]) == 0:
                self.logger.debug("Current stage and previous stage have no packages")

                # List the remaining packages
                if len(packagesToBuild) > 0:
                    self.logger.debug("Remaining packages to build:")
                    for pkg in packagesToBuild:
                        depListForPkg = pkgBuildDataGen.getSortListForPackage(pkg)
                        depListForPkg.remove(pkg)
                        stageDeps = self._flatten(stageDict.values())
                        if problemDeps == None:
                            problemDeps = []
                        depListForPkg = [x for x in depListForPkg if x not in stageDeps + list(self.listOfPackagesAlreadyBuilt) or x in problemDeps]

                    print("%s\n  > %s" % (pkg, "\n  > ".join(depListForPkg)))
                break

            stageNum += 1

        stageList = []
        for stageNum, pkgList in stageDict.items():
            for pkg in pkgList:
                flaggedDeps = list(set(packagesToFlag) & set(pkgBuildDataGen.getSortListForPackage(pkg)))
                stageList.append("%s,%s,%s" % (pkg, stageNum, "/".join(flaggedDeps)))

        f = open(outputDir + "/%s__st_all_packages.csv" % prefix, "w")
        f.write("\n".join(stageList))
        f.close()

        return self._flatten(stageDict.values()), list(packagesToBuild) + self._flatten(problemDict.values())

    def _flatten(self, listOfLists):
        return [item for sublist in listOfLists for item in sublist]

    def _buildTestPackages(self, buildThreads):
        self.buildToolChain()
        self._buildGivenPackages(constants.listMakeCheckRPMPkgtoInstall, buildThreads)

    def _initializeThreadPool(self, statusEvent):
        ThreadPool.clear()
        ThreadPool.mapPackageToCycle = self.mapPackageToCycle
        ThreadPool.logger = self.logger
        ThreadPool.statusEvent = statusEvent
        ThreadPool.pkgBuildType = self.pkgBuildType

    def _initializeScheduler(self, statusEvent):
        Scheduler.setLog(self.logName, self.logPath, self.logLevel)
        Scheduler.setParams(self.sortedPackageList, self.listOfPackagesAlreadyBuilt)
        Scheduler.setEvent(statusEvent)
        Scheduler.stopScheduling = False

    def _buildGivenPackages(self, listPackages, buildThreads):
        # Extend listPackages from ["name1", "name2",..] to ["name1-vers1", "name2-vers2",..]
        listPackageNamesAndVersions=set()
        for pkg in listPackages:
            base = SPECS.getData().getSpecName(pkg)
            for version in SPECS.getData().getVersions(base):
                listPackageNamesAndVersions.add(base+"-"+version)

        returnVal = self._calculateParams(listPackageNamesAndVersions)
        if not returnVal:
            self.logger.error("Unable to set parameters. Terminating the package manager.")
            raise Exception("Unable to set parameters")

        statusEvent = threading.Event()
        self._initializeScheduler(statusEvent)
        self._initializeThreadPool(statusEvent)

        for i in range(0, buildThreads):
            workerName = "WorkerThread" + str(i)
            self.logger.debug(">>>> Starting worker thread: %s", workerName)
            ThreadPool.addWorkerThread(workerName)
            ThreadPool.startWorkerThread(workerName)

        statusEvent.wait()
        Scheduler.stopScheduling = True
        self.logger.debug("Waiting for all remaining worker threads")
        ThreadPool.join_all()

        setFailFlag = False
        allPackagesBuilt = False
        if Scheduler.isAnyPackagesFailedToBuild():
            setFailFlag = True

        if Scheduler.isAllPackagesBuilt():
            allPackagesBuilt = True

        if setFailFlag:
            self.logger.error("Some of the packages failed:")
            self.logger.error(Scheduler.listOfFailedPackages)
            raise Exception("Failed during building package")

        if not setFailFlag:
            if allPackagesBuilt:
                self.logger.debug("All packages built successfully")
            else:
                self.logger.error("Build stopped unexpectedly.Unknown error.")
                raise Exception("Unknown error")

    def _createBuildContainer(self, usePublishedRPMs):
        self.logger.debug("Generating photon build container..")
        try:
            #TODO image name constants.buildContainerImageName
            self.dockerClient.images.remove(constants.buildContainerImage, force=True)
        except Exception as e:
            #TODO - better handling
            self.logger.debug("Photon build container image not found.")

        # Create toolchain chroot and install toolchain RPMs
        chroot = None
        try:
            #TODO: constants.tcrootname
            chroot = Chroot(self.logger)
            chroot.create("toolchain-chroot")
            tcUtils = ToolChainUtils("toolchain-chroot", self.logPath)
            tcUtils.installToolchainRPMS(chroot, usePublishedRPMS=usePublishedRPMs)
        except Exception as e:
            if chroot:
                chroot.destroy()
            raise e
        self.logger.debug("createBuildContainer: " + chroot.getID())

        # Create photon build container using toolchain chroot
        chroot.unmountAll()
        #TODO: Coalesce logging
        cmdUtils = CommandUtils()
        cmd = "cd " + chroot.getID() + " && tar -czf ../tcroot.tar.gz ."
        cmdUtils.runCommandInShell(cmd, logfn=self.logger.debug)
        cmd = "mv " + chroot.getID() + "/../tcroot.tar.gz ."
        cmdUtils.runCommandInShell(cmd, logfn=self.logger.debug)
        #TODO: Container name, docker file name from constants.
        self.dockerClient.images.build(tag=constants.buildContainerImage,
                                       path=".",
                                       rm=True,
                                       dockerfile="Dockerfile.photon_build_container")

        # Cleanup
        cmd = "rm -f ./tcroot.tar.gz"
        cmdUtils.runCommandInShell(cmd, logfn=self.logger.debug)
        chroot.destroy()
        self.logger.debug("Photon build container successfully created.")
