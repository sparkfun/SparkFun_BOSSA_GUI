from .au_action import AxAction, AxJob
from .SAMBALoader import startLoaderCommand


#--------------------------------------------------------------------------------------
# action testing
class AUxSAMBADetect(AxAction):

    ACTION_ID = "samba-detect"
    NAME = "Processor Detection"

    def __init__(self) -> None:
        super().__init__(self.ACTION_ID, self.NAME)

    def run_job(self, job:AxJob):

        try:
            sysExit, message = startLoaderCommand(job.command)
            job.message = message
            job.sysExit = sysExit

        except Exception:
            return 1

        return 0

class AUxSAMBAErase(AxAction):

    ACTION_ID = "samba-erase"
    NAME = "Erase Processor"

    def __init__(self) -> None:
        super().__init__(self.ACTION_ID, self.NAME)

    def run_job(self, job:AxJob):

        try:
            sysExit, message = startLoaderCommand(job.command)
            job.message = message
            job.sysExit = sysExit

        except Exception:
            return 1

        return 0

class AUxSAMBAProgram(AxAction):

    ACTION_ID = "samba-program"
    NAME = "Program Processor"

    def __init__(self) -> None:
        super().__init__(self.ACTION_ID, self.NAME)

    def run_job(self, job:AxJob):

        try:
            sysExit, message = startLoaderCommand(job.command)
            job.message = message
            job.sysExit = sysExit

        except Exception:
            return 1

        return 0

class AUxSAMBAVerify(AxAction):

    ACTION_ID = "samba-verify"
    NAME = "Verify Processor"

    def __init__(self) -> None:
        super().__init__(self.ACTION_ID, self.NAME)

    def run_job(self, job:AxJob):

        try:
            sysExit, message = startLoaderCommand(job.command)
            job.message = message
            job.sysExit = sysExit

        except Exception:
            return 1

        return 0

class AUxSAMBAReset(AxAction):

    ACTION_ID = "samba-reset"
    NAME = "Reset Processor"

    def __init__(self) -> None:
        super().__init__(self.ACTION_ID, self.NAME)

    def run_job(self, job:AxJob):

        try:
            sysExit, message = startLoaderCommand(job.command)
            job.message = message
            job.sysExit = sysExit

        except Exception:
            return 1

        return 0
        